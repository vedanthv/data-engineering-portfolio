## Cold-Chain Monitoring for Grocery & Dark Stores

Cold-chain monitoring is a critical requirement in grocery retail, convenience stores, and dark-store fulfillment centers. Refrigerated and frozen storage units—such as chillers, freezers, walk-in cold rooms, and refrigerated racks—must consistently maintain strict temperature ranges to keep perishable food safe. Even small deviations can lead to product spoilage, inventory loss, regulatory non-compliance, increased costs, and potential health risks. This project implements a real-time cold-chain monitoring platform designed to simulate sensor data and process it through a full modern streaming-analytics pipeline using Redpanda, Flink, ClickHouse, and Metabase, all deployed via Docker Compose on an EC2 instance.

The primary goal of the system is to continuously ingest, process, and analyze temperature and door-state data coming from cold-storage assets in grocery and dark-store environments. The project includes a realistic data generator that simulates multiple refrigeration assets producing telemetry at fixed intervals. This simulated data mimics real-world behaviors such as cooling/heating patterns, door-open temperature spikes, occasional excursions outside safe ranges, noise in readings, and different behavior for chillers versus freezers. The generator acts as the IoT edge layer, producing JSON events to Redpanda topics using Kafka API compatibility.

From a business standpoint, this system replicates the critical functionality used by large grocery chains to maintain compliance and reduce waste. Continuous monitoring allows companies to reduce spoilage, detect failing equipment early, monitor operational behavior such as frequent door openings, and maintain audit-ready logs of temperature performance for food safety regulators. In dark-store environments—where rapid picking and fulfillment are essential—underperforming cold storage can directly impact order quality and customer satisfaction. The real-time nature of the system helps detect and act on issues before they escalate, potentially saving per incident.

Overall, the Cold-Chain Monitoring for Grocery & Dark Stores project provides a complete, realistic, and technically rich solution that simulates and processes operational IoT-like data at scale. It reflects the architecture used in modern retail operations for ensuring product safety, preventing inventory loss, optimizing store operations, and achieving compliance. Through Redpanda, Flink, ClickHouse, and Metabase, the project delivers a robust analytics pipeline that transforms raw temperature telemetry into actionable insights and operational dashboards suitable for real-world environments.

### Data Generation Parameters

1. ASSET_COUNT

Number of individual refrigeration units simulated.
If set to 50, the generator behaves as though 50 separate units are reporting data.

Business meaning: Each record represents one real device in a cold-chain network.

2. FREEZER_RATIO

Fraction of assets that are freezers instead of fridges.
For example, 0.2 means 20% are freezers and 80% are chillers.

Business meaning: Reflects the mix of frozen and chilled storage equipment in actual operations.

3. SETPOINT_MEAN and SETPOINT_JITTER

SETPOINT_MEAN: Average target temperature for chilled units (e.g., 4.5 °C).

SETPOINT_JITTER: Small variation so that not all units have exactly the same setpoint.

Business meaning: In reality, no two fridges are identical; each may operate at a slightly different optimal temperature.

4. FREEZER_SETPOINT, FREEZER_SPEC_LOW, FREEZER_SPEC_HIGH

Defines the behavior and acceptable temperature range for freezers.

FREEZER_SETPOINT: Target temperature, for example −20.5 °C.

FREEZER_SPEC_LOW / HIGH: Acceptable limits, e.g., −25 °C to −18 °C.

Business meaning: Represents compliance limits for frozen goods. Temperatures above −18 °C could indicate product risk.

5. SPEC_LOW / SPEC_HIGH

Acceptable temperature range for refrigerated (non-frozen) storage.
Typically between +2 °C and +8 °C.

Business meaning: Regulatory or quality-control range for perishable items such as dairy, meat, or pharmaceuticals.

6. AMBIENT_MEAN / AMBIENT_JITTER

Average and variability of the surrounding room or warehouse temperature.
Example: mean 22 °C with ±2 °C fluctuation.

Business meaning: Models real environmental influence on equipment when a door is open or when insulation is imperfect.

7. NOISE_STD

Size of the random variation added to each reading.
A small value such as 0.15 means readings fluctuate within ±0.15 °C.

Business meaning: Real sensors always show minor noise; this produces realistic data for testing analytics and alert logic.

8. DOOR_EVENT_PROB

Probability that an asset’s door changes state (open ↔ close) during each cycle.
Example: 0.05 means roughly 5% of units toggle door state in each reporting interval.

Business meaning: Simulates staff or customer activity and the operational impact of frequent door openings.

9. EXCURSION_PROB

Chance of an abnormal temperature excursion—a sudden, unexpected rise.
Example: 0.02 means about 2% of readings include a fault-like event.

Business meaning: Introduces rare incidents that mimic real-world faults such as compressor failure or power loss.

10. RESPONSE_CLOSED / RESPONSE_OPEN

Rate of temperature change:

RESPONSE_CLOSED: Cooling rate when the door is closed.

RESPONSE_OPEN: Warming rate when the door is open.

Business meaning: Reflects physical behavior: closed units cool slowly back to setpoint; open units warm quickly toward room temperature.

11. SLEEP_SECS

Interval between each new batch of readings, in seconds.
Example: 5 means every five seconds new events are produced.

Business meaning: Defines the data frequency and how “real-time” the monitoring appears.