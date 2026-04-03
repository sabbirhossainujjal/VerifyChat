"""POST /api/guess — Save hallucination guess and evaluate with Gemini."""

import json
import uuid

from fastapi import APIRouter
from google.genai import types

from backend import gemini
from backend.database import get_db
from backend.models import GuessRequest, GuessResponse

router = APIRouter()

_EVAL_SYSTEM = (
    "You are evaluating whether a student detected specific hallucinations in an AI response.\n\n"
    "You will receive:\n"
    "1. The student's free-text guess about what was wrong\n"
    "2. The list of actual injected hallucinations (fact_index, injected text, correct text)\n\n"
    "For each hallucination, determine if the student's guess semantically captures it "
    "(partial credit OK — they don't need exact wording, just the right idea).\n\n"
    "Return ONLY JSON — no other text:\n"
    '{"facts": [{"index": 0, "detected": true, "score": 0.85}, {"index": 1, "detected": false, "score": 0.1}], "detected_count": 1}'
)


async def _evaluate_guess(guess_text: str, hallucinations: list[dict]) -> dict:
    """Use Gemini to semantically score the student's guess against ground truth."""
    prompt = (
        f"Student's guess:\n{guess_text}\n\n"
        f"Actual hallucinations:\n{json.dumps(hallucinations, indent=2)}"
    )
    try:
        response = await gemini.generate_content(
            contents=prompt,
            config=types.GenerateContentConfig(system_instruction=_EVAL_SYSTEM),
        )
        raw = response.text.strip()
        # strip markdown fences if present
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        return json.loads(raw.strip())
    except Exception:
        return {"facts": [], "detected_count": 0, "error": "eval_failed"}


@router.post("/guess", response_model=GuessResponse)
async def submit_guess(request: GuessRequest) -> GuessResponse:
    guess_id = uuid.uuid4().hex[:12]

    # Load ground truth hallucinations for this message
    async with get_db() as conn:
        rows = await conn.fetch(
            "SELECT fact_index, injected, correct FROM hallucinated_facts WHERE message_id = $1 AND session_id = $2 ORDER BY fact_index",
            request.message_id, request.session_id,
        )

    hallucinations = [
        {"index": r["fact_index"], "injected": r["injected"], "correct": r["correct"]}
        for r in rows
    ]

    # Evaluate guess (None if no ground truth — e.g. greeting message)
    eval_result = None
    if hallucinations:
        eval_result = await _evaluate_guess(request.guess_text, hallucinations)

    async with get_db() as conn:
        await conn.execute(
            """INSERT INTO hallucination_guesses (id, session_id, message_id, guess_text, eval_result)
               VALUES ($1, $2, $3, $4, $5)""",
            guess_id, request.session_id, request.message_id, request.guess_text,
            json.dumps(eval_result) if eval_result else None,
        )

    return GuessResponse(success=True)
