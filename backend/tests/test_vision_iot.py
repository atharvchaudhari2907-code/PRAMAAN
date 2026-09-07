import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.application import Application, ApplicationStatus
from app.models.user import User
from app.services.vision_provider import get_vision_provider


@pytest.mark.asyncio
async def test_yolov8_vision_provider_structure_and_disclaimer():
    """
    Tests YOLOv8 computer vision detection and mandatory evidence disclaimer.
    The vision provider must explicitly state that it generates evidence for human review only.
    """
    provider = get_vision_provider()
    dummy_image_data = b"\xFF\xD8\xFF\xE0\x00\x10JFIF\x00\x01\x01\x01\x00`\x00`\x00\x00\xFF\xDB\x00C\x00"

    result = await provider.analyze_image(dummy_image_data, "sample_rating_plate.jpg")

    assert result.model_version.startswith("YOLOv8")
    assert len(result.detected_regions) > 0
    # Must contain rating plate, ISI mark, or enclosure detection
    classes = [obj.class_name for obj in result.detected_regions]
    assert "rating_plate" in classes or "isi_mark" in classes or "product_enclosure" in classes
    # Must enforce disclaimer
    assert "human audit review only" in result.disclaimer
    assert "NOT certify a product" in result.disclaimer


@pytest.mark.asyncio
async def test_iot_telemetry_ingestion_and_retrieval(
    client: AsyncClient,
    db_session: AsyncSession,
):
    """Tests laboratory IoT telemetry ingestion and query."""
    user = User(
        email="iot_lab_tech@testinglab.in",
        hashed_password="pw_hash_test",
        full_name="Lab Tech",
        role="lab_technician",
        company_name="National Testing House",
    )
    db_session.add(user)
    await db_session.flush()

    app = Application(
        user_id=user.id,
        application_number="BIS-2026-660001",
        product_name="Induction Cooktop",
        category="Heating Appliances",
        manufacturer="Prestige Kitchen",
        model_number="PIC-20.0",
        primary_standard_id="IS 302 (Part 2/Sec 6)",
        status=ApplicationStatus.APPROVED,
    )
    db_session.add(app)
    await db_session.commit()
    await db_session.refresh(app)

    # 1. Ingest IoT sensor reading
    payload = {
        "device_id": "ESP8266-BENCH-04",
        "lab_id": "NTH-LAB-DELHI",
        "test_type": "Insulation Resistance Test",
        "parameter": "insulation_resistance",
        "value": 25.4,
        "unit": "MΩ",
        "application_id": app.id,
        "notes": "Automated high-voltage megohmmeter bench reading",
    }
    ingest_res = await client.post("/api/iot/test-results", json=payload)
    assert ingest_res.status_code == 201
    ingest_data = ingest_res.json()
    assert ingest_data["parameter_name"] == "insulation_resistance"
    assert ingest_data["measured_value"] == 25.4
    assert ingest_data["unit"] == "MΩ"
    assert ingest_data["device_id"] == "ESP8266-BENCH-04"

    # 2. Retrieve IoT readings for the application
    get_res = await client.get(f"/api/iot/applications/{app.id}/test-results")
    assert get_res.status_code == 200
    records = get_res.json()
    assert len(records) >= 1
    assert records[0]["parameter_name"] == "insulation_resistance"
    assert records[0]["device_id"] == "ESP8266-BENCH-04"
