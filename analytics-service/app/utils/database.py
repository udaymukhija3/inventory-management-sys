import redis.asyncio as redis
import logging
import psycopg2
from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

_redis_client = None

def get_postgres_connection():
    """Create a PostgreSQL connection for analytics reads."""
    return psycopg2.connect(
        host=settings.postgres_host,
        port=settings.postgres_port,
        dbname=settings.postgres_db,
        user=settings.postgres_user,
        password=settings.postgres_password,
    )

async def check_postgres():
    """Validate PostgreSQL connectivity."""
    try:
        with get_postgres_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
                cur.fetchone()
        logger.info("PostgreSQL connection validated successfully")
    except Exception as e:
        logger.error(f"Failed to validate PostgreSQL connection: {e}")
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
    """Deprecated compatibility shim for removed MongoDB dependency."""
    raise RuntimeError("MongoDB is not part of the supported analytics path")

async def get_redis_client():
    """Get Redis client instance"""
    global _redis_client
    if _redis_client is None:
        await init_redis()
    return _redis_client

async def close_connections():
    """Close all database connections"""
    global _redis_client

    if _redis_client:
        await _redis_client.close()
        logger.info("Redis connection closed")
