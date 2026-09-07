from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.middleware.auth_middleware import get_current_user
from app.models.application import Application
from app.models.trust_ledger import Certificate, TrustLedgerRecord
from app.models.user import User
from app.schemas.certificate import (
    CertificateCreate,
    CertificateResponse,
    CertificateStatusUpdate,
    PublicVerificationResponse,
)
from app.schemas.trust_ledger import (
    HashVerificationRequest,
    HashVerificationResponse,
    TrustLedgerRecordCreate,
    TrustLedgerRecordResponse,
)
from app.services.application_service import ApplicationService
from app.services.certificate_service import CertificateService
from app.services.qr_generator import QRGenerator
from app.services.trust_ledger_service import TrustLedgerService

router = APIRouter(tags=["Trust Ledger & Cryptographic Verification"])


@router.get("/public/verify/{public_product_id}", response_model=PublicVerificationResponse)
async def public_verify_certificate(
    public_product_id: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Public verification endpoint for consumers and auditors scanning product QR codes.
    No login required. Performs full cryptographic on-chain integrity checks.
    """
    cert_service = CertificateService(db)
    return await cert_service.verify_certificate_public(public_product_id)


@router.post("/certificates", response_model=CertificateResponse, status_code=status.HTTP_201_CREATED)
async def issue_certificate(
    payload: CertificateCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Issues an official BIS certificate, uploads dossier to IPFS, and anchors hash on-chain."""
    app_service = ApplicationService(db)
    app = await app_service.get_application(payload.application_id, current_user.id)

    cert_service = CertificateService(db)
    cert = await cert_service.issue_certificate(
        application=app,
        document_id=payload.document_id,
        valid_years=payload.valid_years,
    )
    url = QRGenerator.get_public_verification_url(cert.certificate_id)
    svg = QRGenerator.generate_qr_svg(url)

    res = CertificateResponse.model_validate(cert)
    res.public_verification_url = url
    res.qr_code_svg = svg
    return res


@router.get("/certificates/{id}", response_model=CertificateResponse)
async def get_certificate(
    id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Retrieves full certificate record with blockchain transaction and IPFS reference."""
    stmt = (
        select(Certificate)
        .where(
            (Certificate.id == id)
            | (Certificate.certificate_id == id)
            | (Certificate.application_id == id)
        )
        .options(selectinload(Certificate.events), selectinload(Certificate.application))
    )
    result = await db.execute(stmt)
    cert = result.scalar_one_or_none()
    if not cert:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Certificate not found")

    # Multi-tenant isolation: non-admin users can only access certificates belonging to their applications
    if (
        current_user.role != "admin"
        and cert.application
        and cert.application.user_id != current_user.id
    ):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Certificate not found")

    url = QRGenerator.get_public_verification_url(cert.certificate_id)
    svg = QRGenerator.generate_qr_svg(url)
    res = CertificateResponse.model_validate(cert)
    res.public_verification_url = url
    res.qr_code_svg = svg
    return res


@router.patch("/certificates/{id}/status", response_model=CertificateResponse)
async def update_certificate_status(
    id: str,
    payload: CertificateStatusUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Updates certificate status (ACTIVE, SUSPENDED, EXPIRED, REVOKED) and syncs to blockchain."""
    stmt = (
        select(Certificate)
        .where(
            (Certificate.id == id)
            | (Certificate.certificate_id == id)
            | (Certificate.application_id == id)
        )
        .options(selectinload(Certificate.application))
    )
    result = await db.execute(stmt)
    existing_cert = result.scalar_one_or_none()
    if not existing_cert:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Certificate not found")

    # Only admin/auditor or certificate owner can update status
    if (
        current_user.role not in ["admin", "auditor"]
        and existing_cert.application
        and existing_cert.application.user_id != current_user.id
    ):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Certificate not found")

    cert_service = CertificateService(db)
    cert = await cert_service.update_status(id, payload.status, payload.reason)
    if not cert:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Certificate not found")

    url = QRGenerator.get_public_verification_url(cert.certificate_id)
    svg = QRGenerator.generate_qr_svg(url)
    res = CertificateResponse.model_validate(cert)
    res.public_verification_url = url
    res.qr_code_svg = svg
    return res


@router.get("/certificates/{id}/qr")
async def get_certificate_qr(
    id: str,
    db: AsyncSession = Depends(get_db),
):
    """Returns SVG QR code for certificate public verification."""
    stmt = select(Certificate).where((Certificate.id == id) | (Certificate.certificate_id == id))
    result = await db.execute(stmt)
    cert = result.scalar_one_or_none()
    if not cert:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Certificate not found")

    url = QRGenerator.get_public_verification_url(cert.certificate_id)
    svg_str = QRGenerator.generate_qr_svg(url)
    return Response(content=svg_str, media_type="image/svg+xml")


@router.post("/verification/verify-hash", response_model=HashVerificationResponse)
async def verify_hash(
    payload: HashVerificationRequest,
    db: AsyncSession = Depends(get_db),
):
    """Verifies a SHA-256 hash against stored documents and trust ledger certificates."""
    service = TrustLedgerService(db)
    return await service.verify_hash(payload.sha256_hash, payload.document_name)


@router.get("/trust-ledger/records", response_model=List[TrustLedgerRecordResponse])
async def list_trust_ledger_records(
    db: AsyncSession = Depends(get_db),
):
    """Retrieves all anchored trust ledger certificate records."""
    service = TrustLedgerService(db)
    return await service.list_records()


@router.post("/trust-ledger/records", response_model=TrustLedgerRecordResponse, status_code=status.HTTP_201_CREATED)
async def create_trust_ledger_record(
    payload: TrustLedgerRecordCreate,
    db: AsyncSession = Depends(get_db),
):
    """Anchors a certified product record into the trust ledger."""
    service = TrustLedgerService(db)
    return await service.create_record(payload)


@router.get("/trust-ledger/records/{public_product_id}", response_model=TrustLedgerRecordResponse)
async def get_trust_ledger_record(
    public_product_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Public verification lookup for consumers scanning QR codes."""
    service = TrustLedgerService(db)
    rec = await service.get_record_by_public_id(public_product_id)
    if not rec:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No certified product record found for ID {public_product_id}.",
        )
    return rec
