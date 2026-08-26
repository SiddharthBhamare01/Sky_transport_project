import os

from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "").strip()
EXTRACTION_MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
MAX_UPLOAD_BYTES = 10 * 1024 * 1024  # 10 MB

SUPABASE_JWT_SECRET = os.environ.get("SUPABASE_JWT_SECRET", "").strip()
GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID", "").strip()
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET", "").strip()
GMAIL_REFRESH_TOKEN = os.environ.get("GMAIL_REFRESH_TOKEN", "").strip()
GMAIL_SENDER_EMAIL = os.environ.get("GMAIL_SENDER_EMAIL", "").strip()


def has_api_key() -> bool:
    return bool(OPENAI_API_KEY)
