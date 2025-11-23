CREATE TABLE session_trip_summaries (
  trip_id           STRING,
  vehicle_id        STRING,
  driver_id         STRING,
  trip_start        STRING,
  trip_end          STRING,
  trip_duration_sec BIGINT,
  event_count       BIGINT,
  distance_m        DOUBLE,
  distance_km       DOUBLE,
  avg_speed         DOUBLE,
  min_speed         DOUBLE,
  max_speed         DOUBLE,
  PRIMARY KEY (trip_id) NOT ENFORCED
) WITH (
  'connector' = 'upsert-kafka',
  'topic' = 'fleet.prod.trip.sessionsummary',
  'properties.bootstrap.servers' = 'redpanda-1:29092',
  'properties.group.id' = 'sql-telemetry-consumer-v4',
  'key.format' = 'json',
  'value.format' = 'json'
);

INSERT INTO session_trip_summaries
SELECT
  trip_id,
  vehicle_id,
  driver_id,

  -- trip start / end from first / last event
  DATE_FORMAT(
    MIN(event_time),
    'yyyy-MM-dd HH:mm:ss'
  ) AS trip_start,
  DATE_FORMAT(
    MAX(event_time),
    'yyyy-MM-dd HH:mm:ss'
  ) AS trip_end,

  -- duration in seconds
  UNIX_TIMESTAMP(
    DATE_FORMAT(MAX(event_time), 'yyyy-MM-dd HH:mm:ss'),
    'yyyy-MM-dd HH:mm:ss'
  )
  -
  UNIX_TIMESTAMP(
    DATE_FORMAT(MIN(event_time), 'yyyy-MM-dd HH:mm:ss'),
    'yyyy-MM-dd HH:mm:ss'
  ) AS trip_duration_sec,

  COUNT(*)                  AS event_count,
  SUM(delta_m)              AS distance_m,
  SUM(delta_m) / 1000.0     AS distance_km,
  AVG(speed_kmph)           AS avg_speed,
  MIN(speed_kmph)           AS min_speed,
  MAX(speed_kmph)           AS max_speed
FROM telemetry_session_with_delta
WHERE trip_id IS NOT NULL AND trip_id <> ''
GROUP BY trip_id, vehicle_id, driver_id;
