import logging
import re
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.standard import Standard, StandardClause
from app.rag.vector_store import EmbeddingEngine, get_vector_store

logger = logging.getLogger("app.rag.retriever")


class RetrievedClause(BaseModel):
    standard_id: str
    clause: str
    title: str
    text: str
    page: Optional[int] = None
    category: str = "General"
    version: str = "2024"
    relevance_score: float = 0.0


class ClauseRetriever:
    """
    Clause-level RAG retrieval pipeline:
    Product Data & Parameters
        ↓
    Query Generation
        ↓
    Vector Embedding
        ↓
    Pinecone / Local Search
        ↓
    Metadata Filtering (standard_id, category, clause)
        ↓
    Top Clauses
        ↓
    Domain Keyword Reranking
        ↓
    Compliance Engine
    """

    def __init__(self, db: Optional[AsyncSession] = None):
        self.db = db
        self.vector_store = get_vector_store()

    async def retrieve_clauses(
        self,
        standard_id: str,
        product_name: str,
        category: str,
        parameters: Optional[List[Dict[str, Any]]] = None,
        top_k: int = 10,
    ) -> List[RetrievedClause]:
        # 1. Query Generation
        param_terms = []
        if parameters:
            for p in parameters:
                k = p.get("parameter_key") or p.get("name") or ""
                v = p.get("value") or ""
                u = p.get("unit") or ""
                param_terms.append(f"{k} {v}{u}")

        query_str = f"{product_name} {category} {standard_id} " + " ".join(param_terms)

        # 2. Embedding
        query_vector = EmbeddingEngine.get_embedding(query_str)

        # 3. Vector Search with Metadata Filtering
        filter_dict = {"standard_id": standard_id}
        resp = self.vector_store.query(
            vector=query_vector, top_k=top_k * 2, filter=filter_dict
        )

        results: List[RetrievedClause] = []

        # If vector store returned matches
        if resp.matches:
            for match in resp.matches:
                meta = match.metadata
                results.append(
                    RetrievedClause(
                        standard_id=meta.get("standard_id", standard_id),
                        clause=meta.get("clause", "General"),
                        title=meta.get("title", ""),
                        text=meta.get("text", ""),
                        page=meta.get("page"),
                        category=meta.get("category", category),
                        version=meta.get("version", ""),
                        relevance_score=float(match.score),
                    )
                )

        # If vector store is empty or returned no matches for this standard, pull from database and index
        if not results and self.db:
            results = await self._hydrate_and_search_from_db(standard_id, query_str, query_vector)

        # 4. Keyword Reranking
        reranked = self._rerank(results, parameters or [])
        return reranked[:top_k]

    async def _hydrate_and_search_from_db(
        self, standard_id: str, query_str: str, query_vector: List[float]
    ) -> List[RetrievedClause]:
        """Loads clauses directly from standard repository, indexes them into vector store, and returns them."""
        stmt = select(Standard).where(Standard.standard_id == standard_id).options(selectinload(Standard.clauses))
        res = await self.db.execute(stmt)
        std = res.scalar_one_or_none()
        if not std or not std.clauses:
            return []

        vectors_to_upsert = []
        clause_items: List[RetrievedClause] = []

        for c in std.clauses:
            clause_text = f"{c.clause_number} {c.title}: {c.text}"
            c_emb = EmbeddingEngine.get_embedding(clause_text)
            meta = {
                "standard_id": std.standard_id,
                "clause": c.clause_number,
                "title": c.title,
                "text": c.text,
                "page": c.page,
                "category": std.category,
                "version": std.version,
            }
            v_id = f"{std.standard_id}#{c.clause_number}".replace(" ", "_")
            vectors_to_upsert.append({"id": v_id, "values": c_emb, "metadata": meta})

            clause_items.append(
                RetrievedClause(
                    standard_id=std.standard_id,
                    clause=c.clause_number,
                    title=c.title,
                    text=c.text,
                    page=c.page,
                    category=std.category,
                    version=std.version,
                    relevance_score=0.8,
                )
            )

        if vectors_to_upsert:
            self.vector_store.upsert(vectors_to_upsert)

        return clause_items

    def _rerank(
        self, clauses: List[RetrievedClause], parameters: List[Dict[str, Any]]
    ) -> List[RetrievedClause]:
        """Boosts clauses that directly match parameter keys, units, or safety requirements."""
        param_words = set()
        for p in parameters:
            k = (p.get("parameter_key") or "").lower().replace("_", " ")
            n = (p.get("name") or "").lower()
            for w in re.findall(r"\w+", f"{k} {n}"):
                if len(w) > 3:
                    param_words.add(w)

        for clause in clauses:
            boost = 0.0
            content = f"{clause.title} {clause.text}".lower()
            for word in param_words:
                if word in content:
                    boost += 0.15

            # Priority boost for critical safety clauses
            if any(term in content for term in ["shock", "insulation", "proof pressure", "efficacy", "thd", "power factor"]):
                boost += 0.20

            clause.relevance_score = min(1.0, clause.relevance_score + boost)

        clauses.sort(key=lambda x: x.relevance_score, reverse=True)
        return clauses
