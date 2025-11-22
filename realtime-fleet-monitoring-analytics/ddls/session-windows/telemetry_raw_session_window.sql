CREATE TABLE telemetry_raw_session_window (
  event_id   STRING,
  vehicle_id STRING,
  driver_id  STRING,
  trip_id    STRING,        -- NEW: from JSON
  lat        DOUBLE,
  lon        DOUBLE,
  speed_kmph DOUBLE,
  heading    DOUBLE,
  sat_count  INT,
  battery_v  DOUBLE,
  `timestamp` STRING,

  event_time AS CAST(
    REPLACE(SUBSTRING(`timestamp` FROM 1 FOR 23), 'T', ' ')
    AS TIMESTAMP_LTZ(3)
  ),

  WATERMARK FOR event_time AS event_time - INTERVAL '60' SECOND
) WITH (
  'connector' = 'kafka',
  'topic' = 'fleet.prod.telemetry.raw',
  'properties.bootstrap.servers' = 'redpanda-1:29092',
  'properties.group.id' = 'sql-telemetry-consumer-trips',
  'scan.startup.mode' = 'latest-offset',
  'properties.group.id' = 'sql-telemetry-consumer-v4',
  'format' = 'json',
  'json.ignore-parse-errors' = 'false'
);