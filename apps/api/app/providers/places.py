from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

import httpx

from app.services.restaurants import haversine_miles


class PlacesProviderError(RuntimeError):
    """A provider could not fulfil a restaurant search."""


class PlacesProviderUnavailableError(PlacesProviderError):
    """A provider is intentionally unavailable because it is not configured."""


@dataclass(frozen=True)
class Restaurant:
    id: str
    provider: str
    name: str
    categories: list[str]
    latitude: float
    longitude: float
    address: str | None
    city: str | None
    distance_miles: float
    rating: float | None = None
    review_count: int | None = None
    price_level: int | None = None
    open_now: bool | None = None
    website: str | None = None

    def as_dict(self) -> dict[str, object]:
        return {"id": self.id, "provider": self.provider, "name": self.name, "categories": self.categories, "latitude": self.latitude, "longitude": self.longitude, "address": self.address, "city": self.city, "distance_miles": round(self.distance_miles, 2), "rating": self.rating, "review_count": self.review_count, "price_level": self.price_level, "open_now": self.open_now, "website": self.website}


class PlacesProvider(ABC):
    name: str

    @abstractmethod
    def search_restaurants(self, latitude: float, longitude: float, radius_miles: float, query: str, limit: int) -> list[Restaurant]:
        """Return normalized factual candidates around a coordinate."""


_DEMO_FIXTURES = (
    ("saffron-leaf", "Saffron Leaf", ["South Indian", "Indian"], 32.7381, -97.1054, "112 Garden Way"),
    ("biryani-hearth", "Biryani Hearth", ["Biryani", "Indian"], 32.7420, -97.1008, "215 Garden Way"),
    ("juniper-chai", "Juniper Chai House", ["Chai", "Snacks"], 32.7319, -97.1130, "38 Garden Way"),
    ("cactus-table", "Cactus Table", ["Mexican"], 32.7279, -97.1039, "330 Garden Way"),
    ("moonlit-ramen", "Moonlit Ramen Bar", ["Ramen", "Japanese"], 32.7464, -97.1163, "449 Garden Way"),
    ("olive-meridian", "Olive Meridian", ["Mediterranean"], 32.7255, -97.1194, "501 Garden Way"),
)


class DemoPlacesProvider(PlacesProvider):
    """Deterministic Arlington fixtures for explicit demo mode."""
    name = "demo"

    def search_restaurants(self, latitude: float, longitude: float, radius_miles: float, query: str, limit: int) -> list[Restaurant]:
        needle = query.strip().casefold()
        matches: list[Restaurant] = []
        for fixture_id, name, categories, place_latitude, place_longitude, address in _DEMO_FIXTURES:
            haystack = " ".join([name, *categories]).casefold()
            if needle and needle not in haystack:
                continue
            distance = haversine_miles(latitude, longitude, place_latitude, place_longitude)
            if distance <= radius_miles:
                matches.append(Restaurant(id=fixture_id, provider=self.name, name=name, categories=categories, latitude=place_latitude, longitude=place_longitude, address=address, city="Arlington", distance_miles=distance))
        return matches[:limit]


class FoursquarePlacesProvider(PlacesProvider):
    """Foursquare Places API adapter; no raw provider payloads leak outward."""
    name = "foursquare"
    endpoint = "https://api.foursquare.com/v3/places/search"

    def __init__(self, api_key: str, client: httpx.Client | None = None) -> None:
        if not api_key:
            raise PlacesProviderUnavailableError("Live restaurant search is not configured.")
        self._api_key = api_key
        self._client = client

    def search_restaurants(self, latitude: float, longitude: float, radius_miles: float, query: str, limit: int) -> list[Restaurant]:
        params: dict[str, str | int] = {"ll": f"{latitude},{longitude}", "radius": int(radius_miles * 1609.344), "limit": limit}
        if query:
            params["query"] = query
        if self._client is None:
            with httpx.Client(timeout=8.0) as client:
                response = client.get(self.endpoint, headers={"Authorization": self._api_key}, params=params)
        else:
            response = self._client.get(self.endpoint, headers={"Authorization": self._api_key}, params=params)
        response.raise_for_status()
        payload = response.json()
        results = payload.get("results", []) if isinstance(payload, dict) else []
        if not isinstance(results, list):
            return []
        normalized: list[Restaurant] = []
        for result in results:
            restaurant = self._normalize(result, latitude, longitude)
            if restaurant is not None:
                normalized.append(restaurant)
        return normalized

    def _normalize(self, result: object, latitude: float, longitude: float) -> Restaurant | None:
        if not isinstance(result, dict):
            return None
        identifier, name, geocodes = result.get("fsq_id"), result.get("name"), result.get("geocodes")
        main = geocodes.get("main") if isinstance(geocodes, dict) else None
        if not isinstance(identifier, str) or not isinstance(name, str) or not isinstance(main, dict):
            return None
        place_latitude, place_longitude = main.get("latitude"), main.get("longitude")
        if not isinstance(place_latitude, (int, float)) or not isinstance(place_longitude, (int, float)):
            return None
        categories = result.get("categories")
        names = [item["name"] for item in categories if isinstance(item, dict) and isinstance(item.get("name"), str)] if isinstance(categories, list) else []
        location = result.get("location")
        return Restaurant(id=identifier, provider=self.name, name=name, categories=names, latitude=float(place_latitude), longitude=float(place_longitude), address=location.get("formatted_address") if isinstance(location, dict) and isinstance(location.get("formatted_address"), str) else None, city=location.get("locality") if isinstance(location, dict) and isinstance(location.get("locality"), str) else None, distance_miles=haversine_miles(latitude, longitude, float(place_latitude), float(place_longitude)))