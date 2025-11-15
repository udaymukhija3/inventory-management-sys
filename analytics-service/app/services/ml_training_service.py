import logging
import asyncio
from app.ml.training_pipeline import InventoryMLPipeline
from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

class MLTrainingService:
    """Service for running ML training pipeline"""
    
    def __init__(self):
        self.pipeline = None
    
    async def run_training(self, config_path: str = None):
        """Run the ML training pipeline"""
        try:
            logger.info("Starting ML training pipeline")
            # Run the synchronous pipeline in executor to avoid blocking
            loop = asyncio.get_event_loop()
            self.pipeline = InventoryMLPipeline(config_path=config_path)
            await loop.run_in_executor(None, self.pipeline.run_training_pipeline)
            logger.info("ML training pipeline completed successfully")
            return {"status": "success", "message": "Training completed"}
        except Exception as e:
            logger.error(f"Error in ML training: {e}", exc_info=True)
            return {"status": "error", "message": str(e)}

