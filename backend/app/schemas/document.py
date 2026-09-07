from datetime import datetime
from pydantic import BaseModel
from app.models.application import DocumentType


class DocumentResponse(BaseModel):
    id: str
    application_id: str
    document_type: DocumentType
    original_filename: str
    file_size: int
    mime_type: str
    sha256_hash: str
    created_at: datetime

    model_config = {"from_attributes": True}


class DocumentUploadResponse(BaseModel):
    document: DocumentResponse
    message: str
