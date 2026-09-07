from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.application import Application, ApplicationStatus, ApplicationStatusEvent
from app.models.product import Product, ProductParameter


class ApplicationRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, app: Application) -> Application:
        self.db.add(app)
        await self.db.flush()
        return app

    async def get_by_id(self, application_id: str, load_details: bool = False) -> Optional[Application]:
        stmt = select(Application).where(Application.id == application_id)
        if load_details:
            stmt = stmt.options(
                selectinload(Application.documents),
                selectinload(Application.status_events),
                selectinload(Application.product).selectinload(Product.parameters),
            )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_id_and_user(
        self, application_id: str, user_id: str, load_details: bool = False
    ) -> Optional[Application]:
        stmt = select(Application).where(
            Application.id == application_id, Application.user_id == user_id
        )
        if load_details:
            stmt = stmt.options(
                selectinload(Application.documents),
                selectinload(Application.status_events),
                selectinload(Application.product).selectinload(Product.parameters),
            )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def list_by_user(self, user_id: str) -> List[Application]:
        stmt = (
            select(Application)
            .where(Application.user_id == user_id)
            .order_by(Application.created_at.desc())
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def delete(self, app: Application) -> None:
        await self.db.delete(app)
        await self.db.flush()

    async def add_status_event(self, event: ApplicationStatusEvent) -> ApplicationStatusEvent:
        self.db.add(event)
        await self.db.flush()
        return event

    async def get_status_events(self, application_id: str) -> List[ApplicationStatusEvent]:
        stmt = (
            select(ApplicationStatusEvent)
            .where(ApplicationStatusEvent.application_id == application_id)
            .order_by(ApplicationStatusEvent.created_at.asc())
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
