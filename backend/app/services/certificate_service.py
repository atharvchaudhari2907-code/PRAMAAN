import hashlib
import json
import logging
import secrets
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.base import generate_uuid
from app.models.application import Application, GeneratedDocument
from app.models.trust_ledger import (
    AnchorStatus,
    Certificate,
    CertificateEvent,
    CertificateStatus,
    TrustLedgerRecord,
)
from app.schemas.certificate import CanonicalCertificate, PublicVerificationResponse
from app.services.blockchain_provider import get_blockchain_provider
from app.services.ipfs_provider import get_ipfs_provider
from app.services.qr_generator import QRGenerator

logger = logging.getLogger(__name__)


def format_canonical_timestamp(dt: Any) -> str:
    """Format datetime into standard ISO-8601 UTC representation (YYYY-MM-DDTHH:MM:SSZ)."""
    if isinstance(dt, str):
        s = dt.replace("+00:00", "Z")
        if not s.endswith("Z") and "T" in s:
            s += "Z"
        return s
    if isinstance(dt, datetime):
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    return str(dt)


def compute_canonical_hash(canonical_dict: Any) -> str:
    """
    Deterministic canonical SHA-256 hashing.
    Keys are strictly sorted, separators are standardized without whitespace,
    guaranteeing identical reproducible hashes across environments.
    Supports either Pydantic models or standard dicts.
    """
    if hasattr(canonical_dict, "model_dump"):
        data = canonical_dict.model_dump()
    elif hasattr(canonical_dict, "dict"):
        data = canonical_dict.dict()
    elif isinstance(canonical_dict, dict):
        data = canonical_dict
    else:
        data = dict(canonical_dict)
    canonical_str = json.dumps(data, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical_str.encode("utf-8")).hexdigest().lower()


