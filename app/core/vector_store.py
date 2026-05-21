from qdrant_client import AsyncQdrantClient
from typing import AsyncGenerator

from qdrant_client.models import (
    Distance,
    VectorParams,
    PointStruct,
    Filter,
    FieldCondition,
    MatchValue,
)

from app.core.config import settings

_qdrant_client: AsyncQdrantClient | None = None


async def get_qdrant() -> AsyncQdrantClient:
    global _qdrant_client
    if _qdrant_client is None:
        _qdrant_client = AsyncQdrantClient(
            url=settings.QDRANT_URL,
            api_key=settings.QDRANT_API_KEY or None,
        )
        try:
            await _ensure_collection(_qdrant_client)
        except Exception as e:
            _qdrant_client = None
            raise e
    return _qdrant_client

async def close_qdrant() -> None:
    global _qdrant_client
    if _qdrant_client:
        await _qdrant_client.close()
        _qdrant_client = None


async def _ensure_collection(client: AsyncQdrantClient) -> None:
    existing = await client.get_collections()
    names = [c.name for c in existing.collections]
    if settings.QDRANT_COLLECTION not in names:
        await client.create_collection(
            collection_name=settings.QDRANT_COLLECTION,
            vectors_config=VectorParams(
                size=settings.EMBEDDING_DIM,
                distance=Distance.COSINE,
            ),
        )


async def upsert_vectors(
    client: AsyncQdrantClient,
    points: list[PointStruct],
) -> None:
    await client.upsert(
        collection_name=settings.QDRANT_COLLECTION,
        points=points,
        wait=True,
    )


async def similarity_search(
    client: AsyncQdrantClient,
    query_vector: list[float],
    top_k: int = 5,
    document_id: str | None = None,
) -> list[dict]:
    search_filter: Filter | None = None
    if document_id:
        search_filter = Filter(
            must=[
                FieldCondition(
                    key="document_id",
                    match=MatchValue(value=document_id),
                )
            ]
        )
    results = await client.query_points(
        collection_name=settings.QDRANT_COLLECTION,
        query=query_vector,
        limit=top_k,
        query_filter=search_filter,
        with_payload=True,
        )
    return [
    {
        "score": r.score,
        "text": r.payload.get("text", ""),
        "chunk_index": r.payload.get("chunk_index"),
        "document_id": r.payload.get("document_id"),
        "filename": r.payload.get("filename"),
    }
    for r in results.points
]
async def get_qdrant_dep() -> AsyncGenerator[AsyncQdrantClient, None]:
        client = await get_qdrant()
        yield client