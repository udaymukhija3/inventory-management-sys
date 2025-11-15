import logging
from typing import Dict
from datetime import datetime, timedelta
from app.models.inventory import VelocityMetrics
from app.utils.database import get_mongodb_client

logger = logging.getLogger(__name__)

class VelocityAnalyzer:
    """
    Analyzes inventory velocity and trends (basic analytics, not ML)
    Calculates velocity metrics from transaction data
    """
    
    async def calculate_velocity(self, sku: str, warehouse_id: str, period_days: int = 30) -> VelocityMetrics:
        """
        Calculate inventory velocity for a SKU
        Returns velocity metrics: 7-day velocity, 30-day velocity, and averages
        """
        mongo_client = await get_mongodb_client()
        db = mongo_client.inventory_analytics
        collection = db.inventory_transactions
        
        end_date = datetime.now()
        
        # Calculate 7-day velocity
        start_date_7d = end_date - timedelta(days=7)
        velocity_7d = await self._calculate_period_velocity(
            collection, sku, warehouse_id, start_date_7d, end_date, 7
        )
        
        # Calculate 30-day velocity
        start_date_30d = end_date - timedelta(days=30)
        velocity_30d = await self._calculate_period_velocity(
            collection, sku, warehouse_id, start_date_30d, end_date, 30
        )
        
        # Calculate total sales for the period
        total_sales = velocity_30d * period_days if period_days <= 30 else velocity_30d * 30
        
        # Calculate average daily sales
        average_daily_sales = velocity_30d if period_days >= 30 else velocity_7d
        
        return VelocityMetrics(
            sku=sku,
            warehouse_id=warehouse_id,
            velocity_7d=round(velocity_7d, 2),
            velocity_30d=round(velocity_30d, 2),
            total_sales=round(total_sales, 2),
            average_daily_sales=round(average_daily_sales, 2),
            period_days=period_days
        )
    
    async def _calculate_period_velocity(
        self, collection, sku: str, warehouse_id: str, 
        start_date: datetime, end_date: datetime, days: int
    ) -> float:
        """Calculate velocity for a specific period"""
        pipeline = [
            {
                "$match": {
                    "sku": sku,
                    "warehouse_id": warehouse_id,
                    "timestamp": {"$gte": start_date, "$lte": end_date},
                    "transaction_type": {"$in": ["SALE", "RETURN"]}
                }
            },
            {
                "$group": {
                    "_id": None,
                    "total_quantity": {"$sum": "$quantity"},
                    "transaction_count": {"$sum": 1}
                }
            }
        ]
        
        result = list(collection.aggregate(pipeline))
        
        if not result:
            return 0.0
        
        total_quantity = abs(result[0]['total_quantity'])
        velocity = total_quantity / days if days > 0 else 0.0
        
        return velocity
