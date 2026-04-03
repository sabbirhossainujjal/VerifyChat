"""VerifyChat FastAPI application entry point."""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.config import ALLOWED_ORIGINS
from backend.database import close_db, init_db
from backend.routers import admin, chat, guess, logs, predict, reveal, session_mode, sessions, standard_chat, verify


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Run DB initialisation on startup and teardown on shutdown."""
    await init_db()
    yield
    await close_db()


app = FastAPI(
    title="VerifyChat",
    description="Chat-integrated fact-checking API for HCI user study.",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat.router, prefix="/api")
app.include_router(verify.router, prefix="/api")
app.include_router(predict.router, prefix="/api")
app.include_router(reveal.router, prefix="/api")
app.include_router(sessions.router, prefix="/api")
app.include_router(logs.router, prefix="/api")
app.include_router(admin.router, prefix="/api")
app.include_router(standard_chat.router, prefix="/api")
app.include_router(guess.router, prefix="/api")
app.include_router(session_mode.router, prefix="/api")
