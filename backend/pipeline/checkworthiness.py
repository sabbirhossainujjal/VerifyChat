"""Stage 2: Filter to 4–7 most checkworthy claims."""

import json
import re

from google.genai import types

from backend import gemini

_SYSTEM_PROMPT = (
    "You are a fact-checking editor deciding which claims deserve investigation.\n\n"
    "Given a numbered list of claims, select the 4–7 most checkworthy ones. "
    "Prefer claims that are:\n"
    "- Specific (exact dates, numbers, named entities)\n"
    "- Potentially incorrect or surprising\n"
    "- Independently verifiable via web search\n"
    "- Impactful if wrong\n\n"
    "Return ONLY a JSON array of zero-based indices (integers) — no other text:\n"
    "[0, 2, 5]\n\n"
    "IMPORTANT: Always return between 4 and 7 indices. Never fewer than 4, never more than 7."
)


def _strip_fences(text: str) -> str:
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    return text.strip()


async def filter_checkworthy(claims: list[dict]) -> list[dict]:
    """Return the 4–7 most checkworthy claims from *claims*.

    Falls back to the first min(5, len(claims)) if the LLM call fails.
    """
    if not claims:
        return []

    numbered = "\n".join(f"{i}. {c['claim']}" for i, c in enumerate(claims))

    try:
        response = await gemini.generate_content(
            contents=f"Claims:\n{numbered}",
            config=types.GenerateContentConfig(
                system_instruction=_SYSTEM_PROMPT,
            ),
        )
        raw = _strip_fences(response.text)
        indices: list[int] = json.loads(raw)

        valid_indices = [
            i for i in indices
            if isinstance(i, int) and 0 <= i < len(claims)
        ]

        # Pad up to 5 if LLM returned fewer than 4
        if len(valid_indices) < 4:
            used = set(valid_indices)
            for j in range(len(claims)):
                if j not in used:
                    valid_indices.append(j)
                if len(valid_indices) >= 5:
                    break

        # Cap at 7
        valid_indices = valid_indices[:7]
        return [claims[i] for i in valid_indices]

    except Exception:
        return claims[: min(5, len(claims))]
