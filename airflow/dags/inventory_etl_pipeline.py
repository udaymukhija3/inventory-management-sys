from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.postgres.operators.postgres import PostgresOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook
from airflow.models import Variable
from datetime import datetime, timedelta
import pandas as pd
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
    'execution_timeout': timedelta(hours=2)
}

dag = DAG(
    'inventory_etl_pipeline',
    default_args=default_args,
    description='Daily ETL pipeline for inventory data processing and analytics',
    schedule_interval='0 2 * * *',  # Run at 2 AM daily
    catchup=False,
    max_active_runs=1,
    tags=['inventory', 'etl', 'analytics']
)

def extract_inventory_data(**context):
    """Extract current inventory data from PostgreSQL"""
    logger.info("Starting inventory data extraction")
    
    pg_hook = PostgresHook(postgres_conn_id='inventory_db')
    
    # Query for current inventory levels and recent transactions
    inventory_query = """
    WITH inventory_summary AS (
        SELECT 
            i.sku,
            i.warehouse_id,
            i.quantity_on_hand,
            i.quantity_reserved,
            i.reorder_point,
            i.reorder_quantity,
            i.unit_cost,
            i.inventory_status as status,
            i.last_reorder_date,
            (i.quantity_on_hand * COALESCE(i.unit_cost, 0)) as inventory_value
        FROM inventory_items i
        WHERE i.inventory_status != 'DISCONTINUED'
    ),
    transaction_summary AS (
        SELECT 
            t.sku,
            t.warehouse_id,
            COUNT(CASE WHEN t.transaction_type = 'SALE' THEN 1 END) as sales_count_30d,
            SUM(CASE WHEN t.transaction_type = 'SALE' THEN ABS(t.quantity_change) ELSE 0 END) as total_sales_30d,
            AVG(CASE WHEN t.transaction_type = 'SALE' THEN ABS(t.quantity_change) END) as avg_sale_quantity,
            STDDEV(CASE WHEN t.transaction_type = 'SALE' THEN ABS(t.quantity_change) END) as stddev_sale_quantity,
            MAX(t.timestamp) as last_transaction_date
        FROM inventory_transactions t
        WHERE t.timestamp >= CURRENT_DATE - INTERVAL '30 days'
        GROUP BY t.sku, t.warehouse_id
    )
    SELECT 
        i.*,
        COALESCE(t.sales_count_30d, 0) as sales_count_30d,
        COALESCE(t.total_sales_30d, 0) as total_sales_30d,
        COALESCE(t.avg_sale_quantity, 0) as avg_sale_quantity,
        COALESCE(t.stddev_sale_quantity, 0) as stddev_sale_quantity,
        t.last_transaction_date,
        CASE 
            WHEN i.quantity_on_hand = 0 THEN 'STOCKOUT'
            WHEN i.quantity_on_hand - i.quantity_reserved <= i.reorder_point THEN 'NEEDS_REORDER'
            WHEN t.total_sales_30d = 0 THEN 'NO_MOVEMENT'
            ELSE 'NORMAL'
        END as action_required,
        CASE
            WHEN t.total_sales_30d > 0 THEN (t.total_sales_30d::float / 30)
            ELSE 0
        END as daily_velocity
    FROM inventory_summary i
    LEFT JOIN transaction_summary t 
        ON i.sku = t.sku AND i.warehouse_id = t.warehouse_id
    """
    
    df = pg_hook.get_pandas_df(inventory_query)
    logger.info(f"Extracted {len(df)} inventory records")
    
    # Save to temporary location
    output_path = '/tmp/inventory_data.parquet'
    df.to_parquet(output_path, index=False)
    
    # Push summary statistics to XCom
    context['task_instance'].xcom_push(key='total_skus', value=df['sku'].nunique())
    context['task_instance'].xcom_push(key='total_warehouses', value=df['warehouse_id'].nunique())
    context['task_instance'].xcom_push(key='stockout_count', value=len(df[df['action_required'] == 'STOCKOUT']))
    context['task_instance'].xcom_push(key='reorder_count', value=len(df[df['action_required'] == 'NEEDS_REORDER']))
    context['task_instance'].xcom_push(key='data_path', value=output_path)
    
    return output_path

