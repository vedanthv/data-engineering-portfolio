## [UserMingle : Kafka-Driven User Profile Streaming]() 🧔

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

**Setup and Requirements**

1. Clone the repository
```git clone https://github.com/vedanthv/data-engineering-portfolio.git```

2. Navigate to the project directory:
```cd data-engineering-portfolio/user-mingle```

3. Run Docker Compose to Spin Up the Service
```docker-compose up```

**Demo**

**Apache Airflow DAG**

![image](https://github.com/vedanthv/data-engineering-portfolio/assets/44313631/3f34b376-804b-4534-a2c6-0225049350c0)

**Confluent Control Center Consumption Stats and Health of Broker**

![image](https://github.com/vedanthv/data-engineering-portfolio/assets/44313631/0bc1fda0-8fd6-43cb-96e3-648f84fba894)

**Confluent Control Center Message Queue**

![image](https://github.com/vedanthv/data-engineering-portfolio/assets/44313631/ed4c9f80-0248-4502-b5c2-ddbd43ea7d81)

**Video Demo - DAG Running and Message Queue**

https://github.com/vedanthv/data-engineering-portfolio/assets/44313631/6a98c2c5-23f0-4c31-8fe1-4ff306cc15be