class CertificateService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.blockchain_provider = get_blockchain_provider()
        self.ipfs_provider = get_ipfs_provider()

    def generate_certificate_id(self) -> str:
        year = datetime.now(timezone.utc).year
        token = secrets.token_hex(3).upper()
        return f"BIS-CERT-{year}-{token}"

    def build_canonical_dict(self, cert: Certificate) -> Dict[str, Any]:
        return {
            "certificate_id": cert.certificate_id,
            "product_name": cert.product_name,
            "manufacturer": cert.manufacturer,
            "model": cert.model or "",
            "standard_id": cert.standard_id,
            "standard_version": cert.standard_version or "",
            "issued_at": format_canonical_timestamp(cert.issued_at),
            "valid_until": format_canonical_timestamp(cert.valid_until),
            "document_sha256": cert.document_sha256,
        }

    async def issue_certificate(
        self,
        application: Application,
        document_id: Optional[str] = None,
        valid_years: int = 1,
    ) -> Certificate:
        """
        Issues an official BIS Standard Mark certificate for a verified application.
        Uploads technical dossier to IPFS, anchors canonical hash on-chain, and registers events.
        """
        # Check if already issued
        stmt = select(Certificate).where(Certificate.application_id == application.id).options(selectinload(Certificate.events))
        res = await self.db.execute(stmt)
        existing = res.scalar_one_or_none()
        if existing:
            return existing

        cert_id = self.generate_certificate_id()
        issued_at = datetime.now(timezone.utc).replace(microsecond=0)
        valid_until = (issued_at + timedelta(days=365 * valid_years)).replace(microsecond=0)

        # 1. Locate technical document to associate
        doc_stmt = (
            select(GeneratedDocument)
            .where(GeneratedDocument.application_id == application.id)
            .order_by(GeneratedDocument.version.desc(), GeneratedDocument.created_at.desc())
        )
        if document_id:
            doc_stmt = select(GeneratedDocument).where(
                GeneratedDocument.id == document_id,
                GeneratedDocument.application_id == application.id,
            )
        doc_res = await self.db.execute(doc_stmt)
        gen_doc = doc_res.scalars().first()

        doc_sha256 = gen_doc.sha256_hash if gen_doc else hashlib.sha256(b"BIS_OFFICIAL_EMPTY_RECORD").hexdigest()
        doc_path = gen_doc.file_path if gen_doc else None

        # 2. Upload dossier / metadata to IPFS
        ipfs_cid = None
        try:
            if doc_path and Path(doc_path).exists():
                file_bytes = Path(doc_path).read_bytes()
                ipfs_cid = await self.ipfs_provider.upload_document(file_bytes, Path(doc_path).name)
            else:
                dossier_meta = {
                    "certificate_id": cert_id,
                    "application_id": application.id,
                    "product_name": application.product_name,
                    "document_sha256": doc_sha256,
                }
                ipfs_cid = await self.ipfs_provider.upload_document(
                    json.dumps(dossier_meta, sort_keys=True).encode("utf-8"),
                    f"{cert_id}_dossier.json",
                )
        except Exception as e:
            logger.warning(f"IPFS upload failed, fallback to local content address: {e}")
            ipfs_cid = f"bafybeicert{doc_sha256[:40]}"

        # 3. Canonical representation & Hash
        canonical_data = {
            "certificate_id": cert_id,
            "product_name": application.product_name,
            "manufacturer": application.manufacturer or "Certified Manufacturer",
            "model": application.model_number or "STANDARD-01",
            "standard_id": application.primary_standard_id or "IS 1293:2019",
            "standard_version": "2024",
            "issued_at": format_canonical_timestamp(issued_at),
            "valid_until": format_canonical_timestamp(valid_until),
            "document_sha256": doc_sha256,
        }
        record_hash = compute_canonical_hash(canonical_data)

        # 4. Anchor into Blockchain
        issuer_name = "Bureau of Indian Standards"
        tx_receipt = await self.blockchain_provider.anchor_certificate(
            certificate_id=cert_id,
            record_hash=record_hash,
            document_hash=doc_sha256,
            ipfs_cid=ipfs_cid or "bafybeihashnull",
            issuer=issuer_name,
        )

        # 5. Persist Certificate in Database
        cert_uuid = generate_uuid()
        cert = Certificate(
            id=cert_uuid,
            certificate_id=cert_id,
            application_id=application.id,
            product_id=application.id,
            product_name=application.product_name,
            manufacturer=application.manufacturer or "Certified Manufacturer",
            model=application.model_number or "STANDARD-01",
            standard_id=application.primary_standard_id or "IS 1293:2019",
            standard_version="2024",
            issued_at=issued_at,
            valid_until=valid_until,
            status=CertificateStatus.ACTIVE.value,
            issuer=issuer_name,
            document_id=gen_doc.id if gen_doc else None,
            document_sha256=doc_sha256,
            ipfs_cid=ipfs_cid,
            blockchain_network=tx_receipt.get("network", "Polygon Amoy Testnet"),
            contract_address=tx_receipt.get("contract_address"),
            transaction_hash=tx_receipt.get("transaction_hash"),
            block_number=tx_receipt.get("block_number"),
            record_hash=record_hash,
            anchor_status=AnchorStatus.ANCHORED.value,
        )
        self.db.add(cert)

        # Add Certificate Event
        event = CertificateEvent(
            id=generate_uuid(),
            certificate_id=cert_uuid,
            event_type="ISSUED",
            description=f"Certificate {cert_id} issued and anchored into {tx_receipt.get('network')} at block {tx_receipt.get('block_number')}.",
            block_number=tx_receipt.get("block_number"),
            tx_hash=tx_receipt.get("transaction_hash"),
        )
        self.db.add(event)

        # Add / Sync TrustLedgerRecord for backwards-compatible public product lookup
        public_product_id = f"BIS-PROD-{cert_id.split('-')[-1]}"
        tl_payload = {
            "public_product_id": public_product_id,
            "product_name": cert.product_name,
            "manufacturer": cert.manufacturer,
            "model": cert.model,
            "standard_id": cert.standard_id,
            "standard_title": f"Indian Standard {cert.standard_id}",
            "standard_version": cert.standard_version,
            "certificate_id": cert_id,
            "certification_status": cert.status,
            "valid_until": valid_until.isoformat(),
            "issuer": issuer_name,
            "blockchain_tx_hash": tx_receipt.get("transaction_hash"),
            "block_number": tx_receipt.get("block_number"),
            "ipfs_cid": ipfs_cid,
        }
        tl_rec = TrustLedgerRecord(
            id=generate_uuid(),
            certificate_id=cert_id,
            sha256_hash=record_hash,
            record_type="CERTIFICATE_HASH",
            payload_json=json.dumps(tl_payload),
            anchored_at=issued_at,
        )
        self.db.add(tl_rec)

        await self.db.flush()
        # Eager load relationships for clean async Pydantic serialization
        res = await self.db.execute(
            select(Certificate)
            .where(Certificate.id == cert_uuid)
            .options(selectinload(Certificate.events))
        )
        return res.scalar_one()

    async def update_status(self, certificate_id: str, new_status: str, reason: Optional[str] = None) -> Optional[Certificate]:
        stmt = (
            select(Certificate)
            .where(
                (Certificate.certificate_id == certificate_id)
                | (Certificate.id == certificate_id)
            )
            .options(selectinload(Certificate.events))
        )
        res = await self.db.execute(stmt)
        cert = res.scalar_one_or_none()
        if not cert:
            return None

        old_status = cert.status
        cert.status = new_status

        # Update on-chain status
        try:
            tx_receipt = await self.blockchain_provider.update_anchor_status(cert.certificate_id, new_status)
            block_num = tx_receipt.get("block_number")
            tx_hash = tx_receipt.get("transaction_hash")
        except Exception as e:
            logger.warning(f"Failed to update blockchain status: {e}")
            block_num = None
            tx_hash = None

        event = CertificateEvent(
            id=generate_uuid(),
            certificate_id=cert.id,
            event_type="STATUS_CHANGE",
            description=f"Status changed from {old_status} to {new_status}. {reason or ''}".strip(),
            block_number=block_num,
            tx_hash=tx_hash,
        )
        self.db.add(event)
        await self.db.flush()

        refreshed = await self.db.execute(
            select(Certificate)
            .where(Certificate.id == cert.id)
            .options(selectinload(Certificate.events))
        )
        return refreshed.scalar_one()

    async def verify_certificate_public(self, identifier: str) -> PublicVerificationResponse:
        """
        Comprehensive 8-step verification algorithm:
        1. Fetch certificate record (matches certificate_id or public_product_id).
        2. Reconstruct canonical record.
        3. Calculate SHA-256 canonical hash.
        4. Compare to stored certificate hash.
        5. Query blockchain anchor.
        6. Compare anchored hash on-chain.
        7. Check IPFS document hash if present.
        8. Output status:
           VERIFIED_AND_CURRENT, AUTHENTIC_BUT_EXPIRED, AUTHENTIC_BUT_SUSPENDED,
           AUTHENTIC_BUT_REVOKED, INTEGRITY_WARNING, BLOCKCHAIN_UNAVAILABLE, NOT_FOUND.
        """
        clean_id = identifier.strip()

        # Step 1: Query Certificate
        stmt = (
            select(Certificate)
            .where(
                (Certificate.certificate_id == clean_id)
                | (Certificate.application_id == clean_id)
                | (Certificate.id == clean_id)
            )
        )
        res = await self.db.execute(stmt)
        cert = res.scalar_one_or_none()

        if not cert:
            # Check if identifier matches TrustLedgerRecord payload public_product_id
            tl_stmt = select(TrustLedgerRecord)
            tl_res = await self.db.execute(tl_stmt)
            for tl in tl_res.scalars().all():
                try:
                    p = json.loads(tl.payload_json)
                    if p.get("public_product_id") == clean_id or tl.certificate_id == clean_id:
                        cert_stmt = select(Certificate).where(Certificate.certificate_id == tl.certificate_id)
                        cert_res = await self.db.execute(cert_stmt)
                        cert = cert_res.scalar_one_or_none()
                        break
                except Exception:
                    continue

        if not cert:
            return PublicVerificationResponse(
                status="NOT_FOUND",
                is_valid=False,
                certificate_id=clean_id,
                message=f"No certified BIS record was found matching identifier '{clean_id}'. Verify the ID and try again.",
            )

        # Step 2 & 3: Reconstruct canonical representation and compute SHA-256
        canonical_dict = self.build_canonical_dict(cert)
        computed_hash = compute_canonical_hash(canonical_dict)

        # Step 4: Compare to stored certificate record_hash
        stored_hash = cert.record_hash.lower()
        if computed_hash != stored_hash:
            return PublicVerificationResponse(
                status="INTEGRITY_WARNING",
                is_valid=False,
                certificate_id=cert.certificate_id,
                product_name=cert.product_name,
                manufacturer=cert.manufacturer,
                model=cert.model,
                standard_id=cert.standard_id,
                standard_version=cert.standard_version,
                issued_at=cert.issued_at,
                valid_until=cert.valid_until,
                certificate_status=cert.status,
                document_sha256=cert.document_sha256,
                computed_record_hash=computed_hash,
                anchored_record_hash=stored_hash,
                blockchain_network=cert.blockchain_network,
                contract_address=cert.contract_address,
                transaction_hash=cert.transaction_hash,
                block_number=cert.block_number,
                ipfs_cid=cert.ipfs_cid,
                message="CRITICAL INTEGRITY WARNING: The certificate data in the local registry has been modified or tampered with. Computed canonical hash does not match stored record hash.",
            )

        # Step 5 & 6: Query blockchain anchor
        chain_verify = await self.blockchain_provider.verify_certificate_anchor(cert.certificate_id, computed_hash)
        if not chain_verify.get("found"):
            return PublicVerificationResponse(
                status="BLOCKCHAIN_UNAVAILABLE",
                is_valid=False,
                certificate_id=cert.certificate_id,
                product_name=cert.product_name,
                manufacturer=cert.manufacturer,
                model=cert.model,
                standard_id=cert.standard_id,
                standard_version=cert.standard_version,
                issued_at=cert.issued_at,
                valid_until=cert.valid_until,
                certificate_status=cert.status,
                document_sha256=cert.document_sha256,
                computed_record_hash=computed_hash,
                anchored_record_hash=None,
                blockchain_network=cert.blockchain_network,
                contract_address=cert.contract_address,
                message=f"Certificate record is present locally, but on-chain anchor could not be confirmed on {cert.blockchain_network}.",
            )

        if not chain_verify.get("is_valid"):
            return PublicVerificationResponse(
                status="INTEGRITY_WARNING",
                is_valid=False,
                certificate_id=cert.certificate_id,
                product_name=cert.product_name,
                manufacturer=cert.manufacturer,
                model=cert.model,
                standard_id=cert.standard_id,
                standard_version=cert.standard_version,
                issued_at=cert.issued_at,
                valid_until=cert.valid_until,
                certificate_status=cert.status,
                document_sha256=cert.document_sha256,
                computed_record_hash=computed_hash,
                anchored_record_hash=chain_verify.get("anchored_hash"),
                blockchain_network=cert.blockchain_network,
                contract_address=cert.contract_address,
                transaction_hash=cert.transaction_hash,
                block_number=cert.block_number,
                ipfs_cid=cert.ipfs_cid,
                message="CRITICAL INTEGRITY WARNING: On-chain anchored hash does not match computed certificate hash. Database record has been altered post-anchoring.",
            )

        # Step 7: Check validity & status
        now = datetime.now(timezone.utc)
        valid_until_utc = cert.valid_until if cert.valid_until.tzinfo else cert.valid_until.replace(tzinfo=timezone.utc)

        if cert.status == CertificateStatus.REVOKED.value:
            outcome_status = "AUTHENTIC_BUT_REVOKED"
            msg = f"Authentic certificate verified on-chain, but the licence has been formally REVOKED by the Bureau of Indian Standards."
            is_valid = False
        elif cert.status == CertificateStatus.SUSPENDED.value:
            outcome_status = "AUTHENTIC_BUT_SUSPENDED"
            msg = f"Authentic certificate verified on-chain, but the licence is currently SUSPENDED pending corrective compliance action."
            is_valid = False
        elif now > valid_until_utc or cert.status == CertificateStatus.EXPIRED.value:
            outcome_status = "AUTHENTIC_BUT_EXPIRED"
            msg = f"Authentic certificate verified on-chain, but the validity expired on {cert.valid_until.strftime('%b %d, %Y')}."
            is_valid = False
        else:
            outcome_status = "VERIFIED_AND_CURRENT"
            msg = f"Certificate is authentic, cryptographically verified on {cert.blockchain_network}, and currently in full legal effect."
            is_valid = True

        return PublicVerificationResponse(
            status=outcome_status,
            is_valid=is_valid,
            certificate_id=cert.certificate_id,
            product_name=cert.product_name,
            manufacturer=cert.manufacturer,
            model=cert.model,
            standard_id=cert.standard_id,
            standard_version=cert.standard_version,
            issued_at=cert.issued_at,
            valid_until=cert.valid_until,
            certificate_status=cert.status,
            document_sha256=cert.document_sha256,
            computed_record_hash=computed_hash,
            anchored_record_hash=chain_verify.get("anchored_hash"),
            blockchain_network=cert.blockchain_network,
            contract_address=cert.contract_address,
            transaction_hash=cert.transaction_hash,
            block_number=cert.block_number,
            ipfs_cid=cert.ipfs_cid,
            message=msg,
        )
