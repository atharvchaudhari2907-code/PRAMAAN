from datetime import datetime, timezone, timedelta
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.application import Application, ApplicationStatus
from app.models.trust_ledger import Certificate, CertificateStatus
from app.models.user import User
from app.schemas.certificate import CanonicalCertificate
from app.services.certificate_service import CertificateService, compute_canonical_hash
from app.services.ipfs_provider import get_ipfs_provider
from app.services.qr_generator import QRGenerator


@pytest.mark.asyncio
async def test_canonical_hash_determinism():
    """Validates that compute_canonical_hash produces identical hashes regardless of dict insertion order."""
    payload1 = CanonicalCertificate(
        certificate_id="CM/L-1234567",
        product_name="LED Smart Bulb",
        manufacturer="Syska Tech",
        model="LED-9W",
        standard_id="IS 16102 (Part 1)",
        standard_version="2012",
        issued_at="2026-01-01T00:00:00Z",
        valid_until="2028-01-01T00:00:00Z",
        document_sha256="abcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890",
    )
    payload2 = CanonicalCertificate(
        valid_until="2028-01-01T00:00:00Z",
        document_sha256="abcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890",
        certificate_id="CM/L-1234567",
        issued_at="2026-01-01T00:00:00Z",
        model="LED-9W",
        manufacturer="Syska Tech",
        product_name="LED Smart Bulb",
        standard_id="IS 16102 (Part 1)",
        standard_version="2012",
    )

    hash1 = compute_canonical_hash(payload1)
    hash2 = compute_canonical_hash(payload2)

    assert hash1 == hash2
    assert len(hash1) == 64
    assert int(hash1, 16) > 0


@pytest.mark.asyncio
async def test_ipfs_provider_upload_and_retrieval():
    """Tests that IPFS provider writes content and computes valid CIDv1 multihash."""
    ipfs = get_ipfs_provider()
    content = b'{"dossier": "BIS Compliance Report IS 302", "timestamp": "2026-09-08"}'
    cid = await ipfs.upload_document(content, filename="dossier.json")

    assert cid.startswith("bafy")
    retrieved = await ipfs.get_document(cid)
    assert retrieved == content


@pytest.mark.asyncio
async def test_qr_generator_svg():
    """Tests QR code generator creates valid SVG."""
    url = "https://bis-compliance.gov.in/verify/CM-L-98765432"
    svg = QRGenerator.generate_qr_svg(url)

    assert svg.startswith("<svg") or "<svg" in svg
    assert "</svg>" in svg
    assert "xmlns" in svg


@pytest.mark.asyncio
async def test_certificate_lifecycle_and_public_verification(
    client: AsyncClient,
    db_session: AsyncSession,
):
    """
    Tests complete lifecycle:
    1. Issue certificate.
    2. Public verify: VERIFIED_AND_CURRENT.
    3. Update to SUSPENDED -> Public verify: AUTHENTIC_BUT_SUSPENDED.
    4. Update to REVOKED -> Public verify: AUTHENTIC_BUT_REVOKED.
    5. Check QR endpoint returns SVG.
    """
    # Create test user and app
    user = User(
        email="lifecycle_tester@bis.gov.in",
        hashed_password="pw_hash_test",
        full_name="Lifecycle Auditor",
        role="admin",
        company_name="BIS Central Office",
    )
    db_session.add(user)
    await db_session.flush()

    app = Application(
        user_id=user.id,
        application_number="BIS-2026-880001",
        product_name="Smart Submersible Pump",
        category="Pumps & Motors",
        manufacturer="Kirloskar Power",
        model_number="KP-PUMP-500",
        primary_standard_id="IS 8472",
        status=ApplicationStatus.APPROVED,
    )
    db_session.add(app)
    await db_session.commit()
    await db_session.refresh(app)

    cert_service = CertificateService(db_session)
    cert = await cert_service.issue_certificate(app, valid_years=1)
    await db_session.commit()
    cert_id = cert.certificate_id

    # 1. Public verify (No authentication required)
    res = await client.get(f"/api/public/verify/{cert_id}")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "VERIFIED_AND_CURRENT"
    assert data["is_valid"] is True
    assert data["product_name"] == "Smart Submersible Pump"
    assert data["manufacturer"] == "Kirloskar Power"
    assert data["blockchain_network"] is not None
    assert data["transaction_hash"] is not None
    assert data["block_number"] is not None
    assert data["ipfs_cid"].startswith("bafy")

    # 2. Update status to SUSPENDED
    updated_suspended = await cert_service.update_status(cert_id, CertificateStatus.SUSPENDED, "Pending quality audit")
    assert updated_suspended.status == CertificateStatus.SUSPENDED
    await db_session.commit()

    res_suspended = await client.get(f"/api/public/verify/{cert_id}")
    assert res_suspended.status_code == 200
    data_suspended = res_suspended.json()
    assert data_suspended["status"] == "AUTHENTIC_BUT_SUSPENDED"
    assert data_suspended["is_valid"] is False

    # 3. Update status to REVOKED
    updated_revoked = await cert_service.update_status(cert_id, CertificateStatus.REVOKED, "Critical non-conformity")
    assert updated_revoked.status == CertificateStatus.REVOKED
    await db_session.commit()

    res_revoked = await client.get(f"/api/public/verify/{cert_id}")
    assert res_revoked.status_code == 200
    data_revoked = res_revoked.json()
    assert data_revoked["status"] == "AUTHENTIC_BUT_REVOKED"
    assert data_revoked["is_valid"] is False

    # 4. Check QR code endpoint
    qr_res = await client.get(f"/api/certificates/{cert_id}/qr")
    assert qr_res.status_code == 200
    assert "image/svg+xml" in qr_res.headers.get("content-type", "")
    assert "<svg" in qr_res.text

    # 5. Non-existent certificate lookup
    not_found_res = await client.get("/api/public/verify/NON-EXISTENT-ID-999")
    assert not_found_res.status_code == 200
    assert not_found_res.json()["status"] == "NOT_FOUND"
    assert not_found_res.json()["is_valid"] is False
