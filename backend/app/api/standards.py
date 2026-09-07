from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.standard import StandardDetailResponse, StandardResponse
from app.services.standard_service import StandardService

router = APIRouter(prefix="/standards", tags=["Standards Knowledge Base"])


@router.get("", response_model=List[StandardResponse])
async def list_standards(db: AsyncSession = Depends(get_db)):
    """Lists available verified Indian Standards in the knowledge base."""
    service = StandardService(db)
    standards = await service.list_standards()
    return [StandardResponse.model_validate(s) for s in standards]


@router.get("/{standard_id:path}", response_model=StandardDetailResponse)
async def get_standard_details(standard_id: str, db: AsyncSession = Depends(get_db)):
    """Retrieves full specification and clause hierarchy for a given Indian Standard."""
    service = StandardService(db)
    standard = await service.get_standard(standard_id)
    if not standard:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Standard '{standard_id}' not found in knowledge base.",
        )
    return StandardDetailResponse.model_validate(standard)
