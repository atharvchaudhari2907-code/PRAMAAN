import enum
from datetime import datetime
from typing import List, Optional
from sqlalchemy import DateTime, Enum, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin, generate_uuid


class CertificateStatus(str, enum.Enum):
    CERTIFICATE_PENDING = "CERTIFICATE_PENDING"
    CERTIFICATE_ISSUED = "CERTIFICATE_ISSUED"
    ACTIVE = "ACTIVE"
    SUSPENDED = "SUSPENDED"
    EXPIRED = "EXPIRED"
    REVOKED = "REVOKED"


class AnchorStatus(str, enum.Enum):
    PENDING = "PENDING"
    ANCHORING = "ANCHORING"
    ANCHORED = "ANCHORED"
    ANCHOR_FAILED = "ANCHOR_FAILED"


class Certificate(Base, TimestampMixin):
    __tablename__ = "certificates"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    certificate_id: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    application_id: Mapped[str] = mapped_column(String(36), ForeignKey("applications.id", ondelete="CASCADE"), unique=True, index=True, nullable=False)
    product_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    product_name: Mapped[str] = mapped_column(String(255), nullable=False)
    manufacturer: Mapped[str] = mapped_column(String(255), nullable=False)
    model: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    standard_id: Mapped[str] = mapped_column(String(100), nullable=False)
    standard_version: Mapped[Optional[str]] = mapped_column(String(50), default="2024", nullable=True)
    issued_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    valid_until: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="ACTIVE", nullable=False)  # CertificateStatus
    issuer: Mapped[str] = mapped_column(String(255), default="Bureau of Indian Standards", nullable=False)
    document_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    document_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    ipfs_cid: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    blockchain_network: Mapped[str] = mapped_column(String(100), default="Polygon Amoy Testnet", nullable=False)
    contract_address: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    transaction_hash: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    block_number: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    record_hash: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    anchor_status: Mapped[str] = mapped_column(String(50), default="PENDING", nullable=False)  # AnchorStatus

    # Relationships
    application: Mapped["Application"] = relationship("Application", back_populates="certificate")
    events: Mapped[List["CertificateEvent"]] = relationship(
        "CertificateEvent", back_populates="certificate", cascade="all, delete-orphan", order_by="CertificateEvent.created_at"
    )


class CertificateEvent(Base, TimestampMixin):
    __tablename__ = "certificate_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    certificate_id: Mapped[str] = mapped_column(String(36), ForeignKey("certificates.id", ondelete="CASCADE"), index=True, nullable=False)
    event_type: Mapped[str] = mapped_column(String(50), nullable=False)  # ISSUED, STATUS_CHANGE, ANCHORED, AUDITED, RENEWED, REVOKED
    description: Mapped[str] = mapped_column(Text, nullable=False)
    block_number: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    tx_hash: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    certificate: Mapped["Certificate"] = relationship("Certificate", back_populates="events")


class TrustLedgerRecord(Base, TimestampMixin):
    __tablename__ = "trust_ledger_records"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    certificate_id: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    sha256_hash: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    record_type: Mapped[str] = mapped_column(String(50), default="CERTIFICATE_HASH", nullable=False)
    payload_json: Mapped[Text] = mapped_column(Text, nullable=False)
    anchored_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
