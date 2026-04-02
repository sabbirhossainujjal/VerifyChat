"""Session management routes."""

import uuid

from fastapi import APIRouter, HTTPException

from backend.database import get_db
from backend.models import SessionCreateRequest, SessionCreateResponse

router = APIRouter()

_SERIALIZE = {
    k: (v.isoformat() if hasattr(v, "isoformat") else v)
    for k, v in {}.items()
}


def _row_to_dict(row) -> dict:
    """Convert an asyncpg Record to a JSON-serializable dict."""
    return {k: (v.isoformat() if hasattr(v, "isoformat") else v) for k, v in dict(row).items()}


@router.post("/sessions", response_model=SessionCreateResponse)
async def create_session(request: SessionCreateRequest) -> SessionCreateResponse:
    """Create a new study session and return its ID."""
    session_id = uuid.uuid4().hex[:12]

    async with get_db() as conn:
        await conn.execute(
            "INSERT INTO sessions (id, participant_id) VALUES ($1, $2)",
            session_id, request.participant_id,
        )

    return SessionCreateResponse(session_id=session_id)


@router.get("/sessions/{session_id}")
async def get_session(session_id: str) -> dict:
    """Return session metadata, messages, claims, and predictions."""
    async with get_db() as conn:
        session_row = await conn.fetchrow(
            "SELECT * FROM sessions WHERE id = $1", session_id
        )

        if not session_row:
            raise HTTPException(status_code=404, detail="Session not found.")

        message_rows = await conn.fetch(
            "SELECT * FROM messages WHERE session_id = $1 ORDER BY created_at",
            session_id,
        )
        claim_rows = await conn.fetch(
            "SELECT * FROM claims WHERE session_id = $1 ORDER BY created_at",
            session_id,
        )
        prediction_rows = await conn.fetch(
            "SELECT * FROM predictions WHERE session_id = $1 ORDER BY created_at",
            session_id,
        )

    return {
        "session": _row_to_dict(session_row),
        "messages": [_row_to_dict(r) for r in message_rows],
        "claims": [_row_to_dict(r) for r in claim_rows],
        "predictions": [_row_to_dict(r) for r in prediction_rows],
    }


@router.get("/sessions/{session_id}/metrics")
async def get_session_metrics(session_id: str) -> dict:
    """Return aggregated prediction scores for a session."""
    async with get_db() as conn:
        score_rows = await conn.fetch(
            "SELECT * FROM prediction_scores WHERE session_id = $1 ORDER BY created_at",
            session_id,
        )

    scores = [_row_to_dict(r) for r in score_rows]

    if not scores:
        return {"session_id": session_id, "scores": [], "aggregate": None}

    avg_precision = sum(s["precision"] or 0 for s in scores) / len(scores)
    avg_recall = sum(s["recall"] or 0 for s in scores) / len(scores)
    avg_f1 = sum(s["f1"] or 0 for s in scores) / len(scores)

    return {
        "session_id": session_id,
        "scores": scores,
        "aggregate": {
            "avg_precision": avg_precision,
            "avg_recall": avg_recall,
            "avg_f1": avg_f1,
            "num_interactions": len(scores),
        },
    }
