import json
from typing import Any

import redis.asyncio as aioredis

from app.core.config import settings

_redis_client: aioredis.Redis | None = None


async def get_redis() -> aioredis.Redis:
    global _redis_client
    if _redis_client is None:
        _redis_client = aioredis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
        )
    return _redis_client


async def close_redis() -> None:
    global _redis_client
    if _redis_client:
        await _redis_client.aclose()
        _redis_client = None


class ChatMemoryClient:
    def __init__(self, redis: aioredis.Redis) -> None:
        self._redis = redis

    def _key(self, session_id: str) -> str:
        return f"chat:history:{session_id}"

    def _eval_key(self, session_id: str) -> str:      # <-- ADD THIS
        return f"eval:{session_id}"

    async def get_history(self, session_id: str) -> list[dict[str, Any]]:
        raw = await self._redis.get(self._key(session_id))
        if not raw:
            return []
        return json.loads(raw)

    async def append_message(self, session_id: str, role: str, content: str) -> None:
        history = await self.get_history(session_id)
        history.append({"role": role, "content": content})
        await self._redis.setex(
            self._key(session_id),
            settings.CHAT_HISTORY_TTL,
            json.dumps(history),
        )

    async def clear_history(self, session_id: str) -> None:
        await self._redis.delete(self._key(session_id))
    async def append_eval_sample(self, session_id: str, sample: dict) -> None:
        await self._redis.rpush(self._eval_key(session_id), json.dumps(sample))

    async def get_all_eval_samples(self) -> list[dict]:
        keys = await self._redis.keys("eval:*")
        samples = []
        for key in keys:
            data = await self._redis.lrange(key, 0, -1)
            for item in data:
                samples.append(json.loads(item))
        return samples


async def get_memory() -> ChatMemoryClient:
    redis = await get_redis()
    return ChatMemoryClient(redis)