from airflow import DAG 
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta

from scripts.ingest import run_ingest

default_args = {
    'owner': 'joey', 
    'retries': 2,
    'retry_delay': timedelta(minutes=5)
}

dag = DAG(
    'd_classified_ingest',
    default_args=default_args,
    description='Daily ingestion of job postings from Adzuna into Snowflake',
    schedule='@daily',
    start_date=datetime(2026, 8, 13),
    catchup=False,
    tags=['d_classified'],
)

ingest_task = PythonOperator(
    task_id='run_ingest',
    python_callable=run_ingest,
    dag=dag,
)