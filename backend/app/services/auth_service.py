from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import (
    create_access_token,
    generate_secure_token,
    hash_password,
    hash_token,
    verify_password,
)
from app.models.user import EmailVerificationToken, PasswordResetToken, User, UserSession
from app.repositories.user_repository import UserRepository
from app.schemas.auth import (
    LoginRequest,
    PasswordResetConfirm,
    PasswordResetRequest,
    SignupRequest,
    TokenResponse,
    UserResponse,
)
from app.services.email_service import get_email_service


class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.user_repo = UserRepository(db)
        self.email_service = get_email_service()

    async def register(self, data: SignupRequest) -> Tuple[TokenResponse, str]:
        """
        Registers a new user, hashes password via PBKDF2, creates verification token,
        creates user session, and dispatches verification notification.
        Returns (TokenResponse, raw_refresh_token).
        """
        existing_user = await self.user_repo.get_by_email(data.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="An account with this email address already exists. Please sign in.",
            )

        hashed_pwd = hash_password(data.password)
        user = User(
            email=data.email.strip().lower(),
            hashed_password=hashed_pwd,
            full_name=data.full_name.strip(),
            company_name=data.company_name.strip() if data.company_name else None,
            role="manufacturer",
            auth_provider="local",
            email_verified=False,
            is_active=True,
        )
        await self.user_repo.create(user)

        # Create email verification token
        raw_verify_token, verify_token_hash = generate_secure_token()
        verif_record = EmailVerificationToken(
            user_id=user.id,
            token_hash=verify_token_hash,
            expires_at=datetime.now(timezone.utc) + timedelta(days=2),
        )
        await self.user_repo.create_email_token(verif_record)

        # Dispatch email
        await self.email_service.send_verification_email(
            user.email, raw_verify_token, user.full_name or ""
        )

        # Generate access token & session
        access_token = create_access_token(
            subject=user.id,
            extra_claims={"email": user.email, "role": user.role},
        )
        raw_refresh_token, refresh_hash = generate_secure_token()
        session = UserSession(
            user_id=user.id,
            refresh_token_hash=refresh_hash,
            expires_at=datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
        )
        await self.user_repo.create_session(session)

        token_response = TokenResponse(
            access_token=access_token,
            token_type="bearer",
            user=UserResponse.model_validate(user),
            message="Registration successful. A verification link has been sent to your email.",
        )
        return token_response, raw_refresh_token

    async def login(
        self,
        data: LoginRequest,
        user_agent: Optional[str] = None,
        ip_address: Optional[str] = None,
    ) -> Tuple[TokenResponse, str]:
        """
        Authenticates a user with email and password.
        Returns (TokenResponse, raw_refresh_token).
        """
        user = await self.user_repo.get_by_email(data.email)
        if not user or not verify_password(data.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password.",
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Your account has been deactivated. Please contact support.",
            )

        access_token = create_access_token(
            subject=user.id,
            extra_claims={"email": user.email, "role": user.role},
        )

        raw_refresh_token, refresh_hash = generate_secure_token()
        session = UserSession(
            user_id=user.id,
            refresh_token_hash=refresh_hash,
            user_agent=user_agent,
            ip_address=ip_address,
            expires_at=datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
        )
        await self.user_repo.create_session(session)

        token_response = TokenResponse(
            access_token=access_token,
            token_type="bearer",
            user=UserResponse.model_validate(user),
            message="Login successful.",
        )
        return token_response, raw_refresh_token

    async def refresh_session(self, raw_refresh_token: str) -> Tuple[TokenResponse, str]:
        """
        Validates refresh token, rotates token, and generates new access token.
        """
        refresh_hash = hash_token(raw_refresh_token)
        session = await self.user_repo.get_session_by_hash(refresh_hash)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired session. Please log in again.",
            )

        # Invalidate old session
        session.is_revoked = True

        user = await self.user_repo.get_by_id(session.user_id)
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User account inactive or not found.",
            )

        # Create new access token
        access_token = create_access_token(
            subject=user.id,
            extra_claims={"email": user.email, "role": user.role},
        )

        # Issue rotated refresh token
        new_raw_refresh, new_refresh_hash = generate_secure_token()
        new_session = UserSession(
            user_id=user.id,
            refresh_token_hash=new_refresh_hash,
            user_agent=session.user_agent,
            ip_address=session.ip_address,
            expires_at=datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
        )
        await self.user_repo.create_session(new_session)

        token_response = TokenResponse(
            access_token=access_token,
            token_type="bearer",
            user=UserResponse.model_validate(user),
            message="Token refreshed successfully.",
        )
        return token_response, new_raw_refresh

    async def logout(self, raw_refresh_token: Optional[str]) -> None:
        """Revokes the active user session."""
        if raw_refresh_token:
            refresh_hash = hash_token(raw_refresh_token)
            await self.user_repo.revoke_session_by_hash(refresh_hash)

    async def verify_email(self, raw_token: str) -> None:
        """Validates and consumes an email verification token."""
        token_hash = hash_token(raw_token)
        token_record = await self.user_repo.get_valid_email_token(token_hash)
        if not token_record:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This verification link is invalid or has expired.",
            )

        user = await self.user_repo.get_by_id(token_record.user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found.",
            )

        user.email_verified = True
        await self.user_repo.mark_email_token_used(token_record)

    async def resend_verification(self, email: str) -> None:
        """Issues and sends a fresh verification token."""
        user = await self.user_repo.get_by_email(email)
        if not user:
            # Avoid leaking whether user exists
            return

        if user.email_verified:
            return

        raw_token, token_hash = generate_secure_token()
        record = EmailVerificationToken(
            user_id=user.id,
            token_hash=token_hash,
            expires_at=datetime.now(timezone.utc) + timedelta(days=2),
        )
        await self.user_repo.create_email_token(record)
        await self.email_service.send_verification_email(
            user.email, raw_token, user.full_name or ""
        )

    async def forgot_password(self, data: PasswordResetRequest) -> None:
        """Creates password reset token and dispatches email."""
        user = await self.user_repo.get_by_email(data.email)
        if not user or not user.is_active:
            # Silent return to prevent account enumeration
            return

        raw_token, token_hash = generate_secure_token()
        record = PasswordResetToken(
            user_id=user.id,
            token_hash=token_hash,
            expires_at=datetime.now(timezone.utc) + timedelta(hours=2),
        )
        await self.user_repo.create_password_token(record)
        await self.email_service.send_password_reset_email(user.email, raw_token)

    async def reset_password(self, data: PasswordResetConfirm) -> None:
        """
        Validates password reset token, updates password with PBKDF2 hash,
        and revokes ALL active user sessions across all devices immediately.
        """
        token_hash = hash_token(data.token)
        record = await self.user_repo.get_valid_password_token(token_hash)
        if not record:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This password reset link is invalid or has expired.",
            )

        user = await self.user_repo.get_by_id(record.user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found.",
            )

        user.hashed_password = hash_password(data.new_password)
        await self.user_repo.mark_password_token_used(record)

        # STRICT SECURITY REQUIREMENT: Revoke all existing sessions across all devices
        await self.user_repo.revoke_all_user_sessions(user.id)
