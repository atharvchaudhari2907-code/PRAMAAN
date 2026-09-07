from fastapi import APIRouter
from app.api.auth import router as auth_router
from app.api.users import router as users_router
from app.api.applications import router as applications_router
from app.api.documents import router as documents_router
from app.api.standards import router as standards_router
from app.api.health import router as health_router
from app.api.verification import router as verification_router
from app.api.voice import router as voice_router
from app.api.vision import router as vision_router
from app.api.iot import router as iot_router

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(auth_router)
api_router.include_router(users_router)
api_router.include_router(applications_router)
api_router.include_router(documents_router)
api_router.include_router(standards_router)
api_router.include_router(verification_router)
api_router.include_router(voice_router)
api_router.include_router(vision_router)
api_router.include_router(iot_router)

__all__ = ["api_router"]

