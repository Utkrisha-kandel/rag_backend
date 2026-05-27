import asyncio
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from app.core.redis_client import ChatMemoryClient, get_memory
from app.services.rag import evaluate_rag
from app.core.config import settings

async def main():
    memory = await get_memory()

    # fetch all logged eval samples from Redis
    evaluation_data = await memory.get_all_eval_samples()

    if not evaluation_data:
        print("No evaluation data found. Chat with the bot first to collect data.")
        return

    results = await evaluate_rag(
        evaluation_data=evaluation_data,
        groq_api_key=settings.GROQ_API_KEY
    )
    print(results)
    

asyncio.run(main())