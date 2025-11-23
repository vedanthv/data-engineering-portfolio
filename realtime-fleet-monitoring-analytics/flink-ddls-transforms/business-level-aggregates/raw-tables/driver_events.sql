-- 2) Driver events
CREATE TABLE driver_events (
  driver_id   STRING,
  vehicle_id  STRING,
  event_type  STRING,
  raw_timestamp TIMESTAMP_LTZ(3),
  `timestamp` AS COALESCE(raw_timestamp, CURRENT_TIMESTAMP),
  WATERMARK FOR `timestamp` AS `timestamp` - INTERVAL '5' SECOND
) WITH (
  'connector' = 'kafka',
  'topic' = 'fleet.prod.events.driver',
  'format' = 'json',
  'properties.bootstrap.servers' = 'redpanda-1:29092',
  'properties.group.id' = 'sql-telemetry-consumer-trips',
  'json.timestamp-format.standard' = 'ISO-8601',
  'scan.startup.mode' = 'latest-offset'
);