"""Shared Gemini client pool with automatic key rotation on 429 rate limit errors."""

from google import genai
from google.genai import types

from backend.config import GEMINI_API_KEYS, GEMINI_MODEL

_clients: list[genai.Client] = [genai.Client(api_key=k) for k in GEMINI_API_KEYS if k]


def _is_rate_limit(exc: Exception) -> bool:
    msg = str(exc).lower()
    return "429" in msg or "quota" in msg or "resource_exhausted" in msg


async def generate_content(
    *,
    contents: str,
    config: types.GenerateContentConfig | None = None,
    model: str = GEMINI_MODEL,
):
    """Call generate_content, rotating to the next key on 429."""
    last_exc: Exception | None = None
    for client in _clients:
        try:
            return await client.aio.models.generate_content(
                model=model, contents=contents, config=config
            )
        except Exception as e:
            if _is_rate_limit(e):
                last_exc = e
                continue
            raise
    raise last_exc or RuntimeError("No Gemini API keys available.")


async def generate_content_stream(
    *,
    contents: str,
    config: types.GenerateContentConfig | None = None,
    model: str = GEMINI_MODEL,
):
    """Call generate_content_stream, rotating to the next key on 429."""
    last_exc: Exception | None = None
    for client in _clients:
        try:
            return await client.aio.models.generate_content_stream(
                model=model, contents=contents, config=config
            )
        except Exception as e:
            if _is_rate_limit(e):
                last_exc = e
                continue
            raise
    raise last_exc or RuntimeError("No Gemini API keys available.")
