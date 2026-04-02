"""GET /api/admin/export — full data dump for manual backup."""

import datetime

from fastapi import APIRouter

from backend.database import get_db

router = APIRouter()


def _row_to_dict(row) -> dict:
    """Convert an asyncpg Record to a JSON-serializable dict."""
    return {k: (v.isoformat() if hasattr(v, "isoformat") else v) for k, v in dict(row).items()}


@router.get("/admin/export")
async def export_all() -> dict:
    """Return all session data as a JSON snapshot. Use before/after study sessions."""
    async with get_db() as conn:
        sessions = await conn.fetch("SELECT * FROM sessions ORDER BY created_at")
        messages = await conn.fetch("SELECT * FROM messages ORDER BY created_at")
        claims = await conn.fetch("SELECT * FROM claims ORDER BY created_at")
        predictions = await conn.fetch("SELECT * FROM predictions ORDER BY created_at")
        scores = await conn.fetch("SELECT * FROM prediction_scores ORDER BY created_at")
        events = await conn.fetch("SELECT * FROM interaction_events ORDER BY timestamp")

    return {
        "exported_at": datetime.datetime.utcnow().isoformat() + "Z",
        "sessions": [_row_to_dict(r) for r in sessions],
        "messages": [_row_to_dict(r) for r in messages],
        "claims": [_row_to_dict(r) for r in claims],
        "predictions": [_row_to_dict(r) for r in predictions],
        "prediction_scores": [_row_to_dict(r) for r in scores],
        "interaction_events": [_row_to_dict(r) for r in events],
    }
