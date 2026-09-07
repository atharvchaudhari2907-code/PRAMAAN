import hashlib
import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.application import (
    Application,
    ApplicationStatus,
    ApplicationStatusEvent,
    GeneratedDocument,
)
from app.schemas.dossier import BISFormDefinition
from app.services.checklist_service import ChecklistService
from app.services.form_generator import FormGenerator
from app.services.pdf_builder import SimplePDFBuilder

logger = logging.getLogger(__name__)


def compute_sha256(file_path: str) -> str:
    h = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(8192):
            h.update(chunk)
    return h.hexdigest()


class DossierExporter:

    @staticmethod
    async def generate_dossier(
        db: AsyncSession,
        application: Application,
        document_types: Optional[List[str]] = None,
        force_generate: bool = False,
    ) -> List[GeneratedDocument]:
        """
        Generates official BIS Form I, Form II, Form IV, and 14-section Technical Dossier.
        Stores immutable versioned PDFs & JSONs in uploads/{application.id}/generated/v{version}/.
        Calculates SHA-256 cryptographic hashes for every document.
        """
        # 1. Check readiness gate
        readiness = await ChecklistService.evaluate_readiness_gate(db, application)
        if not readiness.is_ready and not force_generate:
            logger.warning(
                f"Application {application.id} generated dossier with warnings: {readiness.validation_status}. "
                f"Missing docs: {len(readiness.missing_documents)}, critical clauses: {len(readiness.failed_critical_clauses)}"
            )

        # 2. Determine monotonic version
        ver_stmt = select(func.coalesce(func.max(GeneratedDocument.version), 0)).where(
            GeneratedDocument.application_id == application.id
        )
        ver_res = await db.execute(ver_stmt)
        current_version = ver_res.scalar_one()
        new_version = current_version + 1

        # 3. Setup output directory
        base_dir = Path("uploads") / application.id / "generated" / f"v{new_version}"
        os.makedirs(base_dir, exist_ok=True)

        # 4. Build all form definitions
        forms: Dict[str, BISFormDefinition] = await FormGenerator.build_forms(db, application)

        selected_types = document_types or ["FORM_I", "FORM_II", "FORM_IV", "TECHNICAL_DOSSIER"]
        generated_records: List[GeneratedDocument] = []
        bundle_docs_info: List[Dict] = []

        for doc_type in selected_types:
            if doc_type not in forms:
                continue

            form_def = forms[doc_type]

            # Generate PDF
            pdf_filename = f"{doc_type.lower()}_v{new_version}.pdf"
            pdf_path = str(base_dir / pdf_filename)
            pdf_builder = SimplePDFBuilder(title=form_def.title, subtitle=form_def.description)
            pdf_builder.add_header()

            for sec in form_def.sections:
                pdf_builder.add_section_title(sec.section_title)
                for fld in sec.fields:
                    pdf_builder.add_field(
                        label=fld.label,
                        value=str(fld.value),
                        source=fld.source,
                    )

            pdf_builder.build_pdf(pdf_path)
            pdf_hash = compute_sha256(pdf_path)

            # Generate JSON definition
            json_filename = f"{doc_type.lower()}_v{new_version}.json"
            json_path = str(base_dir / json_filename)
            form_json_str = form_def.model_dump_json(indent=2)
            with open(json_path, "w", encoding="utf-8") as jf:
                jf.write(form_json_str)
            json_hash = compute_sha256(json_path)

            # Record PDF in database
            pdf_doc = GeneratedDocument(
                application_id=application.id,
                document_type=doc_type,
                document_name=f"{form_def.title} (v{new_version})",
                version=new_version,
                file_path=pdf_path,
                mime_type="application/pdf",
                sha256_hash=pdf_hash,
                metadata_json=json.dumps(
                    {
                        "form_id": doc_type,
                        "title": form_def.title,
                        "sections_count": len(form_def.sections),
                        "json_companion": json_path,
                        "json_hash": json_hash,
                    }
                ),
            )
            db.add(pdf_doc)
            generated_records.append(pdf_doc)

            bundle_docs_info.append(
                {
                    "document_type": doc_type,
                    "document_name": form_def.title,
                    "pdf_path": pdf_path,
                    "pdf_sha256": pdf_hash,
                    "json_path": json_path,
                    "json_sha256": json_hash,
                }
            )

        # 5. Build Complete Bundle Package JSON
        bundle_data = {
            "application_id": application.id,
            "application_number": application.application_number,
            "bundle_version": new_version,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "readiness_score": readiness.readiness_score,
            "validation_status": readiness.validation_status,
            "documents": bundle_docs_info,
            "forms": {k: v.model_dump() for k, v in forms.items() if k in selected_types},
        }

        bundle_filename = f"dossier_package_v{new_version}.json"
        bundle_path = str(base_dir / bundle_filename)
        with open(bundle_path, "w", encoding="utf-8") as bf:
            json.dump(bundle_data, bf, indent=2)
        bundle_hash = compute_sha256(bundle_path)

        bundle_doc = GeneratedDocument(
            application_id=application.id,
            document_type="DOSSIER_BUNDLE",
            document_name=f"Complete BIS Dossier Package (v{new_version})",
            version=new_version,
            file_path=bundle_path,
            mime_type="application/json",
            sha256_hash=bundle_hash,
            metadata_json=json.dumps({"bundle_version": new_version, "document_count": len(generated_records)}),
        )
        db.add(bundle_doc)
        generated_records.append(bundle_doc)

        # 6. Update application status & log tracking event
        if application.status in (
            ApplicationStatus.DRAFT,
            ApplicationStatus.DOCUMENT_UPLOADED,
            ApplicationStatus.EXTRACTION_PENDING,
            ApplicationStatus.PARAMETER_REVIEW,
            ApplicationStatus.STANDARD_MATCHING,
            ApplicationStatus.COMPLIANCE_ANALYSIS,
            ApplicationStatus.READY_FOR_APPLICATION,
        ):
            application.status = ApplicationStatus.APPLICATION_PREPARED

        event = ApplicationStatusEvent(
            application_id=application.id,
            from_status=application.status.value,
            to_status=ApplicationStatus.APPLICATION_PREPARED.value,
            event_type="DOSSIER_GENERATED",
            description=f"Generated BIS Application Dossier version v{new_version} with {len(generated_records)} documents (Package SHA-256: {bundle_hash[:12]}...).",
            source="SYSTEM",
            metadata_json=json.dumps({"version": new_version, "package_hash": bundle_hash}),
        )
        db.add(event)
        await db.flush()

        return generated_records
