"""Top-level API router configuration."""

from fastapi import APIRouter

from app.api.routes.health import router as health_router
from app.api.routes.image_size import router as image_size_router
from app.api.routes.patterns import router as patterns_router

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(image_size_router)
api_router.include_router(patterns_router)
