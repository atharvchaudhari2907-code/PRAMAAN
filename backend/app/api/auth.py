from typing import Optional
from fastapi import APIRouter, Cookie, Depends, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.middleware.auth_middleware import get_current_user
from app.models.user import User
from app.schemas.auth import (
    LoginRequest,
    PasswordResetConfirm,
    PasswordResetRequest,
    ResendVerificationRequest,
    SignupRequest,
    StatusMessage,
    TokenResponse,
    UserResponse,
    VerifyEmailRequest,
)
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Authentication"])


def set_auth_cookies(response: Response, access_token: str, refresh_token: str) -> None:
    # Access token cookie (60 minutes)
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        samesite="lax",
        secure=not settings.DEBUG,
    )
    # Refresh token cookie (30 days)
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400,
        samesite="lax",
        secure=not settings.DEBUG,
    )


def clear_auth_cookies(response: Response) -> None:
    response.delete_cookie(key="access_token")
    response.delete_cookie(key="refresh_token")


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(
    payload: SignupRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    """Registers a new manufacturer account with PBKDF2 hashed credentials."""
    service = AuthService(db)
    token_resp, raw_refresh = await service.register(payload)
    set_auth_cookies(response, token_resp.access_token, raw_refresh)
    return token_resp


@router.post("/login", response_model=TokenResponse)
async def login(
    payload: LoginRequest,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    """Authenticates user credentials and issues short-lived JWT access token and session."""
    service = AuthService(db)
    user_agent = request.headers.get("user-agent")
    ip_address = request.client.host if request.client else None
    token_resp, raw_refresh = await service.login(payload, user_agent, ip_address)
    set_auth_cookies(response, token_resp.access_token, raw_refresh)
    return token_resp


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    response: Response,
    refresh_token: Optional[str] = Cookie(None),
    db: AsyncSession = Depends(get_db),
):
    """Refreshes the access token using the HttpOnly refresh token cookie."""
    if not refresh_token:
        response.status_code = status.HTTP_401_UNAUTHORIZED
        return {"detail": "Refresh token missing."}

    service = AuthService(db)
    token_resp, new_refresh = await service.refresh_session(refresh_token)
    set_auth_cookies(response, token_resp.access_token, new_refresh)
    return token_resp


@router.post("/logout", response_model=StatusMessage)
async def logout(
    response: Response,
    refresh_token: Optional[str] = Cookie(None),
    db: AsyncSession = Depends(get_db),
):
    """Logs out the user and revokes the active session."""
    service = AuthService(db)
    await service.logout(refresh_token)
    clear_auth_cookies(response)
    return StatusMessage(status="success", message="Successfully logged out.")


@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(
    current_user: User = Depends(get_current_user),
):
    """Returns the authenticated user's profile."""
    return UserResponse.model_validate(current_user)


@router.post("/verify-email", response_model=StatusMessage)
async def verify_email(
    payload: VerifyEmailRequest,
    db: AsyncSession = Depends(get_db),
):
    """Verifies user email via single-use cryptographically hashed token."""
    service = AuthService(db)
    await service.verify_email(payload.token)
    return StatusMessage(status="success", message="Email address verified successfully.")


@router.post("/resend-verification", response_model=StatusMessage)
async def resend_verification(
    payload: ResendVerificationRequest,
    db: AsyncSession = Depends(get_db),
):
    """Re-sends an email verification link to the given address."""
    service = AuthService(db)
    await service.resend_verification(payload.email)
    return StatusMessage(
        status="success",
        message="If an account exists with this email, a new verification link has been sent.",
    )


@router.post("/forgot-password", response_model=StatusMessage)
async def forgot_password(
    payload: PasswordResetRequest,
    db: AsyncSession = Depends(get_db),
):
    """Dispatches a password reset link to the given email address."""
    service = AuthService(db)
    await service.forgot_password(payload)
    return StatusMessage(
        status="success",
        message="If an account exists with this email, password reset instructions have been dispatched.",
    )


@router.post("/reset-password", response_model=StatusMessage)
async def reset_password(
    payload: PasswordResetConfirm,
    db: AsyncSession = Depends(get_db),
):
    """Resets password and invalidates all active sessions across all devices."""
    service = AuthService(db)
    await service.reset_password(payload)
    return StatusMessage(
        status="success",
        message="Password reset successfully. All existing sessions have been terminated. Please log in.",
    )
