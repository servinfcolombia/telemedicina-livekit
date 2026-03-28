from typing import Optional
import redis.asyncio as redis
from src.core.config import settings


class RedisClient:
    def __init__(self):
        self._client: Optional[redis.Redis] = None
    
    async def get_client(self) -> redis.Redis:
        if self._client is None:
            self._client = redis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True
            )
        return self._client
    
    async def close(self):
        if self._client:
            await self._client.close()
            self._client = None


redis_client = RedisClient()


async def get_redis() -> redis.Redis:
    return await redis_client.get_client()


class QueueNames:
    TRANSCRIPTION = "queue:transcription"
    FHIR_EXTRACTION = "queue:fhir_extraction"
    NOTIFICATIONS = "queue:notifications"


async def enqueue_task(queue: str, task_data: dict) -> str:
    client = await get_redis()
    import uuid
    task_id = str(uuid.uuid4())
    task_data["task_id"] = task_id
    await client.hset(f"task:{task_id}", mapping=task_data)
    await client.lpush(queue, task_id)
    return task_id


async def get_task_status(task_id: str) -> Optional[dict]:
    client = await get_redis()
    task_data = await client.hgetall(f"task:{task_id}")
    return task_data if task_data else None


async def update_task_status(task_id: str, status: str, **kwargs):
    client = await get_redis()
    updates = {"status": status, **kwargs}
    await client.hset(f"task:{task_id}", mapping=updates)


async def get_queue_length(queue: str) -> int:
    client = await get_redis()
    return await client.llen(queue)


async def dequeue_task(queue: str) -> Optional[str]:
    client = await get_redis()
    task_id = await client.brpop(queue, timeout=30)
    return task_id[1] if task_id else None
