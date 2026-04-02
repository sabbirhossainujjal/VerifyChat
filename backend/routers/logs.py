"""POST /api/log — persist interaction events."""

import json

from fastapi import APIRouter

from backend.database import get_db
from backend.models import LogRequest

router = APIRouter()


@router.post("/log")
async def log_event(request: LogRequest) -> dict:
    """Save an interaction event. Never raises — silent failure on error."""
    try:
        async with get_db() as conn:
            await conn.execute(
                """
                INSERT INTO interaction_events (session_id, event_type, event_data)
                VALUES ($1, $2, $3)
                """,
                request.session_id,
                request.event_type,
                json.dumps(request.event_data),
            )
    except Exception:
        # Logging must never break UX
        pass

    return {"success": True}
