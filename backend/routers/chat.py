"""POST /api/chat — stream an AI response via SSE."""

import json
import uuid
from typing import AsyncGenerator

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from google.genai import types

from backend import gemini
from backend.database import get_db
from backend.models import ChatRequest

router = APIRouter()

_SYSTEM_INSTRUCTION = (
    "You are a knowledgeable academic assistant. "
    "Answer the student's question thoroughly and factually. "
    "Include specific facts, dates, numbers, and names where relevant. "
    "Do not hedge excessively or add disclaimers about being an AI."
)


async def _stream_chat(session_id: str, user_message: str) -> AsyncGenerator[str, None]:
    """Stream Gemini tokens as SSE chunks and persist messages to DB."""
    message_id = uuid.uuid4().hex[:12]

    # Persist user message
    async with get_db() as conn:
        await conn.execute(
            "INSERT INTO messages (id, session_id, role, content) VALUES ($1, $2, $3, $4)",
            uuid.uuid4().hex[:12], session_id, "user", user_message,
        )

    full_response_parts: list[str] = []

    try:
        response_stream = await gemini.generate_content_stream(
            contents=user_message,
            config=types.GenerateContentConfig(
                system_instruction=_SYSTEM_INSTRUCTION,
            ),
        )
        async for chunk in response_stream:
            token: str = chunk.text if chunk.text else ""
            if token:
                full_response_parts.append(token)
                payload = json.dumps({"token": token, "done": False})
                yield f"data: {payload}\n\n"
    except Exception as exc:
        error_payload = json.dumps({"token": "", "done": True, "error": str(exc)})
        yield f"data: {error_payload}\n\n"
        return

    full_response = "".join(full_response_parts)

    # Persist assistant message
    async with get_db() as conn:
        await conn.execute(
            "INSERT INTO messages (id, session_id, role, content) VALUES ($1, $2, $3, $4)",
            message_id, session_id, "assistant", full_response,
        )

    final_payload = json.dumps({
        "token": "",
        "done": True,
        "message_id": message_id,
        "full_response": full_response,
    })
    yield f"data: {final_payload}\n\n"


@router.post("/chat")
async def chat(request: ChatRequest) -> StreamingResponse:
    """Stream an AI response for a user message in *session_id*."""
    return StreamingResponse(
        _stream_chat(request.session_id, request.message),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
