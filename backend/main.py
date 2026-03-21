"""VerifyChat FastAPI application entry point."""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.database import init_db
from backend.routers import chat, logs, predict, reveal, sessions, verify


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Run DB initialisation on startup."""
    await init_db()
    yield


app = FastAPI(
    title="VerifyChat",
    description="Chat-integrated fact-checking API for HCI user study.",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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
