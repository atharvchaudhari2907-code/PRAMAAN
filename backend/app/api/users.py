from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.middleware.auth_middleware import get_current_user
from app.models.user import ManufacturerProfile, User

router = APIRouter(prefix="/users", tags=["Users"])


class ProfileUpdateRequest(BaseModel):
    legal_name: str
    gst_number: Optional[str] = None
    pan_number: Optional[str] = None
    registered_address: Optional[str] = None
    factory_address: Optional[str] = None
    contact_phone: Optional[str] = None


class ProfileResponse(BaseModel):
    user_id: str
    email: str
    full_name: Optional[str]
    company_name: Optional[str]
    legal_name: Optional[str] = None
    gst_number: Optional[str] = None
    pan_number: Optional[str] = None
    registered_address: Optional[str] = None
    factory_address: Optional[str] = None
    contact_phone: Optional[str] = None


@router.get("/profile", response_model=ProfileResponse)
async def get_profile(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ManufacturerProfile).where(ManufacturerProfile.user_id == current_user.id)
    )
    profile = result.scalar_one_or_none()

    return ProfileResponse(
        user_id=current_user.id,
        email=current_user.email,
        full_name=current_user.full_name,
        company_name=current_user.company_name,
        legal_name=profile.legal_name if profile else None,
        gst_number=profile.gst_number if profile else None,
        pan_number=profile.pan_number if profile else None,
        registered_address=profile.registered_address if profile else None,
        factory_address=profile.factory_address if profile else None,
        contact_phone=profile.contact_phone if profile else None,
    )


@router.put("/profile", response_model=ProfileResponse)
async def update_profile(
    payload: ProfileUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ManufacturerProfile).where(ManufacturerProfile.user_id == current_user.id)
    )
    profile = result.scalar_one_or_none()

    if not profile:
        profile = ManufacturerProfile(
            user_id=current_user.id,
            legal_name=payload.legal_name.strip(),
            gst_number=payload.gst_number,
            pan_number=payload.pan_number,
            registered_address=payload.registered_address,
            factory_address=payload.factory_address,
            contact_phone=payload.contact_phone,
        )
        db.add(profile)
    else:
        profile.legal_name = payload.legal_name.strip()
        profile.gst_number = payload.gst_number
        profile.pan_number = payload.pan_number
        profile.registered_address = payload.registered_address
        profile.factory_address = payload.factory_address
        profile.contact_phone = payload.contact_phone

    await db.flush()
    return await get_profile(current_user, db)
