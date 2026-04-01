"""Stage 3: Generate 1–2 search queries per claim (batched, single API call)."""

import json
import re

from google import genai
from google.genai import types

from backend.config import GEMINI_API_KEY, GEMINI_MODEL

_client = genai.Client(api_key=GEMINI_API_KEY)

_SYSTEM_PROMPT = (
    "You are a search query specialist.\n\n"
    "Given a numbered list of factual claims, produce 1–2 concise web search queries "
    "for each claim that would surface evidence confirming or refuting it. "
    "Queries should be specific, using key names, dates, and numbers from the claim.\n\n"
    "Return ONLY a JSON object mapping each index (as a string) to its queries — no other text:\n"
    '{"0": ["query one", "query two"], "1": ["query three"], ...}'
)


def _strip_fences(text: str) -> str:
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    return text.strip()


async def generate_queries(claims: list[dict]) -> list[dict]:
    """Generate search queries for all *claims* in a single API call.

    Returns a new list of dicts each with a ``search_queries`` key.
    Falls back to the claim text as the query for any missing index.
    """
    if not claims:
        return []

    numbered = "\n".join(f"{i}. {c['claim']}" for i, c in enumerate(claims))

    try:
        response = await _client.aio.models.generate_content(
            model=GEMINI_MODEL,
            contents=f"Claims:\n{numbered}",
            config=types.GenerateContentConfig(
                system_instruction=_SYSTEM_PROMPT,
            ),
        )
        raw = _strip_fences(response.text)
        parsed: dict[str, list[str]] = json.loads(raw)
    except Exception:
        parsed = {}

    enriched: list[dict] = []
    for i, claim in enumerate(claims):
        queries = parsed.get(str(i), [])
        if not queries:
            queries = [claim["claim"]]
        enriched.append({**claim, "search_queries": queries})

    return enriched
