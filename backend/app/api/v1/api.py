from fastapi import APIRouter
from app.api.v1.endpoints import wardrobe, health, outfits

api_router = APIRouter()

api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(wardrobe.router, prefix="/wardrobe", tags=["wardrobe"])
api_router.include_router(outfits.router, prefix="/outfits", tags=["outfits"])
