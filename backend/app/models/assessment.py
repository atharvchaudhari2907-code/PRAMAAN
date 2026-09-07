from typing import List, Optional
from sqlalchemy import Boolean, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin, generate_uuid


class Assessment(Base, TimestampMixin):
    __tablename__ = "assessments"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    application_id: Mapped[str] = mapped_column(String(36), ForeignKey("applications.id", ondelete="CASCADE"), index=True, nullable=False)
    standard_id: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    readiness_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    success_probability: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    application: Mapped["Application"] = relationship("Application", back_populates="assessments")
    parameters: Mapped[List["AssessmentParameter"]] = relationship(
        "AssessmentParameter", back_populates="assessment", cascade="all, delete-orphan"
    )
    compliance_results: Mapped[List["ComplianceResult"]] = relationship(
        "ComplianceResult", back_populates="assessment", cascade="all, delete-orphan"
    )
    gaps: Mapped[List["ComplianceGap"]] = relationship(
        "ComplianceGap", back_populates="assessment", cascade="all, delete-orphan"
    )


class AssessmentParameter(Base, TimestampMixin):
    __tablename__ = "assessment_parameters"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    assessment_id: Mapped[str] = mapped_column(String(36), ForeignKey("assessments.id", ondelete="CASCADE"), index=True, nullable=False)
    parameter_key: Mapped[str] = mapped_column(String(100), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    expected_value: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    actual_value: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    unit: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="EVALUATED", nullable=False)

    assessment: Mapped["Assessment"] = relationship("Assessment", back_populates="parameters")


class ComplianceResult(Base, TimestampMixin):
    __tablename__ = "compliance_results"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    assessment_id: Mapped[str] = mapped_column(String(36), ForeignKey("assessments.id", ondelete="CASCADE"), index=True, nullable=False)
    clause_number: Mapped[str] = mapped_column(String(50), index=True, nullable=False)
    clause_title: Mapped[str] = mapped_column(String(255), nullable=False)
    compliance_status: Mapped[str] = mapped_column(String(50), nullable=False)  # PASS, FAIL, DEFICIT, INSUFFICIENT_INFO
    reasoning: Mapped[str] = mapped_column(Text, nullable=False)
    deterministic_check_passed: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    evidence_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    assessment: Mapped["Assessment"] = relationship("Assessment", back_populates="compliance_results")


class ComplianceGap(Base, TimestampMixin):
    __tablename__ = "compliance_gaps"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    assessment_id: Mapped[str] = mapped_column(String(36), ForeignKey("assessments.id", ondelete="CASCADE"), index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    parameter_name: Mapped[str] = mapped_column(String(255), nullable=False)
    current_value: Mapped[str] = mapped_column(String(255), nullable=False)
    reference_requirement: Mapped[str] = mapped_column(Text, nullable=False)
    severity: Mapped[str] = mapped_column(String(50), default="CRITICAL", nullable=False)  # CRITICAL, MAJOR, MINOR
    remediation_guide: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    assessment: Mapped["Assessment"] = relationship("Assessment", back_populates="gaps")
