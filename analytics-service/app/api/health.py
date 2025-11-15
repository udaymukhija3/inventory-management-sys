from fastapi import APIRouter
from app.utils.database import get_mongodb_client, get_redis_client
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/")
async def health():
    """Basic health check"""
    return {
        "status": "UP",
        "service": "analytics-service"
    }

@router.get("/detailed")
async def health_detailed():
    """Detailed health check with database connectivity"""
    health_status = {
        "status": "UP",
        "service": "analytics-service",
        "checks": {
            "mongodb": "UNKNOWN",
            "redis": "UNKNOWN"
        }
    }
    
    # Check MongoDB
    try:
        mongo_client = await get_mongodb_client()
        await mongo_client.admin.command('ping')
        health_status["checks"]["mongodb"] = "UP"
    except Exception as e:
        logger.error(f"MongoDB health check failed: {e}")
        health_status["checks"]["mongodb"] = "DOWN"
        health_status["status"] = "DEGRADED"
    
    # Check Redis
    try:
        redis_client = await get_redis_client()
        await redis_client.ping()
        health_status["checks"]["redis"] = "UP"
    except Exception as e:
        logger.error(f"Redis health check failed: {e}")
        health_status["checks"]["redis"] = "DOWN"
        health_status["status"] = "DEGRADED"
    
    return health_status
