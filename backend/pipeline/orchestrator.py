"""Orchestrator: runs all 5 pipeline stages in order."""

import asyncio

from backend.pipeline.checkworthiness import filter_checkworthy
from backend.pipeline.decomposer import decompose_claims
from backend.pipeline.evidence_retriever import retrieve_evidence
from backend.pipeline.query_generator import generate_queries
from backend.pipeline.verifier import verify_claims


async def run_verification_pipeline(ai_response: str) -> list[dict]:
    """Run the full 5-stage verification pipeline on *ai_response*.

    Stage 1 — Decompose: extract 8-15 raw atomic claims.
    Stage 2 — Checkworthiness: filter to 4-7 most checkworthy.
    Stage 3 — Query generation: produce search queries per claim.
    Stage 4 — Evidence retrieval: fetch web sources per claim.
    Stage 5 — Verification: produce verdict per claim.

    Error resilience: a failure in any single claim is caught and
    that claim is skipped. Returns an empty list only if all claims fail.
    """
    # Stage 1
    raw_claims = await decompose_claims(ai_response)
    if not raw_claims:
        return []

    # Stage 2
    checkworthy = await filter_checkworthy(raw_claims)
    if not checkworthy:
        return []

    # Stage 3
    with_queries = await generate_queries(checkworthy)

    # Stage 4
    with_evidence = await retrieve_evidence(with_queries)

    # Stage 5
    verified = await verify_claims(with_evidence)

    return verified
