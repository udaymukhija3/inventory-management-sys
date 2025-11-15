from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class PredictionRequest(BaseModel):
    sku: str
    warehouse_id: str
    horizon_days: int = 30

class PredictionDataPoint(BaseModel):
    date: str
    predicted_demand: float
    lower_bound: float
    upper_bound: float
    trend: float
    seasonality: float

class PredictionResponse(BaseModel):
    sku: str
    warehouse_id: str
    predictions: List[PredictionDataPoint]
    current_inventory: int
    reorder_point: int
    recommended_order_quantity: int
    stockout_date: Optional[str]
    stockout_probability: float
    model_accuracy: float
    confidence_level: float

