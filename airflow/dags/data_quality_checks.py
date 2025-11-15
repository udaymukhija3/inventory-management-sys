from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook
from airflow.providers.postgres.operators.postgres import PostgresOperator
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
    'data_quality_checks',
    default_args=default_args,
    description='Comprehensive data quality validation checks for inventory data',
    schedule_interval=timedelta(hours=12),  # Run twice daily
    catchup=False,
    max_active_runs=1,
    tags=['inventory', 'data-quality', 'validation']
)

def validate_inventory_data(**context):
    """Validate inventory data quality"""
    logger.info("Running inventory data quality checks")
    
    pg_hook = PostgresHook(postgres_conn_id='inventory_db')
    
    # Data quality validation queries
    quality_check_sql = """
    SELECT 
        COUNT(CASE WHEN quantity_on_hand < 0 THEN 1 END) as negative_inventory,
        COUNT(CASE WHEN quantity_reserved > quantity_on_hand THEN 1 END) as over_reserved,
        COUNT(CASE WHEN reorder_point < 0 THEN 1 END) as negative_reorder_point,
        COUNT(CASE WHEN reorder_quantity < 0 THEN 1 END) as negative_reorder_quantity,
        COUNT(CASE WHEN sku IS NULL OR sku = '' THEN 1 END) as missing_sku,
        COUNT(CASE WHEN warehouse_id IS NULL OR warehouse_id = '' THEN 1 END) as missing_warehouse_id,
        COUNT(CASE WHEN unit_cost < 0 THEN 1 END) as negative_unit_cost,
        COUNT(*) as total_records
    FROM inventory_items
    WHERE inventory_status != 'DISCONTINUED';
    """
    
    result = pg_hook.get_first(quality_check_sql)
    
    issues = []
    if result[0] > 0:
        issues.append(f"Negative inventory: {result[0]} records")
    if result[1] > 0:
        issues.append(f"Over-reserved items: {result[1]} records")
    if result[2] > 0:
        issues.append(f"Negative reorder points: {result[2]} records")
    if result[3] > 0:
        issues.append(f"Negative reorder quantities: {result[3]} records")
    if result[4] > 0:
        issues.append(f"Missing SKUs: {result[4]} records")
    if result[5] > 0:
        issues.append(f"Missing warehouse IDs: {result[5]} records")
    if result[6] > 0:
        issues.append(f"Negative unit costs: {result[6]} records")
    
    total_records = result[7]
    
    if issues:
        logger.warning(f"Data quality issues found: {', '.join(issues)}")
        logger.warning(f"Total records checked: {total_records}")
    else:
        logger.info("No data quality issues found")
        logger.info(f"Total records checked: {total_records}")
    
    # Push results to XCom
    context['task_instance'].xcom_push(key='quality_issues', value=issues)
    context['task_instance'].xcom_push(key='total_records', value=total_records)
    context['task_instance'].xcom_push(key='issue_count', value=len(issues))
    
    return {
        'issues': issues,
        'total_records': total_records,
        'issue_count': len(issues)
    }

def validate_transaction_data(**context):
    """Validate transaction data quality"""
    logger.info("Running transaction data quality checks")
    
    pg_hook = PostgresHook(postgres_conn_id='inventory_db')
    
    # Transaction data quality validation
    quality_check_sql = """
    SELECT 
        COUNT(CASE WHEN sku IS NULL OR sku = '' THEN 1 END) as missing_sku,
        COUNT(CASE WHEN warehouse_id IS NULL OR warehouse_id = '' THEN 1 END) as missing_warehouse_id,
        COUNT(CASE WHEN quantity_change = 0 THEN 1 END) as zero_quantity_change,
        COUNT(CASE WHEN transaction_type IS NULL OR transaction_type = '' THEN 1 END) as missing_transaction_type,
        COUNT(CASE WHEN timestamp IS NULL THEN 1 END) as missing_timestamp,
        COUNT(CASE WHEN timestamp > NOW() THEN 1 END) as future_timestamp,
        COUNT(*) as total_transactions
    FROM inventory_transactions
    WHERE timestamp >= NOW() - INTERVAL '30 days';
    """
    
    result = pg_hook.get_first(quality_check_sql)
    
    issues = []
    if result[0] > 0:
        issues.append(f"Missing SKUs: {result[0]} transactions")
    if result[1] > 0:
        issues.append(f"Missing warehouse IDs: {result[1]} transactions")
    if result[2] > 0:
        issues.append(f"Zero quantity changes: {result[2]} transactions")
    if result[3] > 0:
        issues.append(f"Missing transaction types: {result[3]} transactions")
    if result[4] > 0:
        issues.append(f"Missing timestamps: {result[4]} transactions")
    if result[5] > 0:
        issues.append(f"Future timestamps: {result[5]} transactions")
    
    total_transactions = result[6]
    
    if issues:
        logger.warning(f"Transaction data quality issues found: {', '.join(issues)}")
        logger.warning(f"Total transactions checked: {total_transactions}")
    else:
        logger.info("No transaction data quality issues found")
        logger.info(f"Total transactions checked: {total_transactions}")
    
    # Push results to XCom
    context['task_instance'].xcom_push(key='transaction_quality_issues', value=issues)
    context['task_instance'].xcom_push(key='total_transactions', value=total_transactions)
    context['task_instance'].xcom_push(key='transaction_issue_count', value=len(issues))
    
    return {
        'issues': issues,
        'total_transactions': total_transactions,
        'issue_count': len(issues)
    }

