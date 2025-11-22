CREATE TABLE fleet_utilization_metrics (
  window_start TIMESTAMP_LTZ(3),
  window_end   TIMESTAMP_LTZ(3),
  active_count BIGINT,
  idle_count   BIGINT,
  offline_count BIGINT
) WITH (
 'connector' = 'kafka',
  'topic' = 'fleet.prod.metrics.live',
  'format' = 'json',
  'properties.bootstrap.servers' = 'redpanda-1:29092',
  'properties.group.id' = 'sql-telemetry-consumer-trips',
  'json.timestamp-format.standard' = 'ISO-8601',
  'scan.startup.mode' = 'latest-offset'
);