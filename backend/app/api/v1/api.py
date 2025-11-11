from fastapi import APIRouter
from app.api.v1.endpoints import wardrobe, health

api_router = APIRouter()

api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(wardrobe.router, prefix="/wardrobe", tags=["wardrobe"])
