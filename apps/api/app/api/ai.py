from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.core.config import get_settings
from app.providers.llm import LLMProviderResponseError, LLMProviderTimeoutError, LLMProviderUnavailableError, OllamaLLMProvider
from app.schemas.intent import FoodIntent, IntentRequest
from app.services.intent import IntentExtractionService

router = APIRouter(prefix="/api/v1/ai", tags=["ai"])


class AIHealthResponse(BaseModel):
    status: str
    provider: str
    model: str


def _provider() -> OllamaLLMProvider:
    settings = get_settings()
    if settings.llm_provider.casefold() != "ollama":
        raise LLMProviderUnavailableError("The configured LLM provider is unavailable.")
    return OllamaLLMProvider(settings.ollama_base_url, settings.ollama_model, settings.ollama_timeout_seconds)


def _service() -> IntentExtractionService:
    return IntentExtractionService(_provider())


@router.get("/health", response_model=AIHealthResponse)
def ai_health() -> AIHealthResponse:
    provider = _provider()
    if provider.is_available():
        return AIHealthResponse(status="healthy", provider=provider.name, model=provider.model)
    raise HTTPException(status_code=503, detail=AIHealthResponse(status="unavailable", provider=provider.name, model=provider.model).model_dump())


@router.post("/intent", response_model=FoodIntent)
def extract_intent(request: IntentRequest) -> FoodIntent:
    try:
        return _service().extract(request.message)
    except LLMProviderTimeoutError as error:
        raise HTTPException(status_code=504, detail="Ahara's local AI took too long to respond.") from error
    except LLMProviderUnavailableError as error:
        raise HTTPException(status_code=503, detail="Ahara's local AI is unavailable right now.") from error
    except LLMProviderResponseError as error:
        raise HTTPException(status_code=502, detail="Ahara's local AI returned an invalid intent response.") from error