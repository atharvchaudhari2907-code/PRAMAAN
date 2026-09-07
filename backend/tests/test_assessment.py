import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_full_assessment_pipeline(client: AsyncClient):
    # 1. Register user
    reg_res = await client.post(
        "/api/auth/register",
        json={
            "email": "manufacturer_assessment@test.com",
            "password": "SecurePassword123!",
            "full_name": "Assessment Engineer",
            "company_name": "Luminous Tech Pvt Ltd",
        },
    )
    assert reg_res.status_code == 201
    token = reg_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Create Application
    create_res = await client.post(
        "/api/applications",
        headers=headers,
        json={
            "product_name": "9W LED Bulb Series A",
            "category": "Lighting & Luminaires",
            "model_number": "LED-9W-01",
            "manufacturer": "Luminous Tech Pvt Ltd",
            "manufacturing_location": "Noida, Uttar Pradesh",
        },
    )
    assert create_res.status_code == 201
    app_id = create_res.json()["id"]

    # 3. Extract Parameters
    extract_res = await client.post(f"/api/applications/{app_id}/extract", headers=headers)
    assert extract_res.status_code == 200
    extract_data = extract_res.json()
    assert "parameters" in extract_data
    assert len(extract_data["parameters"]) > 0
    param_keys = [p["parameter_key"] for p in extract_data["parameters"]]
    assert "luminous_efficacy" in param_keys or "wattage" in param_keys

    # 4. Update Parameters
    update_params_res = await client.put(
        f"/api/applications/{app_id}/parameters",
        headers=headers,
        json={"parameters": extract_data["parameters"]},
    )
    assert update_params_res.status_code == 200

    # 5. Identify Standards
    identify_res = await client.post(f"/api/applications/{app_id}/identify-standard", headers=headers)
    assert identify_res.status_code == 200
    candidates = identify_res.json()
    assert len(candidates) > 0
    primary_std = next((c for c in candidates if c["is_primary"]), candidates[0])
    assert "16102" in primary_std["standard_id"]

    # 6. Select Standard
    select_res = await client.post(
        f"/api/applications/{app_id}/select-standard",
        headers=headers,
        json={"standard_id": primary_std["standard_id"]},
    )
    assert select_res.status_code == 200

    # 7. Retrieve Requirements
    retrieve_res = await client.post(f"/api/applications/{app_id}/retrieve", headers=headers)
    assert retrieve_res.status_code == 200
    clauses = retrieve_res.json()
    assert len(clauses) > 0

    # 8. Run Compliance Analysis
    analyze_res = await client.post(f"/api/applications/{app_id}/analyze", headers=headers)
    assert analyze_res.status_code == 200
    analysis = analyze_res.json()
    assert "readinessScore" in analysis
    assert "gaps" in analysis
    assert "complianceResults" in analysis
    assert len(analysis["complianceResults"]) > 0

    # 9. Recheck with improved luminous efficacy
    recheck_res = await client.post(
        f"/api/applications/{app_id}/recheck?custom_efficacy=85.0",
        headers=headers,
    )
    assert recheck_res.status_code == 200
    recheck_data = recheck_res.json()
    assert recheck_data["isPostRecheck"] is True
    assert recheck_data["readinessScore"] >= 90.0

    # 10. Prepare Form IV Application
    prep_res = await client.post(f"/api/applications/{app_id}/prepare-application", headers=headers)
    assert prep_res.status_code == 200
    prep_data = prep_res.json()
    assert prep_data["validation_status"] == "READY_FOR_MANAKONLINE"
    assert len(prep_data["fields"]) > 0

    # 11. Contextual RAG Chat
    chat_res = await client.post(
        f"/api/applications/{app_id}/chat",
        headers=headers,
        json={"message": "What are the insulation resistance and marking requirements?"},
    )
    assert chat_res.status_code == 200
    chat_data = chat_res.json()
    assert "content" in chat_data
    assert len(chat_data["citations"]) > 0
