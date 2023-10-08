# Socrata-API-Data-To-BigQuery
![image](https://github.com/krissemmy/Socrata-API-Data-To-BigQuery/assets/119800888/59e25b7d-a151-4e3d-97ec-9d85e099c1dc)


## Overview
• An Extract and Load pipeline that gets Eviction Notice data from San Francisco Open Data [Website](https://data.sfgov.org/Housing-and-Buildings/Eviction-Notices/5cei-gny5),
loads it into GCS Bucket and transfer the data from the GCS Bucket to a BigQuery Table.

• Built using a custom Operator that utilize GCS Hook under the hood. For the data transfer, the GCS_To_BigQuery Operator is utilized

• The data pipeline is built and run in a Docker container and executed with Celery executor so it gives room for scalability.

## Setup (official)

### Requirements
1. Upgrade docker-compose version:2.x.x+
2. Allocate memory to docker between 4gb-8gb
3. Python: version 3.8+


### Set Airflow

1.  On Linux, the quick-start needs to know your host user-id and needs to have group id set to 0.
    Otherwise the files created in `dags`, `logs` and `plugins` will be created with root user.

2.  set your airflow user id using:

    ```bash
    echo -e "AIRFLOW_UID=$(id -u)" > .env
    ```

    For Windows same as above.

    Create `.env` file with the content below as:

    ```
    AIRFLOW_UID=50000
    ```
3. Download or import the docker setup file from airflow's website : Run this on terminal
```
curl -LfO 'https://airflow.apache.org/docs/apache-airflow/stable/docker-compose.yaml'
```
4. Create "Dockerfile" use to build airflow container image.

5. Add this to the Dockerfile:
```
FROM apache/airflow:2.6.3
# For local file running
RUN pip install --no-cache-dir "apache-airflow==${AIRFLOW_VERSION}" pandas sqlalchemy psycopg2-binary
USER root
RUN apt-get update \
&& apt-get install -y --no-install-recommends \
vim \
&& apt-get autoremove -yqq --purge \
&& apt-get clean \
&& rm -rf /var/lib/apt/lists/*
WORKDIR $AIRFLOW_HOME
USER $AIRFLOW_UID
```
6. Go into the docker-compose.yaml file for the airflow and replace the build context with:
```
 build:
    context: .
    dockerfile: ./Dockerfile
```
7. Save all the modified files

8. Build image: docker-compose build

9. Initialize airflow db; docker-compose up airflow-init

10. Initialize all the other services: docker-compose up

### SetUp GCP for Local System (Local Environment Oauth-authentication)
1. Create GCP PROJECT
2. Create service account: Add Editor and storage admin, storage object admins and bigquery admin
3. Create credential keys and download it
4. Change name and location
```bash
cd ~ && mkdir -p ~/.google/credentials/

mv <path/to/your/service-account-authkeys>.json ~/.google/credentials/google_credentials.json
```

   Below is an example
   
```
mv  /home/krissemmy/Downloads/alt-data-engr-1dfdbf9f8dbf.json ~/.google/credentials/google_credentials.json
```
4. Install gcloud on system : open new terminal and run    (follow this link to install gcloud-sdk : https://cloud.google.com/sdk/docs/install-sdk)

    ```bash
    gcloud -v
    ```
  to see if its installed successfully
5. Set the google applications credentials environment variable

  ```bash
  export GOOGLE_APPLICATION_CREDENTIALS="/path/to/.json-file"
  ```

  Below is an example

  ```bash
  export GOOGLE_APPLICATION_CREDENTIALS = "/home/krissemmy/.google/credentials/google_credentials.json"
  ```
6. Run gcloud auth application-default login
7. Redirect to the website and authenticate local environment with the cloud environment

## Enable API
perform the following on your Google Cloud Platform
1. Enable Identity  and Access management API
2. Enable IAM Service Account Credentials API


## Update docker-compose file and Dockerfile
1. Add google credentials "GOOGLE_APPLICATION_CREDENTIALS" , project_id, bucket name and API key (From [Socrata Website](https://data.sfgov.org/profile/edit/developer_settings))
    ```
        GOOGLE_APPLICATION_CREDENTIALS: /.google/credentials/google_credentials.json
        AIRFLOW_CONN_GOOGLE_CLOUD_DEFAULT: 'google-cloud-platform://?extra__google_cloud_platform__key_path=/.google/credentials/google_credentials.json'

        GCP_PROJECT_ID: "my-project-id"
        GCP_GCS_BUCKET: "my-bucket"
    ```
2. Add the below line to the volumes of the airflow documentation

    ```
    ~/.google/credentials/:/.google/credentials:ro
    ```
    ![image](https://github.com/krissemmy/Socrata-API-Data-To-BigQuery/assets/119800888/5b21c7f8-0605-434c-9885-c3b0662c4d3a)


3. build airflow container image with:
```bash
docker-compose build
```
4. Initialize airflow db;
```bash
docker-compose up airflow-init
```
5. Initialize all the other services: 
```bash
docker-compose up
```
6. Inside plugins/web/operators folder is the python file with the SocrataToGCSOperator.
7. Inside dags folder is Evc_to_gcs_bq.py file with all the neccessary dag code, you can make modifications to the time schedules and any other thing you feel like
8. To check if all containers are running fine and healthy, open a new terminal run the below
```bash
docker ps
```
9. You can connect to your Airflow webserver interface at http://localhost:8080/
10. Default username and password is 

username : airflow

password : airflow

11. Unpause your DAG and watch your pipeline get kickstarted, and happy Data Engineering.

## Data Dictionary

#### eviction_id

The eviction notice ID is the internal case record primarily used for administrative purposes.

- Data Type: Text

#### address	
The address where the eviction notice was issued. The addresses are represented at the block level.

- Data Type: Text


#### city	
The city where the eviction notice was issued. In this dataset, always San Francisco.

- Data Type: Text

#### state	
The state where the eviction notice was issued. In this dataset, always CA.

- Data Type: Text

#### zip
The zip code where the eviction notice was issued.(Eviction Notice Source Zipcode)

- Data Type: Text


#### file_date	
The date on which the eviction notice was filed with the Rent Board of Arbitration.

- Data Type: Floating Timestamp(Date & Time)

#### non_payment	
This field is checked (true) if the landlord indicated non-payment of rent as a grounds for eviction.

- Data Type: Boolean

#### breach	
This field is checked (true) if the landlord indicated breach of lease as a grounds for eviction.

- Data Type: Boolean

#### nuisance	
This field is checked (true) if the landlord indicated nuisance as a grounds for eviction.

- Data Type: Boolean

#### illegal_use	
This field is checked (true) if the landlord indicated an illegal use of the rental unit as a grounds for eviction.

- Data Type: Boolean

#### failure_to_sign_renewal	
This field is checked (true) if the landlord indicated failure to sign lease renewal as a grounds for eviction.

- Data Type: Boolean

#### access_denial	
This field is checked (true) if the landlord indicated unlawful denial of access to unit as a grounds for eviction.

- Data Type: Boolean

#### unapproved_subtenant	
This field is checked (true) if the landlord indicated the tenant had an unapproved subtenant as a grounds for eviction.

- Data Type: Boolean

#### owner_move_in	
This field is checked (true) if the landlord indicated an owner move in as a grounds for eviction.

- Data Type: Boolean

#### demolition	
This field is checked (true) if the landlord indicated demolition of property as a grounds for eviction.

- Data Type: Boolean

#### capital_improvement	
This field is checked (true) if the landlord indicated a capital improvement as a grounds for eviction.

- Data Type: Boolean

#### substantial_rehab	
This field is checked (true) if the landlord indicated substantial rehabilitation as a grounds for eviction.

- Data Type: Boolean

#### ellis_act_withdrawal	
This field is checked (true) if the landlord indicated an Ellis Act withdrawal (going out of business) as a grounds for eviction.

- Data Type: Boolean

#### condo_conversion	
This field is checked (true) if the landlord indicated a condo conversion as a grounds for eviction.

- Data Type: Boolean

#### roommate_same_unit	
This field is checked (true) if the landlord indicated if they were evicting a roommate in their unit as a grounds for eviction.

- Data Type: Boolean

#### other_cause	
This field is checked (true) if some other cause not covered by the admin code was indicated by the landlord. These are not enforceable grounds, but are indicated here for record keeping.

- Data Type: Boolean

#### late_payments	
This field is checked (true) if the landlord indicated habitual late payment of rent as a grounds for eviction.

- Data Type: Boolean

#### lead_remediation	
This field is checked (true) if the landlord indicated lead remediation as a grounds for eviction.

- Data Type: Boolean

#### development	
This field is checked (true) if the landlord indicated a development agreement as a grounds for eviction.

- Data Type: Boolean

#### good_samaritan_ends	
This field is checked (true) if the landlord indicated the period of good samaritan laws coming to an end as a grounds for eviction.

- Data Type: Boolean

#### constraints_date	
In the case of certain just cause evictions like Ellis and Owner Move In, constraints are placed on the property and recorded by the the City Recorder. This date represents the date through which the relevant constraints apply. You can learn more on fact sheet 4 of the Rent Board available at: http://sfrb.org/fact-sheet-4-eviction-issues

Data Type: Floating Timestamp(Date & Time)

#### supervisor_district	
District Number - San Francisco Board of Supervisors (1 to 11). Please note these are automatically assigned based on the latitude and longitude. These will be blank if the automated geocoding was unsuccessful.

- Data Type: Number

#### neighborhood	
Analysis neighborhoods corresponding to census boundaries. You can see these boundaries here: https://data.sfgov.org/d/p5b7-5n3h Please note these are automatically assigned based on the latitude and longitude. These will be blank if the automated geocoding was unsuccessful.

- Data Type: Text

#### client_location	
The location of the record is at the mid block level and is represented by it's latitude and longitude. Some addresses are not well formed and do not get geocoded. These will be blank. Geocoders produce a confidence match rate. Since this field is automated, we set the match at 90% or greater. Please note, that even this rate could result in false positives however more unlikely than at lower confidence levels.

- Data Type : Location/records(dictionary)


#### shape	
The location of the record as a Point type is at the mid block level and is represented by it's latitude and longitude. Some addresses are not well formed and do not get geocoded. These will be blank. Geocoders produce a confidence match rate. Since this field is automated, we set the match at 90% or greater. Please note, that even this rate could result in false positives however more unlikely than at lower confidence levels.

- Data Type: Point
