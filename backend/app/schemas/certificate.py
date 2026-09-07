from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class CertificateCreate(BaseModel):
    application_id: str
    document_id: Optional[str] = None
    valid_years: int = Field(default=1, ge=1, le=5)


class CertificateStatusUpdate(BaseModel):
    status: str = Field(..., description="ACTIVE, SUSPENDED, EXPIRED, REVOKED")
    reason: Optional[str] = None


class CanonicalCertificate(BaseModel):
    certificate_id: str
    product_name: str
    manufacturer: str
    model: Optional[str] = ""
    standard_id: str
    standard_version: Optional[str] = ""
    issued_at: str
    valid_until: str
    document_sha256: str


class CertificateEventResponse(BaseModel):
    id: str
    certificate_id: str
    event_type: str
    description: str
    block_number: Optional[int] = None
    tx_hash: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CertificateResponse(BaseModel):
    id: str
    certificate_id: str
    application_id: str
    product_id: Optional[str] = None
    product_name: str
    manufacturer: str
    model: Optional[str] = None
    standard_id: str
    standard_version: Optional[str] = None
    issued_at: datetime
    valid_until: datetime
    status: str
    issuer: str
    document_id: Optional[str] = None
    document_sha256: str
    ipfs_cid: Optional[str] = None
    blockchain_network: str
    contract_address: Optional[str] = None
    transaction_hash: Optional[str] = None
    block_number: Optional[int] = None
    record_hash: str
    anchor_status: str
    public_verification_url: Optional[str] = None
    qr_code_svg: Optional[str] = None
    events: List[CertificateEventResponse] = Field(default_factory=list)
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PublicVerificationResponse(BaseModel):
    status: str = Field(
        ...,
        description="VERIFIED_AND_CURRENT, AUTHENTIC_BUT_EXPIRED, AUTHENTIC_BUT_SUSPENDED, AUTHENTIC_BUT_REVOKED, INTEGRITY_WARNING, BLOCKCHAIN_UNAVAILABLE, or NOT_FOUND"
    )
    is_valid: bool
    certificate_id: Optional[str] = None
    product_name: Optional[str] = None
    manufacturer: Optional[str] = None
    model: Optional[str] = None
    standard_id: Optional[str] = None
    standard_version: Optional[str] = None
    issued_at: Optional[datetime] = None
    valid_until: Optional[datetime] = None
    certificate_status: Optional[str] = None
    document_sha256: Optional[str] = None
    computed_record_hash: Optional[str] = None
    anchored_record_hash: Optional[str] = None
    blockchain_network: Optional[str] = None
    contract_address: Optional[str] = None
    transaction_hash: Optional[str] = None
    block_number: Optional[int] = None
    ipfs_cid: Optional[str] = None
    message: str
    verification_timestamp: datetime = Field(default_factory=datetime.utcnow)
