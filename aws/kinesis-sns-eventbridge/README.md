# Order Streaming System using AWS (Kinesis, Lambda, EventBridge, SNS, SQS, Step Functions)

## Overview

This project demonstrates an event-driven, streaming data pipeline built using AWS services. It simulates an order processing system where events are ingested in real time, routed dynamically, and processed asynchronously.

The architecture emphasizes decoupling, scalability, and extensibility using managed AWS services.

---

## Architecture

```
Producer → Kinesis → Lambda → EventBridge → (SNS, Step Functions)
                                              │
                                              ▼
                                             SQS
                                              │
                                              ▼
                                          Lambda Worker
```

---

## Components

### 1. Producer (Python)

* Sends order events to Kinesis Data Stream
* Acts as the entry point for streaming data

### 2. Amazon Kinesis Data Stream

* Ingests real-time streaming data
* Provides buffering and scalability

### 3. Lambda (Kinesis Consumer)

* Triggered by Kinesis
* Decodes and processes records
* Publishes events to EventBridge

### 4. Amazon EventBridge

* Central event bus for routing events
* Uses rules to match events based on `source` and `detail-type`
* Routes events to multiple targets

### 5. Amazon SNS

* Sends notifications (e.g., email)
* Demonstrates fan-out messaging

### 6. AWS Step Functions

* Orchestrates workflow for order processing
* Sends messages to SQS

### 7. Amazon SQS

* Buffers messages for asynchronous processing
* Decouples processing from ingestion

### 8. Lambda (SQS Worker)

* Consumes messages from SQS
* Processes orders

---

## Event Structure

Events published to EventBridge follow this format:

```json
{
  "source": "app.orders",
  "detail-type": "OrderCreated",
  "detail": {
    "order_id": "string",
    "amount": "number",
    "customer_email": "string"
  }
}
```

---

## Setup Instructions

### 1. Create Kinesis Stream

* Name: `order-stream`
* Shards: 1

### 2. Create SQS Queue

* Name: `order-queue`

### 3. Create SNS Topic

* Name: `order-notifications`
* Add email subscription and confirm

### 4. Create Lambda Functions

#### Kinesis Consumer Lambda

* Runtime: Python 3.x
* Trigger: Kinesis (`order-stream`)
* Permission required:

  * `events:PutEvents`

#### SQS Worker Lambda

* Trigger: SQS (`order-queue`)

### 5. Create EventBridge Rule

Event pattern:

```json
{
  "source": ["app.orders"],
  "detail-type": ["OrderCreated"]
}
```

Targets:

* SNS topic
* Step Function

### 6. Create Step Function

* Sends event detail to SQS
* Requires permission:

  * `sqs:SendMessage`

---

## Running the Project

1. Install dependencies:

```bash
pip install boto3
```

2. Run producer:

```bash
python producer.py
```

---

## Expected Behavior

* Events are sent to Kinesis
* Lambda processes and forwards to EventBridge
* EventBridge routes events to:

  * SNS (email notification)
  * Step Function (workflow)
* Step Function sends messages to SQS
* Worker Lambda processes messages

---

## Key Concepts Demonstrated

* Event-driven architecture
* Stream processing with Kinesis
* Event routing with EventBridge
* Fan-out using SNS
* Workflow orchestration with Step Functions
* Asynchronous processing with SQS
* Decoupled microservices design

---

## Possible Enhancements

* Add Dead Letter Queues (DLQ) for failure handling
* Implement retry policies in Step Functions
* Add schema validation before publishing events
* Store processed data in DynamoDB or S3
* Integrate analytics layer using Athena or Redshift
* Use infrastructure as code (Terraform or CDK)