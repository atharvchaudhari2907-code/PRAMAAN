import os
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_phase3_complete_certification_workflow(client: AsyncClient):
    # 1. Register and login
    user_payload = {
        "email": "manufacturer_phase3@example.com",
        "password": "Password123!",
        "full_name": "Apex Electricals",
        "company_name": "Apex Electrical Industries Pvt Ltd",
    }
    reg_res = await client.post("/api/auth/register", json=user_payload)
    assert reg_res.status_code == 201
    token = reg_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Create Application with manufacturer details
    app_payload = {
        "product_name": "Apex 16A 3-Pin Safety Plug",
        "category": "Electrical Accessories",
        "model_number": "APX-PLUG-16A",
        "manufacturer": "Apex Electrical Industries Pvt Ltd",
        "manufacturing_location": "Plot 42, Electronics Zone, Okhla Phase III, New Delhi 110020",
        "primary_standard_id": "IS 1293:2019",
    }
    create_res = await client.post("/api/applications", json=app_payload, headers=headers)
    assert create_res.status_code == 201
    app_data = create_res.json()
    app_id = app_data["id"]

    # 3. Dynamic Checklist - Initial retrieval & seeding
    checklist_res = await client.get(f"/api/applications/{app_id}/checklist", headers=headers)
    assert checklist_res.status_code == 200
    checklist = checklist_res.json()
    assert len(checklist) >= 6
    mandatory_items = [item for item in checklist if item["required"]]
    assert len(mandatory_items) >= 4
    first_item_id = checklist[0]["id"]

    # 4. Readiness Gate - Initial evaluation (Should not be ready because documents are missing)
    readiness_res = await client.get(f"/api/applications/{app_id}/readiness", headers=headers)
    assert readiness_res.status_code == 200
    readiness_data = readiness_res.json()
    assert readiness_data["application_id"] == app_id
    assert isinstance(readiness_data["readiness_score"], float)
    assert len(readiness_data["missing_documents"]) > 0

    # 5. Verify checklist items
    for item in checklist:
        verify_res = await client.post(
            f"/api/applications/{app_id}/checklist/{item['id']}/verify",
            json={"verified": True, "verification_notes": f"Verified by QC Manager: {item['name']}"},
            headers=headers,
        )
        assert verify_res.status_code == 200
        assert verify_res.json()["verified"] is True
        assert verify_res.json()["status"] == "VERIFIED"

    # Re-evaluate readiness gate after checklist verification
    readiness_after = await client.get(f"/api/applications/{app_id}/readiness", headers=headers)
    assert readiness_after.status_code == 200
    r_data_after = readiness_after.json()
    assert len(r_data_after["missing_documents"]) == 0
    assert r_data_after["is_ready"] is True
    assert r_data_after["validation_status"] == "READY"

    # 6. BIS Forms Inspection & Field Provenance Tracking
    forms_res = await client.get(f"/api/applications/{app_id}/forms", headers=headers)
    assert forms_res.status_code == 200
    forms = forms_res.json()
    assert "FORM_I" in forms
    assert "FORM_II" in forms
    assert "FORM_IV" in forms
    assert "TECHNICAL_DOSSIER" in forms

    # Validate provenance and technical dossier 14 sections
    dossier_form = forms["TECHNICAL_DOSSIER"]
    assert len(dossier_form["sections"]) == 14
    for sec in dossier_form["sections"]:
        for fld in sec["fields"]:
            assert fld["source"] in (
                "AI_EXTRACTED",
                "MANUFACTURER_INPUT",
                "BIS_STANDARD_CATALOG",
                "SYSTEM_DEFAULT",
            )

    # 7. Document Generation (Version 1)
    gen_res = await client.post(f"/api/applications/{app_id}/documents/generate", headers=headers)
    assert gen_res.status_code == 200
    docs_v1 = gen_res.json()
    assert len(docs_v1) >= 5
    for doc in docs_v1:
        assert doc["version"] == 1
        assert len(doc["sha256_hash"]) == 64
        assert os.path.exists(doc["file_path"])

    # Download one generated PDF
    pdf_doc = next(d for d in docs_v1 if d["mime_type"] == "application/pdf")
    dl_res = await client.get(
        f"/api/applications/{app_id}/generated-documents/{pdf_doc['id']}/download",
        headers=headers,
    )
    assert dl_res.status_code == 200
    assert dl_res.content.startswith(b"%PDF-1.4")

    # Direct Form Downloads: Verify FORM I, FORM II, FORM IV, and TECHNICAL DOSSIER downloads
    for form_t in ["FORM_I", "FORM_II", "FORM_IV", "TECHNICAL_DOSSIER"]:
        # PDF download
        pdf_dl = await client.get(f"/api/applications/{app_id}/forms/{form_t}/download?format=pdf", headers=headers)
        assert pdf_dl.status_code == 200, f"PDF download for {form_t} failed: {pdf_dl.text}"
        assert pdf_dl.content.startswith(b"%PDF-1.4")

        # JSON download
        json_dl = await client.get(f"/api/applications/{app_id}/forms/{form_t}/download?format=json", headers=headers)
        assert json_dl.status_code == 200, f"JSON download for {form_t} failed: {json_dl.text}"
        assert b"form_id" in json_dl.content or b"title" in json_dl.content

    # 8. Monotonic Versioning (Generate Version 2)
    gen_v2_res = await client.post(f"/api/applications/{app_id}/documents/generate", headers=headers)
    assert gen_v2_res.status_code == 200
    docs_v2 = gen_v2_res.json()
    for doc in docs_v2:
        assert doc["version"] == 2

    # Verify both v1 and v2 files exist on disk simultaneously
    list_docs_res = await client.get(f"/api/applications/{app_id}/generated-documents", headers=headers)
    assert list_docs_res.status_code == 200
    all_docs = list_docs_res.json()
    versions = {d["version"] for d in all_docs}
    assert 1 in versions
    assert 2 in versions

    # 9. Submission Manifest
    manifest_res = await client.get(f"/api/applications/{app_id}/submission-manifest", headers=headers)
    assert manifest_res.status_code == 200
    manifest = manifest_res.json()
    assert manifest["portal_url"] == "https://www.manakonline.in"
    assert manifest["package_version"] == 2
    assert len(manifest["instructions"]) > 0

    # 10. Official BIS Portal Submission
    submission_payload = {
        "reference_number": "BIS-MANAK-2026-894120",
        "portal_url": "https://www.manakonline.in",
        "submitted_by": "Apex Quality Director (rajesh.kumar@apex.in)",
        "notes": "Completed preliminary inspection fee deposit. Application submitted under Scheme I.",
    }
    submit_res = await client.post(f"/api/applications/{app_id}/submit", json=submission_payload, headers=headers)
    assert submit_res.status_code == 200
    sub_data = submit_res.json()
    assert sub_data["reference_number"] == submission_payload["reference_number"]
    assert sub_data["submission_status"] == "SUBMITTED"

    # Verify application status transitioned
    get_app_res = await client.get(f"/api/applications/{app_id}", headers=headers)
    assert get_app_res.status_code == 200
    assert get_app_res.json()["status"] == "SUBMITTED"

    # 11. Real Event Logging & Status Transitions
    events_res = await client.get(f"/api/applications/{app_id}/events", headers=headers)
    assert events_res.status_code == 200
    events = events_res.json()
    event_types = [e["event_type"] for e in events if e.get("event_type")]
    assert "DOSSIER_GENERATED" in event_types
    assert "APPLICATION_SUBMITTED" in event_types

    # Create next lifecycle milestone event (Lab Testing)
    new_event_payload = {
        "to_status": "LAB_TESTING",
        "event_type": "SAMPLE_DISPATCHED",
        "description": "5 test specimens dispatched to National Test House (NTH), Ghaziabad.",
        "note": "Courier AWB: DTDC-99281726",
        "source": "MANUFACTURER",
    }
    create_event_res = await client.post(
        f"/api/applications/{app_id}/events",
        json=new_event_payload,
        headers=headers,
    )
    assert create_event_res.status_code == 200
    assert create_event_res.json()["to_status"] == "LAB_TESTING"

    # Confirm updated status
    updated_app = await client.get(f"/api/applications/{app_id}", headers=headers)
    assert updated_app.json()["status"] == "LAB_TESTING"
