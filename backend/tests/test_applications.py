import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_application_lifecycle_and_tracking(client: AsyncClient):
    # Register & Login
    reg_resp = await client.post(
        "/api/auth/register",
        json={
            "email": "appuser@example.com",
            "password": "AppUser@Pass123",
            "full_name": "App User",
            "company_name": "App Electronics Ltd",
        },
    )
    token = reg_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Create Application
    create_resp = await client.post(
        "/api/applications",
        headers=headers,
        json={
            "product_name": "Smart Iron 1500W",
            "category": "Household Electrical Appliances",
            "model_number": "SI-1500",
            "manufacturer": "App Electronics Ltd",
            "manufacturing_location": "Bengaluru, Karnataka",
            "primary_standard_id": "IS 302 (Part 2/Sec 3) : 2007",
        },
    )
    assert create_resp.status_code == 201
    app_data = create_resp.json()
    app_id = app_data["id"]
    assert app_data["status"] == "DRAFT"
    assert app_data["application_number"].startswith("BIS-")

    # 2. Get Application Details
    detail_resp = await client.get(f"/api/applications/{app_id}", headers=headers)
    assert detail_resp.status_code == 200
    assert detail_resp.json()["product_name"] == "Smart Iron 1500W"
    assert len(detail_resp.json()["status_events"]) >= 1

    # 3. Update status to READY_FOR_APPLICATION
    patch_resp = await client.patch(
        f"/api/applications/{app_id}",
        headers=headers,
        json={"status": "READY_FOR_APPLICATION", "readiness_score": 92.5},
    )
    assert patch_resp.status_code == 200
    assert patch_resp.json()["status"] == "READY_FOR_APPLICATION"
    assert patch_resp.json()["readiness_score"] == 92.5

    # 4. Check Tracking Events
    tracking_resp = await client.get(f"/api/applications/{app_id}/tracking", headers=headers)
    assert tracking_resp.status_code == 200
    events = tracking_resp.json()
    assert len(events) >= 5
    assert any(e["status"] == "IN_PROGRESS" for e in events)

    # 5. Delete Application
    del_resp = await client.delete(f"/api/applications/{app_id}", headers=headers)
    assert del_resp.status_code == 200

    # 6. Verify Deletion
    get_del = await client.get(f"/api/applications/{app_id}", headers=headers)
    assert get_del.status_code == 404
