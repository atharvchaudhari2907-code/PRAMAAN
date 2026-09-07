import base64
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.middleware.auth_middleware import get_current_user
from app.models.user import User
from app.services.application_service import ApplicationService
from app.services.voice_service import SUPPORTED_LANGUAGES, VoiceService

router = APIRouter(prefix="/applications", tags=["Multilingual Voice Assistant"])


class VoiceQueryRequest(BaseModel):
    language_code: str = Field(default="en", description="ISO 639-1 code (e.g. en, hi, mr, bn, ta, te, kn, ml, pa, gu, or, as)")
    query_text: Optional[str] = None
    audio_base64: Optional[str] = None


class VoiceQueryResponse(BaseModel):
    application_id: str
    language_code: str
    language_name: str
    transcript: str
    response: str
    citations: List[Dict[str, Any]] = Field(default_factory=list)
    audio_data: Optional[str] = None
    created_at: str


@router.get("/voice/languages")
async def get_supported_languages() -> Dict[str, str]:
    """Returns the 12 supported Indian languages for voice interaction."""
    return SUPPORTED_LANGUAGES


@router.post("/{id}/voice/query", response_model=VoiceQueryResponse)
async def query_voice_assistant(
    id: str,
    payload: VoiceQueryRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Submits a spoken or text query to the grounded multilingual voice assistant.
    Interprets current application context and BIS standards in 12 Indian languages.
    """
    app_service = ApplicationService(db)
    app = await app_service.get_application(id, current_user.id)

    audio_bytes = None
    if payload.audio_base64:
        try:
            audio_bytes = base64.b64decode(payload.audio_base64)
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid audio base64 payload")

    voice_service = VoiceService(db)
    result = await voice_service.process_voice_query(
        application_id=app.id,
        user_id=current_user.id,
        query_text=payload.query_text,
        audio_bytes=audio_bytes,
        language_code=payload.language_code,
    )
    return VoiceQueryResponse(**result)
