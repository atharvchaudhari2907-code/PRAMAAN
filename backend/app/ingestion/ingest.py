import argparse
import asyncio
import os
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Ensure backend directory is in sys.path
BASE_DIR = Path(__file__).resolve().parent.parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from pypdf import PdfReader
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import async_session_factory, init_db
from app.models.standard import Standard, StandardClause
from app.rag.vector_store import EmbeddingEngine, get_vector_store
from app.services.standard_service import VERIFIED_STANDARDS_SEED


class StandardPdfIngester:
    """
    Ingests Indian Standard specification PDF files:
    - Parses text preserving page indices
    - Identifies clause numbers and titles
    - Creates chunked metadata documents
    - Generates vector embeddings
    - Indexes into Pinecone (with LocalVectorStore fallback)
    - Persists standard and clause records to database
    """

    def __init__(self, db: Optional[AsyncSession] = None):
        self.db = db
        self.vector_store = get_vector_store()

    def parse_pdf_clauses(self, pdf_path: str) -> List[Dict[str, Any]]:
        """Parses a PDF file and segments text into clause blocks with page traceability."""
        reader = PdfReader(pdf_path)
        clauses: List[Dict[str, Any]] = []

        clause_pattern = re.compile(
            r"(?:Clause\s+)?(\d+(?:\.\d+)*)\s+([A-Z][A-Za-z0-9\s,\-–()&/]+?)(?:\n|\.\s+)(.*?)(?=(?:\n(?:Clause\s+)?\d+(?:\.\d+)*\s+[A-Z]|\Z))",
            re.DOTALL,
        )

        for page_idx, page in enumerate(reader.pages):
            page_num = page_idx + 1
            text = page.extract_text() or ""
            matches = clause_pattern.findall(text)
            for num, title, body in matches:
                clean_body = re.sub(r"\s+", " ", body).strip()
                if len(clean_body) > 20:  # Ignore trivial headers
                    clauses.append(
                        {
                            "clause_number": num.strip(),
                            "title": title.strip(),
                            "text": clean_body,
                            "page": page_num,
                        }
                    )

        # If strict clause regex found nothing, chunk page by page
        if not clauses:
            for page_idx, page in enumerate(reader.pages):
                text = page.extract_text() or ""
                clean_text = re.sub(r"\s+", " ", text).strip()
                if clean_text:
                    clauses.append(
                        {
                            "clause_number": f"Page-{page_idx + 1}",
                            "title": f"Specification Section (Page {page_idx + 1})",
                            "text": clean_text[:2000],
                            "page": page_idx + 1,
                        }
                    )

        return clauses

    async def ingest_standard(
        self,
        standard_id: str,
        title: str,
        category: str,
        version: str,
        scope: str,
        clauses: List[Dict[str, Any]],
        source_doc: Optional[str] = None,
    ) -> int:
        """Indexes parsed clauses into vector store and database."""
        vectors = []
        for c in clauses:
            chunk_text = f"Standard: {standard_id} Clause {c['clause_number']} {c['title']}: {c['text']}"
            embedding = EmbeddingEngine.get_embedding(chunk_text)
            v_id = f"{standard_id}#{c['clause_number']}".replace(" ", "_")
            meta = {
                "standard_id": standard_id,
                "clause": c["clause_number"],
                "title": c["title"],
                "text": c["text"],
                "page": c.get("page", 1),
                "category": category,
                "version": version,
            }
            vectors.append({"id": v_id, "values": embedding, "metadata": meta})

        # 1. Upsert into Vector Store
        indexed_count = self.vector_store.upsert(vectors)

        # 2. Persist to Database if session provided
        if self.db:
            stmt = select(Standard).where(Standard.standard_id == standard_id)
            res = await self.db.execute(stmt)
            std = res.scalar_one_or_none()
            if not std:
                std = Standard(
                    standard_id=standard_id,
                    title=title,
                    version=version,
                    category=category,
                    scope=scope,
                    source=source_doc or "Bureau of Indian Standards",
                    active=True,
                )
                self.db.add(std)
                await self.db.flush()

            for c in clauses:
                cl_obj = StandardClause(
                    standard_id=standard_id,
                    clause_number=c["clause_number"],
                    title=c["title"],
                    text=c["text"],
                    page=c.get("page", 1),
                    source_document=source_doc,
                    embedding_id=f"{standard_id}#{c['clause_number']}".replace(" ", "_"),
                )
                self.db.add(cl_obj)
            await self.db.commit()

        return indexed_count

    async def ingest_verified_sample_standards(self) -> int:
        """Ingests the verified standards seed with full clause indexing."""
        total = 0
        for item in VERIFIED_STANDARDS_SEED:
            count = await self.ingest_standard(
                standard_id=item["standard_id"],
                title=item["title"],
                category=item["category"],
                version=item["version"],
                scope=item["scope"],
                clauses=item.get("clauses", []),
                source_doc="Official Gazette & BIS Repository",
            )
            total += count
            print(f"  [+] Ingested {item['standard_id']} ({len(item.get('clauses', []))} clauses)")
        return total


async def run_cli():
    parser = argparse.ArgumentParser(description="Bureau of Indian Standards (BIS) Knowledge Ingestion CLI")
    parser.add_argument("--pdf", type=str, help="Path to BIS Standard PDF file")
    parser.add_argument("--standard-id", type=str, help="Standard ID (e.g. 'IS 16102 (Part 1) : 2012')")
    parser.add_argument("--title", type=str, help="Standard Title")
    parser.add_argument("--category", type=str, default="General", help="Product Category")
    parser.add_argument("--version", type=str, default="2024", help="Standard Edition / Year")
    parser.add_argument("--sample", action="store_true", help="Ingest sample verified Indian Standards into vector index")

    args = parser.parse_args()

    await init_db()

    async with async_session_factory() as session:
        ingester = StandardPdfIngester(session)

        if args.sample:
            print("==================================================")
            print("INGESTING VERIFIED INDIAN STANDARDS KNOWLEDGE BASE")
            print("==================================================")
            total = await ingester.ingest_verified_sample_standards()
            stats = ingester.vector_store.describe_index_stats()
            print(f"\n[OK] Successfully indexed {total} verified clauses into vector store.")
            print(f"Vector Store Stats: {stats}")
            return

        if args.pdf:
            pdf_path = Path(args.pdf)
            if not pdf_path.exists():
                print(f"[ERROR] PDF file not found: {args.pdf}")
                sys.exit(1)

            std_id = args.standard_id or pdf_path.stem
            title = args.title or f"Indian Standard {std_id}"

            print(f"Parsing PDF: {args.pdf}...")
            clauses = ingester.parse_pdf_clauses(str(pdf_path))
            print(f"Found {len(clauses)} clauses. Generating embeddings and indexing...")

            count = await ingester.ingest_standard(
                standard_id=std_id,
                title=title,
                category=args.category,
                version=args.version,
                scope=f"Standard specification for {title}",
                clauses=clauses,
                source_doc=pdf_path.name,
            )
            print(f"[OK] Ingestion complete: {count} clauses indexed into vector store.")
        else:
            parser.print_help()


if __name__ == "__main__":
    asyncio.run(run_cli())
