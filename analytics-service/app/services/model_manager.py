import logging
import os
from typing import Dict, Optional
from app.config import get_settings
from app.ml.model_registry import ModelRegistry

logger = logging.getLogger(__name__)
settings = get_settings()

class ModelManager:
    """Manages ML models lifecycle"""
    
    def __init__(self):
        self.model_registry = ModelRegistry(settings.model_path)
        self.models: Dict[str, any] = {}
    
    async def load_existing_models(self):
        """Load all existing models from disk"""
        try:
            model_path = settings.model_path
            if not os.path.exists(model_path):
                os.makedirs(model_path, exist_ok=True)
                logger.info(f"Created model directory: {model_path}")
                return
            
            # List all model files
            model_files = [
                f for f in os.listdir(model_path)
                if f.endswith('.pkl')
            ]
            
            loaded_count = 0
            for model_file in model_files:
                try:
                    model_key = model_file.replace('.pkl', '')
                    model = self.model_registry.load_model(model_key)
                    if model:
                        self.models[model_key] = model
                        loaded_count += 1
                except Exception as e:
                    logger.warning(f"Failed to load model {model_file}: {e}")
            
            logger.info(f"Loaded {loaded_count} existing models")
        except Exception as e:
            logger.error(f"Error loading existing models: {e}")
    
    async def get_model(self, model_key: str):
        """Get a model by key"""
        if model_key in self.models:
            return self.models[model_key]
        
        # Try to load from registry
        model = self.model_registry.load_model(model_key)
        if model:
            self.models[model_key] = model
        return model
    
    async def save_model(self, model_key: str, model):
        """Save a model"""
        try:
            self.model_registry.save_model(model_key, model)
            self.models[model_key] = model
            logger.info(f"Model {model_key} saved successfully")
        except Exception as e:
            logger.error(f"Error saving model {model_key}: {e}")
            raise
    
    async def delete_model(self, model_key: str):
        """Delete a model"""
        try:
            self.model_registry.remove_model(model_key)
            if model_key in self.models:
                del self.models[model_key]
            logger.info(f"Model {model_key} deleted successfully")
        except Exception as e:
            logger.error(f"Error deleting model {model_key}: {e}")
            raise
    
    def list_models(self) -> Dict[str, any]:
        """List all available models"""
        return {
            "loaded_models": list(self.models.keys()),
            "total_loaded": len(self.models)
        }

