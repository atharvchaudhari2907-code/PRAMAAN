from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.middleware.auth_middleware import get_current_user
from app.models.user import User
from app.services.iot_provider import IoTTestPayload, IoTTestResponse, IoTTestResultProvider

router = APIRouter(prefix="/iot", tags=["IoT Test Telemetry Ingestion"])


@router.post("/test-results", response_model=IoTTestResponse, status_code=status.HTTP_201_CREATED)
async def ingest_iot_test_result(
    payload: IoTTestPayload,
    db: AsyncSession = Depends(get_db),
):
    """
    Ingests laboratory sensor telemetry (e.g. from ESP8266 or bench data logger).
    Accepts automated electrical/physical test readings for continuous quality monitoring.
    """
    record = await IoTTestResultProvider.ingest_result(db, payload)
    return IoTTestResponse(
        id=record.id,
        application_id=record.application_id,
        device_id=record.device_id,
        parameter_name=record.parameter_name,
        measured_value=record.measured_value,
        unit=record.unit,
        notes=record.notes,
        created_at=record.created_at.isoformat(),
    )


@router.get("/applications/{application_id}/test-results", response_model=List[IoTTestResponse])
async def list_iot_test_results(
    application_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Retrieves all sensor readings recorded for a specific application."""
    records = await IoTTestResultProvider.list_results(db, application_id)
    return [
        IoTTestResponse(
            id=r.id,
            application_id=r.application_id,
            device_id=r.device_id,
            parameter_name=r.parameter_name,
            measured_value=r.measured_value,
            unit=r.unit,
            notes=r.notes,
            created_at=r.created_at.isoformat(),
        )
        for r in records
    ]
