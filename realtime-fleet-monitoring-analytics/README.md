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

```mermaid

%%{ init: { 'theme': 'default', 'themeVariables': { 'primaryColor': '#ffffff', 'background': '#ffffff', 'lineColor': '#333333', 'fontSize': '14px' } } }%%

flowchart LR

  %% --- Telemetry & Event Producers ---
  subgraph Producers["<b>Telemetry & Event Producers</b>"]
    A1["<b>Vehicle GPS Device</b><br>Lat, Lon, Speed"]
    A2["<b>OBD / CANBus Unit</b><br>RPM, Fuel, Diagnostics"]
    A3["<b>Driver Mobile App</b><br>Driver Status, Trip Events"]
  end

  %% --- Redpanda ---
  subgraph RedpandaCluster["<b>Redpanda – Streaming Platform</b>"]
    RP1["<b>Topic:</b> fleet.telemetry.raw"]
    RP2["<b>Topic:</b> fleet.trip.events"]
    RP3["<b>Topic:</b> fleet.events.driver"]
    RP4["<b>Topic:</b> fleet.alerts.outbound"]
  end

  %% --- Flink Layer ---
  subgraph FlinkLayer["<b>Apache Flink – Streaming, SQL, CEP</b>"]
    F1["<b>Telemetry Processing</b><br>Cleaning, Validation, Enrichment"]
    F2["<b>Sessionization Engine</b><br>Trip Start/End, Idle Detection, Distance"]
    F3["<b>Driver Behavior Scoring</b><br>Overspeed, Harsh Brake, Windows"]
    F4["<b>CEP Rule Engine</b><br>Overspeed, Idle, Deviation"]
    F5["<b>ClickHouse Sink Operators</b><br>JDBC / HTTP Sink"]
  end

  %% --- ClickHouse Layer ---
  subgraph ClickHouseDB["<b>ClickHouse – OLAP Warehouse</b>"]
    CH1["<b>fact_telemetry</b>"]
    CH2["<b>fact_trip_sessions</b>"]
    CH3["<b>fact_driver_behavior</b>"]
    CH4["<b>fact_alerts</b>"]
    CH5["<b>Materialized Views</b><br>Pre-Aggregated KPIs"]
  end

  %% --- Metabase Layer ---
  subgraph MetabaseLayer["<b>Metabase – BI & Dashboards</b>"]
    M1["<b>Driver Scorecards</b>"]
    M2["<b>Trip Analytics</b>"]
    M3["<b>Fleet Utilization KPIs</b>"]
    M4["<b>Alert Monitoring</b>"]
    M5["<b>Geo / Heatmaps</b>"]
  end

  %% --- Flows ---
  A1 --> RP1
  A2 --> RP1
  A3 --> RP2
  A3 --> RP3

  RP1 --> F1
  RP2 --> F2
  RP3 --> F3

  F1 --> F2
  F2 --> F3
  F3 --> F4
  F4 --> RP4
  F4 --> F5

  F5 --> CH1
  F5 --> CH2
  F5 --> CH3
  RP4 --> CH4

  CH1 --> M2
  CH2 --> M2
  CH3 --> M1
  CH4 --> M4
  CH1 --> M5
  CH3 --> M3


```
### Flink Pipelines and Clickhouse Architecture
```mermaid
%%{ init: { 'theme': 'default', 'themeVariables': { 'primaryColor': '#ffffff', 'background': '#ffffff', 'lineColor': '#333333', 'fontSize': '14px' } } }%%

flowchart TB

  %% ==============================
  %% Redpanda Topics
  %% ==============================
  subgraph RedpandaTopics["<b>Redpanda Topics</b>"]
    RP_TEL["<b>fleet.telemetry.raw</b><br>High-frequency GPS/OBD events"]
    RP_TRIP["<b>fleet.trip.events</b><br>Trip start/stop, status events"]
    RP_DRV["<b>fleet.events.driver</b><br>Driver status, login/logout"]
    RP_ALERTS["<b>fleet.alerts.outbound</b><br>Realtime alerts for ops"]
  end

  %% ==============================
  %% Flink Job 1 - Raw Telemetry → fact_telemetry
  %% ==============================
  subgraph Job1["<b>Flink Job 1</b><br><b>Telemetry Enrichment & Storage</b>"]
    J1_SRC["<b>Source</b><br>Kafka Source from<br>fleet.telemetry.raw"]
    J1_CLEAN["<b>Validate & Clean</b><br>Drop bad records,<br>fix nulls, parse JSON"]
    J1_ENR["<b>Enrich</b><br>Attach vehicle/driver dims<br>Compute H3 cell, bearing, etc."]
    J1_SINK["<b>Sink</b><br>ClickHouse<br>fact_telemetry"]
  end

  %% ==============================
  %% Flink Job 2 - Trip / Sessionization
  %% ==============================
  subgraph Job2["<b>Flink Job 2</b><br><b>Trip & Sessionization</b>"]
    J2_SRC_TEL["<b>Source</b><br>Kafka Source from<br>fleet.telemetry.raw"]
    J2_SRC_TRIP["<b>Side Input</b><br>fleet.trip.events<br>(explicit starts/stops)"]
    J2_KEY["<b>KeyBy vehicle_id</b>"]
    J2_SESSION["<b>Session Windows</b><br>Trip sessions by gaps<br>Idle detection"]
    J2_AGG["<b>Aggregate</b><br>Distance, duration,<br>idle_time, avg speed"]
    J2_SINK["<b>Sink</b><br>ClickHouse<br>fact_trip_sessions"]
  end

  %% ==============================
  %% Flink Job 3 - Driver Behavior Scoring
  %% ==============================
  subgraph Job3["<b>Flink Job 3</b><br><b>Driver Behavior Scoring</b>"]
    J3_SRC_TEL["<b>Source</b><br>fleet.telemetry.raw"]
    J3_KEY["<b>KeyBy driver_id</b>"]
    J3_WINDOWS["<b>Hopping / Tumbling Windows</b><br>1–5 min windows"]
    J3_METRICS["<b>Metrics</b><br>overspeed_cnt,<br>harsh_brake_cnt,<br>idle_cnt"]
    J3_SCORE["<b>Score Calculation</b><br>Weighted risk score"]
    J3_SINK["<b>Sink</b><br>ClickHouse<br>fact_driver_behavior"]
  end

  %% ==============================
  %% Flink Job 4 - CEP Alerts
  %% ==============================
  subgraph Job4["<b>Flink Job 4</b><br><b>CEP-based Alerting</b>"]
    J4_SRC_TEL["<b>Source</b><br>fleet.telemetry.raw"]
    J4_SRC_DRV["<b>Side Input</b><br>fleet.events.driver"]
    J4_KEY["<b>KeyBy vehicle_id / driver_id</b>"]
    J4_CEP["<b>CEP Patterns</b><br>Overspeed sequences,<br>long idle, harsh events"]
    J4_BUILD["<b>Build Alert Payload</b><br>title, severity,<br>trip_id, coords"]
    J4_SINK_TOPIC["<b>Sink</b><br>Redpanda<br>fleet.alerts.outbound"]
    J4_SINK_CH["<b>Sink</b><br>ClickHouse<br>fact_alerts"]
  end

  %% ==============================
  %% ClickHouse Tables
  %% ==============================
  subgraph ClickHouse["<b>ClickHouse Tables</b>"]
    CH_FTEL["<b>fact_telemetry</b>"]
    CH_TRIP["<b>fact_trip_sessions</b>"]
    CH_BEH["<b>fact_driver_behavior</b>"]
    CH_ALERT["<b>fact_alerts</b>"]
  end

  %% ---------- WIRES: Redpanda → Flink ----------
  RP_TEL --> J1_SRC
  RP_TEL --> J2_SRC_TEL
  RP_TEL --> J3_SRC_TEL
  RP_TEL --> J4_SRC_TEL

  RP_TRIP --> J2_SRC_TRIP
  RP_DRV --> J4_SRC_DRV
  RP_DRV --> J3_KEY

  %% ---------- Job 1 flow ----------
  J1_SRC --> J1_CLEAN --> J1_ENR --> J1_SINK
  J1_SINK --> CH_FTEL

  %% ---------- Job 2 flow ----------
  J2_SRC_TEL --> J2_KEY
  J2_SRC_TRIP --> J2_KEY
  J2_KEY --> J2_SESSION --> J2_AGG --> J2_SINK
  J2_SINK --> CH_TRIP

  %% ---------- Job 3 flow ----------
  J3_SRC_TEL --> J3_KEY --> J3_WINDOWS --> J3_METRICS --> J3_SCORE --> J3_SINK
  J3_SINK --> CH_BEH

  %% ---------- Job 4 flow ----------
  J4_SRC_TEL --> J4_KEY
  J4_SRC_DRV --> J4_KEY
  J4_KEY --> J4_CEP --> J4_BUILD
  J4_BUILD --> J4_SINK_TOPIC
  J4_BUILD --> J4_SINK_CH
  J4_SINK_CH --> CH_ALERT
  J4_SINK_TOPIC --> RP_ALERTS
```

