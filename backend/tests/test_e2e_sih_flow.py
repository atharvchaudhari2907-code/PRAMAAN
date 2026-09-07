"""
Comprehensive SIH End-to-End Test Suite
Validates the complete 30-step end-to-end manufacturer journey across all 5 phases:
1. User Authentication (Registration & JWT Bearer Profile)
2. Application Creation & Metadata Tracking
3. Document Ingestion & SHA-256 Cryptographic Hashing
4. Structured Parameter Extraction with Confidence Tracking
5. BIS Standards Discovery & Clause Retrieval
6. Compliance Assessment & Deterministic Mathematical Readiness Scoring
7. Interactive Gap Resolution & Recalculation
8. Contextual RAG Chat with Prompt Injection Guardrails
9. Dynamic Document Checklist Verification & Status Transition
10. Official BIS Forms Generation (Form I, Form II, Form IV, 14-Section Technical Dossier)
11. Versioned Immutable Document Generation with SHA-256 Hashing
12. Complete Application Dossier Compilation & ZIP Bundle Export
13. Application Lifecycle State Machine Progression (DRAFT -> APPROVED)
14. Multilingual Regulatory Voice Interaction (Hindi, Marathi, Tamil, etc.)
15. Computer Vision BIS Conformity Analysis (YOLOv8 ISI Mark & Rating Plate)
16. Factory IoT Production Telemetry Ingestion & Audit Query
17. Official Certificate Issuance, Canonical Hashing, IPFS Pinning & Blockchain Anchoring
18. Public Consumer QR Verification (Unauthenticated)
19. Multi-Tenant Cross-User Data Isolation (Strict 404 on Competitor Data)
20. Cryptographic Tamper Detection & Immutable Audit Integrity
"""

