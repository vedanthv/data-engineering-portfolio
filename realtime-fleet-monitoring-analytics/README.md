# Realtime Fleet Monitoring Analysis with Flink

A real-time analytics pipeline for vehicle telemetry, driver scoring, alerts, trip intelligence, and operational dashboards.

This project demonstrates how to build a production-grade fleet intelligence system using modern streaming technologies such as Apache Flink, Kafka/Redpanda, ClickHouse, Docker, and FastAPI.

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

```mermaid

%%{ init: { 'theme': 'default', 'themeVariables': { 'primaryColor': '#ffffff', 'background': '#ffffff', 'lineColor': '#333333', 'fontSize': '14px' } } }%%

flowchart LR
    %% GROUP: Telemetry Producers
    subgraph PRODUCERS[Telemetry & Event Producers]
        A1[Vehicle GPS Device\n• Lat, Lon, Speed\n• Bearing, Accuracy]
        A2[OBD/CANBus Unit\n• RPM, Fuel, Engine Load\n• Diagnostics]
        A3[Driver Mobile App\n• Driver Status\n• Trip Events]
    end

    %% Redpanda ingestion
    subgraph REDPANDA[Redpanda (Kafka API)]
        RP1[(fleet.telemetry.raw)]
        RP2[(fleet.trip.events)]
        RP3[(fleet.events.driver)]
        RP4[(fleet.alerts.outbound)]
    end

    %% Flink processing
    subgraph FLINK[Apache Flink\nStreaming + SQL + CEP]
        F1[Telemetry Stream Processing\n• Cleaning/Validation\n• Coordinate transformations]
        F2[Sessionization Engine\n• Trip start/end\n• Idle detection\n• Distance computation]
        F3[Behavior Scoring Engine\n• Overspeeding\n• Harsh brake\n• Window aggregations]
        F4[CEP Rule Engine\n• Overspeed alerts\n• Idle > X min\n• Route deviation]
        F5[Sink Operators → ClickHouse]
    end

    %% ClickHouse Analytics
    subgraph CLICKHOUSE[ClickHouse OLAP]
        CH1[(fact_telemetry)]
        CH2[(fact_trip_sessions)]
        CH3[(fact_driver_behavior)]
        CH4[(fact_alerts)]
        CH5[(Materialized Views)]
    end

    %% Metabase Layer
    subgraph METABASE[Metabase Dashboards]
        M1[Driver Scorecards]
        M2[Trip Analytics]
        M3[Fleet Utilization KPIs]
        M4[Alerting & Ops Dashboard]
        M5[Heatmaps / Geo Visualizations]
    end

    %% FLOWS
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