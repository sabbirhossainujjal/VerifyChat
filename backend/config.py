import os

from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY: str = os.environ.get("GEMINI_API_KEY", "")
SERPER_API_KEY: str = os.environ.get("SERPER_API_KEY", "")
DATABASE_URL: str = os.environ.get("DATABASE_URL", "verifychat.db")

GEMINI_MODEL: str = "gemini-2.0-flash"
