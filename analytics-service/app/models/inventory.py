from pydantic import BaseModel
from datetime import datetime

class InventoryTransaction(BaseModel):
    sku: str
    warehouse_id: str
    quantity: int
    transaction_type: str
    timestamp: datetime

class VelocityMetrics(BaseModel):
    sku: str
    warehouse_id: str
    velocity_7d: float
    velocity_30d: float
    total_sales: float
    average_daily_sales: float
    period_days: int
