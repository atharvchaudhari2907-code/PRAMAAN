from fastapi import APIRouter, Depends, File, Form, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.middleware.auth_middleware import get_current_user
from app.models.application import DocumentType
from app.models.user import User
from app.schemas.document import DocumentResponse, DocumentUploadResponse
from app.services.document_service import DocumentService

router = APIRouter(tags=["Documents"])


@router.post(
    "/applications/{id}/documents",
    response_model=DocumentUploadResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_document(
    id: str,
    file: UploadFile = File(...),
    document_type: DocumentType = Form(DocumentType.TECHNICAL_DATASHEET),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Secure document upload with MIME, extension, size, and magic byte validation."""
    service = DocumentService(db)
    doc = await service.upload_document(id, current_user.id, file, document_type)
    return DocumentUploadResponse(
        document=DocumentResponse.model_validate(doc),
        message="Document uploaded and cryptographically hashed successfully.",
    )


@router.post(
    "/applications/{id}/upload",
    response_model=DocumentUploadResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_document_alias(
    id: str,
    file: UploadFile = File(...),
    document_type: DocumentType = Form(DocumentType.TECHNICAL_DATASHEET),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Alias for upload endpoint to support existing client conventions."""
    return await upload_document(id, file, document_type, current_user, db)


@router.get("/applications/{id}/documents/{document_id}/download")
async def download_document(
    id: str,
    document_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Streams stored document file only if requested by the authorized application owner."""
    service = DocumentService(db)
    file_path, mime_type, filename = await service.get_document_for_download(
        document_id, current_user.id
    )
    return FileResponse(
        path=file_path,
        media_type=mime_type,
        filename=filename,
    )
