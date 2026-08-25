import os

from dotenv import load_dotenv

load_dotenv()

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "").strip()
EXTRACTION_MODEL = os.environ.get("EXTRACTION_MODEL", "claude-sonnet-5")
MAX_UPLOAD_BYTES = 10 * 1024 * 1024  # 10 MB


def has_api_key() -> bool:
    return bool(ANTHROPIC_API_KEY)
