from contextlib import asynccontextmanager
from typing import AsyncGenerator

import asyncpg

from backend.config import DATABASE_URL

_pool: asyncpg.Pool | None = None

_CREATE_SESSIONS = """
CREATE TABLE IF NOT EXISTS sessions (
    id TEXT PRIMARY KEY,
    participant_id TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    topic TEXT
);
"""

_CREATE_MESSAGES = """
CREATE TABLE IF NOT EXISTS messages (
    id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL REFERENCES sessions(id),
    role TEXT NOT NULL CHECK(role IN ('user', 'assistant')),
    content TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
"""

_CREATE_CLAIMS = """
CREATE TABLE IF NOT EXISTS claims (
    id TEXT PRIMARY KEY,
    message_id TEXT NOT NULL REFERENCES messages(id),
    session_id TEXT NOT NULL REFERENCES sessions(id),
    claim_text TEXT NOT NULL,
    original_sentence TEXT,
    is_checkworthy BOOLEAN DEFAULT TRUE,
    search_queries TEXT,
    source_url TEXT,
    source_title TEXT,
    source_snippet TEXT,
    verdict TEXT CHECK(verdict IN ('supported', 'unsupported', 'insufficient_evidence')),
    confidence REAL,
    explanation TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
"""

_CREATE_PREDICTIONS = """
CREATE TABLE IF NOT EXISTS predictions (
    id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL REFERENCES sessions(id),
    message_id TEXT NOT NULL REFERENCES messages(id),
    claim_id TEXT NOT NULL REFERENCES claims(id),
    predicted_inaccurate BOOLEAN NOT NULL,
    prediction_label TEXT CHECK(prediction_label IN ('accurate', 'neutral', 'false')),
    reasoning TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
"""

_CREATE_PREDICTION_SCORES = """
CREATE TABLE IF NOT EXISTS prediction_scores (
    id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL REFERENCES sessions(id),
    message_id TEXT NOT NULL REFERENCES messages(id),
    precision REAL,
    recall REAL,
    f1 REAL,
    correct_predictions INTEGER,
    total_flagged_by_student INTEGER,
    total_unsupported_by_system INTEGER,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
"""

_CREATE_INTERACTION_EVENTS = """
CREATE TABLE IF NOT EXISTS interaction_events (
    id BIGSERIAL PRIMARY KEY,
    session_id TEXT NOT NULL REFERENCES sessions(id),
    event_type TEXT NOT NULL,
    event_data TEXT,
    timestamp TIMESTAMPTZ DEFAULT NOW()
);
"""

_CREATE_SESSION_MODE_EVENTS = """
CREATE TABLE IF NOT EXISTS session_mode_events (
    id          TEXT PRIMARY KEY,
    session_id  TEXT NOT NULL REFERENCES sessions(id),
    mode        TEXT NOT NULL CHECK (mode IN ('standard', 'verifychat')),
    switched_at TIMESTAMPTZ DEFAULT NOW()
);
"""

_CREATE_HALLUCINATED_FACTS = """
CREATE TABLE IF NOT EXISTS hallucinated_facts (
    id           TEXT PRIMARY KEY,
    session_id   TEXT NOT NULL,
    message_id   TEXT NOT NULL,
    fact_index   SMALLINT NOT NULL CHECK (fact_index IN (0, 1)),
    injected     TEXT NOT NULL,
    correct      TEXT NOT NULL,
    created_at   TIMESTAMPTZ DEFAULT NOW()
);
"""

_CREATE_HALLUCINATION_GUESSES = """
CREATE TABLE IF NOT EXISTS hallucination_guesses (
    id           TEXT PRIMARY KEY,
    session_id   TEXT NOT NULL,
    message_id   TEXT NOT NULL UNIQUE,
    guess_text   TEXT NOT NULL,
    eval_result  JSONB,
    submitted_at TIMESTAMPTZ DEFAULT NOW()
);
"""


async def init_db() -> None:
    """Create the connection pool and all tables if they do not exist."""
    global _pool
    _pool = await asyncpg.create_pool(DATABASE_URL, min_size=1, max_size=10)
    async with _pool.acquire() as conn:
        await conn.execute(_CREATE_SESSIONS)
        await conn.execute(_CREATE_MESSAGES)
        await conn.execute(_CREATE_CLAIMS)
        await conn.execute(_CREATE_PREDICTIONS)
        await conn.execute(_CREATE_PREDICTION_SCORES)
        await conn.execute(_CREATE_INTERACTION_EVENTS)
        await conn.execute(_CREATE_SESSION_MODE_EVENTS)
        await conn.execute(_CREATE_HALLUCINATED_FACTS)
        await conn.execute(_CREATE_HALLUCINATION_GUESSES)
        await conn.execute(
            "ALTER TABLE sessions ADD COLUMN IF NOT EXISTS mode TEXT NOT NULL DEFAULT 'standard'"
        )


async def close_db() -> None:
    """Close the connection pool."""
    if _pool:
        await _pool.close()


@asynccontextmanager
async def get_db() -> AsyncGenerator[asyncpg.Connection, None]:
    """Yield an asyncpg connection from the pool."""
    async with _pool.acquire() as conn:
        yield conn
