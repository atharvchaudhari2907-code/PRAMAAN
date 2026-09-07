from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field
from app.models.application import ApplicationStatus, DocumentType


class ApplicationCreate(BaseModel):
    product_name: str = Field(..., min_length=1, max_length=255)
    category: str = Field(..., min_length=1, max_length=100)
    model_number: Optional[str] = Field(None, max_length=100)
    manufacturer: Optional[str] = Field(None, max_length=255)
    manufacturing_location: Optional[str] = Field(None, max_length=255)
    additional_notes: Optional[str] = None
    primary_standard_id: Optional[str] = None
    # Optional parameters sent in initial form
    wattage: Optional[float] = None
    voltage: Optional[float] = None
    luminous_efficacy: Optional[float] = None


class ApplicationUpdate(BaseModel):
    product_name: Optional[str] = None
    category: Optional[str] = None
    model_number: Optional[str] = None
    manufacturer: Optional[str] = None
    manufacturing_location: Optional[str] = None
    additional_notes: Optional[str] = None
    primary_standard_id: Optional[str] = None
    status: Optional[ApplicationStatus] = None
    readiness_score: Optional[float] = None


class DocumentSummaryResponse(BaseModel):
    id: str
    document_type: DocumentType
    original_filename: str
    file_size: int
    mime_type: str
    sha256_hash: str
    created_at: datetime

    model_config = {"from_attributes": True}


class StatusEventResponse(BaseModel):
    id: str
    from_status: Optional[str] = None
    to_status: str
    note: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ApplicationResponse(BaseModel):
    id: str
    user_id: str
    application_number: str
    status: ApplicationStatus
    product_name: str
    category: str
    model_number: Optional[str] = None
    manufacturer: Optional[str] = None
    manufacturing_location: Optional[str] = None
    primary_standard_id: Optional[str] = None
    readiness_score: Optional[float] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ApplicationDetailResponse(ApplicationResponse):
    documents: List[DocumentSummaryResponse] = []
    status_events: List[StatusEventResponse] = []


class TrackingEventResponse(BaseModel):
    id: str
    title: str
    stage: str
    status: str  # COMPLETED, IN_PROGRESS, PENDING, BLOCKED
    description: str
    date: Optional[str] = None
    completed_at: Optional[str] = None
