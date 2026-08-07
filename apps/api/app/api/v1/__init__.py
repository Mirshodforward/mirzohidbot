from fastapi import APIRouter

from app.api.v1 import admin, auth, stores

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth.router)
api_router.include_router(stores.router)
api_router.include_router(admin.router)

__all__ = ["api_router"]
