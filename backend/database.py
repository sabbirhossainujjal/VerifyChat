from contextlib import asynccontextmanager
from typing import AsyncGenerator

import aiosqlite

from backend.config import DATABASE_URL

_CREATE_SESSIONS = """
CREATE TABLE IF NOT EXISTS sessions (
    id TEXT PRIMARY KEY,
    participant_id TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    topic TEXT
);
"""

_CREATE_MESSAGES = """
CREATE TABLE IF NOT EXISTS messages (
    id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL REFERENCES sessions(id),
    role TEXT NOT NULL CHECK(role IN ('user', 'assistant')),
    content TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
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
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
"""

_CREATE_PREDICTIONS = """
CREATE TABLE IF NOT EXISTS predictions (
    id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL REFERENCES sessions(id),
    message_id TEXT NOT NULL REFERENCES messages(id),
    claim_id TEXT NOT NULL REFERENCES claims(id),
    predicted_inaccurate BOOLEAN NOT NULL,
    reasoning TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
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
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
"""

_CREATE_INTERACTION_EVENTS = """
CREATE TABLE IF NOT EXISTS interaction_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL REFERENCES sessions(id),
    event_type TEXT NOT NULL,
    event_data TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
);
"""


async def init_db() -> None:
    """Create all tables if they do not exist."""
    async with aiosqlite.connect(DATABASE_URL) as db:
        await db.execute(_CREATE_SESSIONS)
        await db.execute(_CREATE_MESSAGES)
        await db.execute(_CREATE_CLAIMS)
        await db.execute(_CREATE_PREDICTIONS)
        await db.execute(_CREATE_PREDICTION_SCORES)
        await db.execute(_CREATE_INTERACTION_EVENTS)
        await db.commit()


@asynccontextmanager
async def get_db() -> AsyncGenerator[aiosqlite.Connection, None]:
    """Yield an aiosqlite connection."""
    async with aiosqlite.connect(DATABASE_URL) as db:
        db.row_factory = aiosqlite.Row
        yield db
