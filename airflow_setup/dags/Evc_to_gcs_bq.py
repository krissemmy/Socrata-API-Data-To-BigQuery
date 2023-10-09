import os
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.empty import EmptyOperator
from web.operators.Socrota_To_GCS import SocrataToGCSHKOperator
from airflow.providers.google.cloud.transfers.gcs_to_bigquery import GCSToBigQueryOperator

AIRFLOW_HOME = os.environ.get("AIRFLOW_HOME", "/opt/airflow/")

DEFAULT_ARGS = {
    "owner": "airflow",
    "start_date": datetime(2023, 1, 1),
    "email": [os.getenv("ALERT_EMAIL", "")],
    "email_on_failure": True,
    "email_on_retry": False,
    "retries": 2,
    "retry_delay": timedelta(minutes=1),
}

PROJECT_ID = os.environ.get("GCP_PROJECT_ID")
BUCKET = os.environ.get("GCP_GCS_BUCKET")
API_TOKEN = os.environ.get("API_TOKEN")
OBJECT = "eviction_data"
DATASET="alt_data"

with DAG(
    dag_id="Load-Eviction-Data-From-Web-To-GCS-To-BQ",
    description="Job to move data from Eviction website to Google Cloud Storage and then from GCS to BigQuery",
    default_args=DEFAULT_ARGS,
    schedule_interval="0 6 2 * *",
    max_active_runs=1,
    catchup=True,
    tags=["Eviction-Website-to-GCS-Bucket-to-BQ"],
) as dag:
    start = EmptyOperator(task_id="start")

    # Create a task with a different endpoint
    download_web_to_gcs = SocrataToGCSHKOperator(
        task_id='my_download_task', # Task ID
        endpoint="5cei-gny5.json", # Provide the unique identifier for the data
        file_name=OBJECT,  # Provide the desired file name
        destination_bucket=BUCKET,  # Your GCS Bucket name
        api_token=API_TOKEN,  # Your API Token gotten from the developer website
        order_by='eviction_id', # The column/field for the data to be ordered by
    )

    load_gcs_to_bigquery =  GCSToBigQueryOperator(
        task_id = "load_gcs_to_bigquery",
        bucket=f"{BUCKET}", #BUCKET
        source_objects=[f"{OBJECT}.parquet"], # name of object/file in GCS bucket
        destination_project_dataset_table=f"{DATASET}.{OBJECT}_table", # `alt_data.eviction_data_table` i.e table name
        autodetect=True, #DETECT SCHEMA : the columns and the type of data in each columns of the CSV file
        write_disposition="WRITE_TRUNCATE", # command to update the table with what's in our file upon every job run or task run
        source_format="PARQUET",
    )
    end = EmptyOperator(task_id="end")

    start >> download_web_to_gcs >> load_gcs_to_bigquery >> end
