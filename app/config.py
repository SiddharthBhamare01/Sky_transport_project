import os

from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "").strip()
EXTRACTION_MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
MAX_UPLOAD_BYTES = 10 * 1024 * 1024  # 10 MB


def has_api_key() -> bool:
    return bool(OPENAI_API_KEY)
