import os
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.empty import EmptyOperator
from web.operators.socrota_to_gcs import EvictionToGCSHKOperator
from airflow.providers.dbt.cloud.operators.dbt import DbtCloudRunJobOperator
from airflow.providers.dbt.cloud.sensors.dbt import DbtCloudJobRunSensor
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
#FILE_FORMAT= "PARQUET"


with DAG(
    dag_id="Load-Eviction-Data-From-Web-To-GCS-To-BQ",
    description="Job to move data from Eviction website to Google Cloud Storage and then transfer from GCS to BigQuery, and finally create a data model using dbt",
    default_args=DEFAULT_ARGS,
    schedule_interval="0 0 1 1 *",
    max_active_runs=1,
    catchup=True,
    tags=["Eviction-Website-to-GCS-Bucket-to-BQ"],
) as dag:
    start = EmptyOperator(task_id="start")

    # Create a task with a different endpoint
    download_web_to_gcs = EvictionToGCSHKOperator(
        task_id='my_download_task',
        endpoint="5cei-gny5.json",
        file_name="eviction_data",  # Provide the desired file name
        destination_bucket=BUCKET,
        api_token=API_TOKEN,
        order_by='eviction_id'
    )

    load_gcs_to_bigquery =  GCSToBigQueryOperator(
        task_id = "load_gcs_to_bigquery",
        bucket=f"{BUCKET}", #BUCKET
        source_objects=[f"{OBJECT}.parquet"], # SOURCE OBJECT
        destination_project_dataset_table=f"{DATASET}.{OBJECT}", # `nyc.green_dataset_data` i.e table name
        autodetect=True, #DETECT SCHEMA : the columns and the type of data in each columns of the CSV file
        write_disposition="WRITE_APPEND", # command to update table from the  latest (or last row) row number upon every job run or task run
        source_format="PARQUET",
    )

    trigger_job_run = DbtCloudRunJobOperator(
        task_id="trigger_job_run_for_eviction",
        #dbt_cloud_conn_id = "eviction_dbt_job",
        job_id=451408,
        check_interval=10,
        timeout=300,
    )

    job_run_sensor = DbtCloudJobRunSensor(
        task_id="job_run_sensor",
        run_id=trigger_job_run.output, 
        timeout=20
    )
    end = EmptyOperator(task_id="end")

    start >> download_web_to_gcs >> load_gcs_to_bigquery >> trigger_job_run >> job_run_sensor >> end