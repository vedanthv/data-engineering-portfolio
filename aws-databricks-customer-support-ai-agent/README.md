# Customer Support AI Platform (Event-Driven + RAG AI Agent)

## Overview

This project implements a production-grade, event-driven data platform for a Customer Support AI system. It simulates multiple microservices generating realistic, stateful events and processes them through a scalable AWS ingestion pipeline, ultimately enabling downstream analytics and Retrieval-Augmented Generation (RAG) workflows in Databricks.

The system is designed to reflect real-world enterprise architecture patterns including decoupling, streaming ingestion, fault tolerance, and extensibility.

---

## Business Use Cases

### 1. Customer Support Automation

The platform ingests events from orders, payments, logistics, and support systems to build a unified knowledge base. This data can be used by an AI chatbot to answer customer queries such as:

* Where is my order?
* Why did my payment fail?
* When will my package arrive?

---

### 2. Real-Time Issue Detection

Events such as payment failures, delivery delays, and escalations can be processed in near real time to:

* Trigger alerts
* Open support tickets automatically
* Notify operations teams

---

### 3. Customer Experience Analytics

User activity and support events can be analyzed to:

* Identify bottlenecks in delivery
* Measure customer satisfaction
* Track SLA adherence

---

### 4. Fraud Detection and Risk Scoring

Payment events enriched with metadata can be used for:

* Fraud detection pipelines
* Risk scoring models
* Monitoring suspicious transactions

---

### 5. Unified Data Platform for AI

All ingested data is stored in a data lake and later used to:

* Build embeddings
* Enable semantic search
* Power a RAG-based AI assistant

---

## Architecture Overview

### High-Level Flow

Producers → EventBridge → SNS → SQS → Lambda → Kinesis → S3 → Databricks

---

### Components

#### Producers (Python Multi-threaded Simulation)

* Simulate five microservices:

  * Orders
  * Payments
  * Logistics
  * Support Tickets
  * User Activity
* Each service generates approximately 30 fields per event
* Maintains stateful consistency (e.g., order lifecycle progression)

---

#### Amazon EventBridge

* Acts as the central event bus
* Receives events from all producers
* Routes events to downstream targets using rule-based filtering
* Enables loose coupling between producers and consumers

---

#### Amazon SNS (Simple Notification Service)

* Provides fanout capability
* Broadcasts events to multiple subscribers
* Enables extensibility without modifying producers

---

#### Amazon SQS (Simple Queue Service)

* Buffers incoming messages
* Ensures reliable, asynchronous processing
* Protects downstream systems from traffic spikes

---

#### AWS Lambda

* Consumes messages from SQS
* Performs transformation and enrichment
* Sends processed data to Kinesis for streaming ingestion

---

#### Amazon Kinesis

* Serves as the streaming backbone
* Handles high-throughput event ingestion
* Preserves ordering within shards
* Enables replay capability

---

#### Amazon S3 (Data Lake)

* Stores raw and processed data
* Acts as the central storage layer for analytics and AI workloads
* Organizes data using partitioned structure

---

#### Databricks (Downstream Layer)

* Reads data from S3
* Builds Delta Lake tables
* Generates embeddings for RAG
* Provides vector search and model serving endpoints

---

## Event Flow

1. Producers generate events and send them to EventBridge
2. EventBridge routes events to SNS topics based on source
3. SNS broadcasts messages to subscribed SQS queues
4. SQS stores messages and triggers Lambda consumers
5. Lambda processes and forwards events to Kinesis
6. Kinesis streams data to S3 via Firehose
7. Databricks consumes data from S3 for analytics and AI

---

## Data Simulation Details

### Key Features

* Multi-threaded simulation of independent services
* Stateful order lifecycle:

  * CREATED → CONFIRMED → SHIPPED → OUT_FOR_DELIVERY → DELIVERED
* Cross-service consistency:

  * Payments linked to orders
  * Shipments triggered post-shipping
  * Tickets generated probabilistically

---

### Example Data Domains

| Domain        | Description                              |
| ------------- | ---------------------------------------- |
| Orders        | Order lifecycle and transaction data     |
| Payments      | Payment processing and failure scenarios |
| Logistics     | Shipment tracking and delivery data      |
| Support       | Customer issue tracking and resolution   |
| User Activity | Behavioral analytics and session data    |

---

## Security and IAM

### EventBridge to SNS

* SNS topic policy allows `events.amazonaws.com` to publish

### SNS to SQS

* SQS policy allows `sns.amazonaws.com` with source ARN restriction

### Lambda Permissions

* Read from SQS
* Write to Kinesis
* Log to CloudWatch

---

## Design Principles

### Decoupling

Each component operates independently, allowing changes without affecting upstream systems.

---

### Scalability

* SQS buffers traffic spikes
* Lambda scales automatically
* Kinesis supports high throughput

---

### Fault Tolerance

* Messages are persisted in SQS
* Retry mechanisms in Lambda
* Replay capability in Kinesis

---

### Extensibility

New consumers (e.g., fraud detection, analytics) can be added without modifying producers.

---

### Observability

* CloudWatch logs for Lambda
* Metrics for EventBridge, SNS, SQS, and Kinesis

---

## Why This Architecture

### EventBridge

Used for intelligent routing and decoupling producers from consumers.

---

### SNS

Provides fanout capability to support multiple downstream systems.

---

### SQS

Ensures reliable message delivery and absorbs traffic spikes.

---

### Lambda

Enables lightweight, serverless processing.

---

### Kinesis

Supports real-time streaming and replayability.

---

### S3

Acts as a scalable and cost-effective data lake.

---

### Databricks

Provides advanced analytics, Delta Lake, and RAG capabilities.

---

## Future Enhancements

* Add Step Functions for orchestration
* Implement Dead Letter Queues (DLQ)
* Introduce schema registry for event validation
* Add real-time dashboards
* Implement feedback loop for AI model improvement

---

## How to Run

1. Configure AWS credentials locally
2. Create EventBridge event bus
3. Set up SNS topics and SQS queues
4. Configure policies for SNS and SQS
5. Deploy Lambda consumers
6. Run the multi-threaded producer script
7. Monitor events in AWS services


This project demonstrates a full-stack, event-driven data platform integrating AWS services with modern data engineering and AI patterns. It highlights best practices in scalability, decoupling, and real-time processing while enabling advanced use cases such as RAG-based customer support systems.
