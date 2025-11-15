from fastapi import APIRouter, HTTPException
from app.models.inventory import VelocityMetrics
from app.services.velocity_analyzer import VelocityAnalyzer

router = APIRouter()
analyzer = VelocityAnalyzer()

@router.get("/velocity/{sku}/{warehouse_id}", response_model=VelocityMetrics)
async def get_velocity(sku: str, warehouse_id: str, period_days: int = 30):
    """Get inventory velocity for a SKU"""
    try:
        return await analyzer.calculate_velocity(sku, warehouse_id, period_days)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

