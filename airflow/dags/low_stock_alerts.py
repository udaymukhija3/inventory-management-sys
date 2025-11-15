from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook
from airflow.models import Variable
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
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
    'execution_timeout': timedelta(minutes=30)
}

dag = DAG(
    'low_stock_alerts',
    default_args=default_args,
    description='Daily check for low stock items and generate alerts',
    schedule_interval='0 6 * * *',  # Run at 6 AM daily
    catchup=False,
    max_active_runs=1,
    tags=['inventory', 'alerts', 'low-stock']
)

def check_low_stock_items(**context):
    """Check for items that need reordering"""
    logger.info("Checking for low stock items")
    
    pg_hook = PostgresHook(postgres_conn_id='inventory_db')
    
    # Find items that need reorder
    low_stock_query = """
    SELECT 
        i.sku,
        i.warehouse_id,
        i.quantity_on_hand,
        i.quantity_reserved,
        (i.quantity_on_hand - i.quantity_reserved) as available_quantity,
        i.reorder_point,
        i.reorder_quantity,
        i.inventory_status,
        i.unit_cost,
        CASE 
            WHEN i.quantity_on_hand = 0 THEN 'URGENT'
            WHEN (i.quantity_on_hand - i.quantity_reserved) <= i.reorder_point THEN 'HIGH'
            ELSE 'NORMAL'
        END as priority
    FROM inventory_items i
    WHERE i.inventory_status != 'DISCONTINUED'
        AND (i.quantity_on_hand = 0 
             OR (i.quantity_on_hand - i.quantity_reserved) <= i.reorder_point)
    ORDER BY 
        CASE priority
            WHEN 'URGENT' THEN 1
            WHEN 'HIGH' THEN 2
            ELSE 3
        END,
        i.warehouse_id, i.sku
    """
    
    low_stock_items = pg_hook.get_records(low_stock_query)
    
    urgent_count = sum(1 for item in low_stock_items if item[9] == 'URGENT')
    high_priority_count = sum(1 for item in low_stock_items if item[9] == 'HIGH')
    
    logger.info(f"Found {len(low_stock_items)} low stock items: {urgent_count} urgent, {high_priority_count} high priority")
    
    context['task_instance'].xcom_push(key='low_stock_count', value=len(low_stock_items))
    context['task_instance'].xcom_push(key='urgent_count', value=urgent_count)
    context['task_instance'].xcom_push(key='high_priority_count', value=high_priority_count)
    context['task_instance'].xcom_push(key='low_stock_items', value=low_stock_items)
    
    return low_stock_items

def generate_alert_summary(**context):
    """Generate alert summary for notification"""
    logger.info("Generating alert summary")
    
    low_stock_items = context['task_instance'].xcom_pull(task_ids='check_low_stock_items', key='low_stock_items')
    urgent_count = context['task_instance'].xcom_pull(task_ids='check_low_stock_items', key='urgent_count')
    high_priority_count = context['task_instance'].xcom_pull(task_ids='check_low_stock_items', key='high_priority_count')
    
    summary = {
        'date': datetime.now().date().isoformat(),
        'total_low_stock_items': len(low_stock_items),
        'urgent_count': urgent_count,
        'high_priority_count': high_priority_count,
        'items': []
    }
    
    # Add top 10 items for summary
    for item in low_stock_items[:10]:
        summary['items'].append({
            'sku': item[0],
            'warehouse_id': item[1],
            'quantity_on_hand': item[2],
            'available_quantity': item[4],
            'reorder_point': item[5],
            'priority': item[9]
        })
    
    logger.info(f"Alert summary generated: {urgent_count} urgent items, {high_priority_count} high priority items")
    
    # In production, this would send email/Slack notification
    # For now, just log it
    if urgent_count > 0:
        logger.warning(f"URGENT: {urgent_count} items are out of stock!")
    
    context['task_instance'].xcom_push(key='alert_summary', value=summary)
    return summary

# Define tasks
check_low_stock_task = PythonOperator(
    task_id='check_low_stock_items',
    python_callable=check_low_stock_items,
    dag=dag
)

generate_alert_task = PythonOperator(
    task_id='generate_alert_summary',
    python_callable=generate_alert_summary,
    dag=dag
)

# Define task dependencies
check_low_stock_task >> generate_alert_task

