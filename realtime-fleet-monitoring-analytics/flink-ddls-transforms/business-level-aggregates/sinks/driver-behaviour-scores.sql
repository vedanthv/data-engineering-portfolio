CREATE TABLE driver_behavior_scores (
  vehicle_id    STRING,
  PRIMARY KEY(vehicle_id) NOT ENFORCED,
  window_start TIMESTAMP_LTZ(3),
  window_end   TIMESTAMP_LTZ(3),
  score        DOUBLE
) WITH (
  'connector' = 'upsert-kafka',
  'topic' = 'fleet.prod.driver.behaviour.scores',
  'properties.bootstrap.servers' = 'redpanda-1:29092',
  'properties.group.id' = 'sql-telemetry-consumer-v4',
  'key.format' = 'json',
  'value.format' = 'json'
);