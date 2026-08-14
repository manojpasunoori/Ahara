from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.api.profile import router as profile_router
from app.api.context import router as context_router
from app.api.location import router as location_router
from app.api.restaurants import router as restaurants_router
from app.core.cache import create_redis_client
from app.core.config import get_settings
from app.core.database import create_database_engine
from app.services.health import HealthService


@asynccontextmanager
async def lifespan(application: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    application.state.health_service = HealthService(
        database_engine=create_database_engine(),
        redis_client=create_redis_client(),
        version=settings.api_version,
    )
    yield
    application.state.health_service.database_engine.dispose()
    application.state.health_service.redis_client.close()


def create_app() -> FastAPI:
    settings = get_settings()
    application = FastAPI(title="Ahara API", version=settings.api_version, lifespan=lifespan)
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "OPTIONS"],
        allow_headers=["Content-Type"],
    )
    application.include_router(router)
    application.include_router(profile_router)
    application.include_router(context_router)
    application.include_router(location_router)
    application.include_router(restaurants_router)
    return application


def get_app_health_service() -> HealthService:
    return app.state.health_service


app = create_app()