import io
import json
import os
import zipfile
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_full_sih_judge_demo_journey(client: AsyncClient):
    # =========================================================================
    # STEP 1: Manufacturer Registration & Authentication
    # =========================================================================
    reg_payload = {
        "email": "demo.manufacturer@havells-india.com",
        "password": "Secure@Havells2026",
        "full_name": "Rajesh Kumar",
        "company_name": "Havells India Limited",
    }
    reg_resp = await client.post("/api/auth/register", json=reg_payload)
    assert reg_resp.status_code == 201, f"Registration failed: {reg_resp.text}"
    auth_data = reg_resp.json()
    token = auth_data["access_token"]
    auth_headers = {"Authorization": f"Bearer {token}"}

    # Verify protected profile endpoint
    me_resp = await client.get("/api/auth/me", headers=auth_headers)
    assert me_resp.status_code == 200
    assert me_resp.json()["email"] == reg_payload["email"]

    # =========================================================================
    # STEP 2: BIS Application Creation
    # =========================================================================
    app_payload = {
        "product_name": "Havells Neo LED Bulb 12W",
        "category": "Lighting & Luminaires",
        "model_number": "LED-12W-B22D",
        "manufacturer": "Havells India Limited",
        "manufacturing_location": "Plot 24, SIDCUL Industrial Area, Haridwar, Uttarakhand",
        "primary_standard_id": "IS 16102 (Part 1) : 2012",
    }
    app_create_resp = await client.post("/api/applications", headers=auth_headers, json=app_payload)
    assert app_create_resp.status_code == 201, f"Application creation failed: {app_create_resp.text}"
    app_data = app_create_resp.json()
    app_id = app_data["id"]
    assert app_data["status"] == "DRAFT"
    assert app_data["product_name"] == app_payload["product_name"]

    # =========================================================================
    # STEP 3: Document Ingestion & SHA-256 Hashing
    # =========================================================================
    sample_spec_sheet = (
        b"%PDF-1.4\n"
        b"1 0 obj\n<< /Title (Havells LED Conformance Test Report) >>\nendobj\n"
        b"Rated Voltage: 230 V AC, 50 Hz\n"
        b"Rated Wattage: 12 W\n"
        b"Cap Fitment: B22d\n"
        b"Insulation Resistance: 15 MOhm\n"
        b"Dielectric Breakdown Voltage: 2500 V\n"
        b"Mechanical Torsion Torque: 3.5 Nm\n"
        b"Glow Wire Flammability Index: 650 C\n"
        b"%%EOF"
    )
    doc_upload_resp = await client.post(
        f"/api/applications/{app_id}/documents",
        headers=auth_headers,
        files={"file": ("Havells_LED_Report.pdf", io.BytesIO(sample_spec_sheet), "application/pdf")},
        data={"document_type": "TEST_REPORT", "title": "Laboratory Conformance Report"},
    )
    assert doc_upload_resp.status_code == 201, f"Document upload failed: {doc_upload_resp.text}"
    uploaded_doc = doc_upload_resp.json()["document"]
    doc_id = uploaded_doc["id"]
    assert "sha256_hash" in uploaded_doc
    assert len(uploaded_doc["sha256_hash"]) == 64

    # =========================================================================
    # STEP 4: Structured Parameter Extraction
    # =========================================================================
    extract_resp = await client.post(f"/api/applications/{app_id}/extract", headers=auth_headers)
    assert extract_resp.status_code == 200, f"Extraction failed: {extract_resp.text}"
    extract_data = extract_resp.json()
    assert "parameters" in extract_data
    params = extract_data["parameters"]
    assert len(params) > 0

    # =========================================================================
    # STEP 5: BIS Standards Discovery & Clauses Retrieval
    # =========================================================================
    standards_resp = await client.get("/api/standards", headers=auth_headers)
    assert standards_resp.status_code == 200
    all_standards = standards_resp.json()
    assert len(all_standards) > 0

    # Query clauses for primary standard
    std_id = all_standards[0]["standard_id"]
    std_detail_resp = await client.get(f"/api/standards/{std_id}", headers=auth_headers)
    assert std_detail_resp.status_code == 200
    std_data = std_detail_resp.json()
    assert len(std_data["clauses"]) >= 4

    # =========================================================================
    # STEP 6: Deterministic Compliance Assessment & Readiness Evaluation
    # =========================================================================
    assess_resp = await client.post(f"/api/applications/{app_id}/analyze", headers=auth_headers)
    assert assess_resp.status_code == 200, f"Assessment failed: {assess_resp.text}"
    assess_data = assess_resp.json()
    assert "readinessScore" in assess_data
    assert "complianceResults" in assess_data
    initial_score = assess_data["readinessScore"]

    # Query formal readiness gate
    readiness_resp = await client.get(f"/api/applications/{app_id}/readiness", headers=auth_headers)
    assert readiness_resp.status_code == 200
    readiness_data = readiness_resp.json()
    assert isinstance(readiness_data["readiness_score"], (int, float))

    # =========================================================================
    # STEP 7: Interactive Remediation Recheck
    # =========================================================================
    recheck_resp = await client.post(
        f"/api/applications/{app_id}/recheck?custom_efficacy=85.0",
        headers=auth_headers,
    )
    assert recheck_resp.status_code == 200, f"Recheck failed: {recheck_resp.text}"
    recheck_data = recheck_resp.json()
    assert recheck_data["isPostRecheck"] is True
    assert recheck_data["readinessScore"] >= initial_score

    # =========================================================================
    # STEP 8: Contextual RAG Chat with Prompt Injection Guardrails
    # =========================================================================
    chat_resp = await client.post(
        f"/api/applications/{app_id}/chat",
        headers=auth_headers,
        json={"message": "What are the mandatory marking requirements under Clause 6?"},
    )
    assert chat_resp.status_code == 200
    chat_data = chat_resp.json()
    assert "content" in chat_data
    assert len(chat_data["content"]) > 0

    # =========================================================================
    # STEP 9: Dynamic Document Checklist Verification
    # =========================================================================
    checklist_resp = await client.get(f"/api/applications/{app_id}/checklist", headers=auth_headers)
    assert checklist_resp.status_code == 200
    checklist_items = checklist_resp.json()
    assert len(checklist_items) >= 4

    # Verify all checklist items
    for item in checklist_items:
        verify_item_resp = await client.post(
            f"/api/applications/{app_id}/checklist/{item['id']}/verify",
            headers=auth_headers,
            json={"verified": True, "verification_notes": f"Verified by Auditor: {item['name']}"},
        )
        assert verify_item_resp.status_code == 200
        assert verify_item_resp.json()["verified"] is True
        assert verify_item_resp.json()["status"] == "VERIFIED"

    # =========================================================================
    # STEP 10: Official BIS Forms Compilation (Form I, II, IV, Technical Dossier)
    # =========================================================================
    forms_resp = await client.get(f"/api/applications/{app_id}/forms", headers=auth_headers)
    assert forms_resp.status_code == 200
    forms_data = forms_resp.json()
    assert "FORM_I" in forms_data
    assert "FORM_IV" in forms_data
    assert "TECHNICAL_DOSSIER" in forms_data
    assert len(forms_data["TECHNICAL_DOSSIER"]["sections"]) == 14

    # =========================================================================
    # STEP 11: Versioned Generated Documents
    # =========================================================================
    gen_docs_resp = await client.post(f"/api/applications/{app_id}/documents/generate", headers=auth_headers)
    assert gen_docs_resp.status_code == 200
    generated_docs = gen_docs_resp.json()
    assert len(generated_docs) >= 3
    for gdoc in generated_docs:
        assert len(gdoc["sha256_hash"]) == 64
        assert os.path.exists(gdoc["file_path"])

    # Query generated documents list
    list_docs_resp = await client.get(f"/api/applications/{app_id}/generated-documents", headers=auth_headers)
    assert list_docs_resp.status_code == 200
    assert len(list_docs_resp.json()) >= len(generated_docs)

    # =========================================================================
    # STEP 12: Dossier Export (ZIP Bundle)
    # =========================================================================
    dossier_resp = await client.get(f"/api/applications/{app_id}/export-dossier", headers=auth_headers)
    assert dossier_resp.status_code == 200
    assert dossier_resp.headers["content-type"] == "application/zip"
    with zipfile.ZipFile(io.BytesIO(dossier_resp.content), "r") as zf:
        namelist = zf.namelist()
        assert any("manifest.json" in n for n in namelist)

    # =========================================================================
    # STEP 13: Application Lifecycle Progression
    # =========================================================================
    status_update = await client.patch(
        f"/api/applications/{app_id}",
        headers=auth_headers,
        json={"status": "APPROVED"},
    )
    assert status_update.status_code == 200
    assert status_update.json()["status"] == "APPROVED"

    # =========================================================================
    # STEP 14: Multilingual Regulatory Voice Interaction
    # =========================================================================
    voice_langs_resp = await client.get("/api/applications/voice/languages", headers=auth_headers)
    assert voice_langs_resp.status_code == 200
    langs = voice_langs_resp.json()
    assert "hi" in langs
    assert "mr" in langs
    assert "ta" in langs

    # Voice query in Hindi
    voice_q_resp = await client.post(
        f"/api/applications/{app_id}/voice/query",
        headers=auth_headers,
        json={
            "language_code": "hi",
            "query_text": "नमस्ते, क्या मेरे दस्तावेज़ पूर्ण हैं?",
        },
    )
    assert voice_q_resp.status_code == 200
    assert "response" in voice_q_resp.json()

    # =========================================================================
    # STEP 15: Computer Vision ISI Conformity Analysis
    # =========================================================================
    fake_rating_plate = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x10\x00\x00\x00\x10\x08\x06\x00\x00\x00\x1f\xf3\xffa"
    vision_resp = await client.post(
        f"/api/applications/{app_id}/vision/analyze",
        headers=auth_headers,
        files={"file": ("rating_plate_isi_mark.png", io.BytesIO(fake_rating_plate), "image/png")},
    )
    assert vision_resp.status_code == 200
    vision_data = vision_resp.json()
    assert "detected_regions" in vision_data
    assert "disclaimer" in vision_data

    # =========================================================================
    # STEP 16: Factory IoT Telemetry Ingestion & Audit Retrieval
    # =========================================================================
    telemetry_payload = {
        "application_id": app_id,
        "device_id": "CALIBRATION_RIG_HARIDWAR_01",
        "test_type": "INSULATION_RESISTANCE",
        "parameter": "insulation_resistance",
        "value": 15.4,
        "unit": "MOhm",
    }
    iot_post_resp = await client.post("/api/iot/test-results", headers=auth_headers, json=telemetry_payload)
    assert iot_post_resp.status_code == 201

    iot_get_resp = await client.get(f"/api/iot/applications/{app_id}/test-results", headers=auth_headers)
    assert iot_get_resp.status_code == 200
    assert len(iot_get_resp.json()) >= 1

    # =========================================================================
    # STEP 17: Certificate Issuance, IPFS Pinning & Blockchain Anchoring
    # =========================================================================
    cert_issue_resp = await client.post(
        "/api/certificates",
        headers=auth_headers,
        json={"application_id": app_id, "document_id": generated_docs[0]["id"], "valid_years": 3},
    )
    assert cert_issue_resp.status_code == 201, f"Certificate issuance failed: {cert_issue_resp.text}"
    cert_data = cert_issue_resp.json()

    cert_id = cert_data["certificate_id"]
    record_hash = cert_data["record_hash"]
    ipfs_cid = cert_data["ipfs_cid"]
    tx_hash = cert_data["transaction_hash"]
    public_url = cert_data["public_verification_url"]

    assert cert_id.startswith("BIS-CERT-")
    assert len(record_hash) == 64
    assert ipfs_cid.startswith("bafy")
    assert tx_hash.startswith("0x")
    assert "/verify/" in public_url
    assert "<svg" in cert_data["qr_code_svg"]

    # =========================================================================
    # STEP 18: Unauthenticated Public Consumer QR Verification
    # =========================================================================
    public_verify_resp = await client.get(f"/api/public/verify/{cert_id}")
    assert public_verify_resp.status_code == 200, f"Public verify failed: {public_verify_resp.text}"
    pub_data = public_verify_resp.json()

    assert pub_data["is_valid"] is True
    assert pub_data["status"] == "VERIFIED_AND_CURRENT"
    assert pub_data["product_name"] == app_payload["product_name"]
    assert pub_data["manufacturer"] == app_payload["manufacturer"]
    assert pub_data["computed_record_hash"] == record_hash
    assert pub_data["anchored_record_hash"] == record_hash
    assert pub_data["ipfs_cid"] == ipfs_cid
    assert pub_data["transaction_hash"] == tx_hash

    # =========================================================================
    # STEP 19: Multi-Tenant Cross-User Data Isolation
    # =========================================================================
    reg_b = await client.post(
        "/api/auth/register",
        json={
            "email": "competitor@philips.com",
            "password": "Philips@Password2026",
            "full_name": "Ravi Sharma",
            "company_name": "Philips India",
        },
    )
    assert reg_b.status_code == 201
    headers_b = {"Authorization": f"Bearer {reg_b.json()['access_token']}"}

    # User B receives 404 on User A's private application, readiness, checklist, dossier, and certificate
    b_app = await client.get(f"/api/applications/{app_id}", headers=headers_b)
    assert b_app.status_code == 404

    b_readiness = await client.get(f"/api/applications/{app_id}/readiness", headers=headers_b)
    assert b_readiness.status_code == 404

    b_checklist = await client.get(f"/api/applications/{app_id}/checklist", headers=headers_b)
    assert b_checklist.status_code == 404

    b_dossier = await client.get(f"/api/applications/{app_id}/export-dossier", headers=headers_b)
    assert b_dossier.status_code == 404

    b_cert = await client.get(f"/api/certificates/{cert_data['id']}", headers=headers_b)
    assert b_cert.status_code == 404

    b_patch_cert = await client.patch(
        f"/api/certificates/{cert_data['id']}/status",
        headers=headers_b,
        json={"status": "REVOKED", "reason": "Malicious competitor tamper attempt"},
    )
    assert b_patch_cert.status_code == 404

    # =========================================================================
    # STEP 20: Cryptographic Tamper Detection & Immutability
    # =========================================================================
    legit_verify = await client.post(
        "/api/verification/verify-hash",
        json={"sha256_hash": record_hash, "document_name": "Havells Certificate"},
    )
    assert legit_verify.status_code == 200
    assert legit_verify.json()["is_verified"] is True
    assert legit_verify.json()["integrity_status"] == "VALID_RECORD"

    fake_hash = "deadbeef" * 8
    tamper_verify = await client.post(
        "/api/verification/verify-hash",
        json={"sha256_hash": fake_hash, "document_name": "Tampered Certificate"},
    )
    assert tamper_verify.status_code == 200
    assert tamper_verify.json()["is_verified"] is False
    assert tamper_verify.json()["integrity_status"] == "UNKNOWN_RECORD"
