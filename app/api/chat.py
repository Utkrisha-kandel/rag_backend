from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from qdrant_client import AsyncQdrantClient

from app.core.database import get_db
from app.core.redis_client import get_memory, ChatMemoryClient
from app.core.vector_store import get_qdrant_dep
from app.schemas.schemas import ChatRequest, ChatResponse, ClearHistoryResponse
from app.services.rag import run_rag_query

router = APIRouter(prefix="/chat", tags=["Chat"])

@router.post("/", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    db: AsyncSession = Depends(get_db),
    qdrant: AsyncQdrantClient = Depends(get_qdrant_dep),
    memory: ChatMemoryClient = Depends(get_memory),
):
    return await run_rag_query(
        session_id=request.session_id,
        user_message=request.message,
        document_id=request.document_id,
        qdrant=qdrant,
        memory=memory,
        db=db,
    )

@router.delete("/{session_id}/history", response_model=ClearHistoryResponse)
async def clear_history(
    session_id: str,
    memory: ChatMemoryClient = Depends(get_memory),
):
    await memory.clear_history(session_id)
    return ClearHistoryResponse(session_id=session_id, cleared=True)