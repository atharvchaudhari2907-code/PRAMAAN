import io
import json
import os
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.middleware.auth_middleware import get_current_user
from app.models.application import (
    ApplicationChecklistItem,
    ApplicationDocument,
    ApplicationStatus,
    ApplicationStatusEvent,
    ApplicationSubmission,
    GeneratedDocument,
)
from app.models.user import User
from app.schemas.dossier import (
    ReadinessGateResponse,
    ChecklistItemResponse,
    ChecklistVerifyRequest,
    BISFormDefinition,
    DocumentGenerationRequest,
    GeneratedDocumentResponse,
    ApplicationSubmissionRequest,
    ApplicationSubmissionResponse,
    TrackingEventCreate,
    StatusEventResponse,
)
from app.services.checklist_service import ChecklistService
from app.services.form_generator import FormGenerator
from app.services.dossier_exporter import DossierExporter
from app.services.bis_adapter import ManualSubmissionProvider
from app.middleware.auth_middleware import get_current_user
from app.models.user import User
from app.schemas.application import (
    ApplicationCreate,
    ApplicationDetailResponse,
    ApplicationResponse,
    ApplicationUpdate,
    TrackingEventResponse,
)
from app.schemas.assessment import (
    ApplicationPrepResponse,
    AssessmentResultResponse,
    ChatMessageResponse,
    ChatQueryRequest,
    ExtractedParameterItem,
    ParameterExtractResponse,
    ParameterPatchRequest,
    ParametersUpdateRequest,
    StandardCandidateResponse,
    StandardSelectRequest,
)
from app.schemas.auth import StatusMessage
from app.services.application_service import ApplicationService
from app.services.assessment_engine import AssessmentEngine

router = APIRouter(prefix="/applications", tags=["Applications"])



