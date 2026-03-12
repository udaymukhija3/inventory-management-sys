from fastapi import APIRouter
from app.utils.database import check_postgres, get_postgres_connection, get_redis_client
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
            "postgres": "UNKNOWN",
            "redis": "UNKNOWN",
            "pipeline_freshness": "UNKNOWN",
        },
        "pipeline": {},
    }
    
    # Check PostgreSQL
    try:
        await check_postgres()
        health_status["checks"]["postgres"] = "UP"
    except Exception as e:
        logger.error(f"PostgreSQL health check failed: {e}")
        health_status["checks"]["postgres"] = "DOWN"
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

    try:
        with get_postgres_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT run_id, status, started_at, completed_at
                    FROM analytics.pipeline_runs
                    WHERE status = 'SUCCESS'
                    ORDER BY completed_at DESC NULLS LAST, started_at DESC
                    LIMIT 1
                    """
                )
                row = cur.fetchone()
        if row:
            health_status["checks"]["pipeline_freshness"] = "UP"
            health_status["pipeline"] = {
                "last_successful_run_id": row[0],
                "last_successful_status": row[1],
                "started_at": row[2].isoformat() if row[2] else None,
                "completed_at": row[3].isoformat() if row[3] else None,
            }
        else:
            health_status["checks"]["pipeline_freshness"] = "DOWN"
            health_status["status"] = "DEGRADED"
            health_status["pipeline"] = {
                "last_successful_run_id": None,
                "last_successful_status": "MISSING",
            }
    except Exception as e:
        logger.error(f"Pipeline health check failed: {e}")
        health_status["checks"]["pipeline_freshness"] = "DOWN"
        health_status["status"] = "DEGRADED"
    
    return health_status
