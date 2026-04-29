"""POST /api/chat/standard — Standard Chat SSE stream with guaranteed hallucination injection."""

import json
import uuid
from typing import AsyncGenerator

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from google.genai import types

from backend import gemini
from backend.database import get_db
from backend.models import StandardChatRequest
from backend.pipeline.hallucination_injector import inject

router = APIRouter()

_SYSTEM_INSTRUCTION = (
    "You are a knowledgeable academic assistant helping students learn. "
    "Answer the student's question concisely and factually in 3–5 short paragraphs. "
    "Include key facts, dates, numbers, and names where relevant. "
    "For greetings or casual conversation, respond naturally and briefly. "
    "Do not add disclaimers about being an AI."
)

_GREETINGS = {"hi", "hello", "hey", "thanks", "thank you", "ok", "okay", "bye", "good morning", "good evening"}


def _is_greeting(message: str) -> bool:
    return message.strip().lower().rstrip("!.,?") in _GREETINGS


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
                yield f"data: {json.dumps({'token': token, 'done': False})}\n\n"
    except Exception as exc:
        yield f"data: {json.dumps({'token': '', 'done': True, 'error': str(exc)})}\n\n"
        return

    clean_response = "".join(full_parts)
    is_task = not _is_greeting(user_message)

    # Inject exactly 2 hallucinations for task queries
    final_response = clean_response
    hallucinations = []
    if is_task:
        result = await inject(clean_response)
        final_response = result["modified"]
        hallucinations = result["hallucinations"][:2]

    # Persist assistant message (hallucinated version)
    async with get_db() as conn:
        await conn.execute(
            "INSERT INTO messages (id, session_id, role, content) VALUES ($1, $2, $3, $4)",
            message_id, session_id, "assistant", final_response,
        )

    # Persist ground truth for analysis
    if hallucinations:
        async with get_db() as conn:
            for i, h in enumerate(hallucinations):
                await conn.execute(
                    """INSERT INTO hallucinated_facts
                       (id, session_id, message_id, fact_index, injected, correct)
                       VALUES ($1, $2, $3, $4, $5, $6)""",
                    uuid.uuid4().hex[:12], session_id, message_id, i,
                    h.get("injected", ""), h.get("correct", ""),
                )

    yield f"data: {json.dumps({'token': '', 'done': True, 'message_id': message_id, 'full_response': final_response})}\n\n"


@router.post("/chat/standard")
async def standard_chat(request: StandardChatRequest) -> StreamingResponse:
    return StreamingResponse(
        _stream_standard_chat(request.session_id, request.message),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
