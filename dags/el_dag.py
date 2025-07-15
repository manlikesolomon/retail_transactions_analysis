from airflow.decorators import dag, task
from datetime import datetime, timedelta
from airflow.providers.common.sql.operators.sql import SQLExecuteQueryOperator
from airflow_clickhouse_plugin.operators.clickhouse import ClickHouseOperator
from airflow_clickhouse_plugin.hooks.clickhouse import ClickHouseHook
import pandas as pd
import numpy as np
import os
import csv
import ast
from datetime import datetime


FILE_PATH = 'data/raw/Retail_Transactions_Dataset.csv'
CLICKHOUSE_CONNECTION_ID = 'clickhouse_conn'

@task(task_id='check_for_csv_file')
def check_file_exists(path=FILE_PATH):
    if not os.path.exists(path):
        raise FileNotFoundError(f'File not found {path}')
    return True


@task(task_id="load_data_from_csv")
def load_data_from_csv():
    hook = ClickHouseHook(clickhouse_conn_id=CLICKHOUSE_CONNECTION_ID)
    client = hook.get_conn()

    values = []
    with open(FILE_PATH, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            product_list = ast.literal_eval(row["Product"])
            product_string = ", ".join(product_list) if isinstance(product_list, list) else str(product_list)
            values.append((
                int(row["Transaction_ID"]),
                datetime.strptime(row["Date"], "%Y-%m-%d %H:%M:%S"),
                row["Customer_Name"],
                product_string,
                int(row["Total_Items"]),
                float(row["Total_Cost"]),
                row["Payment_Method"],
                row["City"],
                row["Store_Type"],
                int(row["Discount_Applied"] == "True"),
                row["Customer_Category"],
                row["Season"],
                row["Promotion"] if row["Promotion"] else ""
            ))

    insert_sql = "INSERT INTO raw.retail_transactions VALUES"
    client.execute(insert_sql, values)


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
