from typing import Dict, Any, Optional, Sequence, Union
from airflow.models import BaseOperator
from airflow.providers.google.cloud.hooks.gcs import GCSHook
import pandas as pd
import requests
import tempfile

class EvictionToGCSHKOperator(BaseOperator):
    def __init__(
        self,
        api_token: str,
        order_by: str,
        gcp_conn_id: str = "google_cloud_default",
        api_url: str = "https://data.sfgov.org/resource/",
        destination_bucket:  Optional[str] = None,
        delegete_to: Optional[str] = None,
        impersonation_chain: Optional[Union[str, Sequence[str]]] = None,
        file_name: str = "output_file",  # Define a default file name
        endpoint: str = "5cei-gny5.json", #Default Endpoint
        *args,
        **kwargs
    ) -> None:
        super().__init__(*args, **kwargs)
        self.api_url = api_url
        self.api_token = api_token
        self.order_by = order_by
        self.gcp_conn_id = gcp_conn_id
        self.destination_bucket = destination_bucket
        self.file_name = file_name
        self.delegete_to = delegete_to
        self.impersonation_chain = impersonation_chain
        self.endpoint = endpoint

    def execute(self, context: Dict[str, Any]) -> None:
        # download it using requests via into a tempfile a pandas df
        with tempfile.TemporaryDirectory() as tmpdirname:
            api_url = self.api_url + self.endpoint
            self.log.info(f"API url is: {self.api_url}")

            limit = 500000
            offset = 0
            params = {
                '$limit': limit,
                '$offset': offset,
                '$order': self.order_by,  # Specify the field to order by
            }

            # Define the headers with the X-App-Token header
            headers = {
                'X-App-Token': self.api_token,
            }
            # Make a GET request to the API with the headers and parameters
            response = requests.get(api_url, headers=headers, params=params)

            df = pd.DataFrame()

            while True:
                # Make a GET request to the API with the headers and parameters
                response = requests.get(api_url, headers=headers, params=params)

                # Check the response status code
                if response.status_code == 200:
                    data = response.json()
                    df1 = pd.DataFrame(data)
                    df = pd.concat([df,df1],ignore_index=True)
                    self.log.info(f"Dataframe currently has {df.shape[0]} columns")


                    # If the number of results received is less than the limit, you've reached the end
                    if len(data) < limit:
                        break

                    # Increment the offset for the next page
                    offset += limit
                else:
                    self.log.info(f"Request failed with status code: {response.status_code}")
                    break
            csv_file = self.file_name+".csv"
            df.to_csv(f'{tmpdirname}/{csv_file}', index=False)
            # upload it to gcs using GCS hooks
            gcs_hook = GCSHook(
                gcp_conn_id = self.gcp_conn_id,
                delegete_to = self.delegete_to,
                impersonation_chain = self.impersonation_chain
            )
            #Upload as a CSV file
            gcs_hook.upload(
                    bucket_name=self.destination_bucket,
                    object_name=csv_file,
                    filename=f'{tmpdirname}/{csv_file}',
                    mime_type="text/csv",
                    gzip=False,
            )
            self.log.info(f"Loaded CSV: {csv_file}")

            #Upload as a Parquet file
            parquet_file = self.file_name+".parquet"
            df['file_date'] = pd.to_datetime(df['file_date'])
            df.to_parquet(f'{tmpdirname}/{parquet_file}', engine='pyarrow')
            # upload it to gcs using GCS hooks
            gcs_hook.upload(
                    bucket_name=self.destination_bucket,
                    object_name=parquet_file,
                    filename=f'{tmpdirname}/{parquet_file}',
                    mime_type="application/parquet",
                    gzip=False,
            )
            self.log.info(f"Loaded Parquet: {parquet_file}")
