# Realtime Fleet Monitoring Analysis with Flink

This project solves a core problem in modern fleet and mobility operations: the need to monitor thousands of vehicles in real time, detect risky driving patterns early, and optimize operational efficiency. 

Businesses such as logistics companies, ride-hailing platforms, last-mile delivery services, and asset-tracking providers rely on continuous telemetry from vehicles to ensure safety, reduce fuel and maintenance costs, and respond instantly to incidents. 

By processing high-velocity telemetry streams with Apache Flink, this system provides immediate insights into trip behavior, driver performance, vehicle health, and operational anomalies. 

The resulting real-time analytics enable businesses to make faster decisions, prevent accidents, minimize downtime, improve driver accountability, and enhance customer service through more accurate ETAs and proactive issue detection.

Below is a dashboard that's benchmarked to ingested **100,000 events per second** into Redpanda, transformed in realtime using Apache Flink, storing the transformed data in Clickhouse and using Metabase for realtime 5 second refresh dashboards.

<img src="/workspaces/data-engineering-portfolio/realtime-fleet-monitoring-analytics/telemetry_v3.gif" width="2000"/>

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

<img width="1536" height="1024" alt="image" src="https://github.com/user-attachments/assets/e523e59c-7640-4bfe-9e37-7a76ef34546a" />

<img width="1704" height="560" alt="image" src="https://github.com/user-attachments/assets/395f4ea9-691f-4e33-a1a0-295d849f797e" />

### Flink Pipelines and Clickhouse Architecture

<img width="1569" height="786" alt="image" src="https://github.com/user-attachments/assets/de95bed8-a841-4a2b-b238-233d8b72f20b" />

### Docker Deployment

<img width="1658" height="710" alt="image" src="https://github.com/user-attachments/assets/40f61625-59e3-4503-b752-38e6ecba7faa" />

### Kubernetes Deployment

<img width="975" height="745" alt="image" src="https://github.com/user-attachments/assets/0655879a-baae-4f75-adf5-a8bda18a5a85" />

## Visuals

Click [here](https://github.com/vedanthv/data-engineering-portfolio/blob/main/realtime-fleet-monitoring-analytics/visuals.md) to view some visuals of the project.
