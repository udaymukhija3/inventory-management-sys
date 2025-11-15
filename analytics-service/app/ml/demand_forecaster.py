from typing import Dict, List
import pandas as pd
from prophet import Prophet

class DemandForecaster:
    """Wrapper for Prophet-based demand forecasting"""
    
    def create_model(self, **kwargs) -> Prophet:
        """Create a Prophet model with custom parameters"""
        return Prophet(**kwargs)
    
    def forecast(self, model: Prophet, periods: int, **kwargs):
        """Generate forecast for future periods"""
        future = model.make_future_dataframe(periods=periods)
        return model.predict(future)

