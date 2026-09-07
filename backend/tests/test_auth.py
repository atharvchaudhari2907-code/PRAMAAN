import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import EmailVerificationToken, PasswordResetToken, User


@pytest.mark.asyncio
async def test_registration_and_duplicate_email(client: AsyncClient):
    payload = {
        "email": "manufacturer@example.com",
        "password": "Password@123",
        "full_name": "Test Manufacturer",
        "company_name": "Acme Industries",
    }
    # 1. Register first time -> 201
    resp = await client.post("/api/auth/register", json=payload)
    assert resp.status_code == 201
    data = resp.json()
    assert "access_token" in data
    assert data["user"]["email"] == "manufacturer@example.com"
    assert data["user"]["full_name"] == "Test Manufacturer"
    assert data["user"]["email_verified"] is False

    # 2. Duplicate registration -> 409
    resp_dup = await client.post("/api/auth/register", json=payload)
    assert resp_dup.status_code == 409
    assert "already exists" in resp_dup.json()["detail"].lower()


@pytest.mark.asyncio
async def test_password_complexity_validation(client: AsyncClient):
    # Missing uppercase, digit, special char
    weak_payload = {
        "email": "weak@example.com",
        "password": "simplepassword",
        "full_name": "Weak User",
    }
    resp = await client.post("/api/auth/register", json=weak_payload)
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_login_success_and_failure(client: AsyncClient):
    # Register user first
    await client.post(
        "/api/auth/register",
        json={
            "email": "loginuser@example.com",
            "password": "Password@123",
            "full_name": "Login User",
        },
    )

    # Valid login
    resp = await client.post(
        "/api/auth/login",
        json={"email": "loginuser@example.com", "password": "Password@123"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert data["user"]["email"] == "loginuser@example.com"

    # Invalid password
    resp_bad = await client.post(
        "/api/auth/login",
        json={"email": "loginuser@example.com", "password": "WrongPassword@123"},
    )
    assert resp_bad.status_code == 401
    assert "invalid email or password" in resp_bad.json()["detail"].lower()


@pytest.mark.asyncio
async def test_protected_endpoint(client: AsyncClient):
    # Unauthenticated request -> 401
    resp_unauth = await client.get("/api/auth/me")
    assert resp_unauth.status_code == 401

    # Authenticated request -> 200
    login_resp = await client.post(
        "/api/auth/register",
        json={
            "email": "protecteduser@example.com",
            "password": "Password@123",
            "full_name": "Protected User",
        },
    )
    token = login_resp.json()["access_token"]
    resp_auth = await client.get(
        "/api/auth/me", headers={"Authorization": f"Bearer {token}"}
    )
    assert resp_auth.status_code == 200
    assert resp_auth.json()["email"] == "protecteduser@example.com"


@pytest.mark.asyncio
async def test_email_verification_flow(client: AsyncClient, db_session: AsyncSession):
    # Register user
    await client.post(
        "/api/auth/register",
        json={
            "email": "verifyuser@example.com",
            "password": "Password@123",
            "full_name": "Verify User",
        },
    )

    # Find the user's verification token
    result = await db_session.execute(
        select(EmailVerificationToken).join(User).where(User.email == "verifyuser@example.com")
    )
    token_record = result.scalars().first()
    assert token_record is not None

    # Replace hash with known token for testing
    from app.core.security import generate_secure_token
    raw_token, token_hash = generate_secure_token()
    token_record.token_hash = token_hash
    await db_session.commit()

    resp = await client.post("/api/auth/verify-email", json={"token": raw_token})
    assert resp.status_code == 200
    assert "verified successfully" in resp.json()["message"].lower()

    # Re-using consumed token must fail
    resp_reuse = await client.post("/api/auth/verify-email", json={"token": raw_token})
    assert resp_reuse.status_code == 400


@pytest.mark.asyncio
async def test_password_reset_and_session_revocation(client: AsyncClient, db_session: AsyncSession):
    # Register user
    await client.post(
        "/api/auth/register",
        json={
            "email": "resetuser@example.com",
            "password": "Password@123",
            "full_name": "Reset User",
        },
    )

    # Request forgot password
    resp_forgot = await client.post(
        "/api/auth/forgot-password", json={"email": "resetuser@example.com"}
    )
    assert resp_forgot.status_code == 200

    # Retrieve reset token
    result = await db_session.execute(
        select(PasswordResetToken).join(User).where(User.email == "resetuser@example.com")
    )
    reset_record = result.scalars().first()
    assert reset_record is not None

    from app.core.security import generate_secure_token
    raw_token, token_hash = generate_secure_token()
    reset_record.token_hash = token_hash
    await db_session.commit()

    # Reset password
    resp_reset = await client.post(
        "/api/auth/reset-password",
        json={
            "token": raw_token,
            "new_password": "NewSecurePassword@456",
            "confirm_password": "NewSecurePassword@456",
        },
    )
    assert resp_reset.status_code == 200

    # Old password no longer works
    resp_old = await client.post(
        "/api/auth/login",
        json={"email": "resetuser@example.com", "password": "Password@123"},
    )
    assert resp_old.status_code == 401

    # New password works
    resp_new = await client.post(
        "/api/auth/login",
        json={"email": "resetuser@example.com", "password": "NewSecurePassword@456"},
    )
    assert resp_new.status_code == 200


@pytest.mark.asyncio
async def test_logout(client: AsyncClient):
    resp = await client.post("/api/auth/logout")
    assert resp.status_code == 200
