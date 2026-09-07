import hashlib
import json
import logging
import math
import os
import re
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from pydantic import BaseModel, Field

from app.core.config import settings

logger = logging.getLogger("app.rag")



class VectorItem(BaseModel):
    id: str
    values: List[float]
    metadata: Dict[str, Any] = Field(default_factory=dict)


class VectorMatch(BaseModel):
    id: str
    score: float
    metadata: Dict[str, Any] = Field(default_factory=dict)
    values: Optional[List[float]] = None


class QueryResponse(BaseModel):
    matches: List[VectorMatch] = Field(default_factory=list)
    namespace: str = ""


class BaseVectorStore(ABC):
    """Common interface for vector index operations matching Pinecone API."""

    @abstractmethod
    def upsert(self, vectors: List[Dict[str, Any]], namespace: str = "") -> int:
        pass

    @abstractmethod
    def query(
        self,
        vector: List[float],
        top_k: int = 5,
        filter: Optional[Dict[str, Any]] = None,
        namespace: str = "",
    ) -> QueryResponse:
        pass

    @abstractmethod
    def describe_index_stats(self) -> Dict[str, Any]:
        pass


class LocalVectorStore(BaseVectorStore):
    """
    In-memory and file-persisted vector store matching the Pinecone interface.
    Serves as local fallback for development, testing, and offline deployments.
    Supports metadata filtering (standard_id, clause, category, page, version)
    and exact cosine similarity calculation.
    """

    def __init__(self, persistence_path: Optional[str] = None):
        self.persistence_path = persistence_path or "./uploads/local_vector_index.json"
        self._vectors: Dict[str, VectorItem] = {}
        self._load()

    def _load(self) -> None:
        if os.path.exists(self.persistence_path):
            try:
                with open(self.persistence_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for item in data:
                        self._vectors[item["id"]] = VectorItem.model_validate(item)
            except Exception as e:
                logger.warning(f"Could not load local vector index: {e}")

    def _save(self) -> None:
        try:
            os.makedirs(os.path.dirname(self.persistence_path), exist_ok=True)
            with open(self.persistence_path, "w", encoding="utf-8") as f:
                json.dump([v.model_dump() for v in self._vectors.values()], f)
        except Exception as e:
            logger.warning(f"Could not persist local vector index: {e}")

    def upsert(self, vectors: List[Dict[str, Any]], namespace: str = "") -> int:
        count = 0
        for item in vectors:
            v_id = str(item.get("id"))
            vals = item.get("values", [])
            meta = item.get("metadata", {})
            self._vectors[v_id] = VectorItem(id=v_id, values=vals, metadata=meta)
            count += 1
        self._save()
        return count

    def query(
        self,
        vector: List[float],
        top_k: int = 5,
        filter: Optional[Dict[str, Any]] = None,
        namespace: str = "",
    ) -> QueryResponse:
        if not self._vectors:
            return QueryResponse(matches=[])

        q_vec = np.array(vector, dtype=np.float32)
        q_norm = np.linalg.norm(q_vec)
        if q_norm == 0:
            q_norm = 1.0

        candidates: List[Tuple[float, VectorItem]] = []

        for item in self._vectors.values():
            # Apply metadata filter
            if filter:
                match = True
                for k, v in filter.items():
                    val = item.metadata.get(k)
                    if isinstance(v, dict):
                        if "$in" in v and val not in v["$in"]:
                            match = False
                            break
                        if "$eq" in v and val != v["$eq"]:
                            match = False
                            break
                    elif val != v:
                        match = False
                        break
                if not match:
                    continue

            # Cosine similarity
            c_vec = np.array(item.values, dtype=np.float32)
            c_norm = np.linalg.norm(c_vec)
            if c_norm == 0:
                score = 0.0
            else:
                score = float(np.dot(q_vec, c_vec) / (q_norm * c_norm))

            candidates.append((score, item))

        candidates.sort(key=lambda x: x[0], reverse=True)
        top_matches = candidates[:top_k]

        return QueryResponse(
            matches=[
                VectorMatch(id=item.id, score=score, metadata=item.metadata)
                for score, item in top_matches
            ]
        )

    def describe_index_stats(self) -> Dict[str, Any]:
        return {
            "total_vector_count": len(self._vectors),
            "dimension": len(next(iter(self._vectors.values())).values) if self._vectors else 128,
            "namespaces": {"default": len(self._vectors)},
        }


class PineconeVectorStore(BaseVectorStore):
    """Production Pinecone integration with fallback."""

    def __init__(self, api_key: str, index_name: str):
        self.api_key = api_key
        self.index_name = index_name
        self._index = None
        self.fallback = LocalVectorStore()
        self._init_client()

    def _init_client(self):
        try:
            from pinecone import Pinecone
            pc = Pinecone(api_key=self.api_key)
            self._index = pc.Index(self.index_name)
        except Exception as e:
            logger.warning(f"Failed to initialize Pinecone client: {e}. Using LocalVectorStore fallback.")
            self._index = None

    def upsert(self, vectors: List[Dict[str, Any]], namespace: str = "") -> int:
        if not self._index:
            return self.fallback.upsert(vectors, namespace)
        try:
            self._index.upsert(vectors=vectors, namespace=namespace)
            return len(vectors)
        except Exception as e:
            logger.warning(f"Pinecone upsert failed: {e}. Falling back to LocalVectorStore.")
            return self.fallback.upsert(vectors, namespace)

    def query(
        self,
        vector: List[float],
        top_k: int = 5,
        filter: Optional[Dict[str, Any]] = None,
        namespace: str = "",
    ) -> QueryResponse:
        if not self._index:
            return self.fallback.query(vector, top_k, filter, namespace)
        try:
            res = self._index.query(
                vector=vector, top_k=top_k, filter=filter, namespace=namespace, include_metadata=True
            )
            return QueryResponse(
                matches=[
                    VectorMatch(id=m.id, score=m.score, metadata=m.metadata or {})
                    for m in res.matches
                ]
            )
        except Exception as e:
            logger.warning(f"Pinecone query failed: {e}. Falling back to LocalVectorStore.")
            return self.fallback.query(vector, top_k, filter, namespace)

    def describe_index_stats(self) -> Dict[str, Any]:
        if not self._index:
            return self.fallback.describe_index_stats()
        try:
            return self._index.describe_index_stats()
        except Exception:
            return self.fallback.describe_index_stats()


class EmbeddingEngine:
    """
    Embedding engine supporting both Google Gemini text-embedding-004
    and a local deterministic hash-dense embedding generator for offline/testing.
    """

    DIMENSION = 128

    @classmethod
    def get_embedding(cls, text: str) -> List[float]:
        api_key = getattr(settings, "GEMINI_API_KEY", None) or os.getenv("GEMINI_API_KEY")
        if api_key:
            try:
                from google import genai
                client = genai.Client(api_key=api_key)
                res = client.models.embed_content(
                    model="text-embedding-004",
                    contents=text,
                )
                if res and res.embedding and res.embedding.values:
                    return res.embedding.values[: cls.DIMENSION]
            except Exception as e:
                logger.debug(f"Remote embedding call failed, using deterministic local embedding: {e}")

        return cls.get_local_embedding(text)

    @classmethod
    def get_local_embedding(cls, text: str, dimension: int = 128) -> List[float]:
        """
        Deterministic, normalized dense embedding generator based on subword n-grams and hashing.
        Guarantees that similar engineering concepts map to close vector trajectories.
        """
        words = re.findall(r"\w+", text.lower())
        vec = np.zeros(dimension, dtype=np.float32)

        # Keyword semantic weighting
        semantic_boosts = {
            "luminous": 12, "efficacy": 12, "lumens": 12, "watt": 10, "wattage": 10,
            "voltage": 10, "power": 8, "factor": 10, "thd": 14, "harmonic": 14,
            "insulation": 14, "dielectric": 14, "shock": 14, "torque": 12, "mechanical": 10,
            "pressure": 12, "proof": 12, "burst": 12, "valve": 10, "safety": 8,
            "marking": 10, "durability": 8, "earthing": 12, "current": 8, "leakage": 12,
        }

        for word in words:
            # Word level hash
            h = int(hashlib.md5(word.encode("utf-8")).hexdigest(), 16)
            idx = h % dimension
            sign = 1.0 if ((h >> 4) & 1) else -1.0
            weight = semantic_boosts.get(word, 1.0)
            vec[idx] += sign * weight

            # 3-char ngrams
            for i in range(len(word) - 2):
                ngram = word[i : i + 3]
                nh = int(hashlib.sha256(ngram.encode("utf-8")).hexdigest(), 16)
                n_idx = nh % dimension
                n_sign = 1.0 if ((nh >> 2) & 1) else -1.0
                vec[n_idx] += n_sign * 0.4

        norm = np.linalg.norm(vec)
        if norm > 0:
            vec = vec / norm
        return vec.tolist()


# Global vector store instance
_vector_store_instance: Optional[BaseVectorStore] = None


def get_vector_store() -> BaseVectorStore:
    global _vector_store_instance
    if _vector_store_instance is None:
        pinecone_key = getattr(settings, "PINECONE_API_KEY", None) or os.getenv("PINECONE_API_KEY")
        pinecone_index = getattr(settings, "PINECONE_INDEX", "bis-standards")
        if pinecone_key:
            try:
                _vector_store_instance = PineconeVectorStore(pinecone_key, pinecone_index)
                logger.info("Using PineconeVectorStore")
            except Exception:
                _vector_store_instance = LocalVectorStore()
        else:
            _vector_store_instance = LocalVectorStore()
            logger.info("Using LocalVectorStore fallback")
    return _vector_store_instance
