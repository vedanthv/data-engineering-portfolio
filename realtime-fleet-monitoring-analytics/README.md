# Realtime Fleet Monitoring Analysis with Flink

A real-time analytics pipeline for vehicle telemetry, driver scoring, alerts, trip intelligence, and operational dashboards.

This project demonstrates how to build a production-grade fleet intelligence system using modern streaming technologies such as Apache Flink, Kafka/Redpanda, ClickHouse, Docker, and Kubernetes.

It captures raw telemetry from vehicles, processes it in real time, detects risky behaviors, computes trip/session analytics, raises alerts, and exposes the results via APIs and dashboards.

## Business Use Cases

### 1. Driver Behavior Monitoring

- Detect overspeeding, harsh braking, aggressive acceleration.
- Score drivers over rolling windows.
- Reduce accidents and insurance premiums.

### 2. Trip Intelligence

- Track trip start/end automatically.
- Compute distance, duration, idle time.
- Monitor ETA accuracy and route compliance.

### 3. Delivery Optimization

- Detect bottlenecks in last-mile delivery.
- Measure loading/unloading delays.
- Improve SLA adherence.

### 4. Fleet Utilization Insights

- Under-utilized vehicles.
- Multi-trip anomalies.
- Asset downtime monitoring.

### 6. Real-time Alerts & Operations Dashboard

- Overspeed alerts.
- Idling alerts.
- Geofence violations.
- SOS & crash detection.

## Architecture

---

| Layer                               | Component                                              | Purpose / Role                                                                 | Key Responsibilities                                                                                                                                                                                                          | Why This Component?                                                                                                                      |
| ----------------------------------- | ------------------------------------------------------ | ------------------------------------------------------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------- |
| **Ingestion Layer**                 | **Redpanda (Kafka-API Compatible Streaming Platform)** | High-throughput ingestion of telemetry, driver events, trip events, and alerts | • Accepts JSON telemetry events at high EPS<br>• Durable, replicated event storage<br>• Topic partitioning for parallel consumption<br>• Acts as source of truth for raw events                                               | • Drop-in Kafka replacement but faster + simpler<br>• No ZooKeeper<br>• Low-latency writes suitable for IoT telemetry                    |
| **Stream Processing Layer**         | **Apache Flink (Streaming SQL + CEP)**                 | Real-time computation, enrichment, sessionization, and alerting                | • Windowed aggregations (tumble/hop/session)<br>• Driver behavior scoring<br>• Trip/session detection<br>• CEP rules for overspeed, harsh brake<br>• Data cleansing + transformations<br>• Writes prepared data to ClickHouse | • Best stream processor for stateful workloads<br>• Checkpoints, exactly-once semantics<br>• SQL + Python + DataStream API flexibility   |
| **Storage / OLAP Layer**            | **ClickHouse (OLAP Columnar DB)**                      | Fast analytics + dashboards on telemetry data                                  | • Stores telemetry facts<br>• Stores trip/session facts<br>• Driver score marts<br>• Alert history<br>• Materialized views for aggregation<br>• Sub-second queries for dashboards                                             | • Extremely fast for time-series & geo data<br>• MergeTree handles millions of rows/sec<br>• Affordable and scalable for fleet analytics |
| **Analytics / Visualization Layer** | **Metabase**                                           | BI dashboards + self-service exploration                                       | • Driver score dashboards<br>• Trip KPIs<br>• Alert trends<br>• Heatmaps (with custom queries)<br>• Ad hoc analysis for operations team                                                                                       | • Simple, free, and integrates directly with ClickHouse<br>• Great for internal fleet operations dashboards                              |

### High Level Architecture

<img width="1704" height="560" alt="image" src="https://github.com/user-attachments/assets/395f4ea9-691f-4e33-a1a0-295d849f797e" />

### Flink Pipelines and Clickhouse Architecture

<img width="1569" height="786" alt="image" src="https://github.com/user-attachments/assets/de95bed8-a841-4a2b-b238-233d8b72f20b" />

### Docker Deployment

<img width="1658" height="710" alt="image" src="https://github.com/user-attachments/assets/40f61625-59e3-4503-b752-38e6ecba7faa" />

### Kubernetes Deployment

<<<<<<< HEAD
<img width="975" height="745" alt="image" src="https://github.com/user-attachments/assets/0655879a-baae-4f75-adf5-a8bda18a5a85" />

## Visuals

### Flink Dashboard

<img width="993" height="476" alt="image" src="https://github.com/user-attachments/assets/710ffb3b-6dfb-4615-b33e-91a116a6beff" />

