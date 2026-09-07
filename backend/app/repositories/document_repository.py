from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.application import ApplicationDocument


class DocumentRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, doc: ApplicationDocument) -> ApplicationDocument:
        self.db.add(doc)
        await self.db.flush()
        return doc

    async def get_by_id(self, document_id: str) -> Optional[ApplicationDocument]:
        result = await self.db.execute(
            select(ApplicationDocument).where(ApplicationDocument.id == document_id)
        )
        return result.scalar_one_or_none()

    async def list_by_application(self, application_id: str) -> List[ApplicationDocument]:
        result = await self.db.execute(
            select(ApplicationDocument)
            .where(ApplicationDocument.application_id == application_id)
            .order_by(ApplicationDocument.created_at.desc())
        )
        return list(result.scalars().all())

    async def delete(self, doc: ApplicationDocument) -> None:
        await self.db.delete(doc)
        await self.db.flush()
