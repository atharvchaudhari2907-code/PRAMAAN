from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import (
    User,
    UserSession,
    EmailVerificationToken,
    PasswordResetToken,
    ManufacturerProfile,
)


class UserRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, user_id: str) -> Optional[User]:
        result = await self.db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> Optional[User]:
        normalized = email.strip().lower()
        result = await self.db.execute(select(User).where(User.email == normalized))
        return result.scalar_one_or_none()

    async def create(self, user: User) -> User:
        self.db.add(user)
        await self.db.flush()
        return user

    async def create_session(self, session: UserSession) -> UserSession:
        self.db.add(session)
        await self.db.flush()
        return session

    async def get_session_by_hash(self, token_hash: str) -> Optional[UserSession]:
        result = await self.db.execute(
            select(UserSession).where(
                UserSession.refresh_token_hash == token_hash,
                UserSession.is_revoked.is_(False),
                UserSession.expires_at > datetime.now(timezone.utc),
            )
        )
        return result.scalar_one_or_none()

    async def revoke_session_by_hash(self, token_hash: str) -> None:
        await self.db.execute(
            update(UserSession)
            .where(UserSession.refresh_token_hash == token_hash)
            .values(is_revoked=True)
        )
        await self.db.flush()

    async def revoke_all_user_sessions(self, user_id: str) -> None:
        await self.db.execute(
            update(UserSession)
            .where(UserSession.user_id == user_id)
            .values(is_revoked=True)
        )
        await self.db.flush()

    async def create_email_token(self, token_record: EmailVerificationToken) -> EmailVerificationToken:
        self.db.add(token_record)
        await self.db.flush()
        return token_record

    async def get_valid_email_token(self, token_hash: str) -> Optional[EmailVerificationToken]:
        result = await self.db.execute(
            select(EmailVerificationToken).where(
                EmailVerificationToken.token_hash == token_hash,
                EmailVerificationToken.used_at.is_(None),
                EmailVerificationToken.expires_at > datetime.now(timezone.utc),
            )
        )
        return result.scalar_one_or_none()

    async def mark_email_token_used(self, token_record: EmailVerificationToken) -> None:
        token_record.used_at = datetime.now(timezone.utc)
        await self.db.flush()

    async def create_password_token(self, token_record: PasswordResetToken) -> PasswordResetToken:
        self.db.add(token_record)
        await self.db.flush()
        return token_record

    async def get_valid_password_token(self, token_hash: str) -> Optional[PasswordResetToken]:
        result = await self.db.execute(
            select(PasswordResetToken).where(
                PasswordResetToken.token_hash == token_hash,
                PasswordResetToken.used_at.is_(None),
                PasswordResetToken.expires_at > datetime.now(timezone.utc),
            )
        )
        return result.scalar_one_or_none()

    async def mark_password_token_used(self, token_record: PasswordResetToken) -> None:
        token_record.used_at = datetime.now(timezone.utc)
        await self.db.flush()
