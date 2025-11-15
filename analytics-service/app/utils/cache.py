import json
from typing import Optional
from app.utils.database import get_redis_client

async def get_cached(key: str) -> Optional[dict]:
    """Get cached value"""
    redis_client = await get_redis_client()
    value = await redis_client.get(key)
    if value:
        return json.loads(value)
    return None

async def set_cache(key: str, value: dict, ttl: int = 3600):
    """Set cached value with TTL"""
    redis_client = await get_redis_client()
    await redis_client.setex(key, ttl, json.dumps(value))

