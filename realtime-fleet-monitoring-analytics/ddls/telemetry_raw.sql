CREATE TABLE telemetry_raw (
  vehicle_id STRING,
  driver_id STRING,
  lat DOUBLE,
  lon DOUBLE,
  speed_kmph DOUBLE,
  `timestamp` STRING,
  event_time AS CAST(
      SUBSTR(REPLACE(`timestamp`, 'T', ' '), 1, 23)
      AS TIMESTAMP_LTZ(3)
  ),
  WATERMARK FOR event_time AS event_time - INTERVAL '30' SECOND
) WITH (
  'connector' = 'kafka',
  'topic' = 'fleet.prod.telemetry.raw',
  'properties.bootstrap.servers' = 'redpanda-1:29092',
  'properties.group.id' = 'sql-telemetry-consumer',
  'scan.startup.mode' = 'latest-offset',
  'format' = 'json',
  'json.ignore-parse-errors' = 'true'
);
