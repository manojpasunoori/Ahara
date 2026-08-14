from __future__ import annotations

import json
import httpx
import pytest
from fastapi.testclient import TestClient
from app.api import restaurants as restaurant_api
from app.main import app
from app.providers.places import DemoPlacesProvider, FoursquarePlacesProvider, PlacesProviderUnavailableError, Restaurant
from app.services.restaurants import haversine_miles

ARLINGTON = (32.73569, -97.10807)

def test_haversine_known_coordinate_example() -> None:
    assert haversine_miles(0, 0, 0, 1) == pytest.approx(69.09, abs=0.1)

@pytest.mark.parametrize("query,expected", [("South Indian", "Saffron Leaf"), ("biryani", "Biryani Hearth"), ("CHAI", "Juniper Chai House"), ("ramen", "Moonlit Ramen Bar"), ("mediterranean", "Olive Meridian")])
def test_demo_provider_filters_case_insensitively(query: str, expected: str) -> None:
    records = DemoPlacesProvider().search_restaurants(*ARLINGTON, 10, query, 10)
    assert [record.name for record in records] == [expected]
    assert records[0].distance_miles > 0 and records[0].rating is None

def test_demo_provider_returns_no_match() -> None:
    assert DemoPlacesProvider().search_restaurants(*ARLINGTON, 10, "something-that-does-not-exist", 10) == []

def test_foursquare_normalizes_multiple_categories_and_missing_fields() -> None:
    payload = {"results": [{"fsq_id": "abc", "name": "Test Place", "categories": [{"name": "Indian"}, {"name": "South Indian"}], "geocodes": {"main": {"latitude": 32.74, "longitude": -97.1}}, "location": {"formatted_address": "1 Test Way", "locality": "Arlington"}}]}
    provider = FoursquarePlacesProvider("test-key", client=httpx.Client(transport=httpx.MockTransport(lambda _: httpx.Response(200, json=payload))))
    record = provider.search_restaurants(*ARLINGTON, 10, "South Indian", 10)[0]
    assert record.categories == ["Indian", "South Indian"] and record.address == "1 Test Way"
    assert record.rating is None and record.website is None and record.open_now is None

@pytest.mark.parametrize("payload", [{"results": []}, {"results": [{}]}, {"results": "bad"}])
def test_foursquare_handles_empty_or_partial_results(payload: dict[str, object]) -> None:
    provider = FoursquarePlacesProvider("test-key", client=httpx.Client(transport=httpx.MockTransport(lambda _: httpx.Response(200, json=payload))))
    assert provider.search_restaurants(*ARLINGTON, 10, "test", 10) == []

def test_foursquare_timeout_propagates() -> None:
    def fail(_: httpx.Request) -> httpx.Response: raise httpx.TimeoutException("timeout")
    provider = FoursquarePlacesProvider("test-key", client=httpx.Client(transport=httpx.MockTransport(fail)))
    with pytest.raises(httpx.TimeoutException): provider.search_restaurants(*ARLINGTON, 10, "test", 10)

def test_foursquare_http_error_propagates() -> None:
    provider = FoursquarePlacesProvider("test-key", client=httpx.Client(transport=httpx.MockTransport(lambda _: httpx.Response(500))))
    with pytest.raises(httpx.HTTPStatusError): provider.search_restaurants(*ARLINGTON, 10, "test", 10)

def test_missing_key_is_cleanly_unavailable() -> None:
    with pytest.raises(PlacesProviderUnavailableError): FoursquarePlacesProvider("")

class FakeProvider:
    name = "test"
    def __init__(self) -> None: self.calls = 0
    def search_restaurants(self, latitude: float, longitude: float, radius_miles: float, query: str, limit: int) -> list[Restaurant]:
        self.calls += 1
        return [Restaurant("one", "test", "One", ["Indian"], latitude, longitude, None, "Arlington", 1.0)]

class FakeCache:
    def __init__(self, value: str | None = None, get_error: bool = False, set_error: bool = False) -> None:
        self.value, self.get_error, self.set_error = value, get_error, set_error; self.writes: list[tuple[str, int, str]] = []
    def get(self, _: str) -> str | None:
        if self.get_error: raise RuntimeError("redis read failed")
        return self.value
    def setex(self, key: str, ttl: int, value: str) -> None:
        if self.set_error: raise RuntimeError("redis write failed")
        self.writes.append((key, ttl, value))

