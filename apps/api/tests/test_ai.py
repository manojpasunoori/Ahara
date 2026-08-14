from __future__ import annotations

import httpx
import pytest
from fastapi.testclient import TestClient

from app.api import ai as ai_api
from app.main import app
from app.providers.llm import LLMProviderResponseError, LLMProviderTimeoutError, LLMProviderUnavailableError, OllamaLLMProvider
from app.schemas.intent import FoodIntent
from app.services.intent import IntentExtractionService


class FakeProvider:
    name = "fake"
    def __init__(self, values: list[dict[str, object]]) -> None: self.values, self.calls = values, 0
    def generate_structured(self, system_prompt: str, user_message: str, schema: dict[str, object]) -> dict[str, object]: self.calls += 1; return self.values.pop(0)


def test_food_intent_validates_budget_range() -> None:
    with pytest.raises(ValueError): FoodIntent(budget_min=25, budget_max=20)


@pytest.mark.parametrize("raw,field,expected", [({"cuisines": ["South Indian"], "spice_preference": "spicy"}, "spice_preference", "spicy"), ({"food_terms": ["biryani"], "budget_max": 20}, "budget_max", None), ({"mood": "tired", "distance_preference": "nearby"}, "mood", "tired"), ({"occasion": "date"}, "occasion", "date"), ({"cuisines": ["Thai"], "dietary_constraints": ["vegetarian"], "dining_mode": "delivery"}, "dining_mode", "delivery")])
def test_intent_service_validates_expected_concepts(raw: dict[str, object], field: str, expected: object) -> None:
    value = getattr(IntentExtractionService(FakeProvider([raw])).extract("sample"), field)
    actual = value.value if hasattr(value, "value") else value
    assert actual == expected


def test_intent_service_retries_once_for_schema_error() -> None:
    provider = FakeProvider([{"spice_preference": "volcanic"}, {"spice_preference": "spicy"}])
    assert IntentExtractionService(provider).extract("spicy food").spice_preference.value == "spicy" and provider.calls == 2


def test_intent_service_raises_after_second_schema_error() -> None:
    with pytest.raises(LLMProviderResponseError): IntentExtractionService(FakeProvider([{"spice_preference": "volcanic"}, {"spice_preference": "invalid"}])).extract("food")


def test_ollama_provider_returns_structured_json() -> None:
    payload = {"message": {"content": '{"cuisines":["Thai"],"dining_mode":"delivery"}'}}
    provider = OllamaLLMProvider("http://ollama.test", "qwen3:8b", 1, httpx.Client(transport=httpx.MockTransport(lambda _: httpx.Response(200, json=payload))))
    assert provider.generate_structured("system", "thai", FoodIntent.model_json_schema())["cuisines"] == ["Thai"]


@pytest.mark.parametrize("payload", [{"message": {"content": "not-json"}}, {"message": {"content": "[]"}}, {"unexpected": True}])
def test_ollama_provider_rejects_invalid_structured_output(payload: dict[str, object]) -> None:
    provider = OllamaLLMProvider("http://ollama.test", "qwen3:8b", 1, httpx.Client(transport=httpx.MockTransport(lambda _: httpx.Response(200, json=payload))))
    with pytest.raises(LLMProviderResponseError): provider.generate_structured("system", "food", FoodIntent.model_json_schema())


def test_ollama_timeout_is_controlled() -> None:
    provider = OllamaLLMProvider("http://ollama.test", "qwen3:8b", 1, httpx.Client(transport=httpx.MockTransport(lambda _: (_ for _ in ()).throw(httpx.TimeoutException("timeout")))))
    with pytest.raises(LLMProviderTimeoutError): provider.generate_structured("system", "food", FoodIntent.model_json_schema())


def test_ollama_connection_failure_is_controlled() -> None:
    provider = OllamaLLMProvider("http://ollama.test", "qwen3:8b", 1, httpx.Client(transport=httpx.MockTransport(lambda _: httpx.Response(503))))
    with pytest.raises(LLMProviderUnavailableError): provider.generate_structured("system", "food", FoodIntent.model_json_schema())


def test_ai_endpoint_rejects_blank_message() -> None:
    assert TestClient(app).post("/api/v1/ai/intent", json={"message": "   "}).status_code == 422


def test_ai_endpoint_returns_intent(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(ai_api, "_service", lambda: IntentExtractionService(FakeProvider([{"cuisines": ["South Indian"], "spice_preference": "spicy"}])))
    response = TestClient(app).post("/api/v1/ai/intent", json={"message": "spicy south indian"})
    assert response.status_code == 200 and response.json()["cuisines"] == ["South Indian"]


def test_ai_endpoint_maps_timeout(monkeypatch: pytest.MonkeyPatch) -> None:
    class TimeoutService:
        def extract(self, _: str) -> FoodIntent: raise LLMProviderTimeoutError("timeout")
    monkeypatch.setattr(ai_api, "_service", lambda: TimeoutService())
    assert TestClient(app).post("/api/v1/ai/intent", json={"message": "food"}).status_code == 504


def test_ai_health_unavailable(monkeypatch: pytest.MonkeyPatch) -> None:
    class OfflineProvider:
        name, model = "ollama", "qwen3:8b"
        def is_available(self) -> bool: return False
    monkeypatch.setattr(ai_api, "_provider", lambda: OfflineProvider())
    assert TestClient(app).get("/api/v1/ai/health").status_code == 503

def test_explicit_hard_constraints_do_not_trigger_a_second_llm_call() -> None:
    provider = FakeProvider([{"cuisines": ["Thai"], "dietary_constraints": ["vegetarian"]}])
    intent = IntentExtractionService(provider).extract(
        "Vegetarian Thai food delivered for Netflix night."
    )
    assert intent.cuisines == ["Thai"]
    assert intent.dining_mode.value == "delivery"
    assert intent.dietary_constraints == ["vegetarian"]
    assert provider.calls == 1

@pytest.mark.parametrize(
    ("message", "raw", "field", "expected"),
    [
        (
            "I want spicy South Indian food under $25.",
            {"cuisines": ["South Indian"], "spice_preference": "spicy", "budget_max": 25},
            "budget_max",
            25,
        ),
        (
            "Biryani pickup, within 5 miles.",
            {"food_terms": ["biryani"], "dining_mode": "pickup", "distance_preference": "very_near"},
            "dining_mode",
            "pickup",
        ),
        ("Mexican.", {"cuisines": ["Mexican"]}, "cuisines", ["Mexican"]),
        ("I'm tired.", {"mood": "tired"}, "cuisines", []),
    ],
)
def test_explicit_fact_examples_remain_model_owned(
    message: str,
    raw: dict[str, object],
    field: str,
    expected: object,
) -> None:
    intent = IntentExtractionService(FakeProvider([raw])).extract(message)
    value = getattr(intent, field)
    actual = value.value if hasattr(value, "value") else value
    assert actual == expected