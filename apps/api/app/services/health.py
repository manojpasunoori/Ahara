from redis import Redis
from sqlalchemy.engine import Engine

from app.core.cache import check_redis_connection
from app.core.database import check_database_connection
from app.schemas.health import HealthResponse


class HealthService:
    """Reports the connectivity status of runtime dependencies."""

    def __init__(self, database_engine: Engine, redis_client: Redis, version: str) -> None:
        self.database_engine = database_engine
        self.redis_client = redis_client
        self.version = version

    def get_health(self) -> HealthResponse:
        database = self._database_status()
        redis = self._redis_status()
        status = "healthy" if database == "healthy" and redis == "healthy" else "degraded"
        return HealthResponse(status=status, version=self.version, database=database, redis=redis)

    def _database_status(self) -> str:
        try:
            check_database_connection(self.database_engine)
        except Exception:
            return "unhealthy"
        return "healthy"

    def _redis_status(self) -> str:
        try:
            check_redis_connection(self.redis_client)
        except Exception:
            return "unhealthy"
        return "healthy"
