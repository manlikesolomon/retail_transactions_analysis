from airflow.decorators import dag, task
from datetime import datetime, timedelta
from airflow_clickhouse_plugin.operators.clickhouse import ClickHouseOperator
from airflow_clickhouse_plugin.hooks.clickhouse import ClickHouseHook


CLICKHOUSE_CONNECTION_ID = 'clickhouse_conn'
SQL_FILE_PATH = '/opt/airflow/include/sql/'

GET_METRICS = {
    'populate_customer_segment_metrics' : 'customer_segment_metrics.sql',
    'populate_city_metrics' : 'daily_city_metrics.sql',
    'populate_payment_behaviour_metrics' : 'payment_behavior.sql',
    'populate_promo_metrics' : 'promo_effectiveness.sql'
}

default_args = {
    'owner': 'solomon',
    'start_date' : datetime(2025,7,10),
    'retries': 3,
    'retry_delay': timedelta(minutes=5),
}

def generate_sql_task(task_id, sql_file):
    @task(task_id=task_id)
    def run_sql():
        hook = ClickHouseHook(clickhouse_conn_id=CLICKHOUSE_CONNECTION_ID)
        sql_path = f"{SQL_FILE_PATH}{sql_file}"
        with open(sql_path, 'r') as f:
            sql_script = f.read()
        hook.run(sql_script)
    return run_sql()

@dag(
    dag_id='get_retail_transaction_metrics',
    schedule='@daily',
    default_args=default_args,
    max_active_runs=1
):
def get_retail_transaction_metrics():

    @task(task_id='start')
    def start():
        return True
    
    @task(task_id='end')
    def end():
        return True
    
    create_schema = ClickHouseOperator(
                        task_id='create_schema',
                        clickhouse_conn_id=CLICKHOUSE_CONNECTION_ID,
                        sql='CREATE DATABASE IF NOT EXISTS summary;'
                        )

    metric_tasks = []
    for task_id, sql_file in GET_METRICS.items():
        t = generate_sql_task(task_id, sql_file)
        metric_tasks.append(t)

    start_task = start()
    end_task = end()

    start_task >> create_schema >> metric_tasks >> end_task

dag = get_retail_transaction_metrics()
