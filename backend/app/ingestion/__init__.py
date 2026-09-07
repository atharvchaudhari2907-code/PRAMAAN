import sys
from pathlib import Path

# Ensure backend directory is in sys.path when imported as backend.app...
_backend_dir = Path(__file__).resolve().parent.parent.parent
if str(_backend_dir) not in sys.path:
    sys.path.insert(0, str(_backend_dir))

try:
    from app.ingestion.ingest import StandardPdfIngester
except ModuleNotFoundError:
    from backend.app.ingestion.ingest import StandardPdfIngester

__all__ = ["StandardPdfIngester"]
