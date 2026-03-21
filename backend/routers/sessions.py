"""Session management routes."""

import uuid

from fastapi import APIRouter, HTTPException

from backend.database import get_db
from backend.models import SessionCreateRequest, SessionCreateResponse

router = APIRouter()


@router.post("/sessions", response_model=SessionCreateResponse)
async def create_session(request: SessionCreateRequest) -> SessionCreateResponse:
    """Create a new study session and return its ID."""
    session_id = uuid.uuid4().hex[:12]

    async with get_db() as db:
        await db.execute(
            "INSERT INTO sessions (id, participant_id) VALUES (?, ?)",
            (session_id, request.participant_id),
        )
        await db.commit()

    return SessionCreateResponse(session_id=session_id)


@router.get("/sessions/{session_id}")
async def get_session(session_id: str) -> dict:
    """Return session metadata, messages, claims, and predictions."""
    async with get_db() as db:
        async with db.execute(
            "SELECT * FROM sessions WHERE id = ?", (session_id,)
        ) as cursor:
            session_row = await cursor.fetchone()

        if not session_row:
            raise HTTPException(status_code=404, detail="Session not found.")

        async with db.execute(
            "SELECT * FROM messages WHERE session_id = ? ORDER BY created_at",
            (session_id,),
        ) as cursor:
            message_rows = await cursor.fetchall()

        async with db.execute(
            "SELECT * FROM claims WHERE session_id = ? ORDER BY created_at",
            (session_id,),
        ) as cursor:
            claim_rows = await cursor.fetchall()

        async with db.execute(
            "SELECT * FROM predictions WHERE session_id = ? ORDER BY created_at",
            (session_id,),
        ) as cursor:
            prediction_rows = await cursor.fetchall()

    return {
        "session": dict(session_row),
        "messages": [dict(r) for r in message_rows],
        "claims": [dict(r) for r in claim_rows],
        "predictions": [dict(r) for r in prediction_rows],
    }


@router.get("/sessions/{session_id}/metrics")
async def get_session_metrics(session_id: str) -> dict:
    """Return aggregated prediction scores for a session."""
    async with get_db() as db:
        async with db.execute(
            "SELECT * FROM prediction_scores WHERE session_id = ? ORDER BY created_at",
            (session_id,),
        ) as cursor:
            score_rows = await cursor.fetchall()

    scores = [dict(r) for r in score_rows]

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
