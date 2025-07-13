from airflow.decorators import dag, task
from datetime import datetime, timedelta
from airflow.providers.common.sql.operators.sql import SQLExecuteQueryOperator
from airflow_clickhouse_plugin.operators.clickhouse import ClickHouseOperator
from airflow_clickhouse_plugin.hooks.clickhouse import ClickHouseHook
import pandas as pd
import numpy as np
import os


FILE_PATH = 'data/raw/Retail_Transactions_Dataset.csv'
CLICKHOUSE_CONNECTION_ID = 'clickhouse_conn'

@task(task_id='check_for_csv_file')
def check_file_exists(path=FILE_PATH):
    if not os.path.exists(path):
        raise FileNotFoundError(f'File not found {path}')
    return True

def flatten_cell(cell):
    # Convert list/tuple/np.ndarray to string recursively
    if isinstance(cell, (list, tuple, np.ndarray)):
        # Convert each element to string recursively, then join with comma (or just str(cell))
        return str(cell)
    return cell

@task(task_id="load_data_from_csv")
def load_data_from_csv():
    import numpy as np
    hook = ClickHouseHook(clickhouse_conn_id=CLICKHOUSE_CONNECTION_ID)
    client = hook.get_conn()
    df = pd.read_csv(FILE_PATH)
    df = df.applymap(flatten_cell)

    client.insert_dataframe(
        'INSERT INTO raw.retail_transactions VALUES', df
    )


default_args = {
    'owner': 'solomon',
    'start_date' : datetime(2025,7,10),
    'retries': 3,
    'retry_delay': timedelta(minutes=5),
}

@dag(
    dag_id='load_data_pipeline',
    default_args=default_args,
    schedule=None,
    max_active_runs=1
)
def load_clickhouse():

    @task
    def start():
        return True

    @task
    def end():
        return True
    
    check_file_task = check_file_exists()

    create_table = ClickHouseOperator(
        task_id='create_table_if_not_exist',
        clickhouse_conn_id=CLICKHOUSE_CONNECTION_ID,
        sql='''
        CREATE TABLE IF NOT EXISTS raw.retail_transactions (
          Transaction_ID UInt64,
          Date DateTime,
          Customer_Name String,
          Product String,
          Total_Items UInt32,
          Total_Cost Float32,
          Payment_Method String,
          City String,
          Store_Type String,
          Discount_Applied UInt8,
          Customer_Category String,
          Season String,
          Promotion String
        ) ENGINE = MergeTree()
        ORDER BY (Transaction_ID)
        '''
    )

    load_data = load_data_from_csv()

    start() >> check_file_task >> create_table >> load_data >> end()

dag = load_clickhouse()




