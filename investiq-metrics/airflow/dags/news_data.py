from airflow import DAG
from datetime import timedelta, datetime
import json
import requests
from airflow.operators.python import PythonOperator
from airflow.operators.bash_operator import BashOperator
from airflow.providers.amazon.aws.sensors.s3 import S3KeySensor
from airflow.providers.amazon.aws.transfers.s3_to_redshift import S3ToRedshiftOperator
import pandas as pd
import boto3

s3_client = boto3.client('s3')

api_key = "ADD KEY HERE"
target_bucket_name = "news-data-finance"

now = datetime.now()
dt_now_string = now.strftime("%d%m%Y%H%M%S")

def extract_news_data(**kwargs):
    url = kwargs['url']
    dt_string = kwargs['date_string']
    # return headers
    response = requests.get(url)
    response_data = response.json()
    
    print(response_data)

    # Specify the output file path
    output_file_path = f"/home/ubuntu/news-data/news_data_{dt_string}.json"
    file_str = f'news_data_{dt_string}.csv'

    # Write the JSON response to a file
    with open(output_file_path, "w") as output_file:
        json.dump(response_data, output_file, indent=4)  # indent for pretty formatting
    output_list = [output_file_path, file_str]
    return output_list 

def transform_data(task_instance):
    data_link = task_instance.xcom_pull(task_ids="tsk_extract_news_data_var")[0]
    object_key = task_instance.xcom_pull(task_ids="tsk_extract_news_data_var")[1]

    with open(data_link) as f:
        data = json.load(f)

    df = pd.json_normalize(data["feed"],meta = ["title","url","time_published","authors","summary","source","overall_sentiment_score","overall_sentiment_label"])

    df_split = pd.json_normalize(df['ticker_sentiment'].explode())

    # Concatenate the normalized DataFrame with the original DataFrame
    df_merged = pd.concat([df, df_split], axis=1)
    df_merged.drop(columns=['ticker_sentiment','topics'], inplace=True)

    csv_data = df_merged.to_csv(index=False)

    # Upload CSV to S3
    object_key = f"{object_key}"
    s3_client.put_object(Bucket=target_bucket_name, Key=object_key, Body=csv_data)

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

with DAG('news_analytics_dag',
        default_args=default_args,
        schedule_interval = '@daily',
        catchup=False) as dag:

        extract_news_data_var = PythonOperator(
        task_id= 'tsk_extract_news_data_var',
        python_callable=extract_news_data,
        op_kwargs={'url': f'https://www.alphavantage.co/query?function=NEWS_SENTIMENT&apikey={api_key}','date_string':dt_now_string}
        )

        transform_news_data_var = PythonOperator(
        task_id= 'tsk_transform_news_data_var',
        python_callable=transform_data,
        op_kwargs={'date_string':dt_now_string}
        )
extract_news_data_var >> transform_news_data_var
