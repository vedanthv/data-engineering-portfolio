from airflow import DAG
from datetime import timedelta, datetime
import json
import requests
from airflow.operators.python import PythonOperator
from airflow.operators.bash_operator import BashOperator
from airflow.providers.amazon.aws.sensors.s3 import S3KeySensor
from airflow.providers.amazon.aws.transfers.s3_to_redshift import S3ToRedshiftOperator


# Load JSON config file
with open('/home/ubuntu/airflow/config_api.json', 'r') as config_file:
    api_host_key = json.load(config_file)

now = datetime.now()
dt_now_string = now.strftime("%d%m%Y%H%M%S")
s3_bucket = 'cleaned-data-zone-csv-bucket-nse'

def extract_nse_data(**kwargs):
    url = kwargs['url']
    headers = kwargs['headers']
    dt_string = kwargs['date_string']
    # return headers
    response = requests.get(url, headers=headers)
    response_data = response.json()
    

    # Specify the output file path
    output_file_path = f"/home/ubuntu/eod-data/nse_data_{dt_string}.json"
    file_str = f'nse_data_{dt_string}.csv'

    # Write the JSON response to a file
    with open(output_file_path, "w") as output_file:
        json.dump(response_data, output_file, indent=4)  # indent for pretty formatting
    output_list = [output_file_path, file_str]
    return output_list   

def transform_data(task_instance):
    data = task_instance.xcom_pull(task_ids="tsk_extract_nse_data_var")[0]
    object_key = task_instance.xcom_pull(task_ids="tsk_extract_nse_data_var")[1]

    df = pd.read_json(data)

    # Normalize the JSON column into separate columns
    normalized_df = pd.json_normalize(df['meta'])

    # Concatenate the normalized DataFrame with the original DataFrame
    df = pd.concat([df, normalized_df], axis=1)

    # Drop the original JSON column
    df.drop(columns=['meta'], inplace=True)

    # Convert DataFrame to CSV format
    csv_data = df.to_csv(index=False)

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2023, 8, 1),
    'email': ['myemail@domain.com'],
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(seconds=15)
}

with DAG('nse_analytics_dag',
        default_args=default_args,
        schedule_interval = '@daily',
        catchup=False) as dag:

        extract_nse_data_var = PythonOperator(
        task_id= 'tsk_extract_nse_data_var',
        python_callable=extract_nse_data,
        op_kwargs={'url': 'https://latest-stock-price.p.rapidapi.com/any','headers': api_host_key, 'date_string':dt_now_string}
        )

        transform_nse_data_var = PythonOperator(
        task_id= 'tsk_transform_nse_data_var',
        python_callable=transform_data
        )

        load_to_s3 = BashOperator(
            task_id = 'tsk_load_to_s3',
            bash_command = 'aws s3 mv {{ ti.xcom_pull("tsk_extract_nse_data_var")[0]}} s3://nse-eod-data/',
        )

        is_file_in_s3_available = S3KeySensor(
        task_id='tsk_is_file_in_s3_available',
        bucket_key='{{ti.xcom_pull("tsk_extract_nse_data_var")[1]}}',
        bucket_name=s3_bucket,
        aws_conn_id='aws_s3_conn',
        wildcard_match=False,  # Set this to True if you want to use wildcards in the prefix
        timeout=60,  # Optional: Timeout for the sensor (in seconds)
        poke_interval=5,  # Optional: Time interval between S3 checks (in seconds)
        )

        transfer_s3_to_redshift = S3ToRedshiftOperator(
        task_id="tsk_transfer_s3_to_redshift",
        aws_conn_id='aws_s3_conn',
        redshift_conn_id='conn_id_redshift',
        s3_bucket=s3_bucket,
        s3_key='{{ti.xcom_pull("tsk_extract_nse_data_var")[1]}}',
        schema="PUBLIC",
        table="nse_eod_data",
        copy_options=["csv IGNOREHEADER 1"],
    )

extract_nse_data_var >> load_to_s3 >> is_file_in_s3_available >> transfer_s3_to_redshift
