import pytest
from app.services.predictor import DemandPredictor

@pytest.mark.asyncio
async def test_predictor_initialization():
    predictor = DemandPredictor()
    assert predictor.models == {}
    assert predictor.model_metrics == {}

