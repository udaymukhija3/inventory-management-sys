import logging
from typing import Dict, List
from app.services.predictor import DemandPredictor
from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

class ModelTrainer:
    def __init__(self):
        self.predictor = DemandPredictor()
    
    async def train_models_for_skus(self, sku_warehouse_pairs: List[Dict[str, str]]) -> Dict[str, dict]:
        """Train models for multiple SKU-warehouse pairs"""
        results = {}
        for pair in sku_warehouse_pairs:
            try:
                result = await self.predictor.train_model(
                    pair['sku'],
                    pair['warehouse_id']
                )
                results[f"{pair['sku']}_{pair['warehouse_id']}"] = result
            except Exception as e:
                logger.error(f"Failed to train model for {pair}: {e}")
                results[f"{pair['sku']}_{pair['warehouse_id']}"] = {
                    'status': 'error',
                    'error': str(e)
                }
        return results