### Job Graph for Trip Summaries

<img width="984" height="414" alt="image" src="https://github.com/user-attachments/assets/e7bc2595-1091-4881-83b9-5bb81fad0557" />

### Details with Execution Plan, No of Records Received and Sent

<img width="829" height="408" alt="image" src="https://github.com/user-attachments/assets/3230ba1f-b9dc-4e4e-8fee-1089c2acd99f" />

<img width="808" height="367" alt="image" src="https://github.com/user-attachments/assets/a15384fd-413f-4a2c-b616-d16ed9a90907" />

<img width="813" height="417" alt="image" src="https://github.com/user-attachments/assets/3afb1aef-430e-4902-a426-cc518f402c3c" />

### Redpanda Console with Topic Info

<img width="1097" height="543" alt="image" src="https://github.com/user-attachments/assets/b763f542-fb4c-481e-854d-fb1cff491f8e" />

### Main Data Producer Topic with 500k+ Messages

<img width="1186" height="641" alt="image" src="https://github.com/user-attachments/assets/c3f1c013-e692-4128-bab1-4b0dd66db3d2" />
=======
```mermaid
%%{ init: { 'theme': 'default', 'themeVariables': { 'primaryColor': '#ffffff', 'background': '#ffffff', 'lineColor': '#333333', 'fontSize': '14px' } } }%%

flowchart LR
  %% Styles
  classDef service fill:#e3f2fd,stroke:#1565c0,stroke-width:1px;
  classDef deploy fill:#e8f5e9,stroke:#2e7d32,stroke-width:1px;
  classDef config fill:#fff8e1,stroke:#ff8f00,stroke-width:1px;
  classDef app fill:#f3e5f5,stroke:#6a1b9a,stroke-width:1px;
  classDef db fill:#fbe9e7,stroke:#d84315,stroke-width:1px;

  subgraph NS["Kubernetes Namespace: telemetry"]

    %% Redpanda Cluster
    subgraph RP["Redpanda Brokers"]
      RP1S["Service: redpanda-1<br/>port 29092"]:::service
      RP1D["Deployment: redpanda-1<br/>Pod: redpanda (node-id=1)"]:::deploy

      RP2S["Service: redpanda-2<br/>port 29093"]:::service
      RP2D["Deployment: redpanda-2<br/>Pod: redpanda (node-id=2, seed=redpanda-1)"]:::deploy

      RP1S --> RP1D
      RP2S --> RP2D
      RP2D -->|seed| RP1D
    end

    %% Redpanda Console
    subgraph RPC["Redpanda Console"]
      RPCS["Service: redpanda-console<br/>port 8080"]:::service
      RPCD["Deployment: redpanda-console<br/>Pod: console"]:::deploy

      RPCS --> RPCD
      RPCD -->|brokers: 29092/29093| RP1S
      RPCD --> RP2S
    end

    %% Flink Cluster
    subgraph FL["Flink Cluster"]
      CM["ConfigMap: flink-config<br/>flink-conf.yaml"]:::config

      JMS["Service: jobmanager<br/>rpc 6123, ui 8081"]:::service
      JMD["Deployment: jobmanager<br/>Pod: jobmanager"]:::deploy
      TMD["Deployment: taskmanager<br/>Pod: taskmanager"]:::deploy
      SCD["Deployment: sql-client<br/>Pod: sql-client (sleep infinity)"]:::deploy

      CM --> JMD
      CM --> TMD
      CM --> SCD

      JMS --> JMD
      JMD <-->|control & coordination| TMD
      SCD -->|RPC / REST| JMS
    end

    %% ClickHouse
    subgraph CH["ClickHouse"]
      CHS["Service: clickhouse<br/>http 8123, native 9000"]:::service
      CHD["Deployment: clickhouse<br/>Pod: clickhouse-server"]:::db

      CHS --> CHD
    end

    %% Telemetry Producer
    subgraph TP["Telemetry Producer (Python)"]
      TPD["Deployment: telemetry-producer<br/>env KAFKA_BOOTSTRAP_SERVERS=redpanda-1:29092<br/>topic=fleet.prod.telemetry.raw"]:::app
    end

  end

  %% Data Flows
  TPD -->|produce telemetry<br/>fleet.prod.telemetry.raw| RP1S

  JMD -->|consume/produce Kafka| RP1S
  JMD --> RP2S

  JMD -->|write analytics| CHS
```
Click here for [visuals]()
>>>>>>> e56e621 ([code] clickhouse-transforms metabase setup)

