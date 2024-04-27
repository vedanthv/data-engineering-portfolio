# InvestIQ Metrics : Indian Stock Exchange Analytics

In this project titled **InvestIQ Metrics** I have showcased an end to end data engineering application in AWS using a wide range of cloud services to provide useful metrics and visualizations into the Indian NSE share exchange on of end of day basis with complete orchestration pipelines built using Apache Airflow.

![image](https://github.com/vedanthv/data-engineering-portfolio/assets/44313631/df9a8200-0252-4957-ab1d-e673bca36a33)

## Tech Stack

- AWS EC2 Instances
- Apache Airflow
- RapidAPI
- AWS Lambda Functions
- AWS S3 Storage
- AWS Cloudwatch
- AWS Redshift
- PowerBI

## Project Architecture

![InvestIQ](https://github.com/vedanthv/data-engineering-portfolio/assets/44313631/be8cc57d-f51f-498d-a9aa-dc2386a96f62)

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

### Architecture Components

#### EC2 Setup

The entire project is orchestrated using Airflow and hosted on an EC2 instance.

Amazon Elastic Compute Cloud (Amazon EC2) is a web service offered by Amazon Web Services (AWS) that provides resizable compute capacity in the cloud. It's essentially a virtual computing environment, allowing users to rent virtual servers (known as instances) on which they can run their own applications.

You can create an EC2 instance by heading to Services -> EC2 on your dashboard.

I recommend that you select ```t2.medium``` instance type for smooth functioning of your Airflow scheduler. If you opt for ```t2.small``` there would be some freezing and may cause your platform to hang at times.

After the instance is created, you can either use your root email to configure all the other services or create a User Group by configuring it with administrative access to your entire EC2 instance.

After this create Access Keys in ```pem``` format and download it.

#### Airflow Setup

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

##### Setting up an SSH shell from EC2 to VSCode

For setting up EC2 instance code in your VSCode editor, please watch this [video](https://www.youtube.com/watch?v=KQr0eI97cLQ&pp=ygUKdnNjb2RlIGVjMg%3D%3D) and follow the steps.


