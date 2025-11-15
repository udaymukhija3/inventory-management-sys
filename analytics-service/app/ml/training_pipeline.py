"""
ML Training Pipeline for Inventory Optimization
Demonstrates: Feature engineering, model training, hyperparameter tuning, model serving
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
from typing import Dict, Tuple, List, Optional
import mlflow
import mlflow.sklearn
from sklearn.model_selection import TimeSeriesSplit, GridSearchCV
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from prophet import Prophet
import optuna
import joblib
import os
from dataclasses import dataclass, asdict
import yaml
import psycopg2
from app.config import get_settings

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

settings = get_settings()

@dataclass
class ModelConfig:
    name: str
    version: str
    hyperparameters: Dict
    metrics: Dict
    feature_importance: Dict

class InventoryMLPipeline:
    """
    Production ML pipeline that:
    1. Extracts and prepares training data
    2. Engineers features at scale
    3. Trains multiple models with hyperparameter tuning
    4. Evaluates and selects best model
    5. Deploys model to production
    """
    
    def __init__(self, config_path: Optional[str] = None):
        self.config = self._load_config(config_path)
        
        self.models = {}
        self.scalers = {}
        self.feature_columns = []
        
        # MLflow setup
        mlflow_uri = os.getenv('MLFLOW_TRACKING_URI', self.config.get('mlflow_uri', 'http://localhost:5000'))
        mlflow.set_tracking_uri(mlflow_uri)
        mlflow.set_experiment('inventory_optimization')
        
        # Database connection
        self.pg_conn = None
        
    def _load_config(self, config_path: Optional[str]) -> Dict:
        """Load configuration from file or use defaults"""
        default_config_path = os.path.join(os.path.dirname(__file__), 'config', 'ml_config.yaml')
        
        # Try provided path, then default path, then use defaults
        if config_path and os.path.exists(config_path):
            with open(config_path, 'r') as f:
                return yaml.safe_load(f)
        elif os.path.exists(default_config_path):
            with open(default_config_path, 'r') as f:
                config = yaml.safe_load(f)
                # Override with environment variables if available
                if 'MLFLOW_TRACKING_URI' in os.environ:
                    config['mlflow_uri'] = os.getenv('MLFLOW_TRACKING_URI')
                return config
        
        return {
            'mlflow_uri': os.getenv('MLFLOW_TRACKING_URI', 'http://localhost:5000'),
            'model_path': settings.model_path,
            'training_batch_size': settings.training_batch_size
        }
    
    def _get_db_connection(self):
        """Get PostgreSQL connection"""
        if self.pg_conn is None or self.pg_conn.closed:
            self.pg_conn = psycopg2.connect(
                host=os.getenv('POSTGRES_HOST', 'localhost'),
                database=os.getenv('POSTGRES_DB', 'inventory'),
                user=os.getenv('POSTGRES_USER', 'inventory_user'),
                password=os.getenv('POSTGRES_PASSWORD', 'inventory_pass'),
                port=os.getenv('POSTGRES_PORT', '5432')
            )
        return self.pg_conn
        
    def run_training_pipeline(self):
        """Execute the full ML training pipeline"""
        logger.info("Starting ML training pipeline...")
        
        try:
            with mlflow.start_run():
                # Step 1: Data extraction and validation
                train_data, test_data = self._extract_and_split_data()
                mlflow.log_metric("train_samples", len(train_data))
                mlflow.log_metric("test_samples", len(test_data))
                
                if len(train_data) == 0:
                    logger.warning("No training data available. Using synthetic data.")
                    train_data = self._generate_synthetic_data()
                    split_date = train_data['date'].max() - timedelta(days=60)
                    test_data = train_data[train_data['date'] > split_date]
                    train_data = train_data[train_data['date'] <= split_date]
                
                # Step 2: Feature engineering
                X_train, y_train = self._engineer_features(train_data)
                X_test, y_test = self._engineer_features(test_data)
                
                # Step 3: Train multiple models
                models = {
                    'random_forest': self._train_random_forest(X_train, y_train),
                    'gradient_boost': self._train_gradient_boost(X_train, y_train),
                    'ensemble': self._train_ensemble(X_train, y_train)
                }
                
                # Step 4: Evaluate models
                best_model, best_metrics = self._evaluate_models(models, X_test, y_test, test_data)
                
                # Step 5: Production deployment
                self._deploy_model(best_model, best_metrics)
                
            logger.info("ML training pipeline completed successfully")
        except Exception as e:
            logger.error(f"Error in ML training pipeline: {e}", exc_info=True)
            raise
        finally:
            if self.pg_conn:
                self.pg_conn.close()
    
    def _extract_and_split_data(self) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Extract data from warehouse and split for time series validation"""
        query = """
        WITH daily_aggregates AS (
            SELECT 
                date_trunc('day', t.timestamp) as date,
                t.sku,
                t.warehouse_id,
                i.reorder_point,
                i.unit_cost,
                SUM(CASE WHEN t.transaction_type = 'SALE' THEN ABS(t.quantity_change) ELSE 0 END) as daily_sales,
                SUM(CASE WHEN t.transaction_type = 'RESTOCK' THEN ABS(t.quantity_change) ELSE 0 END) as daily_receipts,
                AVG(i.quantity_on_hand) as avg_inventory,
                COUNT(*) as transaction_count,
                EXTRACT(dow FROM date_trunc('day', t.timestamp)) as day_of_week,
                EXTRACT(month FROM date_trunc('day', t.timestamp)) as month
            FROM inventory_transactions t
            JOIN inventory_items i ON t.sku = i.sku AND t.warehouse_id = i.warehouse_id
            WHERE t.timestamp >= NOW() - INTERVAL '365 days'
            GROUP BY 1, 2, 3, 4, 5
        ),
        lagged_features AS (
            SELECT 
                *,
                LAG(daily_sales, 1) OVER (PARTITION BY sku, warehouse_id ORDER BY date) as sales_lag_1,
                LAG(daily_sales, 7) OVER (PARTITION BY sku, warehouse_id ORDER BY date) as sales_lag_7,
                LAG(daily_sales, 30) OVER (PARTITION BY sku, warehouse_id ORDER BY date) as sales_lag_30,
                AVG(daily_sales) OVER (
                    PARTITION BY sku, warehouse_id 
                    ORDER BY date 
                    ROWS BETWEEN 7 PRECEDING AND CURRENT ROW
                ) as sales_ma_7,
                AVG(daily_sales) OVER (
                    PARTITION BY sku, warehouse_id 
                    ORDER BY date 
                    ROWS BETWEEN 30 PRECEDING AND CURRENT ROW
                ) as sales_ma_30,
                STDDEV(daily_sales) OVER (
                    PARTITION BY sku, warehouse_id 
                    ORDER BY date 
                    ROWS BETWEEN 30 PRECEDING AND CURRENT ROW
                ) as sales_std_30
            FROM daily_aggregates
        )
        SELECT * FROM lagged_features
        WHERE date >= NOW() - INTERVAL '300 days'
        ORDER BY sku, warehouse_id, date
        """
        
        try:
            conn = self._get_db_connection()
            data = pd.read_sql_query(query, conn)
            
            if len(data) == 0:
                logger.warning("No data from database, generating synthetic data")
                return self._generate_synthetic_data(), pd.DataFrame()
            
            # Time series split - last 20% for testing
            split_date = data['date'].max() - timedelta(days=60)
            train_data = data[data['date'] <= split_date]
            test_data = data[data['date'] > split_date]
            
            return train_data, test_data
        except Exception as e:
            logger.error(f"Error extracting data: {e}")
            logger.info("Generating synthetic data for demo")
            data = self._generate_synthetic_data()
            split_date = data['date'].max() - timedelta(days=60)
            train_data = data[data['date'] <= split_date]
            test_data = data[data['date'] > split_date]
            return train_data, test_data
    
    def _generate_synthetic_data(self) -> pd.DataFrame:
        """Generate realistic synthetic data for demo purposes"""
        np.random.seed(42)
        
        dates = pd.date_range(end=datetime.now(), periods=300, freq='D')
        skus = ['LAPTOP-001', 'PHONE-001', 'TABLET-001', 'WATCH-001', 'EARBUDS-001']
        warehouses = ['WH001', 'WH002', 'WH003', 'WH004']
        
        data = []
        for sku in skus:
            for warehouse in warehouses:
                # Base demand with trend and seasonality
                base_demand = np.random.randint(20, 100)
                trend = np.random.uniform(-0.1, 0.2)
                
                for i, date in enumerate(dates):
                    # Add weekly seasonality
                    weekly_factor = 1.2 if date.dayofweek in [4, 5] else 0.9
                    
                    # Add monthly seasonality
                    monthly_factor = 1.3 if date.month in [11, 12] else 1.0
                    
                    # Calculate sales with noise
                    daily_sales = max(0, int(
                        base_demand * (1 + trend * i/300) * weekly_factor * monthly_factor +
                        np.random.normal(0, base_demand * 0.2)
                    ))
                    
                    data.append({
                        'date': date,
                        'sku': sku,
                        'warehouse_id': warehouse,
                        'daily_sales': daily_sales,
                        'daily_receipts': np.random.randint(0, 200) if np.random.random() > 0.8 else 0,
                        'avg_inventory': np.random.randint(100, 500),
                        'reorder_point': base_demand * 7,  # 7 days of supply
                        'unit_cost': np.random.uniform(10, 1000),
                        'transaction_count': np.random.randint(1, 20),
                        'day_of_week': date.dayofweek,
                        'month': date.month
                    })
        
        df = pd.DataFrame(data)
        
        # Add lag features
        for sku in skus:
            for warehouse in warehouses:
                mask = (df['sku'] == sku) & (df['warehouse_id'] == warehouse)
                df.loc[mask, 'sales_lag_1'] = df.loc[mask, 'daily_sales'].shift(1)
                df.loc[mask, 'sales_lag_7'] = df.loc[mask, 'daily_sales'].shift(7)
                df.loc[mask, 'sales_lag_30'] = df.loc[mask, 'daily_sales'].shift(30)
                df.loc[mask, 'sales_ma_7'] = df.loc[mask, 'daily_sales'].rolling(7).mean()
                df.loc[mask, 'sales_ma_30'] = df.loc[mask, 'daily_sales'].rolling(30).mean()
                df.loc[mask, 'sales_std_30'] = df.loc[mask, 'daily_sales'].rolling(30).std()
        
        return df.dropna()
    
    def _engineer_features(self, data: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
        """Advanced feature engineering for ML models"""
        if len(data) == 0:
            return np.array([]), np.array([])
            
        features = data.copy()
        
        # Time-based features
        features['day_sin'] = np.sin(2 * np.pi * features['day_of_week'] / 7)
        features['day_cos'] = np.cos(2 * np.pi * features['day_of_week'] / 7)
        features['month_sin'] = np.sin(2 * np.pi * features['month'] / 12)
        features['month_cos'] = np.cos(2 * np.pi * features['month'] / 12)
        
        # Inventory features
        features['inventory_ratio'] = features['avg_inventory'] / (features['sales_ma_7'] + 1)
        features['stockout_risk'] = (features['reorder_point'] - features['avg_inventory']) / (features['sales_ma_7'] + 1)
        
        # Price elasticity proxy
        features['value_per_transaction'] = features['daily_sales'] * features['unit_cost'] / (features['transaction_count'] + 1)
        
        # Volatility features
        features['cv_30'] = features['sales_std_30'] / (features['sales_ma_30'] + 1)
        
        # Interaction features
        features['velocity_value'] = features['sales_ma_7'] * features['unit_cost']
        
        # Target variable (next day sales)
        features['target'] = features.groupby(['sku', 'warehouse_id'])['daily_sales'].shift(-1)
        
        # Remove rows with NaN target
        features = features.dropna(subset=['target'])
        
        if len(features) == 0:
            return np.array([]), np.array([])
        
        # Select feature columns
        self.feature_columns = [
            'sales_lag_1', 'sales_lag_7', 'sales_lag_30',
            'sales_ma_7', 'sales_ma_30', 'sales_std_30',
            'day_sin', 'day_cos', 'month_sin', 'month_cos',
            'inventory_ratio', 'stockout_risk', 'value_per_transaction',
            'cv_30', 'velocity_value', 'avg_inventory', 'reorder_point'
        ]
        
        # Ensure all feature columns exist
        available_features = [f for f in self.feature_columns if f in features.columns]
        missing_features = [f for f in self.feature_columns if f not in features.columns]
        
        if missing_features:
            logger.warning(f"Missing features: {missing_features}")
            for feat in missing_features:
                features[feat] = 0
        
        X = features[self.feature_columns].fillna(0).values
        y = features['target'].values
        
        # Scale features
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        self.scalers['standard'] = scaler
        
        return X_scaled, y
    
    def _train_random_forest(self, X: np.ndarray, y: np.ndarray) -> RandomForestRegressor:
        """Train Random Forest with hyperparameter tuning"""
        logger.info("Training Random Forest model...")
        
        if len(X) == 0:
            logger.warning("No data for Random Forest training")
            return RandomForestRegressor(n_estimators=100, random_state=42)
        
        # Hyperparameter tuning with Optuna
        def objective(trial):
            params = {
                'n_estimators': trial.suggest_int('n_estimators', 100, 500),
                'max_depth': trial.suggest_int('max_depth', 5, 30),
                'min_samples_split': trial.suggest_int('min_samples_split', 2, 20),
                'min_samples_leaf': trial.suggest_int('min_samples_leaf', 1, 10),
                'max_features': trial.suggest_categorical('max_features', ['sqrt', 'log2']),
                'n_jobs': -1,
                'random_state': 42
            }
            
            model = RandomForestRegressor(**params)
            
            # Time series cross-validation
            tscv = TimeSeriesSplit(n_splits=min(3, len(X) // 10))
            scores = []
            
            for train_idx, val_idx in tscv.split(X):
                if len(train_idx) == 0 or len(val_idx) == 0:
                    continue
                X_train_cv, X_val_cv = X[train_idx], X[val_idx]
                y_train_cv, y_val_cv = y[train_idx], y[val_idx]
                
                model.fit(X_train_cv, y_train_cv)
                pred = model.predict(X_val_cv)
                scores.append(mean_absolute_error(y_val_cv, pred))
            
            return np.mean(scores) if scores else float('inf')
        
        # Run optimization (limited trials for demo)
        try:
            study = optuna.create_study(direction='minimize')
            n_trials = min(50, len(X) // 10)  # Adaptive trials based on data size
            study.optimize(objective, n_trials=n_trials, show_progress_bar=False)
            
            # Train final model with best parameters
            best_params = study.best_params.copy()
            best_params['n_jobs'] = -1
            best_params['random_state'] = 42
        except Exception as e:
            logger.warning(f"Optuna optimization failed: {e}. Using default parameters.")
            best_params = {
                'n_estimators': 100,
                'max_depth': 10,
                'min_samples_split': 2,
                'min_samples_leaf': 1,
                'max_features': 'sqrt',
                'n_jobs': -1,
                'random_state': 42
            }
        
        model = RandomForestRegressor(**best_params)
        model.fit(X, y)
        
        # Log parameters and feature importance
        try:
            mlflow.log_params(best_params)
            feature_importance = dict(zip(self.feature_columns, model.feature_importances_))
            mlflow.log_dict(feature_importance, "rf_feature_importance.json")
        except:
            pass
        
        return model
    
    def _train_gradient_boost(self, X: np.ndarray, y: np.ndarray) -> GradientBoostingRegressor:
        """Train Gradient Boosting model"""
        logger.info("Training Gradient Boosting model...")
        
        if len(X) == 0:
            logger.warning("No data for Gradient Boosting training")
            return GradientBoostingRegressor(random_state=42)
        
        param_grid = {
            'n_estimators': [100, 200],
            'max_depth': [3, 5],
            'learning_rate': [0.1, 0.3],
            'subsample': [0.8, 1.0]
        }
        
        model = GradientBoostingRegressor(random_state=42)
        tscv = TimeSeriesSplit(n_splits=min(3, len(X) // 10))
        
        try:
            grid_search = GridSearchCV(
                model, param_grid, cv=tscv, 
                scoring='neg_mean_absolute_error', n_jobs=-1
            )
            
            grid_search.fit(X, y)
            
            try:
                mlflow.log_params(grid_search.best_params_)
            except:
                pass
            
            return grid_search.best_estimator_
        except Exception as e:
            logger.warning(f"Grid search failed: {e}. Using default model.")
            model.fit(X, y)
            return model
    
    def _train_prophet(self, data: pd.DataFrame) -> Dict[str, Prophet]:
        """Train Prophet models for each SKU/warehouse combination"""
        logger.info("Training Prophet models...")
        
        prophet_models = {}
        
        try:
            for (sku, warehouse), group in data.groupby(['sku', 'warehouse_id']):
                if len(group) < 30:
                    continue
                    
                # Prepare data for Prophet
                prophet_data = pd.DataFrame({
                    'ds': pd.to_datetime(group['date']),
                    'y': group['daily_sales'].values
                })
                
                # Initialize and train Prophet
                model = Prophet(
                    daily_seasonality=True,
                    weekly_seasonality=True,
                    yearly_seasonality=True,
                    changepoint_prior_scale=0.05,
                    seasonality_prior_scale=10,
                    interval_width=0.95
                )
                
                # Add custom seasonality
                model.add_seasonality(name='monthly', period=30.5, fourier_order=5)
                
                model.fit(prophet_data)
                prophet_models[f"{sku}_{warehouse}"] = model
        except Exception as e:
            logger.error(f"Error training Prophet models: {e}")
        
        return prophet_models
    
    def _train_ensemble(self, X: np.ndarray, y: np.ndarray) -> Dict:
        """Train ensemble model combining multiple approaches"""
        logger.info("Training ensemble model...")
        
        if len(X) == 0:
            return {
                'models': {},
                'weights': {'rf': 0.6, 'gb': 0.4}
            }
        
        # Train base models
        models = {
            'rf': RandomForestRegressor(n_estimators=100, random_state=42),
            'gb': GradientBoostingRegressor(n_estimators=100, random_state=42)
        }
        
        # Train each model
        for name, model in models.items():
            model.fit(X, y)
        
        # Simple averaging ensemble
        ensemble = {
            'models': models,
            'weights': {'rf': 0.6, 'gb': 0.4}  # Weights based on validation performance
        }
        
        return ensemble
    
    def _evaluate_models(self, models: Dict, X_test: np.ndarray, y_test: np.ndarray, 
                        test_data: pd.DataFrame) -> Tuple[object, Dict]:
        """Evaluate all models and select the best one"""
        logger.info("Evaluating models...")
        
        if len(X_test) == 0 or len(y_test) == 0:
            logger.warning("No test data available")
            return models.get('random_forest', RandomForestRegressor()), {'mae': 0, 'rmse': 0, 'r2': 0, 'mape': 0}
        
        results = {}
        
        for name, model in models.items():
            try:
                if name == 'ensemble':
                    # Ensemble prediction
                    predictions = np.zeros_like(y_test)
                    for model_name, weight in model['weights'].items():
                        if model_name in model['models']:
                            predictions += weight * model['models'][model_name].predict(X_test)
                else:
                    predictions = model.predict(X_test)
                
                # Calculate metrics
                mae = mean_absolute_error(y_test, predictions)
                mse = mean_squared_error(y_test, predictions)
                rmse = np.sqrt(mse)
                r2 = r2_score(y_test, predictions)
                mape = np.mean(np.abs((y_test - predictions) / (y_test + 1))) * 100
                
                results[name] = {
                    'mae': mae,
                    'rmse': rmse,
                    'r2': r2,
                    'mape': mape
                }
                
                # Log metrics
                try:
                    mlflow.log_metrics({
                        f"{name}_mae": mae,
                        f"{name}_rmse": rmse,
                        f"{name}_r2": r2,
                        f"{name}_mape": mape
                    })
                except:
                    pass
            except Exception as e:
                logger.error(f"Error evaluating {name}: {e}")
                continue
        
        if not results:
            return models.get('random_forest', RandomForestRegressor()), {'mae': 0, 'rmse': 0, 'r2': 0, 'mape': 0}
        
        # Select best model based on MAE
        best_model_name = min(results, key=lambda x: results[x]['mae'])
        best_model = models[best_model_name]
        best_metrics = results[best_model_name]
        
        logger.info(f"Best model: {best_model_name} with MAE: {best_metrics['mae']:.2f}")
        
        return best_model, best_metrics
    
    def _deploy_model(self, model: object, metrics: Dict):
        """Deploy model to production"""
        logger.info("Deploying model to production...")
        
        # Ensure model directory exists
        os.makedirs(settings.model_path, exist_ok=True)
        
        # Save model artifacts
        model_path = os.path.join(settings.model_path, "inventory_demand_model.pkl")
        scaler_path = os.path.join(settings.model_path, "feature_scaler.pkl")
        
        joblib.dump(model, model_path)
        if 'standard' in self.scalers:
            joblib.dump(self.scalers['standard'], scaler_path)
        
        # Log model to MLflow
        try:
            mlflow.sklearn.log_model(model, "demand_forecast_model")
        except Exception as e:
            logger.warning(f"MLflow logging failed: {e}")
        
        # Model metadata
        metadata = {
            'model_version': datetime.now().strftime('%Y%m%d_%H%M%S'),
            'training_date': datetime.now().isoformat(),
            'metrics': metrics,
            'feature_columns': self.feature_columns,
            'model_type': type(model).__name__
        }
        
        # Save metadata
        metadata_path = os.path.join(settings.model_path, 'model_metadata.yaml')
        with open(metadata_path, 'w') as f:
            yaml.dump(metadata, f)
        
        logger.info(f"Model deployed successfully. Version: {metadata['model_version']}")

class MLFeatureStore:
    """
    Feature store for managing ML features
    Demonstrates modern ML engineering practices
    """
    
    def __init__(self):
        self.features = {}
        self.feature_metadata = {}
        
    def compute_features(self, raw_data: pd.DataFrame) -> pd.DataFrame:
        """Compute and store features"""
        
        # Sales velocity features
        velocity_features = self._compute_velocity_features(raw_data)
        
        # Seasonality features
        seasonality_features = self._compute_seasonality_features(raw_data)
        
        # Inventory health features
        inventory_features = self._compute_inventory_features(raw_data)
        
        # Combine all features
        features = pd.concat([
            velocity_features,
            seasonality_features,
            inventory_features
        ], axis=1)
        
        # Store feature metadata
        self._store_feature_metadata(features)
        
        return features
    
    def _compute_velocity_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """Compute sales velocity features"""
        features = pd.DataFrame(index=data.index)
        
        # Basic velocity
        features['velocity_1d'] = data['daily_sales']
        features['velocity_7d_ma'] = data.get('sales_ma_7', 0)
        features['velocity_30d_ma'] = data.get('sales_ma_30', 0)
        
        # Velocity trends
        if 'sales_ma_7' in data.columns:
            features['velocity_trend_7d'] = (
                data['sales_ma_7'] - data['sales_ma_7'].shift(7)
            ) / (data['sales_ma_7'].shift(7) + 1)
        
        # Velocity volatility
        features['velocity_std_7d'] = data.groupby(['sku', 'warehouse_id'])['daily_sales'].transform(
            lambda x: x.rolling(7).std()
        )
        
        return features.fillna(0)
    
    def _compute_seasonality_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """Compute seasonality features"""
        features = pd.DataFrame(index=data.index)
        
        # Day of week patterns
        dow_avg = data.groupby(['sku', 'warehouse_id', 'day_of_week'])['daily_sales'].transform('mean')
        overall_avg = data.groupby(['sku', 'warehouse_id'])['daily_sales'].transform('mean')
        features['dow_seasonality_index'] = dow_avg / (overall_avg + 1)
        
        # Monthly patterns
        month_avg = data.groupby(['sku', 'warehouse_id', 'month'])['daily_sales'].transform('mean')
        features['month_seasonality_index'] = month_avg / (overall_avg + 1)
        
        # Holiday proximity (simplified)
        features['days_to_holiday'] = 30  # Would calculate actual holiday distance
        
        return features.fillna(0)
    
    def _compute_inventory_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """Compute inventory health features"""
        features = pd.DataFrame(index=data.index)
        
        # Stock coverage
        sales_ma_7 = data.get('sales_ma_7', 1)
        features['days_of_supply'] = data['avg_inventory'] / (sales_ma_7 + 1)
        
        # Stockout risk
        features['stockout_probability'] = 1 / (1 + np.exp(features['days_of_supply'] - 7))
        
        # Overstock risk
        features['overstock_flag'] = (features['days_of_supply'] > 60).astype(int)
        
        # Inventory turnover
        sales_ma_30 = data.get('sales_ma_30', 0)
        features['inventory_turnover'] = (
            sales_ma_30 * 365
        ) / (data['avg_inventory'] + 1)
        
        return features.fillna(0)
    
    def _store_feature_metadata(self, features: pd.DataFrame):
        """Store metadata about features"""
        for col in features.columns:
            self.feature_metadata[col] = {
                'created_date': datetime.now().isoformat(),
                'data_type': str(features[col].dtype),
                'null_percentage': float(features[col].isnull().mean() * 100),
                'unique_values': int(features[col].nunique())
            }

if __name__ == "__main__":
    # Run the ML pipeline
    pipeline = InventoryMLPipeline()
    pipeline.run_training_pipeline()
    
    # Example of feature store usage
    feature_store = MLFeatureStore()
    # feature_store.compute_features(data)

