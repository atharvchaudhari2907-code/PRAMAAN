import random
from datetime import datetime, timezone
from typing import List, Optional
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.application import Application, ApplicationStatus, ApplicationStatusEvent
from app.models.product import Product, ProductParameter
from app.repositories.application_repository import ApplicationRepository
from app.schemas.application import (
    ApplicationCreate,
    ApplicationDetailResponse,
    ApplicationResponse,
    ApplicationUpdate,
    TrackingEventResponse,
)


class ApplicationService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.app_repo = ApplicationRepository(db)

    def _generate_application_number(self) -> str:
        year = datetime.now(timezone.utc).year
        random_digits = "".join(random.choices("0123456789", k=6))
        return f"BIS-{year}-{random_digits}"

    async def create_application(self, user_id: str, data: ApplicationCreate) -> Application:
        app_number = self._generate_application_number()
        app = Application(
            user_id=user_id,
            application_number=app_number,
            status=ApplicationStatus.DRAFT,
            product_name=data.product_name.strip(),
            category=data.category.strip(),
            model_number=data.model_number.strip() if data.model_number else None,
            manufacturer=data.manufacturer.strip() if data.manufacturer else None,
            manufacturing_location=data.manufacturing_location.strip() if data.manufacturing_location else None,
            additional_notes=data.additional_notes.strip() if data.additional_notes else None,
            primary_standard_id=data.primary_standard_id,
        )
        await self.app_repo.create(app)

        # Create linked product
        product = Product(
            application_id=app.id,
            name=app.product_name,
            category=app.category,
            model_number=app.model_number,
            manufacturer=app.manufacturer,
            additional_notes=app.additional_notes,
        )
        self.db.add(product)
        await self.db.flush()

        # Add initial status event
        event = ApplicationStatusEvent(
            application_id=app.id,
            from_status=None,
            to_status=ApplicationStatus.DRAFT.value,
            note="Application created in DRAFT status.",
            actor_id=user_id,
        )
        await self.app_repo.add_status_event(event)
        return app

    async def list_applications(self, user_id: str) -> List[Application]:
        return await self.app_repo.list_by_user(user_id)

    async def get_application(self, application_id: str, user_id: str) -> Application:
        app = await self.app_repo.get_by_id_and_user(application_id, user_id, load_details=True)
        if not app:
            # Fallback 1: Match by application_number across user applications
            stmt = (
                select(Application)
                .where(
                    Application.user_id == user_id,
                    (Application.application_number == application_id) | (Application.id == application_id),
                )
                .options(
                    selectinload(Application.documents),
                    selectinload(Application.status_events),
                    selectinload(Application.product).selectinload(Product.parameters),
                )
            )
            res = await self.db.execute(stmt)
            app = res.scalar_one_or_none()

            # Fallback 2: If demo ID (ASMT- or demo), return latest active application for this user
            if not app and (application_id.startswith("ASMT-") or "demo" in application_id.lower()):
                stmt_latest = (
                    select(Application)
                    .where(Application.user_id == user_id)
                    .order_by(Application.created_at.desc())
                    .options(
                        selectinload(Application.documents),
                        selectinload(Application.status_events),
                        selectinload(Application.product).selectinload(Product.parameters),
                    )
                )
                res_latest = await self.db.execute(stmt_latest)
                app = res_latest.scalars().first()

        if not app:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Application not found or you do not have permission to access it.",
            )
        return app

    async def update_application(
        self, application_id: str, user_id: str, data: ApplicationUpdate
    ) -> Application:
        app = await self.get_application(application_id, user_id)

        old_status = app.status.value
        if data.product_name is not None:
            app.product_name = data.product_name.strip()
        if data.category is not None:
            app.category = data.category.strip()
        if data.model_number is not None:
            app.model_number = data.model_number.strip()
        if data.manufacturer is not None:
            app.manufacturer = data.manufacturer.strip()
        if data.manufacturing_location is not None:
            app.manufacturing_location = data.manufacturing_location.strip()
        if data.additional_notes is not None:
            app.additional_notes = data.additional_notes.strip()
        if data.primary_standard_id is not None:
            app.primary_standard_id = data.primary_standard_id.strip()
        if data.readiness_score is not None:
            app.readiness_score = data.readiness_score

        if data.status is not None and data.status != app.status:
            app.status = data.status
            event = ApplicationStatusEvent(
                application_id=app.id,
                from_status=old_status,
                to_status=app.status.value,
                note=f"Status transitioned from {old_status} to {app.status.value}.",
                actor_id=user_id,
            )
            await self.app_repo.add_status_event(event)

        await self.db.flush()
        return app

    async def delete_application(self, application_id: str, user_id: str) -> None:
        app = await self.get_application(application_id, user_id)
        await self.app_repo.delete(app)

    async def get_tracking_events(
        self, application_id: str, user_id: str
    ) -> List[TrackingEventResponse]:
        app = await self.get_application(application_id, user_id)

        # Standard BIS Certification Lifecycle Stages
        stages = [
            ("PRE_ASSESSMENT", "Pre-Certification Assessment", "Automated compliance analysis and gap report"),
            ("DOC_SUBMISSION", "Application Filing & Document Verification", "Submission of Form IV and supporting technical file"),
            ("LAB_TESTING", "Accredited Laboratory Testing", "Sample dispatched to BIS-recognized laboratory for performance checks"),
            ("FACTORY_INSPECTION", "Factory Audit & Quality Inspection", "On-site scrutiny of manufacturing controls and test equipment"),
            ("BIS_SCRUTINY", "BIS Directorate Scrutiny", "Final technical review and committee verification"),
            ("CERTIFICATE_GRANT", "Grant of BIS Certification", "Standard Mark License and immutable registry anchoring"),
        ]

        status_order = {
            ApplicationStatus.DRAFT: 0,
            ApplicationStatus.DOCUMENT_UPLOADED: 0,
            ApplicationStatus.EXTRACTION_PENDING: 0,
            ApplicationStatus.PARAMETER_REVIEW: 0,
            ApplicationStatus.STANDARD_MATCHING: 0,
            ApplicationStatus.COMPLIANCE_ANALYSIS: 0,
            ApplicationStatus.GAPS_FOUND: 0,
            ApplicationStatus.READY_FOR_APPLICATION: 0,
            ApplicationStatus.APPLICATION_PREPARED: 1,
            ApplicationStatus.SUBMITTED: 1,
            ApplicationStatus.LAB_TESTING: 2,
            ApplicationStatus.INSPECTION: 3,
            ApplicationStatus.BIS_SCRUTINY: 4,
            ApplicationStatus.APPROVED: 5,
            ApplicationStatus.CERTIFICATE_ISSUED: 5,
        }
        current_idx = status_order.get(app.status, 0)

        events: List[TrackingEventResponse] = []
        for idx, (stage_code, title, desc) in enumerate(stages):
            if idx < current_idx:
                s = "COMPLETED"
            elif idx == current_idx:
                s = "IN_PROGRESS"
            else:
                s = "PENDING"

            events.append(
                TrackingEventResponse(
                    id=f"TRK-{app.id[:6]}-{idx+1}",
                    title=title,
                    stage=stage_code,
                    status=s,
                    description=desc,
                    date=app.created_at.strftime("%b %d, %Y") if idx <= current_idx else None,
                )
            )
        return events
