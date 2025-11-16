-- 4) session-window aggregation to trip summaries
CREATE TABLE trip_summaries_kafka (
  vehicle_id STRING,
  trip_start TIMESTAMP_LTZ(3),
  trip_end TIMESTAMP_LTZ(3),
  PRIMARY KEY (vehicle_id,trip_start,trip_end) NOT ENFORCED,
  event_count BIGINT,
  distance_m DOUBLE,
  avg_speed DOUBLE
) WITH (
  'connector' = 'upsert-kafka',
  'topic' = 'fleet.prod.trip.summary',
  'properties.bootstrap.servers' = 'redpanda-1:29092',
  'key.format' = 'json',
  'value.format' = 'json'
);

INSERT INTO trip_summaries_kafka
SELECT
  vehicle_id,
  SESSION_START(event_time, INTERVAL '20' SECOND) AS trip_start,
  SESSION_END(event_time, INTERVAL '20' SECOND)   AS trip_end,
  COUNT(*) AS event_count,
  SUM(delta_m) AS distance_m,
  AVG(speed_kmph) AS avg_speed
FROM telemetry_with_delta
GROUP BY
  vehicle_id,
  SESSION(event_time, INTERVAL '20' SECOND);
