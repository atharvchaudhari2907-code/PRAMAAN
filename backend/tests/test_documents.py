import hashlib
import io
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_document_upload_validation_and_hashing(client: AsyncClient):
    # Register & Login
    reg_resp = await client.post(
        "/api/auth/register",
        json={
            "email": "docuser@example.com",
            "password": "DocUser@Pass123",
            "full_name": "Doc User",
        },
    )
    token = reg_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Create Application
    create_resp = await client.post(
        "/api/applications",
        headers=headers,
        json={
            "product_name": "Pressure Cooker 5L",
            "category": "Kitchen & Pressure Cookers",
        },
    )
    app_id = create_resp.json()["id"]

    # 1. Valid PDF Upload
    pdf_content = b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog >>\nendobj\ntrailer\n<< /Root 1 0 R >>\n%%EOF"
    expected_hash = hashlib.sha256(pdf_content).hexdigest()

    pdf_file = io.BytesIO(pdf_content)
    upload_resp = await client.post(
        f"/api/applications/{app_id}/documents",
        headers=headers,
        files={"file": ("datasheet.pdf", pdf_file, "application/pdf")},
    )
    assert upload_resp.status_code == 201
    doc_data = upload_resp.json()["document"]
    assert doc_data["sha256_hash"] == expected_hash
    assert doc_data["original_filename"] == "datasheet.pdf"
    doc_id = doc_data["id"]

    # Application status should have transitioned to DOCUMENT_UPLOADED
    app_status_resp = await client.get(f"/api/applications/{app_id}", headers=headers)
    assert app_status_resp.json()["status"] == "DOCUMENT_UPLOADED"

    # 2. Secure Download
    download_resp = await client.get(
        f"/api/applications/{app_id}/documents/{doc_id}/download",
        headers=headers,
    )
    assert download_resp.status_code == 200
    assert download_resp.content == pdf_content

    # 3. Invalid Extension Rejection (.exe)
    exe_file = io.BytesIO(b"MZ\x90\x00\x03")
    bad_ext_resp = await client.post(
        f"/api/applications/{app_id}/documents",
        headers=headers,
        files={"file": ("malicious.exe", exe_file, "application/octet-stream")},
    )
    assert bad_ext_resp.status_code == 400
    assert "not supported" in bad_ext_resp.json()["detail"].lower()

    # 4. Disguised Header Rejection (named .pdf but contents are not PDF)
    fake_pdf = io.BytesIO(b"NOT A REAL PDF HEADER")
    fake_hdr_resp = await client.post(
        f"/api/applications/{app_id}/documents",
        headers=headers,
        files={"file": ("corrupt.pdf", fake_pdf, "application/pdf")},
    )
    assert fake_hdr_resp.status_code == 400
    assert "magic bytes" in fake_hdr_resp.json()["detail"].lower() or "header does not match" in fake_hdr_resp.json()["detail"].lower()
