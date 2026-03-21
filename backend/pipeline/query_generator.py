"""Stage 3: Generate 1–2 search queries per claim."""

import asyncio
import json
import re

from google import genai
from google.genai import types

from backend.config import GEMINI_API_KEY, GEMINI_MODEL

_client = genai.Client(api_key=GEMINI_API_KEY)

_SYSTEM_PROMPT = (
    "You are a search query specialist.\n\n"
    "Given a factual claim, produce 1–2 concise web search queries that would surface "
    "evidence confirming or refuting that claim. Queries should be specific, using "
    "key names, dates, and numbers from the claim.\n\n"
    'Return ONLY a JSON object — no other text:\n{"queries": ["query one", "query two"]}'
)


def _strip_fences(text: str) -> str:
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    return text.strip()


async def _generate_queries_for_claim(claim: dict) -> dict:
    """Generate search queries for a single *claim* dict.

    Attaches a ``search_queries`` key and returns the enriched dict.
    Falls back to the claim text as the sole query on failure.
    """
    try:
        response = await _client.aio.models.generate_content(
            model=GEMINI_MODEL,
            contents=f"Claim: {claim['claim']}",
            config=types.GenerateContentConfig(
                system_instruction=_SYSTEM_PROMPT,
            ),
        )
        raw = _strip_fences(response.text)
        parsed = json.loads(raw)
        queries: list[str] = parsed.get("queries", [])
        if not queries:
            queries = [claim["claim"]]
    except Exception:
        queries = [claim["claim"]]

    return {**claim, "search_queries": queries}


async def generate_queries(claims: list[dict]) -> list[dict]:
    """Generate search queries for all *claims* in parallel.

    Returns a new list of dicts each with a ``search_queries`` key.
    """
    if not claims:
        return []

    results = await asyncio.gather(
        *[_generate_queries_for_claim(c) for c in claims],
        return_exceptions=True,
    )

    enriched: list[dict] = []
    for original, result in zip(claims, results):
        if isinstance(result, Exception):
            enriched.append({**original, "search_queries": [original["claim"]]})
        else:
            enriched.append(result)
    return enriched
