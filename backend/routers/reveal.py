"""POST /api/reveal — return verdicts and compute accuracy metrics."""

import uuid

from fastapi import APIRouter, HTTPException

from backend.database import get_db
from backend.models import (
    AccuracyMetrics,
    RevealRequest,
    RevealResponse,
    VerdictResult,
)

router = APIRouter()


@router.post("/reveal", response_model=RevealResponse)
async def reveal(request: RevealRequest) -> RevealResponse:
    """Load saved verdicts, compute prediction accuracy, persist scores."""
    async with get_db() as conn:
        # Load all claims for this message (verdicts were stored during /verify)
        claim_rows = await conn.fetch(
            """
            SELECT id, claim_text, verdict, confidence, explanation,
                   source_url, source_title, source_snippet
            FROM claims
            WHERE message_id = $1 AND session_id = $2
            """,
            request.message_id, request.session_id,
        )

        if not claim_rows:
            raise HTTPException(
                status_code=404,
                detail="No claims found for this message.",
            )

        # Load student predictions for this message
        prediction_rows = await conn.fetch(
            """
            SELECT claim_id, predicted_inaccurate, prediction_label
            FROM predictions
            WHERE message_id = $1 AND session_id = $2
            """,
            request.message_id, request.session_id,
        )

    # Build lookups
    student_predictions: dict[str, bool] = {
        row["claim_id"]: bool(row["predicted_inaccurate"])
        for row in prediction_rows
    }
    student_labels: dict[str, str] = {
        row["claim_id"]: (row["prediction_label"] or ("false" if row["predicted_inaccurate"] else "neutral"))
        for row in prediction_rows
    }

    # Precision/recall/F1 — detection metric for catching unsupported claims.
    # Only claims with a definitive verdict (supported/unsupported) are eligible;
    # insufficient_evidence claims are excluded so they don't skew precision.
    eligible_ids: set[str] = {
        row["id"] for row in claim_rows
        if row["verdict"] in ("supported", "unsupported")
    }
    system_flagged: set[str] = {
        row["id"] for row in claim_rows
        if row["verdict"] == "unsupported"
    }
    student_flagged: set[str] = {
        row["claim_id"] for row in prediction_rows
        if row["prediction_label"] == "false" and row["claim_id"] in eligible_ids
    }
    true_positives = len(system_flagged & student_flagged)

    precision = true_positives / len(student_flagged) if student_flagged else 0.0
    recall = true_positives / len(system_flagged) if system_flagged else 0.0
    f1 = (
        (2 * precision * recall / (precision + recall))
        if (precision + recall) > 0
        else 0.0
    )

    # Overall correct: student matched verdict (excluding neutral predictions and insufficient_evidence)
    correct_predictions = sum(
        1 for row in claim_rows
        if row["verdict"] != "insufficient_evidence"
        and student_labels.get(row["id"], "neutral") != "neutral"
        and (
            (student_labels[row["id"]] == "accurate" and row["verdict"] == "supported")
            or (student_labels[row["id"]] == "false" and row["verdict"] == "unsupported")
        )
    )

    accuracy = AccuracyMetrics(
        precision=precision,
        recall=recall,
        f1=f1,
        correct_predictions=correct_predictions,
        total_flagged_by_student=len(student_flagged),
        total_unsupported_by_system=len(system_flagged),
    )

    # Build verdict results
    verdicts: list[VerdictResult] = []
    for row in claim_rows:
        sources = []
        if row["source_url"]:
            sources.append({
                "url": row["source_url"],
                "title": row["source_title"] or "",
                "snippet": row["source_snippet"] or "",
            })

        verdicts.append(
            VerdictResult(
                claim_id=row["id"],
                claim_text=row["claim_text"],
                verdict=row["verdict"] or "insufficient_evidence",
                confidence=row["confidence"],
                explanation=row["explanation"],
                sources=sources,
                student_predicted_inaccurate=student_predictions.get(row["id"], False),
            )
        )

    # Persist prediction score
    score_id = uuid.uuid4().hex[:12]
    async with get_db() as conn:
        await conn.execute(
            """
            INSERT INTO prediction_scores (
                id, session_id, message_id,
                precision, recall, f1,
                correct_predictions,
                total_flagged_by_student,
                total_unsupported_by_system
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            """,
            score_id,
            request.session_id,
            request.message_id,
            accuracy.precision,
            accuracy.recall,
            accuracy.f1,
            accuracy.correct_predictions,
            accuracy.total_flagged_by_student,
            accuracy.total_unsupported_by_system,
        )

    return RevealResponse(verdicts=verdicts, accuracy=accuracy)
