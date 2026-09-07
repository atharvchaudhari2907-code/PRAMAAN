import json
import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.application import (
    Application,
    ApplicationStatus,
    ApplicationStatusEvent,
    ApplicationSubmission,
    GeneratedDocument,
)
from app.schemas.dossier import ApplicationSubmissionRequest
from app.services.checklist_service import ChecklistService

logger = logging.getLogger(__name__)


class BISSubmissionProvider(ABC):

    @abstractmethod
    async def prepare_submission_bundle(self, db: AsyncSession, application: Application) -> Dict[str, Any]:
        """Prepares submission manifest and guidelines for official BIS portal."""
        pass

    @abstractmethod
    async def submit_application(
        self,
        db: AsyncSession,
        application: Application,
        submission_req: ApplicationSubmissionRequest,
    ) -> ApplicationSubmission:
        """Records official submission acknowledgement and updates tracking lifecycle."""
        pass


class ManualSubmissionProvider(BISSubmissionProvider):
    """
    Standard submission provider for BIS Manakonline Portal (https://www.manakonline.in).
    Prepares verified PDF dossier bundles and records official acknowledgement references.
    """

    async def prepare_submission_bundle(self, db: AsyncSession, application: Application) -> Dict[str, Any]:
        readiness = await ChecklistService.evaluate_readiness_gate(db, application)
        checklist = await ChecklistService.get_or_create_checklist(db, application)

        # Get latest generated documents
        stmt = (
            select(GeneratedDocument)
            .where(GeneratedDocument.application_id == application.id)
            .order_by(GeneratedDocument.version.desc(), GeneratedDocument.created_at.desc())
        )
        res = await db.execute(stmt)
        docs = list(res.scalars().all())

        latest_version = docs[0].version if docs else 0
        latest_docs = [d for d in docs if d.version == latest_version]

        bundle_doc = next((d for d in latest_docs if d.document_type == "DOSSIER_BUNDLE"), None)
        package_hash = bundle_doc.sha256_hash if bundle_doc else "NOT_GENERATED"

        return {
            "application_id": application.id,
            "application_number": application.application_number,
            "readiness_score": readiness.readiness_score,
            "is_ready": readiness.is_ready,
            "package_version": latest_version,
            "package_hash": package_hash,
            "portal_url": "https://www.manakonline.in",
            "instructions": [
                "1. Log into the official BIS Manakonline Portal (https://www.manakonline.in) using your manufacturer credentials.",
                "2. Navigate to 'Product Certification Scheme (Scheme I)' -> 'Apply for New Licence'.",
                "3. Fill in Form I, Form II, and Form IV using the verified data extracted in your technical dossier.",
                "4. Upload the generated PDF documents (Form I, Form II, Form IV, and Technical Dossier).",
                "5. Upon successful submission on Manakonline, copy the BIS Application Reference / Acknowledgement Number and enter it below to initiate real-time stage tracking.",
            ],
            "documents": [
                {
                    "document_type": d.document_type,
                    "document_name": d.document_name,
                    "file_path": d.file_path,
                    "mime_type": d.mime_type,
                    "sha256_hash": d.sha256_hash,
                }
                for d in latest_docs
            ],
            "checklist": [
                {
                    "name": item.name,
                    "document_type": item.document_type,
                    "status": item.status,
                    "verified": item.verified,
                }
                for item in checklist
            ],
        }

    async def submit_application(
        self,
        db: AsyncSession,
        application: Application,
        submission_req: ApplicationSubmissionRequest,
    ) -> ApplicationSubmission:
        # Check latest package hash
        stmt = (
            select(GeneratedDocument)
            .where(
                GeneratedDocument.application_id == application.id,
                GeneratedDocument.document_type == "DOSSIER_BUNDLE",
            )
            .order_by(GeneratedDocument.version.desc())
        )
        res = await db.execute(stmt)
        bundle_doc = res.scalars().first()
        package_hash = bundle_doc.sha256_hash if bundle_doc else "MANUAL_SUBMISSION"

        prev_status = application.status.value

        # Record submission
        submission = ApplicationSubmission(
            application_id=application.id,
            reference_number=submission_req.reference_number,
            portal_url=submission_req.portal_url or "https://www.manakonline.in",
            submission_status="SUBMITTED",
            submitted_by=submission_req.submitted_by,
            package_hash=package_hash,
            notes=submission_req.notes,
        )
        db.add(submission)

        # Transition application status
        application.status = ApplicationStatus.SUBMITTED

        # Record status tracking event
        event = ApplicationStatusEvent(
            application_id=application.id,
            from_status=prev_status,
            to_status=ApplicationStatus.SUBMITTED.value,
            event_type="APPLICATION_SUBMITTED",
            description=f"Application submitted to BIS Manakonline portal under acknowledgement ref: {submission_req.reference_number}.",
            note=submission_req.notes,
            source="MANUFACTURER_PORTAL",
            metadata_json=json.dumps(
                {
                    "reference_number": submission_req.reference_number,
                    "portal_url": submission_req.portal_url or "https://www.manakonline.in",
                    "submitted_by": submission_req.submitted_by,
                    "package_hash": package_hash,
                }
            ),
        )
        db.add(event)
        await db.flush()

        logger.info(
            f"Application {application.id} submitted with reference {submission_req.reference_number} by {submission_req.submitted_by}"
        )
        return submission
