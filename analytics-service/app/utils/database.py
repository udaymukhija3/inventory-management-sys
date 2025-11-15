import motor.motor_asyncio
import redis.asyncio as redis
import logging
from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

_mongo_client = None
_redis_client = None

async def init_mongodb():
    """Initialize MongoDB connection"""
    global _mongo_client
    try:
        _mongo_client = motor.motor_asyncio.AsyncIOMotorClient(settings.mongodb_url)
        # Test connection
        await _mongo_client.admin.command('ping')
        logger.info("MongoDB connection initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize MongoDB: {e}")
        raise

async def init_redis():
    """Initialize Redis connection"""
    global _redis_client
    try:
        _redis_client = await redis.from_url(settings.redis_url, decode_responses=True)
        # Test connection
        await _redis_client.ping()
        logger.info("Redis connection initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize Redis: {e}")
        raise

async def get_mongodb_client():
    """Get MongoDB client instance"""
    global _mongo_client
    if _mongo_client is None:
        await init_mongodb()
    return _mongo_client

async def get_redis_client():
    """Get Redis client instance"""
    global _redis_client
    if _redis_client is None:
        await init_redis()
    return _redis_client

async def close_connections():
    """Close all database connections"""
    global _mongo_client, _redis_client
    
    if _mongo_client:
        _mongo_client.close()
        logger.info("MongoDB connection closed")
    
    if _redis_client:
        await _redis_client.close()
        logger.info("Redis connection closed")
