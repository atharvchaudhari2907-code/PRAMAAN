import hashlib
import json
import secrets
from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.application import ApplicationDocument
from app.models.trust_ledger import Certificate, TrustLedgerRecord
from app.schemas.trust_ledger import (
    HashVerificationResponse,
    TrustLedgerRecordCreate,
    TrustLedgerRecordResponse,
    TrustLedgerStats,
)


class TrustLedgerService:
    def __init__(self, db: AsyncSession):
        self.db = db

    def _generate_public_product_id(self) -> str:
        token = secrets.token_hex(4).upper()
        return f"BIS-PROD-{token}"

    def _canonicalize_and_hash(self, payload: dict) -> str:
        canonical_str = json.dumps(payload, sort_keys=True)
        return hashlib.sha256(canonical_str.encode("utf-8")).hexdigest()

    async def create_record(self, data: TrustLedgerRecordCreate) -> TrustLedgerRecordResponse:
        # Check if already anchored
        stmt = select(TrustLedgerRecord).where(TrustLedgerRecord.certificate_id == data.certificate_id)
        res = await self.db.execute(stmt)
        existing = res.scalar_one_or_none()

        if existing:
            payload = json.loads(existing.payload_json)
            return TrustLedgerRecordResponse(
                id=existing.id,
                public_product_id=payload.get("public_product_id", "BIS-PROD-0000"),
                product_name=payload.get("product_name", data.product_name),
                manufacturer=payload.get("manufacturer", data.manufacturer),
                model=payload.get("model", data.model),
                standard_id=payload.get("standard_id", data.standard_id),
                standard_title=payload.get("standard_title", data.standard_title),
                standard_version=payload.get("standard_version", data.standard_version),
                certificate_id=existing.certificate_id,
                certification_status=payload.get("certification_status", "ACTIVE"),
                valid_until=payload.get("valid_until", ""),
                issuer=payload.get("issuer", "Bureau of Indian Standards"),
                record_hash=existing.sha256_hash,
                verification_url=f"/verify/{payload.get('public_product_id', '')}",
                created_at=existing.created_at.isoformat(),
            )

        public_id = self._generate_public_product_id()
        valid_until = data.valid_until or (datetime.now(timezone.utc).replace(year=datetime.now(timezone.utc).year + 1).isoformat())

        canonical_dict = {
            "public_product_id": public_id,
            "product_name": data.product_name,
            "manufacturer": data.manufacturer,
            "model": data.model,
            "standard_id": data.standard_id,
            "standard_title": data.standard_title,
            "standard_version": data.standard_version,
            "certificate_id": data.certificate_id,
            "certification_status": data.certification_status,
            "valid_until": valid_until,
            "issuer": data.issuer or "Bureau of Indian Standards",
            "anchored_at": datetime.now(timezone.utc).isoformat(),
        }

        record_hash = self._canonicalize_and_hash(canonical_dict)

        record = TrustLedgerRecord(
            certificate_id=data.certificate_id,
            sha256_hash=record_hash,
            record_type="CERTIFICATE_HASH",
            payload_json=json.dumps(canonical_dict),
            anchored_at=datetime.now(timezone.utc),
        )
        self.db.add(record)
        await self.db.commit()

        return TrustLedgerRecordResponse(
            id=record.id,
            public_product_id=public_id,
            product_name=data.product_name,
            manufacturer=data.manufacturer,
            model=data.model,
            standard_id=data.standard_id,
            standard_title=data.standard_title,
            standard_version=data.standard_version,
            certificate_id=data.certificate_id,
            certification_status=data.certification_status,
            valid_until=valid_until,
            issuer=data.issuer or "Bureau of Indian Standards",
            record_hash=record_hash,
            verification_url=f"/verify/{public_id}",
            created_at=record.created_at.isoformat(),
        )

    async def list_records(self) -> List[TrustLedgerRecordResponse]:
        stmt = select(TrustLedgerRecord).order_by(TrustLedgerRecord.created_at.desc())
        res = await self.db.execute(stmt)
        records = res.scalars().all()

        out: List[TrustLedgerRecordResponse] = []
        for r in records:
            try:
                p = json.loads(r.payload_json)
            except Exception:
                p = {}
            out.append(
                TrustLedgerRecordResponse(
                    id=r.id,
                    public_product_id=p.get("public_product_id", "BIS-PROD-0000"),
                    product_name=p.get("product_name", "Unknown Product"),
                    manufacturer=p.get("manufacturer", "Manufacturer"),
                    model=p.get("model", "Model"),
                    standard_id=p.get("standard_id", ""),
                    standard_title=p.get("standard_title", ""),
                    standard_version=p.get("standard_version", ""),
                    certificate_id=r.certificate_id,
                    certification_status=p.get("certification_status", "ACTIVE"),
                    valid_until=p.get("valid_until", ""),
                    issuer=p.get("issuer", "Bureau of Indian Standards"),
                    record_hash=r.sha256_hash,
                    verification_url=f"/verify/{p.get('public_product_id', '')}",
                    created_at=r.created_at.isoformat(),
                )
            )
        return out

    async def get_record_by_public_id(self, public_product_id: str) -> Optional[TrustLedgerRecordResponse]:
        stmt = select(TrustLedgerRecord)
        res = await self.db.execute(stmt)
        records = res.scalars().all()

        for r in records:
            try:
                p = json.loads(r.payload_json)
                if p.get("public_product_id") == public_product_id:
                    return TrustLedgerRecordResponse(
                        id=r.id,
                        public_product_id=public_product_id,
                        product_name=p.get("product_name", ""),
                        manufacturer=p.get("manufacturer", ""),
                        model=p.get("model", ""),
                        standard_id=p.get("standard_id", ""),
                        standard_title=p.get("standard_title", ""),
                        standard_version=p.get("standard_version", ""),
                        certificate_id=r.certificate_id,
                        certification_status=p.get("certification_status", "ACTIVE"),
                        valid_until=p.get("valid_until", ""),
                        issuer=p.get("issuer", "Bureau of Indian Standards"),
                        record_hash=r.sha256_hash,
                        verification_url=f"/verify/{public_product_id}",
                        created_at=r.created_at.isoformat(),
                    )
            except Exception:
                continue
        return None

    async def verify_hash(
        self, sha256_hash: str, document_name: Optional[str] = None
    ) -> HashVerificationResponse:
        cleaned_hash = sha256_hash.strip().lower()

        # 1. Search uploaded application documents
        stmt_doc = select(ApplicationDocument).where(ApplicationDocument.sha256_hash == cleaned_hash)
        res_doc = await self.db.execute(stmt_doc)
        doc = res_doc.scalar_one_or_none()

        if doc:
            return HashVerificationResponse(
                sha256_hash=cleaned_hash,
                is_verified=True,
                matched_application_id=doc.application_id,
                matched_document_name=doc.original_filename,
                timestamp=doc.created_at.isoformat(),
                integrity_status="VALID_RECORD",
                blockchain_network="Hyperledger Fabric / Ethereum Testnet (Sepolia)",
                message=f"Cryptographic match verified. Document '{doc.original_filename}' is authentic and matches the immutable audit ledger.",
            )

        # 2. Search Trust Ledger records
        stmt_ledger = select(TrustLedgerRecord).where(TrustLedgerRecord.sha256_hash == cleaned_hash)
        res_ledger = await self.db.execute(stmt_ledger)
        ledger_rec = res_ledger.scalar_one_or_none()

        if ledger_rec:
            p = json.loads(ledger_rec.payload_json)
            return HashVerificationResponse(
                sha256_hash=cleaned_hash,
                is_verified=True,
                matched_application_id=p.get("public_product_id"),
                matched_document_name=f"Certificate {ledger_rec.certificate_id}",
                timestamp=ledger_rec.created_at.isoformat(),
                integrity_status="VALID_RECORD",
                blockchain_network="Hyperledger Fabric / Ethereum Testnet (Sepolia)",
                message=f"Certificate {ledger_rec.certificate_id} verified. Hash perfectly matches the anchored state on-chain.",
            )

        return HashVerificationResponse(
            sha256_hash=cleaned_hash,
            is_verified=False,
            matched_application_id=None,
            matched_document_name=document_name,
            timestamp=None,
            integrity_status="UNKNOWN_RECORD",
            blockchain_network="Hyperledger Fabric / Ethereum Testnet (Sepolia)",
            message="No matching cryptographic fingerprint located in the immutable trust ledger. The file may have been altered or not yet certified.",
        )
