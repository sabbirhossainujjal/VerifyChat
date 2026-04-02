import os

from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY: str = os.environ.get("GEMINI_API_KEY", "")
GEMINI_API_KEY_2: str = os.environ.get("GEMINI_API_KEY_2", "")
GEMINI_API_KEYS: list[str] = [k for k in [GEMINI_API_KEY, GEMINI_API_KEY_2] if k]
SERPER_API_KEY: str = os.environ.get("SERPER_API_KEY", "")
DATABASE_URL: str = os.environ.get("DATABASE_URL", "postgresql://localhost/verifychat")

GEMINI_MODEL: str = "gemini-2.5-flash-lite"

_raw_origins: str = os.environ.get("ALLOWED_ORIGINS", "")
ALLOWED_ORIGINS: list[str] = (
    [o.strip() for o in _raw_origins.split(",") if o.strip()]
    if _raw_origins.strip()
    else ["*"]
)
