from fastapi.testclient import TestClient

from app.api.routes import get_health_service
from app.main import app
from app.schemas.health import HealthResponse


class HealthyService:
    def get_health(self) -> HealthResponse:
        return HealthResponse(status="healthy", version="0.1.0", database="healthy", redis="healthy")


def test_root_endpoint() -> None:
    with TestClient(app) as client:
        response = client.get("/")
    assert response.status_code == 200
    assert response.json()["service"] == "ahara-api"


def test_api_health_response_structure() -> None:
    app.dependency_overrides[get_health_service] = HealthyService
    try:
        with TestClient(app) as client:
            response = client.get("/api/v1/health")
    finally:
        app.dependency_overrides.clear()
    assert response.status_code == 200
    assert response.json() == {"status": "healthy", "service": "ahara-api", "version": "0.1.0", "database": "healthy", "redis": "healthy"}


def test_application_imports() -> None:
    assert app.title == "Ahara API"
