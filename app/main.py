from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import chat, ingest
from app.core.config import settings
from app.core.database import Base, engine
from app.core.redis_client import close_redis
from app.core.vector_store import close_qdrant


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    # Startup: create DB tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield  # App is running

    # Shutdown: clean up connection pools
    await close_redis()
    await close_qdrant()
    await engine.dispose()


app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    description=(
        "RAG backend with document ingestion, conversational retrieval, "
        "Redis-backed chat memory, and interview booking support."
    ),
    lifespan=lifespan,
)

# CORS — tighten origins in production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(ingest.router)
app.include_router(chat.router)


