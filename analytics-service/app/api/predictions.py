from fastapi import APIRouter, HTTPException
from app.services.velocity_analyzer import VelocityAnalyzer
from typing import Dict
from datetime import datetime
import logging

logger = logging.getLogger(__name__)
router = APIRouter()
analyzer = VelocityAnalyzer()

@router.get("/trend/{sku}/{warehouse_id}")
async def get_trend(sku: str, warehouse_id: str, period_days: int = 30):
    """
    Get sales trend for a SKU based on historical data (basic analytics, no ML)
    Returns simple trend analysis: average, min, max, trend direction
    """
    try:
        # Get velocity metrics which includes trend information
        velocity_metrics = await analyzer.calculate_velocity(sku, warehouse_id, period_days)
        
        # Calculate simple trend direction based on velocity comparison
        if velocity_metrics.velocity_7d > velocity_metrics.velocity_30d * 1.1:
            trend_direction = "increasing"
        elif velocity_metrics.velocity_7d < velocity_metrics.velocity_30d * 0.9:
            trend_direction = "decreasing"
        else:
            trend_direction = "stable"
        
        return {
            "sku": sku,
            "warehouse_id": warehouse_id,
            "period_days": period_days,
            "velocity_7d": velocity_metrics.velocity_7d,
            "velocity_30d": velocity_metrics.velocity_30d,
            "total_sales": velocity_metrics.total_sales,
            "average_daily_sales": velocity_metrics.average_daily_sales,
            "trend_direction": trend_direction,
            "message": "Basic trend analysis based on historical data (no ML predictions)"
        }
    except Exception as e:
        logger.error(f"Error calculating trend: {e}")
        raise HTTPException(status_code=500, detail=str(e))
