import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class PaymentProvider(ABC):

    @abstractmethod
    async def create_payment_order(self, amount: float, currency: str, application_id: str) -> Dict[str, Any]:
        pass

    @abstractmethod
    async def verify_payment(self, payment_id: str, order_id: str, signature: str) -> bool:
        pass


class DisabledPaymentProvider(PaymentProvider):
    """
    Standard provider when production gateway credentials (Razorpay / PayU) are not configured.
    Strictly avoids mock/fake transactions and reports gateway disabled state transparently.
    """

    async def create_payment_order(self, amount: float, currency: str, application_id: str) -> Dict[str, Any]:
        logger.info(f"Payment requested for application {application_id}, but payment gateway credentials are not configured.")
        return {
            "status": "DISABLED",
            "message": "Direct statutory payment via Manakonline portal required. Gateway credentials are not configured.",
            "amount": amount,
            "currency": currency,
            "application_id": application_id,
            "gateway_configured": False,
        }

    async def verify_payment(self, payment_id: str, order_id: str, signature: str) -> bool:
        logger.warning("Attempted to verify payment on disabled payment provider.")
        return False
