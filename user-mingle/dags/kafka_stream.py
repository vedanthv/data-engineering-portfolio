from datetime import datetime
from airflow import DAG
from airflow.operators.python import PythonOperator

default_args = {
    'owner':'vedanth',
    'start_date': datetime(2023,10,28,00)
}

def get_data():
    import json
    import requests

    res = requests.get("https://randomuser.me/api/")
    res = res.json()
    res = res['results'][0]

    return res

def format_data(res):
    data = {}
    location = res['location']
    data['first_name'] = res['name']['first']
    data['last_name'] = res['name']['last']
    data['gender'] = res['gender']
    data['address'] = f"{str(location['street']['number'])} {location['street']['name']}, " \
                      f"{location['city']}, {location['state']}, {location['country']}"
    data['post_code'] = location['postcode']
    data['email'] = res['email']
    data['username'] = res['login']['username']
    data['dob'] = res['dob']['date']
    data['registered_date'] = res['registered']['date']
    data['phone'] = res['phone']
    data['picture'] = res['picture']['medium']

def stream_data():
    import json
    from kafka import KafkaProducer
    import time

    res = get_data()
    res = format_data(res)

    producer = KafkaProducer(bootstrap_servers = ['broker:29092'],max_block_ms = 10000,api_version=(0,11,5))
    producer.send('testing',json.dumps(res).encode('utf-8'))    
    

with DAG('user_automation',
         default_args=default_args,
         scheduer_interval = '@daily',
         catchup = False) as dag:
    
    streaming_task = PythonOperator(
        task_id = 'stream_data_from_api',
        python_callable = stream_data
    )