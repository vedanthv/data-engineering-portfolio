CREATE TABLE telemetry_raw_session_window (
  event_id   STRING,
  vehicle_id STRING,
  driver_id  STRING,
  trip_id    STRING,
  lat        DOUBLE,
  lon        DOUBLE,
  speed_kmph DOUBLE,
  heading    DOUBLE,
  sat_count  INT,
  battery_v  DOUBLE,

  raw_timestamp TIMESTAMP_LTZ(3),

  event_time AS COALESCE(raw_timestamp, CURRENT_TIMESTAMP),

  WATERMARK FOR event_time AS event_time - INTERVAL '5' SECOND
) WITH (
  'connector' = 'kafka',
  'topic' = 'fleet.prod.telemetry.raw',
  'properties.bootstrap.servers' = 'redpanda-1:29092',
  'properties.group.id' = 'sql-telemetry-consumer-v4',
  'scan.startup.mode' = 'latest-offset',
  'format' = 'json',
  'json.timestamp-format.standard' = 'ISO-8601',
  'json.ignore-parse-errors' = 'true'
);
