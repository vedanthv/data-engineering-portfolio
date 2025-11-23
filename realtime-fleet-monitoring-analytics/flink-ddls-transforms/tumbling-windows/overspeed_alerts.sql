-- 5) overspeed alerts to Kafka
CREATE TABLE overspeed_alerts (
  vehicle_id STRING,
  PRIMARY KEY(vehicle_id) NOT ENFORCED,
  ts TIMESTAMP_LTZ(3),
  speed_kmph DOUBLE
) WITH (
  'connector' = 'upsert-kafka',
  'topic' = 'fleet.prod.alerts.outbound',
  'properties.bootstrap.servers' = 'redpanda-1:29092',
  'key.format' = 'json',
  'value.format' = 'json'
);

INSERT INTO overspeed_alerts
SELECT vehicle_id, event_time AS ts, speed_kmph
FROM telemetry_raw
WHERE speed_kmph > 80.0;