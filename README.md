![image](https://github.com/vedanthv/data-engineering-portfolio/assets/44313631/664c2886-b8d7-41cd-b231-f9f1ca4bbd3e)

Hello World! I'm Vedanth. 

This is a complete portfolio of the projects I have designed with a major focus on implementing various data engineering tech and cloud services across Azure, AWS and GCP.

Feel Free to Connect with me 🤠

**[LinkedIn](https://www.linkedin.com/in/vedanthbaliga/) | [GitHub](https://github.com/vedanthv/)**

## [UserMingle : Kafka-Driven User Profile Streaming](https://github.com/vedanthv/data-engineering-portfolio/tree/main/user-mingle) 🧔

**Brief Overview**

In this project, I have used the [Random User Generator](https://randomuser.me/) API to fetch data intermittedly using Airflow DAG pipelines and store the data in Postgres DB.
The entire streaming process is managed by a Kafka setup that has a Zookeeper pipeline to manage multiple broadcasts and process them from the message queue. There is a master-worker architecture setup on Apache Spark. Finally there is a Cassandra DB setup that has a listener that takes the stream data from Spark and stores in a columnar format. The entire project is containerized with Docker.

**Solution Architecture**

![image](https://github.com/vedanthv/data-engineering-portfolio/assets/44313631/bf025b1f-e051-4f1e-9353-1d2b837060b4)

**Tech Stack**

- **Apache Airflow**: Responsible for orchestrating the pipeline and storing fetched data in a PostgreSQL database.
- **Apache Kafka and Zookeeper**: Used for streaming data from PostgreSQL to the processing engine.
- **Control Center and Schema Registry**: Helps in monitoring and schema management of our Kafka streams.
- **Apache Spark**: For data processing with its master and worker nodes.
- **Cassandra**: Where the processed data will be stored.

##  [Grand Prix Data Odyssey: Deep Formula 1 Insights](https://github.com/vedanthv/data-engineering-projects/tree/main/formula-1-analytics-engg) 🏎️

**Brief Overview**

This is a complete end to end Formula 1 race analytics project that encompasses extraction of data from ErgastAPI, applying the right schema and using slowly changing dimensions with three different layers for raw, processed and presented data. The data is analysed using **Azure Databricks** after applying SQL filters and transformations to make the data understandable. The data is also subjected to **incremental load** constraints and data ingestion job is run every Sat at 10pm after the race dynamically with rerun pipelines and Email alerts on failure.

**Solution Architecture**

![image](https://github.com/vedanthv/data-engineering-projects/assets/44313631/0eee5f17-7102-4526-b3e3-8fb185a06553)

**Tech Stack**
- Spark SQL
- Azure Databricks
- Postman
- PySpark
- Azure Blob Storage
- Azure Unity Catalog
- Azure Data Factory
- Azure DevOps
- Azure Synapse Studio
- Delta Lake Storage
- PowerBI

## [Taste-Threads: Realtime Yelp Sentiment Analytics with Sockets and LLMs]() 😋

**Brief Overview**

This project uses the extensive Yelp Dataset with more than 7 million records. The Yelp dataset is a subset of businesses, reviews, and user data for use in connection with academic research. This project involves fetching data in realtime using Sockets and then using Apache Spark and LLMs for processing. The entire pipeline is powered by Kafka and Airflow on Confluent Cloud. Finally, indexing is performed using Elastic Search for better search capabilities.

**Solution Architecture**

![image](https://github.com/vedanthv/data-engineering-portfolio/assets/44313631/6451c979-d846-44e9-bc6a-1736d8b92de1)

**Tech Stack**

- **TCP/IP Socket**: Used to stream data over the network in chunks
- **Apache Spark**: For data processing with its master and worker nodes.
- **Confluent Kafka**: Our cluster on the cloud
- **Control Center and Schema Registry**: Helps in monitoring and schema management of our Kafka streams.
- **Kafka Connect**: For connecting to elasticsearch
- **Elasticsearch**: For indexing and querying

## [Medal Metrics: Tokyo Olympics Data Alchemy](https://github.com/vedanthv/data-engineering-projects/tree/main/tokyo-olympics-de) 🤾‍♀🎖️

**Brief Overview**

The project utilizes the Tokyo Olympics Dataset from Kaggle  with data from over 11,000 athletes with 47 disciplines, along with 743 Teams taking part in the 2021(2020) Tokyo Olympics. There are different data files for coaches, athletes, medals and teams that was first ingested using KaggleAPI analysed using a variety of Azure Services, finally presented as a neat dashboard on Synapse Studio and PowerBI.

**Solution Architecture**

![image](https://github.com/vedanthv/data-engineering-projects/assets/44313631/876cc839-97ec-430d-88d2-f1a04f06698c)

**Tech Stack**
- Azure Data Factory
- Azure Data Lake Gen 2
- Azure Blob Storage
- Azure Databricks
- Synapse Analytics
- PowerBI

## [HarmonicPulse: Analyzing the Heartbeat of Music Sales]()

<img src = "https://images7.alphacoders.com/133/1333817.jpeg" width = 1500, height = 400>

This is an innovative SQL data analytics project designed to decode the intricacies of music sales within a dynamic marketplace. Through meticulous database analysis, the project delves into sales patterns, customer preferences, and genre popularity, unraveling the symphony of consumer behavior. Utilizing SQL queries, the project extracts valuable insights on top-selling artists, album trends, and regional preferences. From dissecting rhythmic patterns to harmonizing with customer demographics, HarmonyHub paints a comprehensive picture of the music retail landscape.

