CREATE TABLE vehicle_health_alerts (
  window_start TIMESTAMP_LTZ(3),
  window_end   TIMESTAMP_LTZ(3),
  vehicle_id   STRING,
  alert_type   STRING,
  details      STRING,
  raw_timestamp TIMESTAMP_LTZ(3)
) WITH (
  'connector' = 'kafka',
  'topic' = 'fleet.prod.vehicle.health.alerts',
  'format' = 'json',
  'properties.bootstrap.servers' = 'redpanda-1:29092'
);