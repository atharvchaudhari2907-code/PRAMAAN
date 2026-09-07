import logging
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.application import (
    Application,
    ApplicationChecklistItem,
    ApplicationDocument,
    ApplicationStatus,
)
from app.models.assessment import Assessment, ComplianceGap, ComplianceResult
from app.schemas.dossier import ReadinessGateResponse

logger = logging.getLogger(__name__)

STANDARD_CHECKLIST_TEMPLATE = [
    {
        "document_type": "TECHNICAL_DATASHEET",
        "name": "Technical Specification & Datasheet",
        "description": "Detailed electrical, physical, and mechanical specifications matching product model.",
        "required": True,
    },
    {
        "document_type": "TEST_REPORT",
        "name": "Laboratory Test Report",
        "description": "Complete test reports covering critical safety clauses issued by in-house or accredited laboratory.",
        "required": True,
    },
    {
        "document_type": "FACTORY_LAYOUT",
        "name": "Factory Layout & Plant Diagram",
        "description": "Diagram of manufacturing premises indicating production line, quality inspection bay, and raw material storage.",
        "required": True,
    },
    {
        "document_type": "MACHINERY_LIST",
        "name": "List of Manufacturing Machinery & Tooling",
        "description": "Comprehensive machinery schedule including machine make, model, capacity, and serial numbers.",
        "required": True,
    },
    {
        "document_type": "QUALITY_PLAN",
        "name": "Scheme of Inspection and Testing (SIT) / Quality Control Plan",
        "description": "Quality assurance plan outlining incoming raw material inspection, in-process controls, and finished product testing.",
        "required": True,
    },
    {
        "document_type": "CALIBRATION_CERT",
        "name": "Test Equipment Calibration Certificates",
        "description": "Valid calibration certificates for all measuring and test equipment from NABL/accredited calibration laboratories.",
        "required": True,
    },
    {
        "document_type": "FORM_IV_DOSSIER",
        "name": "Manufacturing Process Flowchart & BOM",
        "description": "Step-by-step process flow with critical control points and complete Bill of Materials (BOM).",
        "required": False,
    },
    {
        "document_type": "TRADEMARK_REG",
        "name": "Brand / Trademark Authorization",
        "description": "Trademark registration certificate or authorization letter from the brand owner for BIS marking.",
        "required": False,
    },
]


