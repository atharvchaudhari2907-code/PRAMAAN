import enum
from datetime import datetime
from typing import List, Optional
from sqlalchemy import BigInteger, Boolean, DateTime, Enum, Float, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin, generate_uuid


class ApplicationStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    DOCUMENT_UPLOADED = "DOCUMENT_UPLOADED"
    EXTRACTION_PENDING = "EXTRACTION_PENDING"
    PARAMETER_REVIEW = "PARAMETER_REVIEW"
    STANDARD_MATCHING = "STANDARD_MATCHING"
    COMPLIANCE_ANALYSIS = "COMPLIANCE_ANALYSIS"
    GAPS_FOUND = "GAPS_FOUND"
    READY_FOR_APPLICATION = "READY_FOR_APPLICATION"
    APPLICATION_PREPARED = "APPLICATION_PREPARED"
    SUBMITTED = "SUBMITTED"
    LAB_TESTING = "LAB_TESTING"
    INSPECTION = "INSPECTION"
    BIS_SCRUTINY = "BIS_SCRUTINY"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    CERTIFICATE_ISSUED = "CERTIFICATE_ISSUED"
    CLOSED = "CLOSED"


class DocumentType(str, enum.Enum):
    TECHNICAL_DATASHEET = "TECHNICAL_DATASHEET"
    TEST_REPORT = "TEST_REPORT"
    FACTORY_LAYOUT = "FACTORY_LAYOUT"
    MACHINERY_LIST = "MACHINERY_LIST"
    QUALITY_PLAN = "QUALITY_PLAN"
    FORM_IV_DOSSIER = "FORM_IV_DOSSIER"
    OTHER = "OTHER"


class Application(Base, TimestampMixin):
    __tablename__ = "applications"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    application_number: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    status: Mapped[ApplicationStatus] = mapped_column(
        Enum(ApplicationStatus), default=ApplicationStatus.DRAFT, nullable=False, index=True
    )
    product_name: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[str] = mapped_column(String(100), nullable=False)
    model_number: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    manufacturer: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    manufacturing_location: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    additional_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    primary_standard_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    readiness_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="applications")
    documents: Mapped[List["ApplicationDocument"]] = relationship(
        "ApplicationDocument", back_populates="application", cascade="all, delete-orphan"
    )
    status_events: Mapped[List["ApplicationStatusEvent"]] = relationship(
        "ApplicationStatusEvent", back_populates="application", cascade="all, delete-orphan", order_by="ApplicationStatusEvent.created_at"
    )
    product: Mapped[Optional["Product"]] = relationship(
        "Product", back_populates="application", uselist=False, cascade="all, delete-orphan"
    )
    assessments: Mapped[List["Assessment"]] = relationship(
        "Assessment", back_populates="application", cascade="all, delete-orphan"
    )
    generated_documents: Mapped[List["GeneratedDocument"]] = relationship(
        "GeneratedDocument", back_populates="application", cascade="all, delete-orphan"
    )
    checklist_items: Mapped[List["ApplicationChecklistItem"]] = relationship(
        "ApplicationChecklistItem", back_populates="application", cascade="all, delete-orphan"
    )
    submissions: Mapped[List["ApplicationSubmission"]] = relationship(
        "ApplicationSubmission", back_populates="application", cascade="all, delete-orphan"
    )
    certificate: Mapped[Optional["Certificate"]] = relationship(
        "Certificate", back_populates="application", uselist=False, cascade="all, delete-orphan"
    )


class ApplicationDocument(Base, TimestampMixin):
    __tablename__ = "application_documents"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    application_id: Mapped[str] = mapped_column(String(36), ForeignKey("applications.id", ondelete="CASCADE"), index=True, nullable=False)
    document_type: Mapped[DocumentType] = mapped_column(Enum(DocumentType), default=DocumentType.TECHNICAL_DATASHEET, nullable=False)
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_size: Mapped[int] = mapped_column(BigInteger, nullable=False)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    sha256_hash: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    storage_path: Mapped[str] = mapped_column(String(500), nullable=False)

    application: Mapped["Application"] = relationship("Application", back_populates="documents")


class ApplicationStatusEvent(Base, TimestampMixin):
    __tablename__ = "application_status_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    application_id: Mapped[str] = mapped_column(String(36), ForeignKey("applications.id", ondelete="CASCADE"), index=True, nullable=False)
    event_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    from_status: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    to_status: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    actor_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    source: Mapped[str] = mapped_column(String(100), default="SYSTEM", nullable=False)
    metadata_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    application: Mapped["Application"] = relationship("Application", back_populates="status_events")


class GeneratedDocument(Base, TimestampMixin):
    __tablename__ = "generated_documents"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    application_id: Mapped[str] = mapped_column(String(36), ForeignKey("applications.id", ondelete="CASCADE"), index=True, nullable=False)
    document_type: Mapped[str] = mapped_column(String(100), nullable=False)  # FORM_I, FORM_II, FORM_IV, TECHNICAL_FILE, AUDIT_REPORT
    document_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    mime_type: Mapped[str] = mapped_column(String(100), default="application/pdf", nullable=False)
    sha256_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    metadata_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    application: Mapped["Application"] = relationship("Application", back_populates="generated_documents")


class ApplicationChecklistItem(Base, TimestampMixin):
    __tablename__ = "application_checklist_items"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    application_id: Mapped[str] = mapped_column(String(36), ForeignKey("applications.id", ondelete="CASCADE"), index=True, nullable=False)
    document_type: Mapped[str] = mapped_column(String(100), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    required: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="REQUIRED", nullable=False)  # REQUIRED, PENDING, UPLOADED, VERIFIED, REJECTED
    uploaded_document_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    verification_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    application: Mapped["Application"] = relationship("Application", back_populates="checklist_items")


class ApplicationSubmission(Base, TimestampMixin):
    __tablename__ = "application_submissions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    application_id: Mapped[str] = mapped_column(String(36), ForeignKey("applications.id", ondelete="CASCADE"), index=True, nullable=False)
    reference_number: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    portal_url: Mapped[str] = mapped_column(String(255), default="https://www.manakonline.in", nullable=False)
    submission_status: Mapped[str] = mapped_column(String(50), default="SUBMITTED", nullable=False)
    submitted_by: Mapped[str] = mapped_column(String(255), nullable=False)
    package_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    application: Mapped["Application"] = relationship("Application", back_populates="submissions")

