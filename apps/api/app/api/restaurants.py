from __future__ import annotations

import json

import httpx
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from app.core.cache import create_redis_client
from app.core.config import get_settings
from app.providers.places import DemoPlacesProvider, FoursquarePlacesProvider, PlacesProvider, PlacesProviderUnavailableError


class RestaurantResponse(BaseModel):
    id: str
    provider: str
    name: str
    categories: list[str]
    latitude: float
    longitude: float
    address: str | None
    city: str | None
    distance_miles: float
    rating: float | None
    review_count: int | None
    price_level: int | None
    open_now: bool | None
    website: str | None


router = APIRouter(prefix="/api/v1", tags=["restaurants"])


def _provider() -> PlacesProvider:
    settings = get_settings()
    if settings.ahara_mode.casefold() == "demo":
        return DemoPlacesProvider()
    if settings.places_provider.casefold() != "foursquare":
        raise PlacesProviderUnavailableError("Live restaurant search is not configured.")
    if not settings.foursquare_api_key.strip():
        return DemoPlacesProvider()
    return FoursquarePlacesProvider(settings.foursquare_api_key)


def _cache_key(provider: str, latitude: float, longitude: float, radius_miles: float, query: str, limit: int) -> str:
    normalized_query = " ".join(query.casefold().split()) or "nearby"
    return f"restaurants:{provider}:{latitude:.2f}:{longitude:.2f}:{radius_miles:g}:{normalized_query}:{limit}"


@router.get("/restaurants/search", response_model=list[RestaurantResponse])
def search_restaurants(latitude: float = Query(ge=-90, le=90), longitude: float = Query(ge=-180, le=180), radius_miles: float = Query(default=10, gt=0, le=50), query: str = Query(default="", max_length=120), cuisine: str = Query(default="", max_length=120), limit: int = Query(default=10, ge=1, le=25)) -> list[RestaurantResponse]:
    search_query = query.strip() or cuisine.strip()
    try:
        provider = _provider()
    except PlacesProviderUnavailableError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error
    cache_key = _cache_key(provider.name, latitude, longitude, radius_miles, search_query, limit)
    cache = None
    try:
        cache = create_redis_client()
        cached = cache.get(cache_key)
        if cached:
            return [RestaurantResponse.model_validate(item) for item in json.loads(cached)]
    except Exception:
        cache = None
    try:
        records = provider.search_restaurants(latitude, longitude, radius_miles, search_query, limit)
    except httpx.TimeoutException as error:
        raise HTTPException(status_code=503, detail="Live restaurant search timed out.") from error
    except httpx.HTTPError as error:
        raise HTTPException(status_code=503, detail="Live restaurant search is unavailable right now.") from error
    response = [RestaurantResponse.model_validate(record.as_dict()) for record in records]
    if cache is not None:
        try:
            cache.setex(cache_key, 600, json.dumps([item.model_dump() for item in response]))
        except Exception:
            pass
    return response