"""POST /api/predict — save student predictions."""

import uuid

from fastapi import APIRouter, HTTPException

from backend.database import get_db
from backend.models import PredictRequest, PredictResponse

router = APIRouter()


@router.post("/predict", response_model=PredictResponse)
async def predict(request: PredictRequest) -> PredictResponse:
    """Persist each student prediction and return a shared prediction_id."""
    if not request.predictions:
        raise HTTPException(status_code=400, detail="No predictions provided.")

    prediction_id = uuid.uuid4().hex[:12]

    async with get_db() as conn:
        async with conn.transaction():
            for item in request.predictions:
                row_id = uuid.uuid4().hex[:12]
                await conn.execute(
                    """
                    INSERT INTO predictions (
                        id, session_id, message_id, claim_id,
                        predicted_inaccurate, prediction_label, reasoning
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7)
                    """,
                    row_id,
                    request.session_id,
                    request.message_id,
                    item.claim_id,
                    item.predicted_inaccurate,
                    item.prediction_label,
                    item.reasoning,
                )

    return PredictResponse(success=True, prediction_id=prediction_id)
