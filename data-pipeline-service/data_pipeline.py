"""
ETL Pipeline for Inventory Data Processing
Demonstrates: Kafka consumption, data transformation, feature engineering, basic analytics
"""

import json
import logging
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
import psycopg2
from kafka import KafkaConsumer, KafkaProducer
from kafka.errors import KafkaError
import redis
from dataclasses import dataclass
import asyncio
from concurrent.futures import ThreadPoolExecutor
import pyarrow.parquet as pq
import pyarrow as pa
import os

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class InventoryEvent:
    event_id: str
    sku: str
    warehouse_id: str
    quantity_change: int
    timestamp: datetime
    event_type: str
    
@dataclass
class ProcessedMetrics:
    sku: str
    warehouse_id: str
    velocity_7d: float
    velocity_30d: float
    volatility: float
    trend: float
    seasonality_index: float
    stockout_risk: float  # Basic statistical calculation, not ML
    reorder_recommendation: int

class InventoryETLPipeline:
    """
    Real-time ETL pipeline that:
    1. Consumes events from Kafka
    2. Performs data transformation
    3. Calculates basic analytics (velocity, trends, volatility)
    4. Calculates business metrics
    5. Outputs to data warehouse and cache
    """
    
    def __init__(self):
        # Kafka setup
        kafka_bootstrap = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092').split(',')
        self.consumer = KafkaConsumer(
            'inventory-events',
            bootstrap_servers=kafka_bootstrap,
            auto_offset_reset='latest',
            value_deserializer=lambda m: json.loads(m.decode('utf-8')),
            group_id='etl-pipeline-group',
            consumer_timeout_ms=1000
        )
        
        self.producer = KafkaProducer(
            bootstrap_servers=kafka_bootstrap,
            value_serializer=lambda v: json.dumps(v).encode('utf-8')
        )
        
        # Database connections
        self.pg_conn = psycopg2.connect(
            host=os.getenv('POSTGRES_HOST', 'localhost'),
            database=os.getenv('POSTGRES_DB', 'inventory'),
            user=os.getenv('POSTGRES_USER', 'inventory_user'),
            password=os.getenv('POSTGRES_PASSWORD', 'inventory_pass'),
            port=os.getenv('POSTGRES_PORT', '5432')
        )
        
        redis_host = os.getenv('REDIS_HOST', 'localhost')
        redis_port = int(os.getenv('REDIS_PORT', '6379'))
        redis_password = os.getenv('REDIS_PASSWORD', '')
        if redis_password:
            self.redis_client = redis.Redis(
                host=redis_host, 
                port=redis_port, 
                password=redis_password,
                decode_responses=True
            )
        else:
            self.redis_client = redis.Redis(
                host=redis_host, 
                port=redis_port, 
                decode_responses=True
            )
        
        # Batch processing setup
        self.batch_size = int(os.getenv('BATCH_SIZE', '100'))
        self.event_buffer = []
        self.executor = ThreadPoolExecutor(max_workers=4)
        
        # Data output directory
        self.data_dir = os.getenv('DATA_DIR', './data')
        os.makedirs(self.data_dir, exist_ok=True)
        
    async def run(self):
        """Main ETL loop"""
        logger.info("Starting ETL Pipeline...")
        
        try:
            for message in self.consumer:
                try:
                    event = self._parse_event(message.value)
                    self.event_buffer.append(event)
                    
                    # Process in batches for efficiency
                    if len(self.event_buffer) >= self.batch_size:
                        await self._process_batch(self.event_buffer)
                        self.event_buffer = []
                except Exception as e:
                    logger.error(f"Error processing message: {e}", exc_info=True)
                    
        except KeyboardInterrupt:
            logger.info("Shutting down ETL pipeline...")
        except Exception as e:
            logger.error(f"Error in ETL pipeline: {e}", exc_info=True)
        finally:
            # Process remaining events
            if self.event_buffer:
                await self._process_batch(self.event_buffer)
            self._cleanup()
    
    def _parse_event(self, raw_event: dict) -> InventoryEvent:
        """Parse raw Kafka event into structured format"""
        timestamp_str = raw_event.get('timestamp', datetime.now().isoformat())
        if isinstance(timestamp_str, str):
            timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        else:
            timestamp = datetime.now()
            
        return InventoryEvent(
            event_id=raw_event.get('eventId', raw_event.get('id', '')),
            sku=raw_event.get('sku', ''),
            warehouse_id=raw_event.get('warehouse', raw_event.get('warehouseId', '')),
            quantity_change=raw_event.get('quantityChange', 0),
            timestamp=timestamp,
            event_type=raw_event.get('eventType', 'UNKNOWN')
        )
    
    async def _process_batch(self, events: List[InventoryEvent]):
        """Process a batch of events through the ETL pipeline"""
        logger.info(f"Processing batch of {len(events)} events")
        
        try:
            # Step 1: Data Extraction and Transformation
            df = self._events_to_dataframe(events)
            
            # Step 2: Feature Engineering (basic analytics)
            features_df = await self._engineer_features(df)
            
            # Step 3: Calculate Business Metrics (no ML, basic statistics)
            metrics = self._calculate_metrics(features_df)
            
            # Step 5: Load to Data Stores
            await self._load_results(metrics)
            
            # Step 6: Publish processed events
            self._publish_processed_events(metrics)
            
            logger.info(f"Batch processing complete. Processed {len(metrics)} items")
        except Exception as e:
            logger.error(f"Error processing batch: {e}", exc_info=True)
    
    def _events_to_dataframe(self, events: List[InventoryEvent]) -> pd.DataFrame:
        """Convert events to pandas DataFrame for processing"""
        data = [{
            'event_id': e.event_id,
            'sku': e.sku,
            'warehouse_id': e.warehouse_id,
            'quantity_change': e.quantity_change,
            'timestamp': e.timestamp,
            'event_type': e.event_type,
            'hour': e.timestamp.hour,
            'day_of_week': e.timestamp.weekday(),
            'is_weekend': e.timestamp.weekday() >= 5
        } for e in events]
        
        return pd.DataFrame(data)
    
    async def _engineer_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Feature engineering for basic analytics
        Demonstrates data transformation and aggregation
        """
        features = df.copy()
        
        # Initialize feature columns
        features['velocity_7d'] = 0.0
        features['velocity_30d'] = 0.0
        features['volatility'] = 0.0
        features['trend'] = 0.0
        features['seasonality_index'] = 1.0
        
        # Aggregate features by SKU/Warehouse
        grouped = df.groupby(['sku', 'warehouse_id'])
        for (sku, warehouse), group_df in grouped:
            try:
                # Get historical data for this SKU/warehouse
                hist_data = await self._get_historical_data(sku, warehouse)
                
                if hist_data is not None and len(hist_data) > 0:
                    # Calculate velocity (items sold per day)
                    velocity_7d = self._calculate_velocity(hist_data, days=7)
                    velocity_30d = self._calculate_velocity(hist_data, days=30)
                    
                    # Calculate volatility (standard deviation of daily sales)
                    volatility = self._calculate_volatility(hist_data)
                    
                    # Calculate trend (linear regression slope)
                    trend = self._calculate_trend(hist_data)
                    
                    # Seasonality index
                    seasonality = self._calculate_seasonality(hist_data)
                    
                    # Add features to dataframe
                    mask = (features['sku'] == sku) & (features['warehouse_id'] == warehouse)
                    features.loc[mask, 'velocity_7d'] = velocity_7d
                    features.loc[mask, 'velocity_30d'] = velocity_30d
                    features.loc[mask, 'volatility'] = volatility
                    features.loc[mask, 'trend'] = trend
                    features.loc[mask, 'seasonality_index'] = seasonality
            except Exception as e:
                logger.error(f"Error engineering features for {sku}:{warehouse}: {e}")
        
        # Fill missing values
        features = features.fillna(0)
        
        return features
    
    async def _get_historical_data(self, sku: str, warehouse_id: str) -> pd.DataFrame:
        """Fetch historical data from database"""
        query = """
        SELECT 
            date_trunc('day', timestamp) as date,
            SUM(CASE WHEN transaction_type = 'SALE' THEN ABS(quantity_change) ELSE 0 END) as daily_sales,
            COUNT(*) as transaction_count
        FROM inventory_transactions
        WHERE sku = %s AND warehouse_id = %s
            AND timestamp >= NOW() - INTERVAL '90 days'
        GROUP BY date
        ORDER BY date
        """
        
        try:
            with self.pg_conn.cursor() as cur:
                cur.execute(query, (sku, warehouse_id))
                columns = [desc[0] for desc in cur.description]
                data = cur.fetchall()
                
            if data:
                return pd.DataFrame(data, columns=columns)
        except Exception as e:
            logger.error(f"Error fetching historical data for {sku}:{warehouse_id}: {e}")
        
        return pd.DataFrame()
    
    def _calculate_velocity(self, hist_data: pd.DataFrame, days: int) -> float:
        """Calculate average daily velocity"""
        if len(hist_data) == 0:
            return 0.0
        recent_data = hist_data.tail(days)
        if len(recent_data) > 0 and 'daily_sales' in recent_data.columns:
            return float(recent_data['daily_sales'].mean())
        return 0.0
    
    def _calculate_volatility(self, hist_data: pd.DataFrame) -> float:
        """Calculate sales volatility"""
        if len(hist_data) > 1 and 'daily_sales' in hist_data.columns:
            return float(hist_data['daily_sales'].std())
        return 0.0
    
    def _calculate_trend(self, hist_data: pd.DataFrame) -> float:
        """Calculate trend using linear regression"""
        if len(hist_data) > 7 and 'daily_sales' in hist_data.columns:
            x = np.arange(len(hist_data))
            y = hist_data['daily_sales'].values
            slope, _ = np.polyfit(x, y, 1)
            return float(slope)
        return 0.0
    
    def _calculate_seasonality(self, hist_data: pd.DataFrame) -> float:
        """Calculate seasonality index"""
        if len(hist_data) > 30 and 'daily_sales' in hist_data.columns:
            # Simple seasonality: ratio of last 7 days to last 30 days
            recent_avg = hist_data.tail(7)['daily_sales'].mean()
            monthly_avg = hist_data.tail(30)['daily_sales'].mean()
            if monthly_avg > 0:
                return float(recent_avg / monthly_avg)
        return 1.0
    
    
    def _calculate_stockout_risk_basic(self, velocity_30d: float, volatility: float, trend: float, seasonality: float) -> float:
        """
        Calculate stockout risk score (0-1) using basic statistical heuristics
        Not using ML, just basic calculations based on velocity, volatility, trend, and seasonality
        """
        risk = 0.0
        
        # High velocity increases risk
        if velocity_30d > 50:
            risk += 0.3
        
        # High volatility increases risk
        if volatility > velocity_30d * 0.5:
            risk += 0.2
        
        # Negative trend increases risk
        if trend < 0:
            risk += 0.2
        
        # High seasonality increases risk
        if seasonality > 1.5:
            risk += 0.3
        
        return min(risk, 1.0)
    
    def _calculate_metrics(self, features_df: pd.DataFrame) -> List[ProcessedMetrics]:
        """Calculate final business metrics using basic analytics (no ML)"""
        metrics = []
        
        if len(features_df) == 0:
            return metrics
        
        for idx, row in features_df.iterrows():
            try:
                velocity_30d = float(row.get('velocity_30d', 0))
                volatility = float(row.get('volatility', 0))
                trend = float(row.get('trend', 0))
                seasonality = float(row.get('seasonality_index', 1.0))
                
                # Calculate stockout risk using basic heuristics (not ML)
                stockout_risk = self._calculate_stockout_risk_basic(velocity_30d, volatility, trend, seasonality)
                
                # Calculate reorder recommendation
                reorder_qty = self._calculate_reorder_quantity(
                    velocity_30d,
                    volatility,
                    stockout_risk
                )
                
                metric = ProcessedMetrics(
                    sku=row['sku'],
                    warehouse_id=row['warehouse_id'],
                    velocity_7d=float(row.get('velocity_7d', 0)),
                    velocity_30d=velocity_30d,
                    volatility=volatility,
                    trend=trend,
                    seasonality_index=seasonality,
                    stockout_risk=stockout_risk,
                    reorder_recommendation=reorder_qty
                )
                metrics.append(metric)
            except Exception as e:
                logger.error(f"Error calculating metrics for row {idx}: {e}")
        
        return metrics
    
    def _calculate_reorder_quantity(self, velocity: float, volatility: float, risk: float) -> int:
        """Calculate optimal reorder quantity"""
        # Lead time in days
        lead_time = 7
        
        # Safety stock calculation
        safety_factor = 1.5 + risk  # Increase safety stock based on risk
        safety_stock = volatility * np.sqrt(lead_time) * safety_factor
        
        # Reorder quantity = (velocity * lead_time) + safety_stock
        reorder_qty = (velocity * lead_time) + safety_stock
        
        return max(int(reorder_qty), 0)
    
    async def _load_results(self, metrics: List[ProcessedMetrics]):
        """Load processed results to data stores"""
        if len(metrics) == 0:
            return
            
        try:
            # Create analytics schema if it doesn't exist
            with self.pg_conn.cursor() as cur:
                cur.execute("""
                    CREATE SCHEMA IF NOT EXISTS analytics;
                    CREATE TABLE IF NOT EXISTS analytics.processed_metrics (
                        id BIGSERIAL PRIMARY KEY,
                        sku VARCHAR(255) NOT NULL,
                        warehouse_id VARCHAR(255) NOT NULL,
                        velocity_7d DOUBLE PRECISION,
                        velocity_30d DOUBLE PRECISION,
                        volatility DOUBLE PRECISION,
                        trend DOUBLE PRECISION,
                        seasonality_index DOUBLE PRECISION,
                        stockout_risk DOUBLE PRECISION,
                        reorder_recommendation INTEGER,
                        processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                    CREATE INDEX IF NOT EXISTS idx_metrics_sku_wh ON analytics.processed_metrics(sku, warehouse_id);
                    CREATE INDEX IF NOT EXISTS idx_metrics_processed_at ON analytics.processed_metrics(processed_at);
                """)
                self.pg_conn.commit()
        except Exception as e:
            logger.error(f"Error creating analytics schema: {e}")
            self.pg_conn.rollback()
        
        # Batch insert to PostgreSQL
        insert_query = """
        INSERT INTO analytics.processed_metrics 
        (sku, warehouse_id, velocity_7d, velocity_30d, volatility, 
         trend, seasonality_index, stockout_risk, 
         reorder_recommendation, processed_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
        ON CONFLICT DO NOTHING
        """
        
        try:
            with self.pg_conn.cursor() as cur:
                for metric in metrics:
                    cur.execute(insert_query, (
                        metric.sku, metric.warehouse_id, metric.velocity_7d,
                        metric.velocity_30d, metric.volatility, metric.trend,
                        metric.seasonality_index,
                        metric.stockout_risk, metric.reorder_recommendation
                    ))
                self.pg_conn.commit()
        except Exception as e:
            logger.error(f"Error inserting metrics: {e}")
            self.pg_conn.rollback()
        
        # Update Redis cache with latest metrics
        try:
            for metric in metrics:
                cache_key = f"metrics:{metric.sku}:{metric.warehouse_id}"
                cache_data = {
                    'velocity_7d': str(metric.velocity_7d),
                    'velocity_30d': str(metric.velocity_30d),
                    'stockout_risk': str(metric.stockout_risk),
                    'last_updated': datetime.now().isoformat()
                }
                self.redis_client.hset(cache_key, mapping=cache_data)
                self.redis_client.expire(cache_key, 3600)  # 1 hour TTL
        except Exception as e:
            logger.error(f"Error updating Redis cache: {e}")
        
        # Write to Parquet for data lake (batch processing)
        try:
            if len(metrics) > 0:
                df = pd.DataFrame([m.__dict__ for m in metrics])
                table = pa.Table.from_pandas(df)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_path = os.path.join(
                    self.data_dir, 
                    f'processed_metrics_{timestamp}.parquet'
                )
                pq.write_table(table, output_path)
                logger.info(f"Wrote metrics to {output_path}")
        except Exception as e:
            logger.error(f"Error writing Parquet file: {e}")
    
    def _publish_processed_events(self, metrics: List[ProcessedMetrics]):
        """Publish processed metrics to Kafka for downstream consumers"""
        try:
            for metric in metrics:
                # Publish high stockout risks (basic statistical threshold, not ML)
                if metric.stockout_risk > 0.7:
                    risk_event = {
                        'type': 'HIGH_STOCKOUT_RISK',
                        'sku': metric.sku,
                        'warehouse_id': metric.warehouse_id,
                        'risk_score': metric.stockout_risk,
                        'recommended_reorder': metric.reorder_recommendation,
                        'velocity_30d': metric.velocity_30d,
                        'volatility': metric.volatility,
                        'timestamp': datetime.now().isoformat()
                    }
                    self.producer.send('inventory-alerts', risk_event)
        except Exception as e:
            logger.error(f"Error publishing processed events: {e}")
    
    def _cleanup(self):
        """Cleanup connections"""
        try:
            self.consumer.close()
            self.producer.close()
            self.pg_conn.close()
            self.executor.shutdown(wait=True)
            logger.info("ETL pipeline cleanup complete")
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")

if __name__ == "__main__":
    pipeline = InventoryETLPipeline()
    asyncio.run(pipeline.run())

