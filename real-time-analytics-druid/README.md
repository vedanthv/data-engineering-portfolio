# 💵 🦹 FlashMetrics Financial Intelligence with Apache Druid

# What is Apache Druid?

# Components of Apache Druid

# Case Studies and Use in Popular Applications

# Trying it out with One Financial Accounts Table

Here are some visuals where I try out Apache Druid with just one table.

- There is only one broker that consumes data from a python file that has code to produce 100,000 messages per second.
- All components listed above are spun up as shown in the video demo.
- There is a common zookeeper that manages both the broker and druid services.
- The entire setup is on a ```t2.medium``` EC2 instance type and ```ubuntu 24.04``` image.
- The demo and the benchmarking was done on a non docker setup but you can use the ```docker-compose.yml``` script in the repo to follow along with Docker pre setup.
- **Cost of AWS Services on Avg** : Around 8$ over a period of 3 weeks and 100 hours of uptime.

## Video Demo

https://github.com/user-attachments/assets/dcb3ac53-7145-4338-b8d9-aee9944aa410

## Overview

![alt text](image-3.png)

## Extensions

![alt text](image-4.png)

## Services Running

![alt text](image-5.png)

## Leader and Worker Node

![alt text](image-6.png)

## Parsed Data from JSON

![alt text](image-7.png)

## Partitioning by Timestamp

![alt text](image-8.png)

Druid partitions data based on the primary time column of your data. This column is stored internally in Druid as __time.

## Realtime Filtering Capability

![alt text](image-9.png)
Here I have filtered rows where the transaction type is "payment". 

## Query Granularity

![alt text](image-10.png)

Granularity determines how to bucket data across the time dimension, or how to aggregate data by hour, day, minute, etc and defines how it is stored. The granularity formats here apply also to segmentGranularity and queryGranularity in the granularitySpec section of the the ingestion spec.

## Powerful Feature of Druid : Efficient Partition by Time

Configure how Druid will partition data.

Druid datasources are always partitioned by time into time chunks (Primary partitioning), and each time chunk contains one or more segments (Secondary partitioning).

## Tuning Feature

It decides various factors like the number of rows that can be stored in the memory before pushing it to the disk.

Refer : https://druid.apache.org/docs/31.0.0/ingestion/ingestion-spec/#tuningconfig

## Final Nail : JSON Ingestion Spec

- Note that Druid tries to keep data in memory cache as much as possible before moving it to the db.

- The ingestion spec json gives details of all the transformations and filtering that we did.

![alt text](image-11.png)

## Submitting the Spec to the Supervisor

![alt text](image-12.png)

![alt text](image-14.png)

## Supervisor Indexes the data in the **kttm** topic

![alt text](image-15.png)

The status of each task running on the supervisor port 8100 is displayed here

![alt text](image-16.png)

## Segmentation of the Data by Time

- In the below example there is one segment for each day.

- Spapshot versioning of the data in each segment takes place at regular intervals.

- We can also see various otther metrics like replicas, replica factor, IsAvailable? , IsActive? , IsRealTime? etc..

![alt text](image-17.png)

- This feature is called "auto batching" in Druid.

- If a segment is corrupted we can rebuild that segment without affecting the other partitions of the  data.

## Realtime Superfast Querying

Once the supervisor builds the table for us with the partitions, we can start querying the data.
Look at how fast the queries get executed!!

Barely takes 0.1s to read in 800 records!

