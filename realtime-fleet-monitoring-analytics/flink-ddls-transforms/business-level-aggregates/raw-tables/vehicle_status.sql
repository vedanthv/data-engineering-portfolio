CREATE TABLE vehicle_status (
  vehicle_id STRING,
  raw_timestamp TIMESTAMP_LTZ(3),
  fuel_pct DOUBLE,
  engine_temp_c DOUBLE,
  odometer_km DOUBLE,
  fault_codes ARRAY<STRING>
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
