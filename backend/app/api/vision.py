from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.middleware.auth_middleware import get_current_user
from app.models.user import User
from app.services.application_service import ApplicationService
from app.services.vision_provider import VisionAnalysisResult, get_vision_provider

router = APIRouter(prefix="/applications", tags=["Computer Vision & Product Verification"])


@router.post("/{id}/vision/analyze", response_model=VisionAnalysisResult)
async def analyze_product_image(
    id: str,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Analyzes product photograph using YOLOv8 computer vision model.
    Detects BIS Standard Mark (ISI logo), rating plates, and physical enclosures for compliance evidence.
    """
    app_service = ApplicationService(db)
    await app_service.get_application(id, current_user.id)

    content = await file.read()
    if not content:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Uploaded image is empty")

    provider = get_vision_provider()
    return await provider.analyze_image(content, file.filename or "product_image.jpg")
