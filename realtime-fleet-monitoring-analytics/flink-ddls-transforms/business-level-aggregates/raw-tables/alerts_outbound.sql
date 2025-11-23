CREATE TABLE alerts_outbound (
  alert_id   STRING,
  vehicle_id STRING,
  trip_id    STRING,
  alert_type STRING,
  severity   INT,
  details    STRING,

  `timestamp` TIMESTAMP_LTZ(3),

  event_time AS COALESCE(`timestamp`, CURRENT_TIMESTAMP),

  WATERMARK FOR event_time AS event_time - INTERVAL '10' SECOND
) WITH (
  'connector' = 'kafka',
  'topic' = 'fleet.prod.alerts.outbound',
  'format' = 'json',
  'properties.bootstrap.servers' = 'redpanda-1:29092',
  'properties.group.id' = 'sql-telemetry-consumer-trips',
  'json.timestamp-format.standard' = 'ISO-8601',
  'json.ignore-parse-errors' = 'true',
  'scan.startup.mode' = 'latest-offset'
);
