from fastapi import APIRouter, Depends, File, Form, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from qdrant_client import AsyncQdrantClient

from app.core.database import get_db
from app.core.vector_store import get_qdrant_dep
from app.schemas.schemas import IngestResponse
from app.services.chunker import ChunkStrategy
from app.services.ingestion import ingest_document

router = APIRouter(prefix="/ingest", tags=["Ingestion"])

@router.post("/", response_model=IngestResponse)
async def ingest(
    file: UploadFile = File(...),
    strategy: ChunkStrategy = Form("fixed"),
    db: AsyncSession = Depends(get_db),
    qdrant: AsyncQdrantClient = Depends(get_qdrant_dep),
):
    file_bytes = await file.read()
    return await ingest_document(
        filename=file.filename,
        file_bytes=file_bytes,
        strategy=strategy,
        db=db,
        qdrant=qdrant,
    )