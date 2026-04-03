"""POST /api/session/mode — Switch session mode and log the event."""

import uuid

from fastapi import APIRouter, HTTPException

from backend.database import get_db
from backend.models import SessionModeRequest, SessionModeResponse

router = APIRouter()

VALID_MODES = {"standard", "verifychat"}


@router.post("/session/mode", response_model=SessionModeResponse)
async def set_session_mode(request: SessionModeRequest) -> SessionModeResponse:
    if request.mode not in VALID_MODES:
        raise HTTPException(status_code=400, detail=f"mode must be one of {VALID_MODES}")

    async with get_db() as conn:
        await conn.execute(
            "UPDATE sessions SET mode = $1 WHERE id = $2",
            request.mode, request.session_id,
        )
        await conn.execute(
            "INSERT INTO session_mode_events (id, session_id, mode) VALUES ($1, $2, $3)",
            uuid.uuid4().hex[:12], request.session_id, request.mode,
        )

    return SessionModeResponse(success=True)
