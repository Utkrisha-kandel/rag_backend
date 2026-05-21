
import re
from typing import Literal

from app.core.config import settings

ChunkStrategy = Literal["fixed", "sentence"]


# ── Fixed-size chunking ────────────────────────────────────────────────────────

def _split_fixed(
    text: str,
    chunk_size: int = settings.FIXED_CHUNK_SIZE,
    overlap: int = settings.FIXED_CHUNK_OVERLAP,
) -> list[str]:
    
    if chunk_size <= 0:
        raise ValueError("chunk_size must be positive")
    if overlap >= chunk_size:
        raise ValueError("overlap must be smaller than chunk_size")

    chunks: list[str] = []
    start = 0
    text_len = len(text)

    while start < text_len:
        end = min(start + chunk_size, text_len)
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end == text_len:
            break
        start += chunk_size - overlap

    return chunks


# ── Sentence-window chunking ───────────────────────────────────────────────────

_SENTENCE_RE = re.compile(r"(?<=[.!?])\s+")


def _split_sentences(text: str) -> list[str]:
    
    raw = _SENTENCE_RE.split(text.strip())
    return [s.strip() for s in raw if s.strip()]


def _split_sentence_windows(
    text: str,
    window_size: int = settings.SENTENCE_CHUNK_SIZE,
) -> list[str]:
    sentences = _split_sentences(text)
    if not sentences:
        return []

    chunks: list[str] = []
    overlap = max(1, window_size // 2)

    start = 0
    while start < len(sentences):
        end = min(start + window_size, len(sentences))
        chunk = " ".join(sentences[start:end]).strip()
        if chunk:
            chunks.append(chunk)
        if end == len(sentences):
            break
        start += window_size - overlap

    return chunks


# ── Public interface ───────────────────────────────────────────────────────────

def chunk_text(
    text: str,
    strategy: ChunkStrategy = settings.DEFAULT_CHUNK_STRATEGY,
    chunk_size: int = settings.FIXED_CHUNK_SIZE,
    overlap: int = settings.FIXED_CHUNK_OVERLAP,
    sentence_window: int = settings.SENTENCE_CHUNK_SIZE,
) -> list[str]:
   
    if strategy == "fixed":
        return _split_fixed(text, chunk_size=chunk_size, overlap=overlap)
    if strategy == "sentence":
        return _split_sentence_windows(text, window_size=sentence_window)
    raise ValueError(f"Unknown chunking strategy: {strategy!r}")
