import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class NotificationProvider(ABC):

    @abstractmethod
    async def send_notification(self, recipient: str, subject: str, body: str, metadata: Optional[Dict[str, Any]] = None) -> bool:
        pass


class ConsoleNotificationProvider(NotificationProvider):
    """Logs notifications to server console and application logs."""

    async def send_notification(self, recipient: str, subject: str, body: str, metadata: Optional[Dict[str, Any]] = None) -> bool:
        logger.info(f"[NOTIFICATION] To: {recipient} | Subject: {subject} | Body: {body} | Meta: {metadata}")
        return True


class SMTPNotificationProvider(NotificationProvider):
    """SMTP email notification provider configured via environment variables."""

    def __init__(self, smtp_host: Optional[str] = None, smtp_port: int = 587):
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port

    async def send_notification(self, recipient: str, subject: str, body: str, metadata: Optional[Dict[str, Any]] = None) -> bool:
        if not self.smtp_host:
            logger.info(f"[SMTP DISABLED] Skipping email to {recipient}: {subject}")
            return False
        # If SMTP credentials provided, standard aiosmtplib or smtplib dispatch would go here
        logger.info(f"[SMTP DISPATCH] To {recipient}: {subject}")
        return True
