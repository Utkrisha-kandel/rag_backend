from sentence_transformers import SentenceTransformer
from app.core.config import settings

_model: SentenceTransformer | None = None

def get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        _model = SentenceTransformer(settings.EMBEDDING_MODEL)
    return _model

async def embed_texts(texts: list[str], batch_size: int = 100) -> list[list[float]]:
    model = get_model()
    embeddings = model.encode(texts, batch_size=batch_size, convert_to_numpy=True)
    return embeddings.tolist()

async def embed_query(text: str) -> list[float]:
    embeddings = await embed_texts([text])
    return embeddings[0]