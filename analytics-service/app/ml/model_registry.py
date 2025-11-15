import os
import joblib
from typing import Dict, Optional
from prophet import Prophet

class ModelRegistry:
    """Registry for managing ML models"""
    
    def __init__(self, model_path: str = "/models"):
        self.model_path = model_path
        os.makedirs(model_path, exist_ok=True)
        self.loaded_models: Dict[str, Prophet] = {}
    
    def save_model(self, model_key: str, model: Prophet):
        """Save model to disk"""
        file_path = os.path.join(self.model_path, f"{model_key}.pkl")
        joblib.dump(model, file_path)
        self.loaded_models[model_key] = model
    
    def load_model(self, model_key: str) -> Optional[Prophet]:
        """Load model from disk"""
        if model_key in self.loaded_models:
            return self.loaded_models[model_key]
        
        file_path = os.path.join(self.model_path, f"{model_key}.pkl")
        if os.path.exists(file_path):
            model = joblib.load(file_path)
            self.loaded_models[model_key] = model
            return model
        
        return None
    
    def remove_model(self, model_key: str):
        """Remove model from registry"""
        if model_key in self.loaded_models:
            del self.loaded_models[model_key]
        
        file_path = os.path.join(self.model_path, f"{model_key}.pkl")
        if os.path.exists(file_path):
            os.remove(file_path)

