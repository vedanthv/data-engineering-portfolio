## InvestIQ Metrics : Indian Stock Exchange Analytics

In this project titled **InvestIQ Metrics** I have showcased an end to end data engineering application in AWS using a wide range of cloud services to provide useful metrics and visualizations into the Indian NSE share exchange on of end of day basis with complete orchestration pipelines built using Apache Airflow.

![image](https://github.com/vedanthv/data-engineering-portfolio/assets/44313631/df9a8200-0252-4957-ab1d-e673bca36a33)

### Tech Stack

- AWS EC2 Instances
- Apache Airflow
- RapidAPI
- AWS Lambda Functions
- AWS S3 Storage
- AWS Cloudwatch
- AWS Redshift
- PowerBI

### Project Architecture

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
