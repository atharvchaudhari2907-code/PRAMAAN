import os
import pytest
from httpx import AsyncClient
from pathlib import Path

from app.services.standard_service import VERIFIED_STANDARDS_SEED

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"
SAMPLE_PDF_PATH = FIXTURES_DIR / "sample_led_datasheet.pdf"


@pytest.mark.asyncio
async def test_full_real_document_intelligence_pipeline(client: AsyncClient):
    """
    STOP CONDITION INTEGRATION TEST:
    Verifies that a real PDF datasheet travels through the complete Phase 2 pipeline:
    1. UPLOAD (real PDF document)
    2. EXTRACTION (pypdf text extraction + snippet tracking)
    3. PARAMETER REVIEW (GET & PATCH audit trail)
    4. STANDARD MATCH (RAG-based verified BIS matching)
    5. CLAUSE RETRIEVAL (clause-level vector search & reranking)
    6. COMPLIANCE ANALYSIS (deterministic checks + evidence traceability)
    7. MATHEMATICAL READINESS SCORING & GAPS
    8. PARAMETER REMEDIATION & DYNAMIC RE-CHECK
    9. GROUNDED CONTEXTUAL CHAT WITH BIS CITATIONS
    10. APPLICATION DOSSIER PREPARATION (FORM IV)
    """
    # ---------------------------------------------------------------------
    # Step 0: Register & Authenticate Manufacturer
    # ---------------------------------------------------------------------
    auth_email = "engineer@lumenstar.in"
    auth_password = "SecurePassword123!"

    reg_resp = await client.post(
        "/api/auth/register",
        json={
            "email": auth_email,
            "password": auth_password,
            "full_name": "LumenStar Lead Compliance Engineer",
            "company_name": "LumenStar Lighting Technologies Pvt Ltd",
        },
    )
    assert reg_resp.status_code in [200, 201]

    login_resp = await client.post(
        "/api/auth/login",
        json={"email": auth_email, "password": auth_password},
    )
    assert login_resp.status_code == 200
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # ---------------------------------------------------------------------
    # Step 1: Create Application
    # ---------------------------------------------------------------------
    app_resp = await client.post(
        "/api/applications",
        headers=headers,
        json={
            "product_name": "9W Self-Ballasted LED Lamp",
            "category": "Lighting & Luminaires",
            "model_number": "LMN-LED-09W-B22",
            "manufacturer": "LumenStar Lighting Technologies Pvt Ltd",
            "manufacturing_location": "Noida, Uttar Pradesh",
        },
    )
    assert app_resp.status_code == 201
    app_data = app_resp.json()
    app_id = app_data["id"]
    assert app_id is not None
    assert app_data["status"] == "DRAFT"

    # ---------------------------------------------------------------------
    # Step 2: Upload Real PDF Datasheet
    # ---------------------------------------------------------------------
    assert SAMPLE_PDF_PATH.exists(), f"Sample PDF missing at {SAMPLE_PDF_PATH}"
    with open(SAMPLE_PDF_PATH, "rb") as f:
        pdf_bytes = f.read()

    upload_resp = await client.post(
        f"/api/applications/{app_id}/upload",
        headers=headers,
        files={"file": ("sample_led_datasheet.pdf", pdf_bytes, "application/pdf")},
        data={"document_type": "TECHNICAL_DATASHEET"},
    )
    assert upload_resp.status_code == 201
    upload_data = upload_resp.json()["document"]
    assert "sha256_hash" in upload_data
    assert len(upload_data["sha256_hash"]) == 64

    # ---------------------------------------------------------------------
    # Step 3: Extract Parameters from PDF Document
    # ---------------------------------------------------------------------
    extract_resp = await client.post(
        f"/api/applications/{app_id}/extract",
        headers=headers,
    )
    assert extract_resp.status_code == 200
    extract_data = extract_resp.json()
    extracted_params = extract_data["parameters"]
    assert len(extracted_params) >= 5

    # Check required LED parameters were extracted from the PDF
    params_by_key = {p["parameter_key"]: p for p in extracted_params}
    assert "luminous_efficacy" in params_by_key
    assert "wattage" in params_by_key
    assert "voltage" in params_by_key
    assert "power_factor" in params_by_key
    assert "thd" in params_by_key

    # Verify values extracted from the PDF datasheet
    assert params_by_key["luminous_efficacy"]["value"] == "78"
    assert params_by_key["luminous_efficacy"]["unit"] == "lm/W"
    assert params_by_key["luminous_efficacy"]["source_page"] == 1
    assert "Luminous Efficacy" in params_by_key["luminous_efficacy"]["source_snippet"]
    assert params_by_key["luminous_efficacy"]["confidence"] == "HIGH"
    assert params_by_key["luminous_efficacy"]["is_user_modified"] is False

    # ---------------------------------------------------------------------
    # Step 4: Parameter Review (GET & PATCH with Audit Trail)
    # ---------------------------------------------------------------------
    get_params_resp = await client.get(
        f"/api/applications/{app_id}/parameters",
        headers=headers,
    )
    assert get_params_resp.status_code == 200
    reviewed_params = get_params_resp.json()
    assert len(reviewed_params) == len(extracted_params)

    # Patch a parameter to verify modification tracking
    efficacy_param = next(p for p in reviewed_params if p["parameter_key"] == "luminous_efficacy")
    efficacy_param_id = efficacy_param["id"]

    patch_resp = await client.patch(
        f"/api/applications/{app_id}/parameters/{efficacy_param_id}",
        headers=headers,
        json={"value": "78.5", "is_user_verified": True},
    )
    assert patch_resp.status_code == 200
    patched_data = patch_resp.json()
    assert patched_data["value"] == "78.5"
    assert patched_data["original_value"] == "78"
    assert patched_data["modified_value"] == "78.5"
    assert patched_data["is_user_modified"] is True
    assert patched_data["modified_by"] is not None
    assert patched_data["modified_at"] is not None

    # ---------------------------------------------------------------------
    # Step 5: BIS Standard Identification (RAG matching against real standards)
    # ---------------------------------------------------------------------
    std_match_resp = await client.post(
        f"/api/applications/{app_id}/identify-standards",
        headers=headers,
    )
    assert std_match_resp.status_code == 200
    candidates = std_match_resp.json()
    assert len(candidates) >= 1

    # Check that top candidate is verified IS 16102
    primary_candidate = candidates[0]
    assert "16102" in primary_candidate["standard_id"]
    assert primary_candidate["confidence_score"] >= 0.90
    assert primary_candidate["is_primary"] is True

    # Never invent a standard: verify standard is present in knowledge base
    verified_ids = [v["standard_id"] for v in VERIFIED_STANDARDS_SEED]
    assert any(primary_candidate["standard_id"] == vid for vid in verified_ids)

    # Select the standard
    select_resp = await client.post(
        f"/api/applications/{app_id}/select-standard",
        headers=headers,
        json={"standard_id": primary_candidate["standard_id"]},
    )
    assert select_resp.status_code == 200

    # ---------------------------------------------------------------------
    # Step 6: Retrieve Requirements (Clause-level RAG)
    # ---------------------------------------------------------------------
    retrieve_resp = await client.post(
        f"/api/applications/{app_id}/retrieve",
        headers=headers,
    )
    assert retrieve_resp.status_code == 200
    retrieved_clauses = retrieve_resp.json()
    assert len(retrieved_clauses) >= 4
    assert any("6" in str(c.get("clause")) for c in retrieved_clauses)

    # ---------------------------------------------------------------------
    # Step 7: Compliance Analysis & Gap Generation
    # ---------------------------------------------------------------------
    analyze_resp = await client.post(
        f"/api/applications/{app_id}/analyze",
        headers=headers,
    )
    assert analyze_resp.status_code == 200
    analysis = analyze_resp.json()

    # Check evidence traceability
    assert len(analysis["complianceResults"]) >= 5
    efficacy_check = next(
        (r for r in analysis["complianceResults"] if "Efficacy" in r["parameter_name"]), None
    )
    assert efficacy_check is not None
    assert efficacy_check["status"] == "FAIL"
    assert efficacy_check["is_deterministic"] is True
    assert efficacy_check["product_source"] is not None
    assert efficacy_check["bis_source"] is not None
    assert "78.5 lm/W" in efficacy_check["product_evidence"]

    # Check Gaps generated
    assert len(analysis["gaps"]) >= 1
    efficacy_gap = next((g for g in analysis["gaps"] if "Efficacy" in g["parameter"]), None)
    assert efficacy_gap is not None
    assert efficacy_gap["priority"] == "HIGH PRIORITY"
    assert "78.5 lm/W" in efficacy_gap["currentValue"]

    # Check Mathematical Readiness Score (failing efficacy caps score under 78%)
    initial_readiness = analysis["readinessScore"]
    assert initial_readiness < 80.0
    assert analysis["readiness"]["passed_count"] >= 4
    assert analysis["readiness"]["failed_count"] >= 1

    # Check Cost Breakdown estimates (with disclaimers)
    assert analysis["costEstimate"]["totalFees"] > 0
    assert "Gazette" in analysis["costEstimate"]["disclaimer"]


    # ---------------------------------------------------------------------
    # Step 8: Fix Gap via Parameter Remediation & Re-check
    # ---------------------------------------------------------------------
    # Remediate efficacy to 84.0 lm/W (above 80.0 lm/W statutory threshold)
    recheck_resp = await client.post(
        f"/api/applications/{app_id}/recheck?custom_efficacy=84.0",
        headers=headers,
    )
    assert recheck_resp.status_code == 200
    recheck_data = recheck_resp.json()

    assert recheck_data["isPostRecheck"] is True
    new_readiness = recheck_data["readinessScore"]
    # Readiness score must dynamically increase based on verified math
    assert new_readiness > initial_readiness
    assert new_readiness >= 90.0

    # Efficacy compliance result must now PASS
    new_efficacy_check = next(
        (r for r in recheck_data["complianceResults"] if "Efficacy" in r["parameter_name"]), None
    )
    assert new_efficacy_check is not None
    assert new_efficacy_check["status"] == "PASS"

    # Optical gap must be marked resolved
    new_optical_gap = next(
        (g for g in recheck_data["gaps"] if "Efficacy" in g.get("parameter", "") or "Optical" in g.get("title", "")),
        None,
    )
    if new_optical_gap:
        assert new_optical_gap["isResolved"] is True

    # ---------------------------------------------------------------------
    # Step 9: Contextual AI Chat (Grounded with Citations)
    # ---------------------------------------------------------------------
    chat_resp = await client.post(
        f"/api/applications/{app_id}/chat",
        headers=headers,
        json={"message": "What is the luminous efficacy requirement under this standard?"},
    )
    assert chat_resp.status_code == 200
    chat_data = chat_resp.json()
    assert len(chat_data["citations"]) >= 1
    assert any("16102" in c["standard_id"] for c in chat_data["citations"])
    assert "80.0 lm/W" in chat_data["content"] or "Clause" in chat_data["content"]

    # ---------------------------------------------------------------------
    # Step 10: Application Dossier Preparation (Form IV)
    # ---------------------------------------------------------------------
    prep_resp = await client.post(
        f"/api/applications/{app_id}/prepare-application",
        headers=headers,
    )
    assert prep_resp.status_code == 200
    prep_data = prep_resp.json()
    assert len(prep_data["fields"]) >= 5
    assert any("Form IV" in f["value"] for f in prep_data["fields"])
    assert len(prep_data["required_documents"]) >= 3
    assert "manakonline.in" in prep_data["official_portal_url"]
