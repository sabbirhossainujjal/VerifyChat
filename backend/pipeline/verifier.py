"""Stage 5: Verify each claim against retrieved evidence."""

import asyncio
import json
import re

from google import genai
from google.genai import types

from backend.config import GEMINI_API_KEY, GEMINI_MODEL

_client = genai.Client(api_key=GEMINI_API_KEY)

_SYSTEM_PROMPT = (
    "You are an expert fact-checker.\n\n"
    "Given a factual claim and web evidence, determine whether the claim is supported.\n\n"
    "Respond ONLY with a JSON object — no other text:\n"
    "{\n"
    '  "verdict": "supported" | "unsupported" | "insufficient_evidence",\n'
    '  "confidence": <float 0.0–1.0>,\n'
    '  "explanation": "<1–2 sentence explanation citing specific evidence>",\n'
    '  "key_evidence": "<most relevant quote or fact from the evidence>"\n'
    "}\n\n"
    'Rules:\n'
    '- "supported": evidence clearly confirms the claim\n'
    '- "unsupported": evidence clearly contradicts the claim\n'
    '- "insufficient_evidence": evidence is absent, ambiguous, or too weak to decide'
)

_FALLBACK = {
    "verdict": "insufficient_evidence",
    "confidence": 0.0,
    "explanation": "Verification could not be completed.",
    "key_evidence": "",
}


def _strip_fences(text: str) -> str:
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    return text.strip()


async def _verify_one_claim(claim: dict) -> dict:
    """Verify a single *claim* dict against its attached sources."""
    sources: list[dict] = claim.get("sources", [])
    evidence_text = (
        "\n\n".join(
            f"Source {i + 1}: {s.get('title', '')}\n{s.get('snippet', '')}\nURL: {s.get('url', '')}"
            for i, s in enumerate(sources)
        )
        if sources
        else "No evidence retrieved."
    )

    prompt = f"Claim: {claim['claim']}\n\nEvidence:\n{evidence_text}"

    try:
        response = await _client.aio.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=_SYSTEM_PROMPT,
            ),
        )
        raw = _strip_fences(response.text)
        parsed = json.loads(raw)

        verdict = parsed.get("verdict", "insufficient_evidence")
        if verdict not in ("supported", "unsupported", "insufficient_evidence"):
            verdict = "insufficient_evidence"

        return {
            **claim,
            "verdict": verdict,
            "confidence": float(parsed.get("confidence", 0.5)),
            "explanation": parsed.get("explanation", ""),
            "key_evidence": parsed.get("key_evidence", ""),
        }
    except Exception:
        return {**claim, **_FALLBACK}


async def verify_claims(claims: list[dict]) -> list[dict]:
    """Verify all *claims* in parallel.

    Returns the enriched list. Failed verifications receive
    ``insufficient_evidence`` so the pipeline continues.
    """
    if not claims:
        return []

    results = await asyncio.gather(
        *[_verify_one_claim(c) for c in claims],
        return_exceptions=True,
    )

    verified: list[dict] = []
    for original, result in zip(claims, results):
        if isinstance(result, Exception):
            verified.append({**original, **_FALLBACK})
        else:
            verified.append(result)
    return verified
