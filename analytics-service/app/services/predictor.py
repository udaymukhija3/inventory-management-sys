import pandas as pd
import numpy as np
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import asyncio
from prophet import Prophet
from sklearn.metrics import mean_absolute_percentage_error
import joblib
import logging
from app.models.prediction import PredictionRequest, PredictionResponse, PredictionDataPoint
from app.utils.database import get_mongodb_client, get_redis_client
from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

class DemandPredictor:
    def __init__(self):
        self.models: Dict[str, Prophet] = {}
        self.model_metrics: Dict[str, dict] = {}
        self.mongo_client = None
        self.redis_client = None
        
    async def _get_clients(self):
        if self.mongo_client is None:
            self.mongo_client = await get_mongodb_client()
        if self.redis_client is None:
            self.redis_client = await get_redis_client()
        
    async def train_model(self, sku: str, warehouse_id: str) -> dict:
        """Train demand prediction model with comprehensive feature engineering"""
        try:
            await self._get_clients()
            model_key = f"{sku}_{warehouse_id}"
            logger.info(f"Training model for {model_key}")
            
            # Fetch historical data
            db = self.mongo_client.inventory_analytics
            collection = db.inventory_transactions
            
            pipeline = [
                {
                    "$match": {
                        "sku": sku,
                        "warehouse_id": warehouse_id,
                        "transaction_type": {"$in": ["SALE", "RETURN"]}
                    }
                },
                {
                    "$group": {
                        "_id": {
                            "$dateToString": {
                                "format": "%Y-%m-%d",
                                "date": "$timestamp"
                            }
                        },
                        "total_quantity": {"$sum": "$quantity"},
                        "transaction_count": {"$sum": 1}
                    }
                },
                {"$sort": {"_id": 1}}
            ]
            
            cursor = collection.aggregate(pipeline)
            data = list(cursor)
            
            if len(data) < 30:
                raise ValueError("Insufficient historical data")
            
            # Prepare data for Prophet
            df = pd.DataFrame(data)
            df['ds'] = pd.to_datetime(df['_id'])
            df['y'] = df['total_quantity'].abs()
            
            # Add external regressors
            df['day_of_week'] = df['ds'].dt.dayofweek
            df['is_weekend'] = (df['day_of_week'] >= 5).astype(int)
            df['month'] = df['ds'].dt.month
            
            # Configure Prophet with custom parameters
            model = Prophet(
                growth='linear',
                daily_seasonality=True,
                weekly_seasonality=True,
                yearly_seasonality=True,
                seasonality_mode='multiplicative',
                changepoint_prior_scale=0.05,
                interval_width=0.95
            )
            
            # Add custom seasonalities
            model.add_seasonality(
                name='monthly',
                period=30.5,
                fourier_order=5
            )
            
            # Add regressors
            model.add_regressor('is_weekend')
            
            # Fit model
            model.fit(df[['ds', 'y', 'is_weekend']])
            
            # Calculate model metrics
            train_size = int(len(df) * 0.8)
            train_df = df[:train_size]
            test_df = df[train_size:]
            
            # Retrain on training data only
            eval_model = Prophet(
                daily_seasonality=True,
                weekly_seasonality=True,
                yearly_seasonality=True
            )
            eval_model.add_regressor('is_weekend')
            eval_model.fit(train_df[['ds', 'y', 'is_weekend']])
            
            # Predict on test set
            future_test = eval_model.make_future_dataframe(
                periods=len(test_df),
                include_history=False
            )
            future_test['is_weekend'] = (future_test['ds'].dt.dayofweek >= 5).astype(int)
            forecast_test = eval_model.predict(future_test)
            
            # Calculate metrics
            mape = mean_absolute_percentage_error(
                test_df['y'].values,
                forecast_test['yhat'].values
            )
            
            # Store model and metrics
            self.models[model_key] = model
            self.model_metrics[model_key] = {
                'mape': mape,
                'training_date': datetime.now(),
                'data_points': len(df),
                'last_date': df['ds'].max()
            }
            
            # Save model to disk
            import os
            os.makedirs(settings.model_path, exist_ok=True)
            model_path = f"{settings.model_path}/{model_key}.pkl"
            joblib.dump(model, model_path)
            
            # Cache model info in Redis
            await self.redis_client.setex(
                f"model_info:{model_key}",
                3600,
                str({
                    'trained_at': datetime.now().isoformat(),
                    'mape': mape,
                    'status': 'active'
                })
            )
            
            return {
                'model_key': model_key,
                'mape': mape,
                'training_samples': len(df),
                'status': 'success'
            }
            
        except Exception as e:
            logger.error(f"Error training model: {str(e)}")
            raise
    
    async def predict_demand(
        self,
        sku: str,
        warehouse_id: str,
        horizon_days: int = 30
    ) -> PredictionResponse:
        """Generate demand predictions with confidence intervals"""
        await self._get_clients()
        model_key = f"{sku}_{warehouse_id}"
        
        # Load or retrieve model
        if model_key not in self.models:
            import os
            model_path = f"{settings.model_path}/{model_key}.pkl"
            try:
                if os.path.exists(model_path):
                    self.models[model_key] = joblib.load(model_path)
                else:
                    # Train new model if not exists
                    await self.train_model(sku, warehouse_id)
            except Exception as e:
                logger.error(f"Error loading model: {e}")
                await self.train_model(sku, warehouse_id)
        
        model = self.models[model_key]
        
        # Generate future dataframe
        future = model.make_future_dataframe(periods=horizon_days)
        future['is_weekend'] = (future['ds'].dt.dayofweek >= 5).astype(int)
        
        # Make predictions
        forecast = model.predict(future)
        future_forecast = forecast.tail(horizon_days)
        
        # Get current inventory level from Redis
        inventory_key = f"inventory:{sku}:{warehouse_id}"
        current_inventory_str = await self.redis_client.get(inventory_key)
        current_inventory = int(current_inventory_str) if current_inventory_str else 0
        
        # Calculate stockout risk
        cumulative_demand = 0
        stockout_date = None
        stockout_probability = 0
        
        for _, row in future_forecast.iterrows():
            cumulative_demand += row['yhat']
            if cumulative_demand >= current_inventory and stockout_date is None:
                stockout_date = row['ds'].isoformat()
                # Calculate probability based on confidence interval
                if cumulative_demand >= current_inventory:
                    interval_width = row['yhat_upper'] - row['yhat_lower']
                    if interval_width > 0:
                        stockout_probability = 0.5 + (
                            (cumulative_demand - current_inventory) / interval_width
                        ) * 0.5
                        stockout_probability = min(stockout_probability, 1.0)
        
        # Calculate optimal reorder point
        lead_time_days = 7
        safety_stock_days = 3
        
        lead_time_demand = future_forecast.head(lead_time_days)['yhat'].sum()
        safety_stock = future_forecast.head(safety_stock_days)['yhat_upper'].sum()
        reorder_point = lead_time_demand + safety_stock
        
        # Calculate recommended order quantity (EOQ-based)
        avg_daily_demand = future_forecast['yhat'].mean()
        holding_cost_per_unit = 0.1
        ordering_cost = 50
        
        eoq = np.sqrt(
            (2 * avg_daily_demand * 365 * ordering_cost) / holding_cost_per_unit
        )
        recommended_quantity = max(int(eoq), int(reorder_point))
        
        # Prepare response
        predictions = []
        for _, row in future_forecast.iterrows():
            predictions.append(PredictionDataPoint(
                date=row['ds'].isoformat(),
                predicted_demand=round(row['yhat'], 2),
                lower_bound=round(row['yhat_lower'], 2),
                upper_bound=round(row['yhat_upper'], 2),
                trend=round(row['trend'], 2),
                seasonality=round(
                    row.get('yearly', 0) + row.get('weekly', 0) + row.get('daily', 0),
                    2
                )
            ))
        
        return PredictionResponse(
            sku=sku,
            warehouse_id=warehouse_id,
            predictions=predictions,
            current_inventory=current_inventory,
            reorder_point=int(reorder_point),
            recommended_order_quantity=recommended_quantity,
            stockout_date=stockout_date,
            stockout_probability=round(stockout_probability, 2),
            model_accuracy=self.model_metrics.get(model_key, {}).get('mape', 0),
            confidence_level=0.95
        )

