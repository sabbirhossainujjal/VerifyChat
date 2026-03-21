"""Stage 1: Extract atomic factual claims from an AI response."""

import json
import re

from google import genai
from google.genai import types

from backend.config import GEMINI_API_KEY, GEMINI_MODEL

_client = genai.Client(api_key=GEMINI_API_KEY)

_SYSTEM_PROMPT = (
    "You are a precise claim extraction assistant.\n\n"
    "Given an AI assistant's response, extract every distinct atomic factual claim. "
    "Focus on claims that are verifiable: specific facts, dates, numbers, names, "
    "statistics, and cause-effect assertions. Ignore opinions and subjective statements.\n\n"
    "Target 8–15 raw claims. Return ONLY a JSON array with no additional text:\n"
    '[\n  {"claim": "concise factual claim", "original_sentence": "verbatim sentence it came from"},\n  ...\n]'
)


def _strip_fences(text: str) -> str:
    """Remove markdown code fences from an LLM response."""
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    return text.strip()


async def decompose_claims(ai_response: str) -> list[dict]:
    """Extract atomic factual claims from *ai_response*.

    Returns a list of dicts with keys ``claim`` and ``original_sentence``.
    Returns an empty list on failure.
    """
    prompt = f"AI response to analyse:\n{ai_response}"

    try:
        response = await _client.aio.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=_SYSTEM_PROMPT,
            ),
        )
        raw = _strip_fences(response.text)
        claims: list[dict] = json.loads(raw)
        valid = [c for c in claims if isinstance(c, dict) and "claim" in c]
        return valid
    except Exception:
        return []
