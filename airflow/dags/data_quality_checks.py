from datetime import datetime, timedelta
import logging

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook

logger = logging.getLogger(__name__)

default_args = {
    "owner": "inventory-team",
    "depends_on_past": False,
    "start_date": datetime(2024, 1, 1),
    "email": ["inventory-alerts@company.com"],
    "email_on_failure": True,
    "email_on_retry": False,
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
    "execution_timeout": timedelta(hours=1),
}

dag = DAG(
    "data_quality_checks",
    default_args=default_args,
    description="Validate inventory source data, analytics outputs, and reconciliation checks",
    schedule_interval=timedelta(hours=12),
    catchup=False,
    max_active_runs=1,
    tags=["inventory", "data-quality", "validation"],
)


def validate_inventory_core(**context):
    pg_hook = PostgresHook(postgres_conn_id="inventory_db")
    result = pg_hook.get_first(
        """
        SELECT
            COUNT(*) FILTER (WHERE quantity_on_hand < 0) AS negative_inventory,
            COUNT(*) FILTER (WHERE quantity_reserved > quantity_on_hand) AS over_reserved,
            COUNT(*) FILTER (WHERE sku IS NULL OR sku = '') AS missing_sku,
            COUNT(*) FILTER (WHERE warehouse_id IS NULL OR warehouse_id = '') AS missing_warehouse_id,
            COUNT(*) AS total_records
        FROM inventory_items
        """
    )

    issues = []
    if result[0] > 0:
        issues.append(f"negative_inventory={result[0]}")
    if result[1] > 0:
        issues.append(f"over_reserved={result[1]}")
    if result[2] > 0:
        issues.append(f"missing_sku={result[2]}")
    if result[3] > 0:
        issues.append(f"missing_warehouse_id={result[3]}")

    payload = {
        "check": "inventory_core",
        "status": "PASS" if not issues else "FAIL",
        "issues": issues,
        "total_records": result[4],
    }
    logger.info("Inventory core DQ result: %s", payload)
    context["task_instance"].xcom_push(key="inventory_core", value=payload)
    return payload


def validate_analytics_outputs(**context):
    pg_hook = PostgresHook(postgres_conn_id="inventory_db")
    result = pg_hook.get_first(
        """
        WITH duplicate_keys AS (
            SELECT COUNT(*) AS duplicate_groups
            FROM (
                SELECT sku, warehouse_id
                FROM analytics.current_metrics
                GROUP BY sku, warehouse_id
                HAVING COUNT(*) > 1
            ) duplicates
        )
        SELECT
            COUNT(*) FILTER (WHERE sku IS NULL OR sku = '' OR warehouse_id IS NULL OR warehouse_id = '') AS missing_business_keys,
            COUNT(*) FILTER (WHERE velocity_7d < 0 OR velocity_30d < 0 OR stockout_risk < 0 OR stockout_risk > 1) AS invalid_ranges,
            COALESCE((SELECT duplicate_groups FROM duplicate_keys), 0) AS duplicate_groups,
            COALESCE(EXTRACT(EPOCH FROM (NOW() - MAX(updated_at))), 0) AS freshness_seconds,
            COUNT(*) AS total_metrics
        FROM analytics.current_metrics
        """
    )

    issues = []
    if result[0] > 0:
        issues.append(f"missing_business_keys={result[0]}")
    if result[1] > 0:
        issues.append(f"invalid_ranges={result[1]}")
    if result[2] > 0:
        issues.append(f"duplicate_groups={result[2]}")
    if float(result[3] or 0) > 900:
        issues.append(f"stale_metrics_seconds={round(float(result[3]), 2)}")

    payload = {
        "check": "analytics_outputs",
        "status": "PASS" if not issues else "FAIL",
        "issues": issues,
        "total_metrics": result[4],
        "freshness_seconds": round(float(result[3] or 0), 2),
    }
    logger.info("Analytics output DQ result: %s", payload)
    context["task_instance"].xcom_push(key="analytics_outputs", value=payload)
    return payload


def validate_reconciliation(**context):
    pg_hook = PostgresHook(postgres_conn_id="inventory_db")
    rows = pg_hook.get_records(
        """
        SELECT
            cm.sku,
            cm.warehouse_id,
            cm.velocity_30d,
            COALESCE(txn.sales_30d / 30.0, 0) AS expected_velocity_30d
        FROM analytics.current_metrics cm
        LEFT JOIN (
            SELECT
                sku,
                warehouse_id,
                SUM(ABS(quantity_change)) AS sales_30d
            FROM inventory_transactions
            WHERE transaction_type = 'SALE'
              AND timestamp >= NOW() - INTERVAL '30 days'
            GROUP BY sku, warehouse_id
        ) txn
          ON txn.sku = cm.sku
         AND txn.warehouse_id = cm.warehouse_id
        """
    )

    mismatches = []
    for sku, warehouse_id, actual_velocity, expected_velocity in rows:
        actual_velocity = float(actual_velocity or 0)
        expected_velocity = float(expected_velocity or 0)
        if abs(actual_velocity - expected_velocity) > 0.01:
            mismatches.append(
                {
                    "sku": sku,
                    "warehouse_id": warehouse_id,
                    "actual_velocity_30d": round(actual_velocity, 4),
                    "expected_velocity_30d": round(expected_velocity, 4),
                }
            )

    invalid_event_count = pg_hook.get_first(
        """
        SELECT COUNT(*)
        FROM analytics.invalid_inventory_events
        WHERE recorded_at >= NOW() - INTERVAL '12 hours'
        """
    )[0]

    issues = []
    if mismatches:
        issues.append(f"reconciliation_mismatches={len(mismatches)}")
    if invalid_event_count > 0:
        issues.append(f"invalid_events_last_12h={invalid_event_count}")

    payload = {
        "check": "reconciliation",
        "status": "PASS" if not issues else "FAIL",
        "issues": issues,
        "examples": mismatches[:5],
    }
    logger.info("Reconciliation DQ result: %s", payload)
    context["task_instance"].xcom_push(key="reconciliation", value=payload)
    return payload


def generate_quality_report(**context):
    inventory_core = context["task_instance"].xcom_pull(task_ids="validate_inventory_core", key="inventory_core")
    analytics_outputs = context["task_instance"].xcom_pull(task_ids="validate_analytics_outputs", key="analytics_outputs")
    reconciliation = context["task_instance"].xcom_pull(task_ids="validate_reconciliation", key="reconciliation")

    checks = [inventory_core, analytics_outputs, reconciliation]
    total_failures = sum(1 for check in checks if check["status"] == "FAIL")

    report = {
        "timestamp": datetime.now().isoformat(),
        "checks": checks,
        "summary": {
            "status": "PASS" if total_failures == 0 else "FAIL",
            "failed_checks": total_failures,
            "total_checks": len(checks),
        },
    }

    logger.info("Generated quality report: %s", report)
    context["task_instance"].xcom_push(key="quality_report", value=report)
    return report


validate_inventory_task = PythonOperator(
    task_id="validate_inventory_core",
    python_callable=validate_inventory_core,
    dag=dag,
)

validate_analytics_task = PythonOperator(
    task_id="validate_analytics_outputs",
    python_callable=validate_analytics_outputs,
    dag=dag,
)

validate_reconciliation_task = PythonOperator(
    task_id="validate_reconciliation",
    python_callable=validate_reconciliation,
    dag=dag,
)

generate_report_task = PythonOperator(
    task_id="generate_quality_report",
    python_callable=generate_quality_report,
    dag=dag,
)

[validate_inventory_task, validate_analytics_task, validate_reconciliation_task] >> generate_report_task
