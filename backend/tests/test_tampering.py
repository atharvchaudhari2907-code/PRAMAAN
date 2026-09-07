import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.application import Application, ApplicationStatus
from app.models.user import User
from app.services.certificate_service import CertificateService, compute_canonical_hash


@pytest.mark.asyncio
async def test_tamper_detection_and_blockchain_immutability(db_session: AsyncSession):
    """
    Demonstrates blockchain immutability:
    1. Issue authentic certificate anchored on blockchain.
    2. Public verification confirms VERIFIED_AND_CURRENT.
    3. Malicious actor / attacker mutates database record directly (tampering).
    4. Cryptographic integrity check catches hash mismatch and flags INTEGRITY_WARNING.
    """
    # 1. Setup user & application
    user = User(
        email="tamper_audit@acme.in",
        hashed_password="secure_password_hash",
        full_name="Audit Engineer",
        role="manufacturer",
        company_name="Acme Safety Electronics",
    )
    db_session.add(user)
    await db_session.flush()

    app = Application(
        user_id=user.id,
        application_number="BIS-2026-990001",
        product_name="Certified Industrial Heater",
        category="Heating Equipment",
        manufacturer="Acme Safety Electronics",
        model_number="ASH-2000X",
        primary_standard_id="IS 302 (Part 1)",
        status=ApplicationStatus.APPROVED,
    )
    db_session.add(app)
    await db_session.commit()
    await db_session.refresh(app)

    # 2. Issue Certificate via CertificateService
    cert_service = CertificateService(db_session)
    cert = await cert_service.issue_certificate(
        application=app,
        valid_years=2,
    )
    cert_id = cert.certificate_id

    # 3. Verify public verification returns VERIFIED_AND_CURRENT
    clean_verify = await cert_service.verify_certificate_public(cert_id)
    assert clean_verify.status == "VERIFIED_AND_CURRENT"
    assert clean_verify.is_valid is True
    assert clean_verify.computed_record_hash == clean_verify.anchored_record_hash
    assert clean_verify.transaction_hash is not None
    assert clean_verify.block_number is not None

    # 4. Tamper DB directly (simulating unauthorized database modification)
    cert.product_name = "Counterfeit Appliance Pro"
    cert.model = "COUNTERFEIT-999"
    await db_session.commit()
    await db_session.refresh(cert)

    # 5. Public verification after tampering must catch mismatch
    tampered_verify = await cert_service.verify_certificate_public(cert_id)
    assert tampered_verify.status == "INTEGRITY_WARNING"
    assert tampered_verify.is_valid is False
    assert tampered_verify.computed_record_hash != tampered_verify.anchored_record_hash
    assert "CRITICAL INTEGRITY WARNING" in tampered_verify.message

    # 6. Revert DB back to authentic canonical values and verify restoration
    cert.product_name = "Certified Industrial Heater"
    cert.model = "ASH-2000X"
    await db_session.commit()
    await db_session.refresh(cert)

    restored_verify = await cert_service.verify_certificate_public(cert_id)
    assert restored_verify.status == "VERIFIED_AND_CURRENT"
    assert restored_verify.is_valid is True
    assert restored_verify.computed_record_hash == restored_verify.anchored_record_hash