![fast_query_execution_1](https://github.com/user-attachments/assets/b19d130c-2687-42bc-a80c-8b429e70e367)

## Benchmarking

Increasing the producer speed to send 1000 records per sec...

![benchmarking_1000](https://github.com/user-attachments/assets/f17ba663-bd11-4bb3-813a-de7835b9a17a)

100000 records per second...

![alt text](image-19.png)

Grouping Operations for 400,000+ records happens within 0.30 seconds!

![alt text](image-20.png)

## Time Aggregation

Let us do some aggregation based on the time where the total_amount (basically the cash from bank)
that flows in and out per minute.

![alt text](image-21.png)

# Troubleshooting Guide

## Non Docker Vanilla Setup

### Very Important Stuff to Note

I sepnt lot of time SSH'ing into the EC2 instance from VSCode.

Its kind of pointless and doesnt work like before, so best way if you are not using Docker is to 
create multiple terminals and SSH into each one of them.

We need to do this because the SSH session terminates within 15-20 min, and then we need to stop the EC2, get the new public address and again connect. Its a pain. [Solution??](https://codewithsusan.com/notes/vscode-remote-ssh-connection-issues#:~:text=Why%20this%20happens,is%20to%20restart%20the%20server.) 

![alt text](image-13.png)

So...

In one terminal, SSH into it ... like this : ssh -i "D:\...pem" ubuntu@ec2-xx-xxx-xxx-xxx.ap-south-1.compute.amazonaws.com

Start the broker service as mentioned below... in *Setup Kafka Broker*

Open another terminal, SSH into it... in same way and run the Druid setup instructions in *Setup Druid*

In the 3rd and final terminal, run python3 main.py to start generating the messages. make sure the topic name and the broker ports are correct.

Well one disadv of this is that we cant use VSCode to edit anything :( so I need to figure out a solution to this fast.

But... if you are not using Docker then the only real thing to code would be the main.py file that produces the data which you can do on Vim also :)

### Setup Druid

https://dev.to/aws-builders/how-to-deploy-apache-druid-on-aws-ec2-instance-5hib

```
1) sudo apt update -y
2) sudo apt install openjdk-8-jdk -y
3) wget https://dlcdn.apache.org/druid/29.0.1/apache-druid-29.0.1-bin.tar.gz (Last updated version)
4) tar -xzf apache-druid-29.0.1-bin.tar.gz
5) cd apache-druid-29.0.1
6) export JAVA_HOME=/usr/lib/jvm/java-8-openjdk-amd64
7) export DRUID_HOME=/home/ubuntu/apache-druid-29.0.1
8) PATH=$JAVA_HOME/bin:$DRUID_HOME/bin:$PATH
```

### Run Druid

```
./bin/start-micro-quickstart
```

Druid will run on 

```
AWS Public IPv4 address:8888
``` 
Not on your localhost.

### Set up basic Kafka Broker

https://kafka.apache.org/quickstart

```
$ tar -xzf kafka_2.13-3.9.0.tgz
$ cd kafka_2.13-3.9.0
```

### Install Java JDK 8

https://www.digitalocean.com/community/tutorials/how-to-install-java-with-apt-on-ubuntu-22-04

### Start Broker

```
$ ./bin/kafka-server-start.sh config/server.properties
```


Create topic

```
./bin/kafka-topics.sh --create --topic kttm --bootstrap-server localhost:9092
```

**Error : Cluster Id Doesnt match**

https://stackoverflow.com/questions/59481878/unable-to-start-kafka-with-zookeeper-kafka-common-inconsistentclusteridexceptio

![alt text](image.png)

![alt text](image-1.png)

**IMP!!! Since Druid itself starts a Zookeeper we dont need to start one more while creating broker.**

### Error: Port 2181 is already binded

https://stackoverflow.com/questions/11583562/how-to-kill-a-process-running-on-particular-port-in-linux

![alt text](image-2.png)

Prefix all commands by sudo

### What if processes on port 2181 keep spawning?

https://stackoverflow.com/questions/59481878/unable-to-start-kafka-with-zookeeper-kafka-common-inconsistentclusteridexceptio

![alt text](image.png)

![alt text](image-1.png)

This legit works for all kinds of errors!!

### Start Producing Data into the broker

- Now that everything is setup, 

Run

```
python3 main.py
```

To start the creation of messages into the message queue.

### How to Configure Druid to read from the broker and the topic

https://druid.apache.org/docs/latest/tutorials/tutorial-kafka/#load-data-into-druid


