from typing import List, Optional
from sqlalchemy import Boolean, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin, generate_uuid


class Standard(Base, TimestampMixin):
    __tablename__ = "standards"

    standard_id: Mapped[str] = mapped_column(String(100), primary_key=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    version: Mapped[str] = mapped_column(String(50), nullable=False)
    category: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    scope: Mapped[str] = mapped_column(Text, nullable=False)
    source: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    publication_date: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    clauses: Mapped[List["StandardClause"]] = relationship(
        "StandardClause", back_populates="standard", cascade="all, delete-orphan", order_by="StandardClause.clause_number"
    )


class StandardClause(Base, TimestampMixin):
    __tablename__ = "standard_clauses"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    standard_id: Mapped[str] = mapped_column(String(100), ForeignKey("standards.standard_id", ondelete="CASCADE"), index=True, nullable=False)
    clause_number: Mapped[str] = mapped_column(String(50), index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    page: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    source_document: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    embedding_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    standard: Mapped["Standard"] = relationship("Standard", back_populates="clauses")
