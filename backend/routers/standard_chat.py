"""POST /api/chat/standard — Standard Chat SSE stream with hallucination injection."""

import json
import re
import uuid
from typing import AsyncGenerator

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from google.genai import types

from backend import gemini
from backend.database import get_db
from backend.models import StandardChatRequest

router = APIRouter()

_META_RE = re.compile(r'<META>\s*(.*?)\s*</META>', re.DOTALL)

_SYSTEM_INSTRUCTION = (
    "You are a knowledgeable academic assistant helping students learn.\n\n"
    "For TASK or FACTUAL questions: Answer concisely in 3–5 short paragraphs. "
    "You MUST include exactly 2 subtle factual errors — one wrong date or number, "
    "and one wrong name or place. These errors must sound completely plausible and "
    "blend naturally with correct information. Do not signal or mark the errors.\n\n"
    "For GREETINGS or CASUAL conversation: Respond naturally and briefly. No errors.\n\n"
    "ALWAYS end your output with a metadata block in exactly this format:\n"
    "<META>\n"
    '{"is_task": true, "hallucinations": [{"injected": "the false text as it appears in your answer", "correct": "what it should actually be"}, {"injected": "...", "correct": "..."}]}\n'
    "</META>\n\n"
    "For greetings use:\n"
    "<META>\n"
    '{"is_task": false, "hallucinations": []}\n'
    "</META>"
)


def _strip_meta(text: str) -> tuple[str, dict]:
    """Strip <META>...</META> from text. Returns (clean_text, meta_dict)."""
    match = _META_RE.search(text)
    meta = {"is_task": False, "hallucinations": []}
    if match:
        try:
            meta = json.loads(match.group(1))
        except Exception:
            pass
        text = _META_RE.sub("", text).strip()
    return text, meta


async def _stream_standard_chat(session_id: str, user_message: str) -> AsyncGenerator[str, None]:
    message_id = uuid.uuid4().hex[:12]

    async with get_db() as conn:
        await conn.execute(
            "INSERT INTO messages (id, session_id, role, content) VALUES ($1, $2, $3, $4)",
            uuid.uuid4().hex[:12], session_id, "user", user_message,
        )

    full_parts: list[str] = []

    try:
        stream = await gemini.generate_content_stream(
            contents=user_message,
            config=types.GenerateContentConfig(system_instruction=_SYSTEM_INSTRUCTION),
        )
        async for chunk in stream:
            token: str = chunk.text if chunk.text else ""
            if token:
                full_parts.append(token)
                payload = json.dumps({"token": token, "done": False})
                yield f"data: {payload}\n\n"
    except Exception as exc:
        yield f"data: {json.dumps({'token': '', 'done': True, 'error': str(exc)})}\n\n"
        return

    full_raw = "".join(full_parts)
    clean_response, meta = _strip_meta(full_raw)

    # Persist assistant message (clean, no META)
    async with get_db() as conn:
        await conn.execute(
            "INSERT INTO messages (id, session_id, role, content) VALUES ($1, $2, $3, $4)",
            message_id, session_id, "assistant", clean_response,
        )

    # Persist hallucinated facts if this was a task query
    if meta.get("is_task") and meta.get("hallucinations"):
        hallucinations = meta["hallucinations"][:2]  # cap at 2
        async with get_db() as conn:
            for i, h in enumerate(hallucinations):
                await conn.execute(
                    """INSERT INTO hallucinated_facts (id, session_id, message_id, fact_index, injected, correct)
                       VALUES ($1, $2, $3, $4, $5, $6)""",
                    uuid.uuid4().hex[:12], session_id, message_id, i,
                    h.get("injected", ""), h.get("correct", ""),
                )

    yield f"data: {json.dumps({'token': '', 'done': True, 'message_id': message_id, 'full_response': clean_response})}\n\n"


@router.post("/chat/standard")
async def standard_chat(request: StandardChatRequest) -> StreamingResponse:
    return StreamingResponse(
        _stream_standard_chat(request.session_id, request.message),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
