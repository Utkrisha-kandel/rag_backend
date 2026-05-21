# RAG Backend

A production-ready Retrieval-Augmented Generation (RAG) backend built with FastAPI. Supports document ingestion, semantic search, multi-turn conversational querying, and automated interview booking detection.


---

## Features

- Upload `.pdf` or `.txt` files and extract text automatically
- Two selectable chunking strategies — fixed-size and sentence-based
- Generate embeddings and store in Qdrant vector database
- Custom RAG pipeline (no LangChain RetrievalQAChain)
- Multi-turn conversation with Redis-backed chat memory
- LLM-powered interview booking detection — extracts name, email, date, and time from natural conversation and stores it in PostgreSQL
- Full metadata tracking per document

---

## Stack

| Layer | Technology |
|---|---|
| Framework | FastAPI |
| LLM | Groq (LLaMA 3.3 70B) |
| Embeddings | Sentence Transformers (all-MiniLM-L6-v2) |
| Vector Store | Qdrant |
| Chat Memory | Redis |
| Database | PostgreSQL (via SQLAlchemy async) |
| Server | Uvicorn |

---

## API Endpoints

### `POST /ingest/`
Upload a document and ingest it into the vector store.

**Form data:**
- `file` — `.pdf` or `.txt` file
- `strategy` — `fixed` or `sentence`

**Response:**
```json
{
  "document_id": "uuid",
  "filename": "document.pdf",
  "chunk_strategy": "fixed",
  "chunk_count": 12,
  "created_at": "2026-05-21T10:00:00"
}
```

### `POST /chat/`
Send a message and get a RAG-powered response.

**Request body:**
```json
{
  "session_id": "your-session-id",
  "message": "What is this document about?",
  "document_id": "uuid"
}
```

**Response:**
```json
{
  "session_id": "your-session-id",
  "answer": "This document is about...",
  "sources": [...],
  "booking": null
}
```

### `DELETE /chat/{session_id}/history`
Clear chat history for a session.


## Project Structure

```
rag_backend/
├── app/
│   ├── api/
│   │   ├── chat.py         # Chat endpoint
│   │   └── ingest.py       # Ingestion endpoint
│   ├── core/
│   │   ├── config.py       # Settings and env vars
│   │   ├── database.py     # PostgreSQL async session
│   │   ├── redis_client.py # Redis connection
│   │   └── vector_store.py # Qdrant operations
│   ├── models/
│   │   └── models.py       # SQLAlchemy models
│   ├── schemas/
│   │   └── schemas.py      # Pydantic schemas
│   ├── services/
│   │   ├── booking.py      # LLM booking detection
│   │   ├── chunker.py      # Fixed + sentence chunking
│   │   ├── embedder.py     # Embedding generation
│   │   ├── extractor.py    # PDF/TXT text extraction
│   │   ├── ingestion.py    # Ingestion pipeline
│   │   └── rag.py          # RAG query pipeline
│   └── main.py
├── .env.example
├── requirements.txt
└── README.md
```

---

## Setup

### 1. Clone the repo

```bash
git clone https://github.com/Utkrisha-kandel/rag-backend.git
cd rag-backend
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Start required services (Docker)

```bash
# Qdrant
docker run -p 6333:6333 qdrant/qdrant

# Redis
docker run -p 6379:6379 redis:7-alpine
```

### 4. Configure environment

Copy `.env.example` to `.env` and fill in:

```
GROQ_API_KEY="your_groq_api_key"
DATABASE_URL="postgresql+asyncpg://postgres:password@localhost:5432/ragdb"
QDRANT_URL="http://localhost:6333"
QDRANT_API_KEY=""
REDIS_URL="redis://localhost:6379"
```

### 5. Run the server

```bash
uvicorn app.main:app --reload
```

API docs available at `http://localhost:8000/docs`

---

## Design Decisions

- **No RetrievalQAChain** — RAG pipeline is fully custom, giving control over retrieval, prompt construction, and response generation
- **No FAISS/Chroma** — Qdrant used for production-grade vector storage with filtering support
- **Async throughout** — FastAPI, SQLAlchemy, and Qdrant client all use async/await for non-blocking I/O
- **Booking via LLM** — instead of a separate form, the LLM detects booking intent and extracts structured data from natural conversation

---

*Built by [Utkrisha Kandel](https://github.com/Utkrisha-kandel)*
