-- 4) tumbling-window aggregation to trip summaries
  CREATE TABLE trip_summaries_kafka (
    vehicle_id   STRING,
    trip_start   STRING,   -- window start as text
    trip_end     STRING,   -- window end as text
    event_count  BIGINT,
    distance_m   DOUBLE,
    avg_speed    DOUBLE
                ) WITH (
    'connector' = 'kafka',
    'topic' = 'fleet.prod.trip.summary',
    'properties.bootstrap.servers' = 'redpanda-1:29092',
    'format' = 'json'
  );

-- inserting data to the topic
INSERT INTO trip_summaries_kafka
SELECT
  vehicle_id,

  -- human-readable window boundaries
  DATE_FORMAT(
    TUMBLE_START(event_time, INTERVAL '20' SECOND),
    'yyyy-MM-dd HH:mm:ss'
  ) AS trip_start,
  DATE_FORMAT(
    TUMBLE_END(event_time, INTERVAL '20' SECOND),
    'yyyy-MM-dd HH:mm:ss'
  ) AS trip_end,

  -- duration in seconds (using only CHAR-based UNIX_TIMESTAMP)
  UNIX_TIMESTAMP(
    DATE_FORMAT(
      TUMBLE_END(event_time, INTERVAL '20' SECOND),
      'yyyy-MM-dd HH:mm:ss'
    ),
    'yyyy-MM-dd HH:mm:ss'
  )
  -
  UNIX_TIMESTAMP(
    DATE_FORMAT(
      TUMBLE_START(event_time, INTERVAL '20' SECOND),
      'yyyy-MM-dd HH:mm:ss'
    ),
    'yyyy-MM-dd HH:mm:ss'
  ) AS trip_duration_sec,

  COUNT(*)                    AS event_count,
  SUM(delta_m)                AS distance_m,
  SUM(delta_m) / 1000.0       AS distance_km,
  AVG(speed_kmph)             AS avg_speed,
  MIN(speed_kmph)             AS min_speed,
  MAX(speed_kmph)             AS max_speed

FROM telemetry_with_delta
GROUP BY
  vehicle_id,
  TUMBLE(event_time, INTERVAL '20' SECOND);


