import hashlib
import logging
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.interactions import IoTTestResult

logger = logging.getLogger(__name__)


class IoTTestPayload(BaseModel):
    device_id: str = Field(..., description="ESP8266 or bench sensor hardware identifier")
    lab_id: Optional[str] = "NTH-LAB-01"
    test_type: str = Field(..., description="DIELECTRIC_WITHSTAND, TEMPERATURE_RISE, INSULATION_RESISTANCE, PRESSURE_TEST")
    parameter: str
    value: float
    unit: str
    timestamp: Optional[str] = None
    signature: Optional[str] = None
    application_id: str


class IoTTestResponse(BaseModel):
    id: str
    application_id: str
    device_id: str
    parameter_name: str
    measured_value: float
    unit: str
    notes: Optional[str] = None
    status: str = "INGESTED"
    created_at: str


class IoTTestResultProvider:

    @staticmethod
    async def ingest_result(db: AsyncSession, payload: IoTTestPayload) -> IoTTestResult:
        notes = f"Test Type: {payload.test_type} | Lab: {payload.lab_id or 'In-house'} | Signature: {payload.signature or 'unsigned'}"
        record = IoTTestResult(
            application_id=payload.application_id,
            device_id=payload.device_id,
            parameter_name=payload.parameter,
            measured_value=payload.value,
            unit=payload.unit,
            notes=notes,
        )
        db.add(record)
        await db.flush()
        logger.info(f"[IoT Ingest] Ingested {payload.parameter}={payload.value}{payload.unit} from {payload.device_id}")
        return record

    @staticmethod
    async def list_results(db: AsyncSession, application_id: str) -> List[IoTTestResult]:
        stmt = select(IoTTestResult).where(IoTTestResult.application_id == application_id).order_by(IoTTestResult.created_at.desc())
        res = await db.execute(stmt)
        return list(res.scalars().all())
