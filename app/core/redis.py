# backend/app/core/redis.py
import redis.asyncio as redis
from app.core.config import settings

# Initialize a global Redis connection pool
redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)

async def get_redis():
    return redis_client