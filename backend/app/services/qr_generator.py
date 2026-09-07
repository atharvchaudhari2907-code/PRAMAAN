import io
import logging
import os
import qrcode
import qrcode.image.svg

logger = logging.getLogger(__name__)


class QRGenerator:

    @staticmethod
    def get_public_verification_url(public_id: str) -> str:
        """Constructs the canonical public verification URL."""
        base_url = os.getenv("FRONTEND_URL", "http://localhost:5173").rstrip("/")
        return f"{base_url}/verify/{public_id}"

    @staticmethod
    def generate_qr_svg(url: str) -> str:
        """Generates a clean SVG string representing the QR code."""
        factory = qrcode.image.svg.SvgImage
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=10,
            border=2,
            image_factory=factory,
        )
        qr.add_data(url)
        qr.make(fit=True)
        img = qr.make_image()
        svg_bytes = img.to_string()
        if isinstance(svg_bytes, bytes):
            return svg_bytes.decode("utf-8")
        return str(svg_bytes)
