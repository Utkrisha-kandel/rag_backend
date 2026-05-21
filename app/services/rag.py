"""
Custom RAG pipeline (no RetrievalQAChain):
  1. Retrieve relevant chunks from Qdrant
  2. Build a prompt with context + full conversation history
  3. Call the LLM for an answer
  4. Persist the turn to Redis
  5. Optionally detect and save interview bookings
"""

from typing import Any

from groq import AsyncGroq

from qdrant_client import AsyncQdrantClient
from sqlalchemy.ext.asyncio import AsyncSession
from groq import AsyncGroq
from app.services.embedder import embed_query

from app.core.config import settings
from app.core.redis_client import ChatMemoryClient
from app.core.vector_store import similarity_search
from app.schemas.schemas import BookingResponse, ChatResponse, SourceChunk
from app.services.booking import detect_and_save_booking
from app.services.embedder import embed_query

_RAG_SYSTEM_PROMPT = """\
You are a knowledgeable assistant. Answer the user's question using ONLY the
provided context passages. If the context does not contain enough information
to answer the question, say so honestly — do not fabricate information.

When the user asks to book or schedule an interview, acknowledge that you will
process their booking request and confirm the details back to them.

Context:
{context}
"""


async def run_rag_query(
    *,
    session_id: str,
    user_message: str,
    document_id: str | None,
    qdrant: AsyncQdrantClient,
    memory: ChatMemoryClient,
    db: AsyncSession,
) -> ChatResponse:
    """
    Execute a full RAG turn and return a structured response.
    """

    client = AsyncGroq(api_key=settings.GROQ_API_KEY)

    # 1. Check for booking intent first (before RAG)
    booking_result: BookingResponse | None = None
    clarification: str | None = None

    booking_result, clarification = await detect_and_save_booking(
        session_id=session_id,
        user_message=user_message,
        db=db,
    )

    # 2. Embed the user query
    query_vector = await embed_query(user_message)

    # 3. Retrieve top-K chunks from Qdrant
    raw_results = await similarity_search(
        qdrant,
        query_vector=query_vector,
        top_k=settings.TOP_K_RESULTS,
        document_id=document_id,
    )

    sources: list[SourceChunk] = [
        SourceChunk(
            document_id=r["document_id"],
            filename=r["filename"],
            chunk_index=r["chunk_index"],
            score=r["score"],
            text=r["text"],
        )
        for r in raw_results
    ]

    # 4. Build context string
    context_parts = [
        f"[{i+1}] (from '{r['filename']}', chunk {r['chunk_index']})\n{r['text']}"
        for i, r in enumerate(raw_results)
    ]
    context = "\n\n".join(context_parts) if context_parts else "No relevant context found."

    # 5. Retrieve chat history from Redis
    history: list[dict[str, Any]] = await memory.get_history(session_id)

    # 6. Compose messages for the LLM
    system_msg = {"role": "system", "content": _RAG_SYSTEM_PROMPT.format(context=context)}

    # If there's a clarification needed for booking, inject it
    effective_user_message = user_message
    if clarification:
        effective_user_message = user_message  # answer query AND clarify

    messages = [system_msg, *history, {"role": "user", "content": effective_user_message}]

    # 7. Call the LLM
    response = await client.chat.completions.create(
        model=settings.GROQ_CHAT_MODEL,
        messages=messages,
        temperature=0.3,
        max_tokens=1024,
    )
    answer = response.choices[0].message.content or ""

    # Append clarification if booking fields are missing
    if clarification:
        answer = f"{answer}\n\n{clarification}" if answer else clarification

    # If booking was saved, append confirmation
    if booking_result:
        confirmation = (
            f"\n\n **Interview booking confirmed!**\n"
            f"- Name: {booking_result.name}\n"
            f"- Email: {booking_result.email}\n"
            f"- Date: {booking_result.interview_date}\n"
            f"- Time: {booking_result.interview_time}"
        )
        answer += confirmation

    # 8. Persist turn to Redis
    await memory.append_message(session_id, "user", effective_user_message)
    await memory.append_message(session_id, "assistant", answer)

    return ChatResponse(
        session_id=session_id,
        answer=answer,
        sources=sources,
        booking=booking_result,
    )
