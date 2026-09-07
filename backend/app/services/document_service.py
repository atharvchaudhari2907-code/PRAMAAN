import hashlib
import os
import re
from pathlib import Path
from typing import Tuple
from fastapi import HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.application import ApplicationDocument, ApplicationStatus, ApplicationStatusEvent, DocumentType
from app.repositories.application_repository import ApplicationRepository
from app.repositories.document_repository import DocumentRepository


def sanitize_filename(filename: str) -> str:
    """Removes path traversal components and invalid characters from filename."""
    name = os.path.basename(filename)
    name = re.sub(r"[^\w\.-]", "_", name)
    return name or "document"


def validate_file_magic_bytes(header: bytes, mime_type: str) -> bool:
    """
    Validates file magic bytes against stated MIME type to prevent file disguise attacks.
    """
    if mime_type == "application/pdf":
        return header.startswith(b"%PDF-")
    elif mime_type == "image/png":
        return header.startswith(b"\x89PNG\r\n\x1a\n")
    elif mime_type in ("image/jpeg", "image/jpg"):
        return header.startswith(b"\xff\xd8\xff")
    return False


class DocumentService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.app_repo = ApplicationRepository(db)
        self.doc_repo = DocumentRepository(db)

    async def upload_document(
        self,
        application_id: str,
        user_id: str,
        file: UploadFile,
        document_type: DocumentType = DocumentType.TECHNICAL_DATASHEET,
    ) -> ApplicationDocument:
        """
        Validates, cryptographically hashes (SHA-256), and securely stores an uploaded document.
        Transitions application lifecycle to DOCUMENT_UPLOADED.
        """
        app = await self.app_repo.get_by_id_and_user(application_id, user_id)
        if not app:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Application not found or you do not have permission to access it.",
            )

        filename = file.filename or "uploaded_file"
        clean_name = sanitize_filename(filename)
        _, ext = os.path.splitext(clean_name)
        ext = ext.lower()

        if ext not in settings.ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File extension '{ext}' is not supported. Allowed extensions: {', '.join(settings.ALLOWED_EXTENSIONS)}",
            )

        mime = file.content_type or ""
        if mime not in settings.ALLOWED_MIME_TYPES:
            # Map common fallbacks
            if ext == ".pdf":
                mime = "application/pdf"
            elif ext == ".png":
                mime = "image/png"
            elif ext in (".jpg", ".jpeg"):
                mime = "image/jpeg"
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Unsupported MIME type: {mime}",
                )

        # Read first chunk for magic bytes inspection
        header = await file.read(16)
        if not validate_file_magic_bytes(header, mime):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File content header does not match the stated file type.",
            )

        # Ensure upload destination directory exists
        dest_dir = Path(settings.STORAGE_PATH) / application_id
        dest_dir.mkdir(parents=True, exist_ok=True)

        doc_record = ApplicationDocument(
            application_id=application_id,
            document_type=document_type,
            original_filename=clean_name,
            file_size=0,
            mime_type=mime,
            sha256_hash="",
            storage_path="",
        )
        await self.doc_repo.create(doc_record)

        dest_file_path = dest_dir / f"{doc_record.id}_{clean_name}"

        # Stream write and compute SHA-256
        hasher = hashlib.sha256()
        total_size = len(header)
        hasher.update(header)

        with open(dest_file_path, "wb") as f:
            f.write(header)
            while True:
                chunk = await file.read(64 * 1024)  # 64 KB chunks
                if not chunk:
                    break
                total_size += len(chunk)
                if total_size > settings.MAX_UPLOAD_SIZE_BYTES:
                    # Clean up file and abort
                    f.close()
                    if os.path.exists(dest_file_path):
                        os.remove(dest_file_path)
                    raise HTTPException(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        detail=f"File exceeds maximum allowed size of {settings.MAX_UPLOAD_SIZE_BYTES // (1024*1024)}MB.",
                    )
                hasher.update(chunk)
                f.write(chunk)

        doc_record.file_size = total_size
        doc_record.sha256_hash = hasher.hexdigest()
        doc_record.storage_path = str(dest_file_path)

        # Transition application lifecycle if currently DRAFT
        if app.status == ApplicationStatus.DRAFT:
            app.status = ApplicationStatus.DOCUMENT_UPLOADED
            event = ApplicationStatusEvent(
                application_id=app.id,
                from_status=ApplicationStatus.DRAFT.value,
                to_status=ApplicationStatus.DOCUMENT_UPLOADED.value,
                note=f"Uploaded technical specification document: {clean_name} (SHA-256: {doc_record.sha256_hash[:16]}...).",
                actor_id=user_id,
            )
            await self.app_repo.add_status_event(event)

        await self.db.flush()
        return doc_record

    async def get_document_for_download(
        self, document_id: str, user_id: str
    ) -> Tuple[str, str, str]:
        """
        Verifies ownership and returns (file_path, mime_type, original_filename) for secure streaming.
        """
        doc = await self.doc_repo.get_by_id(document_id)
        if not doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found.",
            )

        app = await self.app_repo.get_by_id_and_user(doc.application_id, user_id)
        if not app:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to access this document.",
            )

        if not os.path.exists(doc.storage_path):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Stored document file not found on disk.",
            )

        return doc.storage_path, doc.mime_type, doc.original_filename
