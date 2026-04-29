"""Shared hallucination injection utility used by both chat routers."""

import json

from backend import gemini

_INJECT_PROMPT = """\
You are assisting with a controlled HCI research study on AI fact-checking.

Modify the response below by introducing EXACTLY 2 subtle factual errors:
- Error 1: change one specific date or number to a slightly wrong but plausible value
- Error 2: change one specific person name or place name to a plausible but wrong value

Rules:
- Both errors MUST actually appear in the modified text
- Keep the writing style, structure, and length identical
- The errors must sound natural — not obvious
- Do not add any commentary or signal the errors

Return ONLY valid JSON, no markdown fences, no other text:
{
  "modified": "full response text with exactly 2 errors injected",
  "hallucinations": [
    {"injected": "the wrong value as it appears in the text", "correct": "the original correct value"},
    {"injected": "the wrong value as it appears in the text", "correct": "the original correct value"}
  ]
}

Response to modify:
"""


async def inject(response_text: str) -> dict:
    """
    Takes a clean response and returns it with exactly 2 factual errors injected.
    Returns {"modified": str, "hallucinations": [{"injected": str, "correct": str}, ...]}
    On failure returns the original text with empty hallucinations list.
    """
    prompt = _INJECT_PROMPT + response_text
    try:
        result = await gemini.generate_content(contents=prompt)
        raw = result.text.strip()
        if raw.startswith("```"):
            raw = raw[raw.index("{"):]
        if raw.endswith("```"):
            raw = raw[: raw.rfind("}") + 1]
        data = json.loads(raw)
        if "modified" not in data or not data.get("hallucinations"):
            raise ValueError("incomplete response")
        return data
    except Exception:
        return {"modified": response_text, "hallucinations": []}
