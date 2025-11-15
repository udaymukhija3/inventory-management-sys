from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

default_args = {
    'owner': 'inventory-team',
    'depends_on_past': False,
    'start_date': datetime(2024, 1, 1),
    'email': ['inventory-alerts@company.com'],
    'email_on_failure': True,
    'email_on_retry': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
    'execution_timeout': timedelta(hours=1)
}

dag = DAG(
    'transaction_aggregation',
    default_args=default_args,
    description='Daily and weekly aggregation of inventory transactions',
    schedule_interval='0 3 * * *',  # Run at 3 AM daily
    catchup=False,
    max_active_runs=1,
    tags=['inventory', 'transactions', 'aggregation']
)

def aggregate_daily_transactions(**context):
    """Aggregate transactions by day"""
    logger.info("Aggregating daily transactions")
    
    pg_hook = PostgresHook(postgres_conn_id='inventory_db')
    
    # Create aggregation table if not exists
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS transaction_daily_aggregates (
        id SERIAL PRIMARY KEY,
        aggregation_date DATE NOT NULL,
        sku VARCHAR(50) NOT NULL,
        warehouse_id VARCHAR(20) NOT NULL,
        transaction_type VARCHAR(20) NOT NULL,
        total_quantity INTEGER,
        transaction_count INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(aggregation_date, sku, warehouse_id, transaction_type)
    );
    CREATE INDEX IF NOT EXISTS idx_agg_date ON transaction_daily_aggregates(aggregation_date);
    CREATE INDEX IF NOT EXISTS idx_agg_sku_warehouse ON transaction_daily_aggregates(sku, warehouse_id);
    """
    
    pg_hook.run(create_table_sql)
    
    # Aggregate yesterday's transactions
    yesterday = (datetime.now() - timedelta(days=1)).date()
    
    aggregation_query = """
    INSERT INTO transaction_daily_aggregates 
    (aggregation_date, sku, warehouse_id, transaction_type, total_quantity, transaction_count)
    SELECT 
        DATE(timestamp) as aggregation_date,
        sku,
        warehouse_id,
        transaction_type,
        SUM(ABS(quantity_change)) as total_quantity,
        COUNT(*) as transaction_count
    FROM inventory_transactions
    WHERE DATE(timestamp) = %s
    GROUP BY DATE(timestamp), sku, warehouse_id, transaction_type
    ON CONFLICT (aggregation_date, sku, warehouse_id, transaction_type) 
    DO UPDATE SET
        total_quantity = EXCLUDED.total_quantity,
        transaction_count = EXCLUDED.transaction_count;
    """
    
    pg_hook.run(aggregation_query, parameters=(yesterday,))
    
    logger.info(f"Daily aggregation completed for {yesterday}")
    
    context['task_instance'].xcom_push(key='aggregation_date', value=yesterday.isoformat())
    return yesterday.isoformat()

def aggregate_weekly_transactions(**context):
    """Aggregate transactions by week"""
    logger.info("Aggregating weekly transactions")
    
    pg_hook = PostgresHook(postgres_conn_id='inventory_db')
    
    # Create weekly aggregation table if not exists
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS transaction_weekly_aggregates (
        id SERIAL PRIMARY KEY,
        week_start_date DATE NOT NULL,
        sku VARCHAR(50) NOT NULL,
        warehouse_id VARCHAR(20) NOT NULL,
        transaction_type VARCHAR(20) NOT NULL,
        total_quantity INTEGER,
        transaction_count INTEGER,
        avg_daily_quantity DECIMAL(10,2),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(week_start_date, sku, warehouse_id, transaction_type)
    );
    CREATE INDEX IF NOT EXISTS idx_week_start ON transaction_weekly_aggregates(week_start_date);
    CREATE INDEX IF NOT EXISTS idx_week_sku_warehouse ON transaction_weekly_aggregates(sku, warehouse_id);
    """
    
    pg_hook.run(create_table_sql)
    
    # Aggregate last week's transactions (only on Monday)
    if datetime.now().weekday() == 0:  # Monday
        last_week_start = (datetime.now() - timedelta(days=7)).replace(hour=0, minute=0, second=0, microsecond=0)
        last_week_start = last_week_start - timedelta(days=last_week_start.weekday())
        last_week_end = last_week_start + timedelta(days=6)
        
        aggregation_query = """
        INSERT INTO transaction_weekly_aggregates 
        (week_start_date, sku, warehouse_id, transaction_type, total_quantity, transaction_count, avg_daily_quantity)
        SELECT 
            %s as week_start_date,
            sku,
            warehouse_id,
            transaction_type,
            SUM(ABS(quantity_change)) as total_quantity,
            COUNT(*) as transaction_count,
            AVG(daily_total) as avg_daily_quantity
        FROM (
            SELECT 
                sku,
                warehouse_id,
                transaction_type,
                DATE(timestamp) as transaction_date,
                SUM(ABS(quantity_change)) as daily_total
            FROM inventory_transactions
            WHERE DATE(timestamp) >= %s AND DATE(timestamp) <= %s
            GROUP BY sku, warehouse_id, transaction_type, DATE(timestamp)
        ) daily_agg
        GROUP BY sku, warehouse_id, transaction_type
        ON CONFLICT (week_start_date, sku, warehouse_id, transaction_type) 
        DO UPDATE SET
            total_quantity = EXCLUDED.total_quantity,
            transaction_count = EXCLUDED.transaction_count,
            avg_daily_quantity = EXCLUDED.avg_daily_quantity;
        """
        
        pg_hook.run(aggregation_query, parameters=(last_week_start.date(), last_week_start.date(), last_week_end.date()))
        
        logger.info(f"Weekly aggregation completed for week starting {last_week_start.date()}")
        context['task_instance'].xcom_push(key='week_start_date', value=last_week_start.date().isoformat())
        return last_week_start.date().isoformat()
    else:
        logger.info("Not a Monday, skipping weekly aggregation")
        return None

# Define tasks
daily_aggregation_task = PythonOperator(
    task_id='aggregate_daily_transactions',
    python_callable=aggregate_daily_transactions,
    dag=dag
)

weekly_aggregation_task = PythonOperator(
    task_id='aggregate_weekly_transactions',
    python_callable=aggregate_weekly_transactions,
    dag=dag
)

# Define task dependencies
daily_aggregation_task >> weekly_aggregation_task

