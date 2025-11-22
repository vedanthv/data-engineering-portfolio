CREATE TABLE vehicle_status (
  vehicle_id STRING,
  raw_timestamp TIMESTAMP_LTZ(3),
  fuel_pct DOUBLE,
  engine_temp_c DOUBLE,
  odometer_km DOUBLE,
  fault_codes ARRAY<STRING>,
  SELECT
  d1.driver_id,
  d1.`timestamp` AS break_start,
  d2.`timestamp` AS break_end,
  TIMESTAMPDIFF(MINUTE, d1.`timestamp`, d2.`timestamp`) AS break_minutes
FROM driver_events d1
JOIN driver_events d2
ON d1.driver_id = d2.driver_id
AND d1.event_type = 'break_start'
AND d2.event_type = 'break_end'
AND d2.`timestamp` > d1.`timestamp`
WHERE TIMESTAMPDIFF(MINUTE, d1.`timestamp`, d2.`timestamp`) < 15;
  WATERMARK FOR `timestamp` AS `timestamp` - INTERVAL '5' SECOND
) WITH (
  'connector' = 'kafka',
  'topic' = 'fleet.prod.vehicle.status',
  'format' = 'json',
  'properties.bootstrap.servers' = 'redpanda-1:29092',
  'properties.group.id' = 'sql-telemetry-consumer-trips',
  'json.timestamp-format.standard' = 'ISO-8601',
  'json.ignore-parse-errors' = 'true',
  'scan.startup.mode' = 'latest-offset'
);
