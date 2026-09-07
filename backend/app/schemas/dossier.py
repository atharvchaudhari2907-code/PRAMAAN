from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class ReadinessGateResponse(BaseModel):
    application_id: str
    readiness_score: float = Field(..., description="Overall readiness score (0-100)")
    validation_status: str = Field(..., description="READY, NOT_READY, or GAPS_DETECTED")
    missing_information: List[str] = Field(default_factory=list)
    missing_documents: List[str] = Field(default_factory=list)
    failed_critical_clauses: List[str] = Field(default_factory=list)
    required_actions: List[str] = Field(default_factory=list)
    is_ready: bool = Field(..., description="True if readiness >= 70, 0 failed critical clauses, and all mandatory docs present")


class ChecklistItemResponse(BaseModel):
    id: str
    application_id: str
    document_type: str
    name: str
    description: str
    required: bool
    status: str
    uploaded_document_id: Optional[str] = None
    verified: bool
    verification_notes: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ChecklistVerifyRequest(BaseModel):
    verified: bool
    verification_notes: Optional[str] = None


class FormFieldItem(BaseModel):
    field_key: str
    label: str
    value: Any
    source: str = Field(..., description="AI_EXTRACTED, MANUFACTURER_INPUT, BIS_STANDARD_CATALOG, or SYSTEM_DEFAULT")
    complete: bool
    requires_confirmation: bool = False


class BISFormSection(BaseModel):
    section_id: str
    section_title: str
    fields: List[FormFieldItem] = Field(default_factory=list)


class BISFormDefinition(BaseModel):
    form_id: str
    title: str
    description: str
    is_complete: bool
    sections: List[BISFormSection] = Field(default_factory=list)


class DocumentGenerationRequest(BaseModel):
    document_types: Optional[List[str]] = Field(
        default=None,
        description="List of document types to generate: FORM_I, FORM_II, FORM_IV, TECHNICAL_DOSSIER. Generates all if omitted."
    )


class GeneratedDocumentResponse(BaseModel):
    id: str
    application_id: str
    document_type: str
    document_name: Optional[str] = None
    version: int
    file_path: str
    mime_type: str
    sha256_hash: str
    metadata_json: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ApplicationSubmissionRequest(BaseModel):
    reference_number: str = Field(..., min_length=3, description="Official BIS / Manakonline acknowledgement/reference number")
    portal_url: Optional[str] = Field(default="https://www.manakonline.in", description="Portal endpoint used")
    submitted_by: str = Field(..., description="Name/email of the submitter")
    notes: Optional[str] = None


class ApplicationSubmissionResponse(BaseModel):
    id: str
    application_id: str
    reference_number: str
    portal_url: str
    submission_status: str
    submitted_by: str
    package_hash: str
    notes: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TrackingEventCreate(BaseModel):
    to_status: str
    event_type: Optional[str] = "STATUS_CHANGE"
    description: Optional[str] = None
    note: Optional[str] = None
    source: Optional[str] = "MANUFACTURER"


class StatusEventResponse(BaseModel):
    id: str
    application_id: str
    from_status: Optional[str] = None
    to_status: str
    event_type: Optional[str] = None
    description: Optional[str] = None
    note: Optional[str] = None
    source: str
    metadata_json: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


TrackingEventResponse = StatusEventResponse


class DossierExportResponse(BaseModel):
    application_id: str
    bundle_version: int
    readiness_score: float
    package_hash: str
    generated_at: datetime
    documents: List[GeneratedDocumentResponse] = Field(default_factory=list)
