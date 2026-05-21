import uuid

from qdrant_client import AsyncQdrantClient
from qdrant_client.models import PointStruct
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.vector_store import upsert_vectors
from app.models.models import Document
from app.schemas.schemas import IngestResponse
from app.services.chunker import ChunkStrategy, chunk_text
from app.services.embedder import embed_texts
from app.services.extractor import extract_text


async def ingest_document(
    *,
    filename: str,
    file_bytes: bytes,
    strategy: ChunkStrategy,
    db: AsyncSession,
    qdrant: AsyncQdrantClient,
) -> IngestResponse:
    """
    Full ingestion pipeline for a single document.

    Returns metadata about the ingested document.
    """
    # 1. Extract text
    raw_text = extract_text(filename, file_bytes)
    if not raw_text.strip():
        raise ValueError("Document appears to be empty or contains no extractable text.")

    # 2. Chunk
    chunks = chunk_text(raw_text, strategy=strategy)
    if not chunks:
        raise ValueError("Chunking produced no output. Check the document content.")

    # 3. Embed
    vectors = await embed_texts(chunks)

    # 4. Assign a document ID
    document_id = str(uuid.uuid4())
    file_type = "pdf" if filename.lower().endswith(".pdf") else "txt"

    # 5. Build Qdrant points
    points: list[PointStruct] = [
        PointStruct(
            id=str(uuid.uuid4()),
            vector=vector,
            payload={
                "document_id": document_id,
                "filename": filename,
                "chunk_index": idx,
                "text": chunk,
            },
        )
        for idx, (chunk, vector) in enumerate(zip(chunks, vectors))
    ]

    # 6. Upsert into Qdrant
    await upsert_vectors(qdrant, points)

    # 7.metadata in PostgreSQL
    doc = Document(
        id=document_id,
        filename=filename,
        file_type=file_type,
        chunk_strategy=strategy,
        chunk_count=len(chunks),
    )
    db.add(doc)
    await db.flush()

    return IngestResponse.model_validate(doc)
