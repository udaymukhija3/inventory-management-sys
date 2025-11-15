import pandas as pd
import numpy as np
from typing import Dict

class SeasonalityDetector:
    """Detect seasonal patterns in time series data"""
    
    def detect_seasonality(self, df: pd.DataFrame, period: int = 7) -> Dict[str, float]:
        """Detect seasonality patterns"""
        if len(df) < period * 2:
            return {"detected": False}
        
        # Simple autocorrelation-based detection
        df_sorted = df.sort_values('ds')
        values = df_sorted['y'].values
        
        autocorr = np.correlate(values, values, mode='full')
        autocorr = autocorr[len(autocorr)//2:]
        
        # Check for periodic patterns
        if len(autocorr) > period:
            seasonality_strength = autocorr[period] / autocorr[0] if autocorr[0] > 0 else 0
            return {
                "detected": seasonality_strength > 0.3,
                "strength": float(seasonality_strength),
                "period": period
            }
        
        return {"detected": False}