@router.post("", response_model=ApplicationResponse, status_code=status.HTTP_201_CREATED)
async def create_application(
    payload: ApplicationCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Creates a new certification application owned by the authenticated manufacturer."""
    service = ApplicationService(db)
    app = await service.create_application(current_user.id, payload)
    return ApplicationResponse.model_validate(app)


@router.get("", response_model=List[ApplicationResponse])
async def list_applications(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Lists all certification applications owned by the authenticated user."""
    service = ApplicationService(db)
    apps = await service.list_applications(current_user.id)
    return [ApplicationResponse.model_validate(a) for a in apps]


@router.get("/{id}", response_model=ApplicationDetailResponse)
async def get_application(
    id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Retrieves detailed application data, including documents and status history."""
    service = ApplicationService(db)
    app = await service.get_application(id, current_user.id)
    return ApplicationDetailResponse.model_validate(app)


@router.patch("/{id}", response_model=ApplicationResponse)
async def update_application(
    id: str,
    payload: ApplicationUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Updates application parameters or state with explicit lifecycle audit tracking."""
    service = ApplicationService(db)
    app = await service.update_application(id, current_user.id, payload)
    return ApplicationResponse.model_validate(app)


@router.delete("/{id}", response_model=StatusMessage)
async def delete_application(
    id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Deletes an application owned by the user."""
    service = ApplicationService(db)
    await service.delete_application(id, current_user.id)
    return StatusMessage(status="success", message=f"Application {id} deleted successfully.")


@router.get("/{id}/tracking", response_model=List[TrackingEventResponse])
async def get_tracking(
    id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Returns the progression stages and tracking events for the application."""
    service = ApplicationService(db)
    return await service.get_tracking_events(id, current_user.id)


@router.post("/{id}/extract", response_model=ParameterExtractResponse)
async def extract_parameters(
    id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Extracts technical parameters from uploaded documents and product details."""
    engine = AssessmentEngine(db)
    return await engine.extract_parameters(id, current_user.id)


@router.get("/{id}/parameters", response_model=List[ExtractedParameterItem])
async def get_parameters(
    id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Retrieves all extracted parameters with source snippets, confidence, and audit trail."""
    engine = AssessmentEngine(db)
    return await engine.get_parameters(id, current_user.id)


@router.patch("/{id}/parameters/{parameter_id}", response_model=ExtractedParameterItem)
async def patch_parameter(
    id: str,
    parameter_id: str,
    payload: ParameterPatchRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Edits a single parameter, recording original_value, modified_value, modified_by, and modified_at."""
    engine = AssessmentEngine(db)
    return await engine.patch_parameter(id, parameter_id, payload, current_user.id)


@router.put("/{id}/parameters", response_model=List[ExtractedParameterItem])
async def update_parameters(
    id: str,
    payload: ParametersUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Updates and confirms user-reviewed parameters."""
    engine = AssessmentEngine(db)
    return await engine.update_parameters(id, current_user.id, payload.parameters)


@router.post("/{id}/identify-standards", response_model=List[StandardCandidateResponse])
@router.post("/{id}/identify-standard", response_model=List[StandardCandidateResponse])
async def identify_standards(
    id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Matches applicable Indian Standards against product specifications and category."""
    engine = AssessmentEngine(db)
    return await engine.identify_standards(id, current_user.id)


@router.post("/{id}/select-standard", response_model=StandardCandidateResponse)
async def select_standard(
    id: str,
    payload: StandardSelectRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Assigns the primary Indian Standard to the application."""
    engine = AssessmentEngine(db)
    return await engine.select_standard(id, current_user.id, payload.standard_id)


@router.post("/{id}/retrieve")
async def retrieve_requirements(
    id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Retrieves standard clauses and testing requirements for the selected standard."""
    engine = AssessmentEngine(db)
    return await engine.retrieve_requirements(id, current_user.id)


@router.post("/{id}/analyze", response_model=AssessmentResultResponse)
async def analyze_application(
    id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Executes deterministic compliance checking against BIS clauses, generates readiness score and gap report."""
    engine = AssessmentEngine(db)
    return await engine.run_compliance_analysis(id, current_user.id)


@router.post("/{id}/recheck", response_model=AssessmentResultResponse)
async def recheck_application(
    id: str,
    custom_efficacy: Optional[float] = Query(None, description="Optional remediated luminous efficacy parameter"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Re-evaluates compliance after parameter remediation, recalculating readiness score dynamically from updated evidence."""
    engine = AssessmentEngine(db)
    return await engine.recheck_application(id, current_user.id, custom_efficacy)



@router.post("/{id}/prepare-application", response_model=ApplicationPrepResponse)
async def prepare_application(
    id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Compiles Form IV application dossier, required documentation checklist, and validation status."""
    engine = AssessmentEngine(db)
    return await engine.prepare_application(id, current_user.id)


@router.post("/{id}/chat", response_model=ChatMessageResponse)
async def chat_with_application(
    id: str,
    payload: ChatQueryRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Contextual assistant answering queries with exact Indian Standard clause citations."""
    engine = AssessmentEngine(db)
    return await engine.chat_with_rag(id, current_user.id, payload.message)


@router.get("/{id}/readiness", response_model=ReadinessGateResponse)
async def get_readiness_gate(
    id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Evaluates readiness gate criteria before official BIS dossier generation."""
    service = ApplicationService(db)
    app = await service.get_application(id, current_user.id)
    return await ChecklistService.evaluate_readiness_gate(db, app)


@router.get("/{id}/checklist", response_model=List[ChecklistItemResponse])
async def get_checklist(
    id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Retrieves or initializes dynamic BIS document checklist for the application."""
    service = ApplicationService(db)
    app = await service.get_application(id, current_user.id)
    return await ChecklistService.get_or_create_checklist(db, app)


@router.post("/{id}/checklist/{item_id}/verify", response_model=ChecklistItemResponse)
async def verify_checklist_item(
    id: str,
    item_id: str,
    payload: ChecklistVerifyRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Verifies or rejects a document checklist item with verification notes."""
    service = ApplicationService(db)
    app = await service.get_application(id, current_user.id)
    item = await ChecklistService.verify_checklist_item(
        db, app.id, item_id, payload.verified, payload.verification_notes
    )
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Checklist item not found")
    return item


@router.get("/{id}/forms", response_model=Dict[str, BISFormDefinition])
async def get_forms(
    id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Compiles Form I, Form II, Form IV, and 14-section Technical Dossier with provenance tracking."""
    service = ApplicationService(db)
    app = await service.get_application(id, current_user.id)
    return await FormGenerator.build_forms(db, app)


@router.get("/{id}/forms/{form_type}/download")
async def download_form_file(
    id: str,
    form_type: str,
    format: str = Query("pdf", description="Format: pdf or json"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Directly downloads official BIS Form I, Form II, Form IV, or Technical Dossier as PDF or JSON.
    Generates the document on-the-fly if not already generated.
    """
    service = ApplicationService(db)
    app = await service.get_application(id, current_user.id)

    normalized_type = form_type.upper().replace("-", "_")
    valid_types = ["FORM_I", "FORM_II", "FORM_IV", "TECHNICAL_DOSSIER"]
    if normalized_type not in valid_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid form type '{form_type}'. Allowed types: {', '.join(valid_types)}",
        )

    # 1. Look for existing generated document
    stmt = (
        select(GeneratedDocument)
        .where(
            GeneratedDocument.application_id == app.id,
            GeneratedDocument.document_type == normalized_type,
        )
        .order_by(GeneratedDocument.version.desc())
    )
    res = await db.execute(stmt)
    doc = res.scalars().first()

    if not doc or not (doc.file_path and os.path.exists(doc.file_path)):
        # Generate on-the-fly
        generated_docs = await DossierExporter.generate_dossier(
            db, app, [normalized_type], force_generate=True
        )
        doc = next((d for d in generated_docs if d.document_type == normalized_type), None)
        if not doc:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to generate {normalized_type}",
            )

    safe_id = (app.application_number or app.id)[:12]

    if format.lower() == "json":
        json_path = None
        if doc.metadata_json:
            try:
                meta = json.loads(doc.metadata_json)
                json_path = meta.get("json_companion")
            except Exception:
                pass
        if not json_path or not os.path.exists(json_path):
            candidate = str(Path(doc.file_path).with_suffix(".json"))
            if os.path.exists(candidate):
                json_path = candidate

        if json_path and os.path.exists(json_path):
            return FileResponse(
                path=json_path,
                media_type="application/json",
                filename=f"{normalized_type.lower()}_{safe_id}.json",
            )
        else:
            forms = await FormGenerator.build_forms(db, app)
            if normalized_type in forms:
                content = forms[normalized_type].model_dump_json(indent=2)
                return Response(
                    content=content,
                    media_type="application/json",
                    headers={
                        "Content-Disposition": f"attachment; filename={normalized_type.lower()}_{safe_id}.json"
                    },
                )

    # PDF format
    if not (doc.file_path and os.path.exists(doc.file_path)):
        raise HTTPException(status_code=404, detail="PDF file not found on disk")

    filename = f"{normalized_type}_{safe_id}.pdf"
    return FileResponse(
        path=doc.file_path,
        media_type="application/pdf",
        filename=filename,
    )


@router.post("/{id}/documents/generate", response_model=List[GeneratedDocumentResponse])
async def generate_documents(
    id: str,
    payload: Optional[DocumentGenerationRequest] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Generates official BIS PDF/JSON dossiers, versioned and hashed with SHA-256."""
    service = ApplicationService(db)
    app = await service.get_application(id, current_user.id)
    doc_types = payload.document_types if payload else None
    return await DossierExporter.generate_dossier(db, app, doc_types, force_generate=True)


@router.get("/{id}/generated-documents", response_model=List[GeneratedDocumentResponse])
async def list_generated_documents(
    id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Lists all versioned generated BIS documents and packages for this application."""
    service = ApplicationService(db)
    app = await service.get_application(id, current_user.id)
    stmt = (
        select(GeneratedDocument)
        .where(GeneratedDocument.application_id == app.id)
        .order_by(GeneratedDocument.version.desc(), GeneratedDocument.created_at.desc())
    )
    res = await db.execute(stmt)
    return list(res.scalars().all())


@router.get("/{id}/generated-documents/{doc_id}/download")
async def download_generated_document(
    id: str,
    doc_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Downloads an immutable generated BIS PDF or JSON document."""
    service = ApplicationService(db)
    app = await service.get_application(id, current_user.id)
    stmt = select(GeneratedDocument).where(
        GeneratedDocument.id == doc_id,
        GeneratedDocument.application_id == app.id,
    )
    res = await db.execute(stmt)
    doc = res.scalar_one_or_none()
    if not doc or not os.path.exists(doc.file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Generated document file not found on disk",
        )
    filename = Path(doc.file_path).name
    return FileResponse(
        path=doc.file_path,
        media_type=doc.mime_type,
        filename=filename,
    )


@router.get("/{id}/export-dossier")
async def export_dossier_zip(
    id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Packages all generated BIS documents, forms, and manifest into a downloadable ZIP dossier."""
    service = ApplicationService(db)
    app = await service.get_application(id, current_user.id)

    # Ensure generated documents exist, generate if needed
    stmt = select(GeneratedDocument).where(GeneratedDocument.application_id == app.id)
    res = await db.execute(stmt)
    docs = list(res.scalars().all())
    if not docs:
        docs = await DossierExporter.generate_dossier(db, app, force_generate=True)

    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        manifest_data = {
            "application_id": app.id,
            "application_number": app.application_number,
            "product_name": app.product_name,
            "manufacturer": app.manufacturer,
            "exported_at": datetime.now(timezone.utc).isoformat(),
            "documents": [],
        }
        for doc in docs:
            if doc.file_path and os.path.exists(doc.file_path):
                arcname = f"{doc.document_type}_{Path(doc.file_path).name}"
                zf.write(doc.file_path, arcname=arcname)
                manifest_data["documents"].append({
                    "document_type": doc.document_type,
                    "document_name": doc.document_name,
                    "sha256_hash": doc.sha256_hash,
                    "filename": arcname,
                })
        zf.writestr("manifest.json", json.dumps(manifest_data, indent=2))

    zip_buffer.seek(0)
    filename = f"BIS_Dossier_{app.application_number or app.id}.zip"
    return StreamingResponse(
        zip_buffer,
        media_type="application/zip",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.get("/{id}/submission-manifest")
async def get_submission_manifest(
    id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Prepares submission manifest, document bundle, and Manakonline portal instructions."""
    service = ApplicationService(db)
    app = await service.get_application(id, current_user.id)
    provider = ManualSubmissionProvider()
    return await provider.prepare_submission_bundle(db, app)


@router.post("/{id}/submit", response_model=ApplicationSubmissionResponse)
async def submit_application(
    id: str,
    payload: ApplicationSubmissionRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Records official BIS portal submission acknowledgement and triggers tracking lifecycle."""
    service = ApplicationService(db)
    app = await service.get_application(id, current_user.id)
    provider = ManualSubmissionProvider()
    return await provider.submit_application(db, app, payload)


@router.get("/{id}/events", response_model=List[StatusEventResponse])
async def get_application_events(
    id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Returns chronological audit log of real application lifecycle events."""
    service = ApplicationService(db)
    app = await service.get_application(id, current_user.id)
    stmt = (
        select(ApplicationStatusEvent)
        .where(ApplicationStatusEvent.application_id == app.id)
        .order_by(ApplicationStatusEvent.created_at.asc())
    )
    res = await db.execute(stmt)
    return list(res.scalars().all())


@router.post("/{id}/events", response_model=StatusEventResponse)
async def create_application_event(
    id: str,
    payload: TrackingEventCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Manually logs a lifecycle status transition or milestone note."""
    service = ApplicationService(db)
    app = await service.get_application(id, current_user.id)
    from_status = app.status.value
    try:
        new_status = ApplicationStatus(payload.to_status)
        app.status = new_status
    except ValueError:
        pass

    event = ApplicationStatusEvent(
        application_id=app.id,
        from_status=from_status,
        to_status=payload.to_status,
        event_type=payload.event_type or "STATUS_CHANGE",
        description=payload.description or f"Status transitioned to {payload.to_status}",
        note=payload.note,
        actor_id=current_user.id,
        source=payload.source or "MANUFACTURER",
    )
    db.add(event)
    await db.flush()
    return event