def validate_product_data(**context):
    """Validate product data quality"""
    logger.info("Running product data quality checks")
    
    pg_hook = PostgresHook(postgres_conn_id='inventory_db')
    
    # Product data quality validation
    quality_check_sql = """
    SELECT 
        COUNT(CASE WHEN sku IS NULL OR sku = '' THEN 1 END) as missing_sku,
        COUNT(CASE WHEN name IS NULL OR name = '' THEN 1 END) as missing_name,
        COUNT(CASE WHEN price < 0 THEN 1 END) as negative_price,
        COUNT(CASE WHEN category_id IS NULL THEN 1 END) as missing_category,
        COUNT(*) as total_products
    FROM products
    WHERE is_active = true;
    """
    
    result = pg_hook.get_first(quality_check_sql)
    
    issues = []
    if result[0] > 0:
        issues.append(f"Missing SKUs: {result[0]} products")
    if result[1] > 0:
        issues.append(f"Missing names: {result[1]} products")
    if result[2] > 0:
        issues.append(f"Negative prices: {result[2]} products")
    if result[3] > 0:
        issues.append(f"Missing categories: {result[3]} products")
    
    total_products = result[4]
    
    if issues:
        logger.warning(f"Product data quality issues found: {', '.join(issues)}")
        logger.warning(f"Total products checked: {total_products}")
    else:
        logger.info("No product data quality issues found")
        logger.info(f"Total products checked: {total_products}")
    
    # Push results to XCom
    context['task_instance'].xcom_push(key='product_quality_issues', value=issues)
    context['task_instance'].xcom_push(key='total_products', value=total_products)
    context['task_instance'].xcom_push(key='product_issue_count', value=len(issues))
    
    return {
        'issues': issues,
        'total_products': total_products,
        'issue_count': len(issues)
    }

def generate_quality_report(**context):
    """Generate data quality report"""
    logger.info("Generating data quality report")
    
    # Pull results from previous tasks
    inventory_issues = context['task_instance'].xcom_pull(task_ids='validate_inventory_data', key='quality_issues') or []
    inventory_total = context['task_instance'].xcom_pull(task_ids='validate_inventory_data', key='total_records') or 0
    inventory_issue_count = context['task_instance'].xcom_pull(task_ids='validate_inventory_data', key='issue_count') or 0
    
    transaction_issues = context['task_instance'].xcom_pull(task_ids='validate_transaction_data', key='transaction_quality_issues') or []
    transaction_total = context['task_instance'].xcom_pull(task_ids='validate_transaction_data', key='total_transactions') or 0
    transaction_issue_count = context['task_instance'].xcom_pull(task_ids='validate_transaction_data', key='transaction_issue_count') or 0
    
    product_issues = context['task_instance'].xcom_pull(task_ids='validate_product_data', key='product_quality_issues') or []
    product_total = context['task_instance'].xcom_pull(task_ids='validate_product_data', key='total_products') or 0
    product_issue_count = context['task_instance'].xcom_pull(task_ids='validate_product_data', key='product_issue_count') or 0
    
    # Generate report
    total_issues = inventory_issue_count + transaction_issue_count + product_issue_count
    
    report = {
        'timestamp': datetime.now().isoformat(),
        'inventory': {
            'total_records': inventory_total,
            'issue_count': inventory_issue_count,
            'issues': inventory_issues
        },
        'transactions': {
            'total_records': transaction_total,
            'issue_count': transaction_issue_count,
            'issues': transaction_issues
        },
        'products': {
            'total_records': product_total,
            'issue_count': product_issue_count,
            'issues': product_issues
        },
        'summary': {
            'total_issues': total_issues,
            'status': 'PASS' if total_issues == 0 else 'FAIL'
        }
    }
    
    logger.info(f"Data quality report generated: {report}")
    
    # Push report to XCom
    context['task_instance'].xcom_push(key='quality_report', value=report)
    
    return report

# Define tasks
validate_inventory_task = PythonOperator(
    task_id='validate_inventory_data',
    python_callable=validate_inventory_data,
    dag=dag
)

validate_transaction_task = PythonOperator(
    task_id='validate_transaction_data',
    python_callable=validate_transaction_data,
    dag=dag
)

validate_product_task = PythonOperator(
    task_id='validate_product_data',
    python_callable=validate_product_data,
    dag=dag
)

generate_report_task = PythonOperator(
    task_id='generate_quality_report',
    python_callable=generate_quality_report,
    dag=dag
)

# Define task dependencies
[validate_inventory_task, validate_transaction_task, validate_product_task] >> generate_report_task
