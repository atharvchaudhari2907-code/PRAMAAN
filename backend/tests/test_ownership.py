import io
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_cross_user_ownership_isolation(client: AsyncClient):
    # 1. Register User A
    resp_a = await client.post(
        "/api/auth/register",
        json={
            "email": "usera@example.com",
            "password": "UserA@Password123",
            "full_name": "User Alpha",
            "company_name": "Alpha Corp",
        },
    )
    assert resp_a.status_code == 201
    token_a = resp_a.json()["access_token"]
    headers_a = {"Authorization": f"Bearer {token_a}"}

    # 2. Register User B
    resp_b = await client.post(
        "/api/auth/register",
        json={
            "email": "userb@example.com",
            "password": "UserB@Password123",
            "full_name": "User Beta",
            "company_name": "Beta Corp",
        },
    )
    assert resp_b.status_code == 201
    token_b = resp_b.json()["access_token"]
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # 3. User A creates an application
    create_resp = await client.post(
        "/api/applications",
        headers=headers_a,
        json={
            "product_name": "Alpha LED Bulb",
            "category": "Lighting & Luminaires",
            "model_number": "AL-01",
            "manufacturer": "Alpha Corp",
            "manufacturing_location": "Noida, UP",
        },
    )
    assert create_resp.status_code == 201
    app_id = create_resp.json()["id"]

    # 4. User B attempts to view User A's application -> 404
    resp_b_view = await client.get(
        f"/api/applications/{app_id}",
        headers=headers_b,
    )
    assert resp_b_view.status_code == 404

    # 5. User B attempts to modify User A's application -> 404
    resp_b_patch = await client.patch(
        f"/api/applications/{app_id}",
        headers=headers_b,
        json={"product_name": "Tampered Name"},
    )
    assert resp_b_patch.status_code == 404

    # 6. User B attempts to upload document to User A's application -> 404
    fake_pdf = io.BytesIO(b"%PDF-1.4 Fake PDF Content for Test")
    resp_b_upload = await client.post(
        f"/api/applications/{app_id}/documents",
        headers=headers_b,
        files={"file": ("fake.pdf", fake_pdf, "application/pdf")},
    )
    assert resp_b_upload.status_code == 404

    # 7. User B attempts to delete User A's application -> 404
    resp_b_del = await client.delete(
        f"/api/applications/{app_id}",
        headers=headers_b,
    )
    assert resp_b_del.status_code == 404

    # 8. User B listing applications sees 0 applications
    list_b = await client.get("/api/applications", headers=headers_b)
    assert list_b.status_code == 200
    assert len(list_b.json()) == 0

    # User A listing applications sees 1 application
    list_a = await client.get("/api/applications", headers=headers_a)
    assert list_a.status_code == 200
    assert len(list_a.json()) == 1
    assert list_a.json()[0]["id"] == app_id

    # 9. Phase 3 Isolation: User B cannot inspect User A's readiness, checklist, generated docs, or dossier
    resp_b_readiness = await client.get(f"/api/applications/{app_id}/readiness", headers=headers_b)
    assert resp_b_readiness.status_code == 404

    resp_b_checklist = await client.get(f"/api/applications/{app_id}/checklist", headers=headers_b)
    assert resp_b_checklist.status_code == 404

    resp_b_docs = await client.get(f"/api/applications/{app_id}/generated-documents", headers=headers_b)
    assert resp_b_docs.status_code == 404

    resp_b_dossier = await client.get(f"/api/applications/{app_id}/export-dossier", headers=headers_b)
    assert resp_b_dossier.status_code == 404

    # 10. Phase 4 Isolation: Issue certificate for User A, verify User B cannot read or modify private cert
    cert_issue = await client.post(
        "/api/certificates",
        headers=headers_a,
        json={"application_id": app_id, "valid_years": 3},
    )
    assert cert_issue.status_code == 201
    cert_id = cert_issue.json()["id"]
    public_id = cert_issue.json()["certificate_id"]

    # User B attempting to view private certificate details -> 404
    resp_b_cert = await client.get(f"/api/certificates/{cert_id}", headers=headers_b)
    assert resp_b_cert.status_code == 404

    # User B attempting to update certificate status -> 404
    resp_b_status = await client.patch(
        f"/api/certificates/{cert_id}/status",
        headers=headers_b,
        json={"status": "REVOKED", "reason": "Unauthorized malicious revocation"},
    )
    assert resp_b_status.status_code == 404

    # User A can view own certificate
    resp_a_cert = await client.get(f"/api/certificates/{cert_id}", headers=headers_a)
    assert resp_a_cert.status_code == 200

    # Public verification endpoint remains accessible unauthenticated (for consumers scanning QR code)
    resp_public = await client.get(f"/api/public/verify/{public_id}")
    assert resp_public.status_code == 200
    assert resp_public.json()["certificate_id"] == public_id

