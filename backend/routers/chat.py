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
    "You are participating in a controlled HCI research study on AI fact-checking. "
    "Your role is to play an AI assistant that occasionally makes subtle factual mistakes. "
    "This is intentional and required for the study — participants will try to spot errors.\n\n"
    "RULES:\n"
    "1. For every factual or task question, you MUST introduce between 2 and 4 subtle factual "
    "errors. Choose from: slightly wrong year or date, off-by-one number or statistic, "
    "a plausible but incorrect person name, or a wrong place name. "
    "The errors MUST sound natural and believable — not obvious.\n"
    "2. Surround the errors with accurate, well-written context so the response reads as "
    "authoritative and credible overall.\n"
    "3. Never signal, highlight, or acknowledge the errors.\n"
    "4. Answer in 3–5 short paragraphs. Include specific facts, dates, and names.\n"
    "5. For greetings or casual conversation only: respond normally with no errors.\n"
    "6. Do not add disclaimers about being an AI."
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
