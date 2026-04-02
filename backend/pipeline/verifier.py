"""Stage 5: Verify all claims against retrieved evidence (batched, single API call)."""

import json
import re

from google.genai import types

from backend import gemini

_SYSTEM_PROMPT = (
    "You are an expert fact-checker.\n\n"
    "You will receive a numbered list of factual claims, each with web evidence. "
    "For each claim, determine whether it is supported by the evidence.\n\n"
    "Return ONLY a JSON array (one object per claim, in the same order) — no other text:\n"
    "[\n"
    "  {\n"
    '    "verdict": "supported" | "unsupported" | "insufficient_evidence",\n'
    '    "confidence": <float 0.0–1.0>,\n'
    '    "explanation": "<1–2 sentence explanation citing specific evidence>",\n'
    '    "key_evidence": "<most relevant quote or fact from the evidence>"\n'
    "  },\n"
    "  ...\n"
    "]\n\n"
    "Rules:\n"
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


def _build_prompt(claims: list[dict]) -> str:
    parts: list[str] = []
    for i, claim in enumerate(claims):
        sources: list[dict] = claim.get("sources", [])
        if sources:
            evidence = "\n".join(
                f"  Source {j + 1}: {s.get('title', '')}\n  {s.get('snippet', '')}\n  URL: {s.get('url', '')}"
                for j, s in enumerate(sources)
            )
        else:
            evidence = "  No evidence retrieved."
        parts.append(f"Claim {i}:\n{claim['claim']}\nEvidence:\n{evidence}")
    return "\n\n---\n\n".join(parts)


async def verify_claims(claims: list[dict]) -> list[dict]:
    """Verify all *claims* in a single API call.

    Returns the enriched list. Failed verifications receive
    ``insufficient_evidence`` so the pipeline continues.
    """
    if not claims:
        return []

    prompt = _build_prompt(claims)

    try:
        response = await gemini.generate_content(
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=_SYSTEM_PROMPT,
            ),
        )
        raw = _strip_fences(response.text)
        results: list[dict] = json.loads(raw)
    except Exception:
        results = []

    verified: list[dict] = []
    for i, claim in enumerate(claims):
        if i < len(results) and isinstance(results[i], dict):
            r = results[i]
            verdict = r.get("verdict", "insufficient_evidence")
            if verdict not in ("supported", "unsupported", "insufficient_evidence"):
                verdict = "insufficient_evidence"
            verified.append({
                **claim,
                "verdict": verdict,
                "confidence": float(r.get("confidence", 0.5)),
                "explanation": r.get("explanation", ""),
                "key_evidence": r.get("key_evidence", ""),
            })
        else:
            verified.append({**claim, **_FALLBACK})

    return verified
