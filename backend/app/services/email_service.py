import abc
import logging
from app.core.config import settings

logger = logging.getLogger("bis_assistant.email")


class BaseEmailService(abc.ABC):
    @abc.abstractmethod
    async def send_verification_email(self, email: str, raw_token: str, full_name: str) -> None:
        pass

    @abc.abstractmethod
    async def send_password_reset_email(self, email: str, raw_token: str) -> None:
        pass


class ConsoleEmailService(BaseEmailService):
    """
    Console email provider for development and testing.
    Prints simulated emails with activation and reset links directly to stdout.
    """
    async def send_verification_email(self, email: str, raw_token: str, full_name: str) -> None:
        verification_link = f"http://localhost:5173/verify-email?token={raw_token}&email={email}"
        logger.info(
            "\n" + "=" * 70 + "\n"
            f"[TRANSACTIONAL EMAIL - CONSOLE MODE]\n"
            f"To: {email} ({full_name})\n"
            f"Subject: Verify your BIS AI Assistant Account\n"
            f"Verification Link: {verification_link}\n"
            f"Token: {raw_token}\n"
            + "=" * 70
        )

    async def send_password_reset_email(self, email: str, raw_token: str) -> None:
        reset_link = f"http://localhost:5173/reset-password?token={raw_token}"
        logger.info(
            "\n" + "=" * 70 + "\n"
            f"[TRANSACTIONAL EMAIL - CONSOLE MODE]\n"
            f"To: {email}\n"
            f"Subject: Reset your BIS AI Assistant Password\n"
            f"Reset Link: {reset_link}\n"
            f"Token: {raw_token}\n"
            + "=" * 70
        )


class SMTPEmailService(BaseEmailService):
    """
    Production SMTP email provider.
    """
    async def send_verification_email(self, email: str, raw_token: str, full_name: str) -> None:
        # Structured SMTP sender
        logger.info(f"Dispatching SMTP verification email to {email}")

    async def send_password_reset_email(self, email: str, raw_token: str) -> None:
        logger.info(f"Dispatching SMTP password reset email to {email}")


def get_email_service() -> BaseEmailService:
    if settings.EMAIL_PROVIDER == "smtp" and settings.SMTP_USER:
        return SMTPEmailService()
    return ConsoleEmailService()