def _client(monkeypatch: pytest.MonkeyPatch, provider: FakeProvider, cache: FakeCache) -> TestClient:
    monkeypatch.setattr(restaurant_api, "_provider", lambda: provider); monkeypatch.setattr(restaurant_api, "create_redis_client", lambda: cache)
    return TestClient(app)

def test_restaurant_cache_miss_calls_provider_and_writes(monkeypatch: pytest.MonkeyPatch) -> None:
    provider, cache = FakeProvider(), FakeCache()
    response = _client(monkeypatch, provider, cache).get("/api/v1/restaurants/search?latitude=32.73&longitude=-97.10&query=indian")
    assert response.status_code == 200 and provider.calls == 1 and cache.writes[0][1] == 600

def test_restaurant_cache_hit_skips_provider(monkeypatch: pytest.MonkeyPatch) -> None:
    cached = json.dumps([Restaurant("one", "test", "One", ["Indian"], 32.7, -97.1, None, "Arlington", 1.0).as_dict()])
    provider, cache = FakeProvider(), FakeCache(cached)
    response = _client(monkeypatch, provider, cache).get("/api/v1/restaurants/search?latitude=32.73&longitude=-97.10")
    assert response.status_code == 200 and provider.calls == 0

def test_redis_read_failure_falls_back_to_provider(monkeypatch: pytest.MonkeyPatch) -> None:
    provider = FakeProvider(); response = _client(monkeypatch, provider, FakeCache(get_error=True)).get("/api/v1/restaurants/search?latitude=32.73&longitude=-97.10")
    assert response.status_code == 200 and provider.calls == 1

def test_redis_write_failure_does_not_break_search(monkeypatch: pytest.MonkeyPatch) -> None:
    provider = FakeProvider(); response = _client(monkeypatch, provider, FakeCache(set_error=True)).get("/api/v1/restaurants/search?latitude=32.73&longitude=-97.10")
    assert response.status_code == 200 and provider.calls == 1

@pytest.mark.parametrize("params", ["latitude=91&longitude=0", "latitude=0&longitude=181", "latitude=0&longitude=0&radius_miles=0", "latitude=0&longitude=0&radius_miles=51", "latitude=0&longitude=0&limit=0", "latitude=0&longitude=0&limit=26"])
def test_search_validation(params: str) -> None:
    assert TestClient(app).get(f"/api/v1/restaurants/search?{params}").status_code == 422

def test_live_missing_key_returns_clean_503(monkeypatch: pytest.MonkeyPatch) -> None:
    def unavailable() -> FakeProvider: raise PlacesProviderUnavailableError("Live restaurant search is not configured.")
    monkeypatch.setattr(restaurant_api, "_provider", unavailable)
    response = TestClient(app).get("/api/v1/restaurants/search?latitude=32.73&longitude=-97.10")
    assert response.status_code == 503 and response.json()["detail"] == "Live restaurant search is not configured."

def test_provider_timeout_returns_clean_503(monkeypatch: pytest.MonkeyPatch) -> None:
    class TimeoutProvider(FakeProvider):
        def search_restaurants(self, *args: object) -> list[Restaurant]: raise httpx.TimeoutException("timeout")
    monkeypatch.setattr(restaurant_api, "_provider", TimeoutProvider); monkeypatch.setattr(restaurant_api, "create_redis_client", lambda: FakeCache())
    assert TestClient(app).get("/api/v1/restaurants/search?latitude=32.73&longitude=-97.10").status_code == 503

def test_provider_http_failure_returns_clean_503(monkeypatch: pytest.MonkeyPatch) -> None:
    class ErrorProvider(FakeProvider):
        def search_restaurants(self, *args: object) -> list[Restaurant]:
            request = httpx.Request("GET", "https://example.test")
            raise httpx.HTTPStatusError("bad gateway", request=request, response=httpx.Response(502, request=request))
    monkeypatch.setattr(restaurant_api, "_provider", ErrorProvider); monkeypatch.setattr(restaurant_api, "create_redis_client", lambda: FakeCache())
    assert TestClient(app).get("/api/v1/restaurants/search?latitude=32.73&longitude=-97.10").status_code == 503