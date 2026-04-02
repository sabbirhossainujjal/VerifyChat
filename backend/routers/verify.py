"""POST /api/verify — run the full pipeline, persist verdicts, return claims only."""

import json
import uuid

from fastapi import APIRouter, HTTPException

from backend.database import get_db
from backend.models import ClaimResult, VerifyRequest, VerifyResponse
from backend.pipeline.orchestrator import run_verification_pipeline

router = APIRouter()


@router.post("/verify", response_model=VerifyResponse)
async def verify(request: VerifyRequest) -> VerifyResponse:
    """Run the verification pipeline and store all results.

    Verdicts are saved to the DB but are NOT included in the response.
    Only claim text and source metadata are returned to the client.
    """
    try:
        pipeline_results = await run_verification_pipeline(request.ai_response)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Pipeline error: {exc}") from exc

    claim_results: list[ClaimResult] = []

    async with get_db() as conn:
        async with conn.transaction():
            for item in pipeline_results:
                claim_id = uuid.uuid4().hex[:12]

                sources: list[dict] = item.get("sources", [])
                top_source = sources[0] if sources else {}
                source_url = top_source.get("url")
                source_title = top_source.get("title")
                source_snippet = top_source.get("snippet")

                queries_json = json.dumps(item.get("search_queries", []))

                await conn.execute(
                    """
                    INSERT INTO claims (
                        id, message_id, session_id, claim_text, original_sentence,
                        is_checkworthy, search_queries,
                        source_url, source_title, source_snippet,
                        verdict, confidence, explanation
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
                    """,
                    claim_id,
                    request.message_id,
                    request.session_id,
                    item["claim"],
                    item.get("original_sentence", ""),
                    True,
                    queries_json,
                    source_url,
                    source_title,
                    source_snippet,
                    item.get("verdict", "insufficient_evidence"),
                    item.get("confidence", 0.0),
                    item.get("explanation", ""),
                )

                claim_results.append(
                    ClaimResult(
                        id=claim_id,
                        text=item["claim"],
                        source_url=source_url,
                        source_title=source_title,
                        source_snippet=source_snippet,
                    )
                )

    return VerifyResponse(claims=claim_results)
