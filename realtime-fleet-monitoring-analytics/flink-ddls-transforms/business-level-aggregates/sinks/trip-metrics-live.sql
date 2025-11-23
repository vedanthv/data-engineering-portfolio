-- Live trip metrics sink
CREATE TABLE trip_metrics_live (
  trip_id       STRING,
  vehicle_id    STRING,
  driver_id     STRING,
  window_start  TIMESTAMP_LTZ(3),
  window_end    TIMESTAMP_LTZ(3),
  distance_m    DOUBLE,
  avg_speed     DOUBLE
) WITH (
  'connector' = 'upsert-kafka',
  'topic' = 'fleet.prod.trip.metrics.live',
  'properties.bootstrap.servers' = 'redpanda-1:29092',
  'properties.group.id' = 'sql-telemetry-consumer-v4',
  'key.format' = 'json',
  'value.format' = 'json'
);