import os
from enum import Enum
from pathlib import Path

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parent.parent

load_dotenv(PROJECT_ROOT / ".env")

DATA_DIR = PROJECT_ROOT / "data"
UPLOAD_DIR = DATA_DIR / "uploads"
DB_PATH = DATA_DIR / "civic.db"

LM_STUDIO_URL = os.getenv(
    "LM_STUDIO_URL",
    "http://localhost:1234/v1/chat/completions",
)

LM_STUDIO_MODEL = os.getenv(
    "LM_STUDIO_MODEL",
    "qwen/qwen3-vl-4b",
)

MAX_UPLOAD_SIZE_MB = int(os.getenv("MAX_UPLOAD_SIZE_MB", "10"))
MAX_UPLOAD_SIZE_BYTES = MAX_UPLOAD_SIZE_MB * 1024 * 1024

ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}

ALLOWED_IMAGE_MIME_TYPES = {
    "image/jpeg",
    "image/png",
    "image/webp",
}


class AnalysisStatus(str, Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"


# ============================================================
# Notification configuration (backend only — never exposed to frontend)
# ============================================================

def _env_list(name: str) -> list[str]:
    raw = os.getenv(name, "").strip()
    if not raw:
        return []
    return [item.strip() for item in raw.split(",") if item.strip()]


DEMO_NOTIFICATION_EMAIL_1 = os.getenv("DEMO_NOTIFICATION_EMAIL_1", "").strip() or None
DEMO_NOTIFICATION_EMAIL_2 = os.getenv("DEMO_NOTIFICATION_EMAIL_2", "").strip() or None
DEMO_NOTIFICATION_EMAIL_3 = os.getenv("DEMO_NOTIFICATION_EMAIL_3", "").strip() or None

SMTP_HOST = os.getenv("SMTP_HOST", "").strip() or None
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USERNAME = os.getenv("SMTP_USERNAME", "").strip() or None
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "").strip() or None
SMTP_FROM_EMAIL = (
    os.getenv("SMTP_FROM_EMAIL", "").strip()
    or SMTP_USERNAME
)

NOTIFICATION_ENABLED = os.getenv("NOTIFICATION_ENABLED", "true").lower() != "false"

# Demo notifications are only sent when AI confidence strictly exceeds this
# fraction (0.5 == 50%). Configurable so the threshold can be tuned.
NOTIFICATION_MIN_CONFIDENCE = float(os.getenv("NOTIFICATION_MIN_CONFIDENCE", "0.5"))

APP_BASE_URL = os.getenv("APP_BASE_URL", "http://localhost:5173").rstrip("/")


def demo_recipients() -> list[str]:
    recipients: list[str] = []
    for email in (
        DEMO_NOTIFICATION_EMAIL_1,
        DEMO_NOTIFICATION_EMAIL_2,
        DEMO_NOTIFICATION_EMAIL_3,
    ):
        if email and email not in recipients:
            recipients.append(email)
    return recipients