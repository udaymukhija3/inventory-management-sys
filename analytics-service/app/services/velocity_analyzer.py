import logging
from typing import Dict
from app.models.inventory import VelocityMetrics
from app.utils.database import get_postgres_connection, get_redis_client

logger = logging.getLogger(__name__)

class VelocityAnalyzer:
    """
    Reads analytics published by the ETL pipeline from PostgreSQL and Redis.
    """
    
    async def calculate_velocity(self, sku: str, warehouse_id: str, period_days: int = 30) -> VelocityMetrics:
        """
        Return the latest ETL-derived metrics for a SKU/warehouse pair.
        """
        cached_metrics = await self._read_cached_metrics(sku, warehouse_id)
        db_metrics = self._read_latest_metrics(sku, warehouse_id)

        velocity_7d = cached_metrics.get("velocity_7d", db_metrics["velocity_7d"])
        velocity_30d = cached_metrics.get("velocity_30d", db_metrics["velocity_30d"])
        bounded_period = max(1, min(period_days, 30))
        average_daily_sales = velocity_30d if bounded_period >= 30 else velocity_7d
        total_sales = velocity_30d * bounded_period

        return VelocityMetrics(
            sku=sku,
            warehouse_id=warehouse_id,
            velocity_7d=round(velocity_7d, 2),
            velocity_30d=round(velocity_30d, 2),
            total_sales=round(total_sales, 2),
            average_daily_sales=round(average_daily_sales, 2),
            period_days=period_days
        )

    async def _read_cached_metrics(self, sku: str, warehouse_id: str) -> Dict[str, float]:
        redis_client = await get_redis_client()
        cache_key = f"metrics:{sku}:{warehouse_id}"
        cached_data = await redis_client.hgetall(cache_key)
        if not cached_data:
            return {}

        try:
            return {
                "velocity_7d": float(cached_data.get("velocity_7d", 0.0)),
                "velocity_30d": float(cached_data.get("velocity_30d", 0.0)),
            }
        except (TypeError, ValueError):
            logger.warning("Invalid cached metrics for %s:%s", sku, warehouse_id)
            return {}

    def _read_latest_metrics(self, sku: str, warehouse_id: str) -> Dict[str, float]:
        query = """
            SELECT velocity_7d, velocity_30d
            FROM analytics.current_metrics
            WHERE sku = %s AND warehouse_id = %s
        """
        with get_postgres_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, (sku, warehouse_id))
                row = cur.fetchone()

        if row is None:
            return {"velocity_7d": 0.0, "velocity_30d": 0.0}

        return {
            "velocity_7d": float(row[0] or 0.0),
            "velocity_30d": float(row[1] or 0.0),
        }
