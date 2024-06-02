## InvestIQ Metrics : Indian Stock Exchange Analytics

![image](https://github.com/vedanthv/data-engineering-portfolio/assets/44313631/df9a8200-0252-4957-ab1d-e673bca36a33)


In this project titled **InvestIQ Metrics** I have showcased an end to end data engineering application in AWS using a wide range of cloud services to provide useful metrics and visualizations into the Indian NSE share exchange on of end of day basis with complete orchestration pipelines built using Apache Airflow.

### Tech Stack

- AWS EC2 Instances
- Apache Airflow
- Airbyte
- Docker
- RapidAPI
- AWS Lambda Functions
- AWS S3 Storage
- AWS Cloudwatch
- AWS Redshift
- Prometheus
- Grafana
- PowerBI

### Main Highlights

* Used almost all the main [AWS Services](https://github.com/vedanthv/data-engineering-portfolio/blob/main/investiq-metrics/README.md#tech-stack) in the project
  
* Extracted Data in a variety of ways:
  
    * **NSE Daily OHLC** : RapidAPI
    * **Historical NSE Data** : Airbyte
    * **Global Market News Data** : Alpha Vantage API
    * **Indian Market News Data** : Used Selenium hosted on EC2 to web scrape data from various sources like Yahoo and Google News.
  
* Complete end to end automation of the entire ETL pipeline using Airflow hosted on EC2 server
* Monitoring Dashboard and Metrics Ingestion using StatsD, Prometheus and Grafana.
* [**TODO**] Streaming Data Pipelines with Upstash
* [**TODO**] Utilize Redshift Serverless
* [**TODO**] PowerBI Reporting and Visualization
  
### Project Architecture

![final architecture](https://github.com/vedanthv/data-engineering-portfolio/assets/44313631/6c6afb46-ac1a-4c73-b47b-3915fb7140c6)

### Setup

For implementing or cloning a similar architecture on your system you would need:

1. AWS Account
You would need an AWS account to follow along with the steps. Here is a [link](https://aws.amazon.com/console/) to sign up and get started. Please note that once the billing details are entered it takes 24 hours for your account to get activated.

2. [RapidAPI](https://www.rapidapi.com/) 
In this project, I have used the RapidAPI platform to fetch NSE data. More about the data sources in the next section

I will be going through the rest of the setup later on!

### About the Data Source

As mentioned earlier I have used the NSE stock exchange data for my project.

The National Stock Exchange of India (NSE) is the country's leading stock exchange, facilitating the trading of equities, derivatives, debt securities, and exchange-traded funds (ETFs). Established in 1992, it has become a cornerstone of India's financial ecosystem, offering a transparent and efficient platform for investors and businesses alike. 

As of recent data, NSE is one of the largest stock exchanges in the world by market capitalization. It consistently ranks among the top exchanges globally in terms of the number of trades. There are **2,266** companies listed on the NSE. The market capitalisation of these listed companies on the National Stock Exchange is **₹3,581,291,532** as of Dec 31, 2023

I will be using the following [Latest Stock Price](https://rapidapi.com/suneetk92/api/latest-stock-price) API that is hosted on RapidAPI. It gives realtime data feed of around 900 companies on the NSE with two main endpoints ```price_all``` and ```equity``` in JSON format

![Snapshot of the API](https://snipboard.io/JYTk6N.jpg)

Historic data available for NSE from the website is ingested using a Google Sheets + Airbyte pipeline that enables ingestion of millions of records from Google Sheets to S3 Bucket using Airbyte's easy to use UI. 

The better method to ingest csv data from the website would be scrapping the csv files using Selenium or BeautifulSoup but I wanted to try out Airbyte and found this to be a perfect use case for it.

![airbyte pipeline](https://github.com/vedanthv/data-engineering-portfolio/assets/44313631/06552564-a5ef-40fe-aef1-4700603dfce0)

## Architecture In Detail

### Data Monitoring Setup

#### StatsD Explorer

The Data Monitoring Architecture is used in the project to monitor the Airflow logs using various different metrics.

The metrics cannot be captured directly into Grafana for visualization but has to be streamed in throught **StatsD** explorer.

StatsD is a standard and, by extension, a set of tools that can be used to send, collect, and aggregate custom metrics from any application. Originally, StatsD referred to a daemon written by Etsy in Node.js. Today, the term StatsD refers to both the protocol used in the original daemon, as well as a collection of software and services that implement this protocol.

![](https://snipboard.io/jrYhqd.jpg)

The above image shows the StatsD explorer running on my local machine in the 9102 port.

Here is a view of all the metrics coming into statsD via Airflow.

![](https://snipboard.io/Bsczjb.jpg)

#### Prometheus

Prometheus is an open-source systems monitoring and alerting toolkit originally developed by SoundCloud. It is designed for reliability and scalability, making it ideal for monitoring dynamic cloud environments and microservices. Here’s a brief overview:

**Core Components:**

- Prometheus Server: This is the central component that scrapes and stores time-series data from various endpoints.
Client Libraries: These libraries are used to instrument application code, allowing you to expose metrics that Prometheus can scrape.

- Push Gateway: This component allows short-lived jobs to push metrics to Prometheus, acting as a buffer.

- Alertmanager: It handles alerts generated by Prometheus, managing deduplication, grouping, and routing to various notification channels.

- Exporters: These are used to expose metrics from third-party systems (like databases, hardware, etc.).

**How it Works:**

- Data Collection: Prometheus scrapes metrics from instrumented jobs, which expose data via HTTP endpoints.

- Data Storage: It stores all scraped samples locally and applies efficient time-series database techniques to store data.

- Querying: PromQL (Prometheus Query Language) allows for querying time-series data and creating visualizations.

- Alerting: Users can define alerting rules, and when conditions are met, alerts are sent to the Alertmanager, which handles notifications.

- The main use of Prometheous in this project is to act like a light weight time series database that can store the logs coming from Airflow. The advantage of Prometheus is that it can easily connect to Grafana and we can write custom queries to filter data and perform visualizations.

**Runtime Information**

![](https://snipboard.io/Xn2zxK.jpg)

**TSDB Statistics and Metrics**

![](https://snipboard.io/1S5GCj.jpg)

**Labels with Highest Memory Usage**

![](https://snipboard.io/tZDETJ.jpg)

**Main Configurations**

![](https://snipboard.io/kMN6Fq.jpg)

**Source and Target Scraping Details**

![](https://snipboard.io/ReFHQr.jpg)

**Service Discovery and Target Setup**

![](https://snipboard.io/a1JDsu.jpg)

**Command Line Flags**

Command Line Flags like timeout, concurrency, grace period, outrage tolerance and max memory limit.

![](https://snipboard.io/OKgQJH.jpg)

#### Grafana

**Complete Dashboard Demo**

Running 31 DAGs at once with low latency

![](https://snipboard.io/s4yIGQ.jpg)

In depth DAG Statistics running at 5 second latency

![](https://snipboard.io/1u0JYp.jpg)

### EC2 Setup

The entire project is orchestrated using Airflow and hosted on an EC2 instance.

Amazon Elastic Compute Cloud (Amazon EC2) is a web service offered by Amazon Web Services (AWS) that provides resizable compute capacity in the cloud. It's essentially a virtual computing environment, allowing users to rent virtual servers (known as instances) on which they can run their own applications.

You can create an EC2 instance by heading to Services -> EC2 on your dashboard.

I recommend that you select ```t2.medium``` instance type for smooth functioning of your Airflow scheduler. If you opt for ```t2.small``` there would be some freezing and may cause your platform to hang at times.

After the instance is created, you can either use your root email to configure all the other services or create a User Group by configuring it with administrative access to your entire EC2 instance.

After this create Access Keys in ```pem``` format and download it.

### Airflow Setup

Once you have connected to your EC2 instance cloud shell, run the following commands to get Airflow up and running

```bash
sudo apt update
sudo apt install python3-pip
sudo apt install python3.10-venv
python3 -m venv stock_market_venv
source stock_market_venv/bin/activate

sudo pip install apache-airflow
```

Now to run Airflow, you will have to use the following command 

```bash
airflow standalone
```

After running these commands make sure that you create an Inbound security group rule of type Custom TCP that opens port 8080 on **'All Available Addresses [0.0.0.0/0]'**

In order to run airflow in AWS EC2 you will need to head to ```[Your Public IPv4 address:8080]``` to view the UI.

The username is Admin and the password is mentioned on your AWS EC2 console logs.

### Setting up an SSH shell from EC2 to VSCode

For setting up EC2 instance code in your VSCode editor, please watch this [video](https://www.youtube.com/watch?v=KQr0eI97cLQ&pp=ygUKdnNjb2RlIGVjMg%3D%3D) and follow the steps.

### Complete Code Workflow

Here is an overview of the entire DAG Architecture of this project

![](https://snipboard.io/Y27Fgh.jpg)

#### Phase 1 : DAG Workflow

```tsk_extract_nse_data_var``` - This task basically connects to the API and fetches the data from it. There is a python function that is defined that sends a request to the endpoint with the auth keys and gets the response back in JSON. This is then stored in a file with a unique name that has the date and the time that the file was loaded at.

You will have to define your API key in the ```config_api.json``` file.

Here is the code that achieves this functionality.

```python
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
```

The DAG Code

```python
extract_nse_data_var = PythonOperator(
        task_id= 'tsk_extract_nse_data_var',
        python_callable=extract_nse_data,
        op_kwargs={'url': 'https://latest-stock-price.p.rapidapi.com/any','headers': api_host_key, 'date_string':dt_now_string}
        )
```

Before running the DAG make sure that your EC2 instance has the S3 Access

```load_to_s3``` - This is quite a simple task that loads the file that has been dumped in our local file system to Amazon S3 storage using a bash operator. It pulls the file path of the file added from the XComs and loads it in a bucket called ```nse_eod_data```

```python
load_to_s3 = BashOperator(
            task_id = 'tsk_load_to_s3',
            bash_command = 'aws s3 mv {{ ti.xcom_pull("tsk_extract_nse_data_var")[0]}} s3://nse-eod-data/',
        )
```

If you run this DAG and it succeeds here is the final result that you may see in your S3 bucket.

![](https://snipboard.io/PWauvV.jpg)

Each JSON file will have a structure like this:

![](https://snipboard.io/fELrtH.jpg)

#### Move Data from Landing to Raw Zone

To move the json data from the Landing Zone ```nse_eod_data``` bucket to the raw zone bucket that has the same data but it will be transformed later, we will be using a Lambda function.

- A Lambda function in AWS is a serverless compute service that lets you run code without provisioning or managing servers. 

- Lambda follows the serverless computing model, where you write code (functions) and AWS automatically manages the underlying infrastructure. You don't need to worry about provisioning, scaling, or managing servers. 

- Lambda automatically scales your function based on the incoming request volume. It can handle thousands of requests per second, and you only pay for the compute time consumed by your function.

A Lambda function always has a trigger and in this case whenever any data object lands in out ```nse-eod-data``` S3 bucket, we write it or copy the JSON to our landing zone bucket.

![](https://snipboard.io/7UDSVY.jpg)

Here is the code that acheives this particular logic

```python
import boto3
import json

s3_client = boto3.client('s3')

def lambda_handler(event, context):
    # TODO implement
    source_bucket = event['Records'][0]['s3']['bucket']['name']
    object_key = event['Records'][0]['s3']['object']['key']
   
    
    target_bucket = 'copy-of-raw-bucket-nse-eod-data'
    copy_source = {'Bucket': source_bucket, 'Key': object_key}
   
    waiter = s3_client.get_waiter('object_exists')
    waiter.wait(Bucket=source_bucket, Key=object_key)
    s3_client.copy_object(Bucket=target_bucket, Key=object_key, CopySource=copy_source)
    return {
        'statusCode': 200,
        'body': json.dumps('Copy completed successfully')
    }
```

#### Transformation of the Data

Now that we have a clean copy of the raw data, the next thing to do is to do some transformations on it. I have used another task ```tsk_transform_nse_data``` to do some basic transformations like converting the JSON based columns into separate columns of their own.

```python
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

    # Upload CSV to S3
    object_key = f"{object_key}"
    s3_client.put_object(Bucket=target_bucket_name, Key=object_key, Body=csv_data)
```

Once the data has been transformed, there is another lambda function that runs to store this data into another bucket.

Here is a snapshot of the data in the bucket.
![image](https://github.com/vedanthv/data-engineering-portfolio/assets/44313631/e27dc945-3518-4f3d-9106-5e3aebb36c1f)

This is the lambda function **transformation-convert-to-csv**

![image](https://github.com/vedanthv/data-engineering-portfolio/assets/44313631/db04ad2b-d802-4850-92ba-426ea38062e2)

```python
import boto3
import json
import pandas as pd
# import json

s3_client = boto3.client('s3')

def lambda_handler(event, context):
    # TODO implement
    source_bucket = event['Records'][0]['s3']['bucket']['name']
    object_key = event['Records'][0]['s3']['object']['key']
   
    
    target_bucket = 'cleaned-data-zone-csv-bucket-nse'
    copy_source = {'Bucket': source_bucket, 'Key': object_key}
    
    target_file_name = object_key[:-5]
    print(target_file_name)
    
    waiter = s3_client.get_waiter('object_exists')
    waiter.wait(Bucket=source_bucket, Key=object_key)
    
    response = s3_client.get_object(Bucket=source_bucket, Key=object_key)
    print(response)
    data = response['Body']
    print(data)
    data = response['Body'].read().decode('utf-8')
    print(data)
    # data = json.loads(data)
    data = pd.json_normalize(data)
    print(data)
    
    f = []
    for i in data:
        f.append(i)
    df = pd.DataFrame(f)
    # Select specific columns
    print(df)
    
    # Convert DataFrame to CSV format
    csv_data = df.to_csv(index=True)
    
    # Upload CSV to S3
    bucket_name = target_bucket
    object_key = f"{target_file_name}.csv"
    s3_client.put_object(Bucket=bucket_name, Key=object_key, Body=csv_data)
    
    
    return {
        'statusCode': 200,
        'body': json.dumps('CSV conversion and S3 upload completed successfully')
    }
```

Here is a full view of the DAG runs in Airflow EC2 instance

![image](https://github.com/vedanthv/data-engineering-portfolio/assets/44313631/623fd8b2-74f3-4a11-b3a4-92e59b728b56)

#### News Data from Alpha Vantage

I have used a very similar process to fetch market news data from [Alpha Vantage API](https://www.alphavantage.co/documentation/) that is scheduled to run everyday.

Here is the overview of tasks in the DAG

![image](https://github.com/vedanthv/data-engineering-portfolio/assets/44313631/2cf0d903-e148-4e92-95bb-043882ad195b)



