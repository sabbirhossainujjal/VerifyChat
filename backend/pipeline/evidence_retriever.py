"""Stage 4: Retrieve web evidence via the Serper API."""

import asyncio
from typing import Any

import aiohttp

from backend.config import SERPER_API_KEY

_SERPER_URL = "https://google.serper.dev/search"


async def _search_one(session: aiohttp.ClientSession, query: str) -> list[dict[str, Any]]:
    """Run a single Serper search and return up to 3 organic results."""
    headers = {
        "X-API-KEY": SERPER_API_KEY,
        "Content-Type": "application/json",
    }
    payload = {"q": query, "num": 5}

    try:
        async with session.post(_SERPER_URL, json=payload, headers=headers) as resp:
            if resp.status != 200:
                return []
            data = await resp.json()
            organic = data.get("organic", [])
            results = []
            for item in organic[:3]:
                results.append({
                    "title": item.get("title", ""),
                    "snippet": item.get("snippet", ""),
                    "url": item.get("link", ""),
                })
            return results
    except Exception:
        return []


async def _retrieve_evidence_for_claim(
    session: aiohttp.ClientSession,
    claim: dict,
) -> dict:
    """Retrieve evidence for one *claim* and attach a ``sources`` key."""
    queries: list[str] = claim.get("search_queries", [claim["claim"]])

    # Run all queries for this claim concurrently
    query_results = await asyncio.gather(
        *[_search_one(session, q) for q in queries],
        return_exceptions=True,
    )

    # Flatten results, deduplicate by URL, keep top 3
    seen_urls: set[str] = set()
    sources: list[dict] = []
    for batch in query_results:
        if isinstance(batch, Exception):
            continue
        for item in batch:
            url = item.get("url", "")
            if url and url not in seen_urls:
                seen_urls.add(url)
                sources.append(item)
            if len(sources) >= 3:
                break
        if len(sources) >= 3:
            break

    return {**claim, "sources": sources}


async def retrieve_evidence(claims: list[dict]) -> list[dict]:
    """Retrieve evidence for all *claims* in parallel.

    Returns a new list of dicts each with a ``sources`` key.
    """
    if not claims:
        return []

    async with aiohttp.ClientSession() as session:
        results = await asyncio.gather(
            *[_retrieve_evidence_for_claim(session, c) for c in claims],
            return_exceptions=True,
        )

    enriched: list[dict] = []
    for original, result in zip(claims, results):
        if isinstance(result, Exception):
            enriched.append({**original, "sources": []})
        else:
            enriched.append(result)
    return enriched