### Docker Deployment

```mermaid
%%{ init: { 'theme': 'default', 'themeVariables': { 'primaryColor': '#ffffff', 'background': '#ffffff', 'lineColor': '#333333', 'fontSize': '14px' } } }%%
flowchart LR
  %% Styles
  classDef broker fill:#e3f2fd,stroke:#1565c0,stroke-width:1px;
  classDef console fill:#ede7f6,stroke:#5e35b1,stroke-width:1px;
  classDef flink fill:#e8f5e9,stroke:#2e7d32,stroke-width:1px;
  classDef db fill:#fff3e0,stroke:#ef6c00,stroke-width:1px;
  classDef ext fill:#f5f5f5,stroke:#424242,stroke-width:1px;

  subgraph NET["Docker network: realtimeanalytics"]

    %% Redpanda brokers
    RP1["redpanda-1\nRedpanda broker\nPLAINTEXT 29092\nOUTSIDE 9092\nPandaproxy 28082 and 8082"]:::broker
    RP2["redpanda-2\nRedpanda broker\nPLAINTEXT 29093\nOUTSIDE 9093\nPandaproxy 28083 and 8083"]:::broker

    RP2 -->|"seeds redpanda-1:33145"| RP1

    %% Redpanda Console
    RPC["redpanda-console\nRedpanda Console\nport 8080"]:::console
    RPC -->|"kafka brokers redpanda-1:29092"| RP1
    RPC -->|"kafka brokers redpanda-2:29093"| RP2

    %% Flink cluster
    JM["jobmanager\nFlink JobManager\nUI 8081"]:::flink
    TM["taskmanager\nFlink TaskManager"]:::flink
    SC["sql-client\nFlink SQL Client\nsleep infinity"]:::flink

    TM -->|"RPC and dataflow"| JM
    SC -->|"RPC / REST"| JM

    %% ClickHouse
    CH["clickhouse\nClickHouse Server\nHTTP 8123\nNative 9000"]:::db

    %% Data flows (logical)
    JM -->|"Kafka source or sink"| RP1
    JM -->|"Kafka source or sink"| RP2
    JM -->|"analytics to ClickHouse"| CH

  end

  %% External host access
  subgraph EXT["Host machine (localhost)"]
    HOST["Apps and tools and browser"]:::ext
  end

  HOST -->|"Kafka client to port 9092"| RP1
  HOST -->|"Kafka client to port 9093"| RP2
  HOST -->|"Web UI on port 8080"| RPC
  HOST -->|"Flink UI on port 8081"| JM
  HOST -->|"Pandaproxy on 8082 and 8083"| RP1
  HOST -->|"HTTP or Native on 8123 or 9000"| CH
```

### Kubernetes Deployment

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

