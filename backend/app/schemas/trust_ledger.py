from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class HashVerificationRequest(BaseModel):
    sha256_hash: str
    document_name: Optional[str] = None


class HashVerificationResponse(BaseModel):
    sha256_hash: str
    is_verified: bool
    matched_application_id: Optional[str] = None
    matched_document_name: Optional[str] = None
    timestamp: Optional[str] = None
    integrity_status: str  # VALID_RECORD, TAMPER_EVIDENT_MISMATCH, UNKNOWN_RECORD
    blockchain_network: str = "Hyperledger Fabric / Ethereum Testnet (Sepolia)"
    message: str


class TrustLedgerRecordCreate(BaseModel):
    product_name: str
    manufacturer: str
    model: str
    standard_id: str
    standard_title: str
    standard_version: str
    certificate_id: str
    certification_status: str = "ACTIVE"
    valid_until: Optional[str] = None
    issuer: Optional[str] = "Bureau of Indian Standards"


class TrustLedgerRecordResponse(BaseModel):
    id: str
    public_product_id: str
    product_name: str
    manufacturer: str
    model: str
    standard_id: str
    standard_title: str
    standard_version: str
    certificate_id: str
    certification_status: str
    valid_until: str
    issuer: str
    record_hash: str
    verification_url: str
    qr_code_data_url: Optional[str] = None
    created_at: str


class TrustLedgerStats(BaseModel):
    total_anchored_records: int
    active_certificates: int
    revoked_certificates: int
    total_verifications: int