def transform_and_load(**context):
    """Transform and load data into analytics tables"""
    logger.info("Starting data transformation and loading")
    
    data_path = context['task_instance'].xcom_pull(task_ids='extract_inventory_data', key='data_path')
    df = pd.read_parquet(data_path)
    
    pg_hook = PostgresHook(postgres_conn_id='inventory_db')
    
    # Calculate aggregated metrics
    df['inventory_value'] = df['quantity_on_hand'] * df['unit_cost'].fillna(0)
    df['velocity_score'] = df['daily_velocity']
    
    # Create daily inventory snapshot
    snapshot_date = datetime.now().date()
    
    # Insert into analytics table (create table if not exists)
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS inventory_daily_snapshots (
        id SERIAL PRIMARY KEY,
        snapshot_date DATE NOT NULL,
        sku VARCHAR(50) NOT NULL,
        warehouse_id VARCHAR(20) NOT NULL,
        quantity_on_hand INTEGER,
        quantity_reserved INTEGER,
        available_quantity INTEGER,
        reorder_point INTEGER,
        inventory_status VARCHAR(20),
        inventory_value DECIMAL(10,2),
        daily_velocity DECIMAL(10,2),
        action_required VARCHAR(20),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(snapshot_date, sku, warehouse_id)
    );
    CREATE INDEX IF NOT EXISTS idx_snapshot_date ON inventory_daily_snapshots(snapshot_date);
    CREATE INDEX IF NOT EXISTS idx_snapshot_sku_warehouse ON inventory_daily_snapshots(sku, warehouse_id);
    """
    
    pg_hook.run(create_table_sql)
    
    # Insert snapshot data
    for _, row in df.iterrows():
        insert_sql = """
        INSERT INTO inventory_daily_snapshots 
        (snapshot_date, sku, warehouse_id, quantity_on_hand, quantity_reserved, 
         available_quantity, reorder_point, inventory_status, inventory_value, 
         daily_velocity, action_required)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (snapshot_date, sku, warehouse_id) 
        DO UPDATE SET
            quantity_on_hand = EXCLUDED.quantity_on_hand,
            quantity_reserved = EXCLUDED.quantity_reserved,
            available_quantity = EXCLUDED.available_quantity,
            inventory_status = EXCLUDED.inventory_status,
            inventory_value = EXCLUDED.inventory_value,
            daily_velocity = EXCLUDED.daily_velocity,
            action_required = EXCLUDED.action_required;
        """
        
        pg_hook.run(insert_sql, parameters=(
            snapshot_date, row['sku'], row['warehouse_id'], row['quantity_on_hand'],
            row['quantity_reserved'], row['quantity_on_hand'] - row['quantity_reserved'],
            row['reorder_point'], row['status'], row['inventory_value'],
            row['daily_velocity'], row['action_required']
        ))
    
    logger.info(f"Loaded {len(df)} records into daily snapshot")
    
    context['task_instance'].xcom_push(key='records_loaded', value=len(df))
    return len(df)

def generate_aggregated_metrics(**context):
    """Generate aggregated metrics from daily snapshot"""
    logger.info("Generating aggregated metrics")
    
    pg_hook = PostgresHook(postgres_conn_id='inventory_db')
    
    # Calculate warehouse-level metrics
    warehouse_metrics_query = """
    SELECT 
        warehouse_id,
        COUNT(DISTINCT sku) as total_skus,
        SUM(CASE WHEN action_required = 'STOCKOUT' THEN 1 ELSE 0 END) as stockout_count,
        SUM(CASE WHEN action_required = 'NEEDS_REORDER' THEN 1 ELSE 0 END) as reorder_count,
        SUM(inventory_value) as total_inventory_value,
        AVG(daily_velocity) as avg_velocity
    FROM inventory_daily_snapshots
    WHERE snapshot_date = CURRENT_DATE
    GROUP BY warehouse_id
    """
    
    metrics_df = pg_hook.get_pandas_df(warehouse_metrics_query)
    logger.info(f"Generated metrics for {len(metrics_df)} warehouses")
    
    context['task_instance'].xcom_push(key='warehouse_metrics_count', value=len(metrics_df))
    return len(metrics_df)

def data_quality_check(**context):
    """Perform data quality checks"""
    logger.info("Running data quality checks")
    
    pg_hook = PostgresHook(postgres_conn_id='inventory_db')
    
    quality_check_sql = """
    SELECT 
        COUNT(CASE WHEN quantity_on_hand < 0 THEN 1 END) as negative_inventory,
        COUNT(CASE WHEN quantity_reserved > quantity_on_hand THEN 1 END) as over_reserved,
        COUNT(CASE WHEN reorder_point < 0 THEN 1 END) as negative_reorder_point,
        COUNT(CASE WHEN sku IS NULL OR sku = '' THEN 1 END) as missing_sku,
        COUNT(CASE WHEN warehouse_id IS NULL OR warehouse_id = '' THEN 1 END) as missing_warehouse_id
    FROM inventory_items
    WHERE inventory_status != 'DISCONTINUED';
    """
    
    result = pg_hook.get_first(quality_check_sql)
    
    issues = []
    if result[0] > 0:
        issues.append(f"Negative inventory: {result[0]}")
    if result[1] > 0:
        issues.append(f"Over-reserved items: {result[1]}")
    if result[2] > 0:
        issues.append(f"Negative reorder points: {result[2]}")
    if result[3] > 0:
        issues.append(f"Missing SKUs: {result[3]}")
    if result[4] > 0:
        issues.append(f"Missing warehouse IDs: {result[4]}")
    
    if issues:
        logger.warning(f"Data quality issues found: {', '.join(issues)}")
    else:
        logger.info("No data quality issues found")
    
    context['task_instance'].xcom_push(key='quality_issues', value=issues)
    return len(issues)

# Define tasks
extract_data_task = PythonOperator(
    task_id='extract_inventory_data',
    python_callable=extract_inventory_data,
    dag=dag
)

transform_load_task = PythonOperator(
    task_id='transform_and_load',
    python_callable=transform_and_load,
    dag=dag
)

generate_metrics_task = PythonOperator(
    task_id='generate_aggregated_metrics',
    python_callable=generate_aggregated_metrics,
    dag=dag
)

data_quality_check_task = PostgresOperator(
    task_id='data_quality_check',
    postgres_conn_id='inventory_db',
    sql="""
        -- Data quality validation queries
        SELECT 
            COUNT(CASE WHEN quantity_on_hand < 0 THEN 1 END) as negative_inventory,
            COUNT(CASE WHEN quantity_reserved > quantity_on_hand THEN 1 END) as over_reserved,
            COUNT(CASE WHEN reorder_point < 0 THEN 1 END) as negative_reorder_point
        FROM inventory_items
        WHERE inventory_status != 'DISCONTINUED';
    """,
    dag=dag
)

# Define task dependencies
extract_data_task >> [transform_load_task, data_quality_check_task]
transform_load_task >> generate_metrics_task

