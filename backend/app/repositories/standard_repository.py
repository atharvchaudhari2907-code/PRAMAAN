from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.standard import Standard, StandardClause


class StandardRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_all(self, active_only: bool = True) -> List[Standard]:
        stmt = select(Standard)
        if active_only:
            stmt = stmt.where(Standard.active.is_(True))
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def list_standards(self, active_only: bool = True) -> List[Standard]:
        return await self.get_all(active_only)

    async def get_by_id(self, standard_id: str, load_clauses: bool = False) -> Optional[Standard]:
        stmt = select(Standard).where(Standard.standard_id == standard_id)
        if load_clauses:
            stmt = stmt.options(selectinload(Standard.clauses))
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_standard_by_id(self, standard_id: str, load_clauses: bool = True) -> Optional[Standard]:
        return await self.get_by_id(standard_id, load_clauses)

    async def create_standard(self, standard: Standard) -> Standard:
        self.db.add(standard)
        await self.db.flush()
        return standard

    async def create_clause(self, clause: StandardClause) -> StandardClause:
        self.db.add(clause)
        await self.db.flush()
        return clause

    async def count_standards(self) -> int:
        result = await self.db.execute(select(Standard))
        return len(result.scalars().all())