class ChecklistService:

    @staticmethod
    async def get_or_create_checklist(db: AsyncSession, application: Application) -> List[ApplicationChecklistItem]:
        """Fetch existing checklist items or initialize from BIS template."""
        stmt = (
            select(ApplicationChecklistItem)
            .where(ApplicationChecklistItem.application_id == application.id)
            .order_by(ApplicationChecklistItem.required.desc(), ApplicationChecklistItem.created_at)
        )
        result = await db.execute(stmt)
        items = list(result.scalars().all())

        # Deduplicate items if concurrent requests created duplicate entries
        unique_by_type = {}
        duplicates_to_delete = []
        for item in items:
            dtype = item.document_type
            if dtype not in unique_by_type:
                unique_by_type[dtype] = item
            else:
                existing = unique_by_type[dtype]
                if (item.verified or item.status in ("UPLOADED", "VERIFIED")) and not (
                    existing.verified or existing.status in ("UPLOADED", "VERIFIED")
                ):
                    duplicates_to_delete.append(existing)
                    unique_by_type[dtype] = item
                else:
                    duplicates_to_delete.append(item)

        if duplicates_to_delete:
            for dup in duplicates_to_delete:
                await db.delete(dup)
            await db.flush()
            items = list(unique_by_type.values())

        # If any template document types are missing, seed them
        existing_types = {i.document_type for i in items}
        added = False
        for template in STANDARD_CHECKLIST_TEMPLATE:
            if template["document_type"] not in existing_types:
                item = ApplicationChecklistItem(
                    application_id=application.id,
                    document_type=template["document_type"],
                    name=template["name"],
                    description=template["description"],
                    required=template["required"],
                    status="REQUIRED",
                    verified=False,
                )
                db.add(item)
                existing_types.add(template["document_type"])
                added = True

        if added:
            await db.flush()
            result = await db.execute(stmt)
            items = list(result.scalars().all())

        # Sync with uploaded application documents
        doc_stmt = select(ApplicationDocument).where(ApplicationDocument.application_id == application.id)
        doc_res = await db.execute(doc_stmt)
        docs = list(doc_res.scalars().all())
        doc_by_type = {doc.document_type.value if hasattr(doc.document_type, "value") else str(doc.document_type): doc for doc in docs}

        modified = False
        for item in items:
            if item.status == "REQUIRED" and item.document_type in doc_by_type:
                matched_doc = doc_by_type[item.document_type]
                item.uploaded_document_id = matched_doc.id
                item.status = "UPLOADED"
                modified = True

        if modified:
            await db.flush()

        return items

    @staticmethod
    async def verify_checklist_item(
        db: AsyncSession,
        application_id: str,
        item_id: str,
        verified: bool,
        notes: Optional[str] = None,
    ) -> Optional[ApplicationChecklistItem]:
        stmt = select(ApplicationChecklistItem).where(
            ApplicationChecklistItem.id == item_id,
            ApplicationChecklistItem.application_id == application_id,
        )
        result = await db.execute(stmt)
        item = result.scalar_one_or_none()
        if not item:
            return None

        item.verified = verified
        item.status = "VERIFIED" if verified else "REJECTED"
        if notes:
            item.verification_notes = notes
        await db.flush()
        return item

    @staticmethod
    async def evaluate_readiness_gate(db: AsyncSession, application: Application) -> ReadinessGateResponse:
        """
        Evaluate if application satisfies all criteria to generate formal BIS dossiers and proceed to submission.
        Criteria:
        - Readiness score >= 70.0
        - Zero failed critical clauses
        - All required checklist items uploaded/verified
        - Key manufacturer & product information present
        """
        checklist = await ChecklistService.get_or_create_checklist(db, application)

        # 1. Missing information
        missing_info: List[str] = []
        if not application.manufacturer:
            missing_info.append("Manufacturer legal name is missing")
        if not application.manufacturing_location:
            missing_info.append("Manufacturing facility address is missing")
        if not application.model_number:
            missing_info.append("Product model number is missing")
        if not application.primary_standard_id:
            missing_info.append("Primary BIS standard is not linked")

        # 2. Missing documents (mandatory checklist items not uploaded)
        missing_docs: List[str] = []
        for item in checklist:
            if item.required and item.status not in ("UPLOADED", "VERIFIED"):
                missing_docs.append(f"{item.name} ({item.document_type})")
        missing_docs = list(dict.fromkeys(missing_docs))

        # 3. Critical clauses & assessment results
        failed_critical: List[str] = []
        stmt = (
            select(Assessment)
            .where(Assessment.application_id == application.id)
            .options(
                selectinload(Assessment.compliance_results),
                selectinload(Assessment.gaps),
            )
            .order_by(Assessment.created_at.desc())
        )
        res = await db.execute(stmt)
        latest_assessment = res.scalars().first()

        base_compliance_score = 100.0
        if latest_assessment:
            for gap in latest_assessment.gaps:
                if gap.severity == "CRITICAL":
                    failed_critical.append(f"Critical Gap: {gap.title} - {gap.parameter_name} ({gap.current_value} vs {gap.reference_requirement})")
            for cr in latest_assessment.compliance_results:
                if cr.compliance_status in ("FAIL", "DEFICIT") and "CRITICAL" in cr.clause_title.upper():
                    clause_desc = f"Clause {cr.clause_number}: {cr.clause_title} ({cr.compliance_status})"
                    if clause_desc not in failed_critical:
                        failed_critical.append(clause_desc)
            if latest_assessment.readiness_score is not None:
                base_compliance_score = latest_assessment.readiness_score

        # 4. Calculate weighted readiness score
        # Compliance weight: 50%
        # Document checklist weight: 35%
        # Metadata completeness: 15%
        total_mandatory_docs = sum(1 for i in checklist if i.required)
        verified_or_uploaded_docs = sum(
            1 for i in checklist if i.required and (i.status in ("UPLOADED", "VERIFIED") or i.verified)
        )
        doc_score = (verified_or_uploaded_docs / total_mandatory_docs * 100.0) if total_mandatory_docs > 0 else 100.0

        meta_total = 4
        meta_present = meta_total - len(missing_info)
        meta_score = (meta_present / meta_total * 100.0)

        readiness_score = round(
            (0.50 * base_compliance_score) + (0.35 * doc_score) + (0.15 * meta_score),
            1
        )

        # Severe penalty if critical clauses failed
        if failed_critical:
            readiness_score = min(readiness_score, 45.0)

        is_ready = (readiness_score >= 70.0) and (len(failed_critical) == 0) and (len(missing_docs) == 0)

        if is_ready:
            validation_status = "READY"
        elif failed_critical:
            validation_status = "GAPS_DETECTED"
        else:
            validation_status = "NOT_READY"

        required_actions: List[str] = []
        for info in missing_info:
            required_actions.append(f"Complete manufacturer profile: {info}")
        for doc in missing_docs:
            required_actions.append(f"Upload required document: {doc}")
        for clause in failed_critical:
            required_actions.append(f"Resolve non-compliant safety clause: {clause}")

        if is_ready and not required_actions:
            required_actions.append("All gating conditions satisfied. Proceed to generate official BIS application dossier.")

        # Update application readiness_score in DB
        application.readiness_score = readiness_score
        await db.flush()

        return ReadinessGateResponse(
            application_id=application.id,
            readiness_score=readiness_score,
            validation_status=validation_status,
            missing_information=missing_info,
            missing_documents=missing_docs,
            failed_critical_clauses=failed_critical,
            required_actions=required_actions,
            is_ready=is_ready,
        )
