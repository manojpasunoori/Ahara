from typing import Literal

from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: Literal["healthy", "degraded", "unhealthy"]
    service: str = "ahara-api"
    version: str
    database: Literal["healthy", "unhealthy"]
    redis: Literal["healthy", "unhealthy"]
