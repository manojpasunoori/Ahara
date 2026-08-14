from __future__ import annotations

from math import asin, cos, radians, sin, sqrt

EARTH_RADIUS_MILES = 3_958.8


def haversine_miles(origin_latitude: float, origin_longitude: float, destination_latitude: float, destination_longitude: float) -> float:
    """Return the great-circle distance between two coordinates in miles."""
    latitude_delta = radians(destination_latitude - origin_latitude)
    longitude_delta = radians(destination_longitude - origin_longitude)
    arc = sin(latitude_delta / 2) ** 2 + cos(radians(origin_latitude)) * cos(radians(destination_latitude)) * sin(longitude_delta / 2) ** 2
    return EARTH_RADIUS_MILES * 2 * asin(sqrt(arc))