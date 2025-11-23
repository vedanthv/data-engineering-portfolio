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

  CREATE VIEW telemetry_session_with_prev AS
  SELECT
    vehicle_id,
    driver_id,
    trip_id,
    lat,
    lon,
    speed_kmph,
    event_time,
    LAG(lat)        OVER (PARTITION BY vehicle_id ORDER BY event_time) AS prev_lat,
    LAG(lon)        OVER (PARTITION BY vehicle_id ORDER BY event_time) AS prev_lon,
    LAG(event_time) OVER (PARTITION BY vehicle_id ORDER BY event_time) AS prev_ts,
    LAG(trip_id)    OVER (PARTITION BY vehicle_id ORDER BY event_time) AS prev_trip_id
  FROM telemetry_raw_session_window;

CREATE VIEW telemetry_session_with_delta AS
SELECT
  vehicle_id,
  driver_id,
  trip_id,
  lat,
  lon,
  speed_kmph,
  event_time,
  prev_lat,
  prev_lon,
  prev_ts,
  prev_trip_id,
  CASE
    WHEN prev_lat IS NULL
      OR prev_lon IS NULL
      OR trip_id IS NULL
      OR trip_id = ''
      OR trip_id <> prev_trip_id
    THEN 0.0
    ELSE
      6371000.0 * 2 * ASIN(
        SQRT(
          POWER(SIN(RADIANS((lat - prev_lat)/2)),2)
          + COS(RADIANS(prev_lat)) * COS(RADIANS(lat))
            * POWER(SIN(RADIANS((lon - prev_lon)/2)),2)
        )
      )
  END AS delta_m
FROM telemetry_session_with_prev;

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

CREATE TABLE alerts_outbound (
  alert_id   STRING,
  vehicle_id STRING,
  trip_id    STRING,
  alert_type STRING,
  severity   INT,
  details    STRING,

  `timestamp` TIMESTAMP_LTZ(3),

  event_time AS COALESCE(`timestamp`, CURRENT_TIMESTAMP),

  WATERMARK FOR event_time AS event_time - INTERVAL '10' SECOND
) WITH (
  'connector' = 'kafka',
  'topic' = 'fleet.prod.alerts.outbound',
  'format' = 'json',
  'properties.bootstrap.servers' = 'redpanda-1:29092',
  'properties.group.id' = 'sql-telemetry-consumer-trips',
  'json.timestamp-format.standard' = 'ISO-8601',
  'json.ignore-parse-errors' = 'true',
  'scan.startup.mode' = 'latest-offset'
);

-- 2) Driver events
CREATE TABLE driver_events (
  driver_id   STRING,
  vehicle_id  STRING,
  event_type  STRING,
  raw_timestamp TIMESTAMP_LTZ(3),
  `timestamp` AS COALESCE(raw_timestamp, CURRENT_TIMESTAMP),
  WATERMARK FOR `timestamp` AS `timestamp` - INTERVAL '5' SECOND
) WITH (
  'connector' = 'kafka',
  'topic' = 'fleet.prod.events.driver',
  'format' = 'json',
  'properties.bootstrap.servers' = 'redpanda-1:29092',
  'properties.group.id' = 'sql-telemetry-consumer-trips',
  'json.timestamp-format.standard' = 'ISO-8601',
  'scan.startup.mode' = 'latest-offset'
);

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

CREATE TABLE break_violations (
  driver_id STRING,
  break_start TIMESTAMP_LTZ(3),
  break_end  TIMESTAMP_LTZ(3),
  break_minutes INT
) WITH (
 'connector' = 'kafka',
  'topic' = 'fleet.prod.driver.break.violations',
  'format' = 'json',
  'properties.bootstrap.servers' = 'redpanda-1:29092',
  'properties.group.id' = 'sql-telemetry-consumer-trips',
  'json.timestamp-format.standard' = 'ISO-8601',
  'scan.startup.mode' = 'latest-offset'
);

INSERT INTO break_violations
SELECT
  d1.driver_id,
  d1.`timestamp` AS break_start,
  d2.`timestamp` AS break_end,
  TIMESTAMPDIFF(SECOND, d1.`timestamp`, d2.`timestamp`) AS break_minutes
FROM driver_events d1
JOIN driver_events d2
ON d1.driver_id = d2.driver_id
AND d1.event_type = 'break_start'
AND d2.event_type = 'break_end'
AND d2.`timestamp` > d1.`timestamp`
WHERE TIMESTAMPDIFF(SECOND, d1.`timestamp`, d2.`timestamp`) < 5;

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

INSERT INTO driver_behavior_scores
SELECT
  vehicle_id,
  window_start,
  window_end,
  (
    overspeed_cnt * 2.0 +
    harsh_brake_cnt * 3.0 +
    idle_cnt * 1.0
  ) AS score
FROM (
  SELECT
    vehicle_id,
    window_start,
    window_end,
    SUM(CASE WHEN alert_type = 'overspeed' THEN 1 ELSE 0 END) AS overspeed_cnt,
    SUM(CASE WHEN alert_type = 'harsh_brake' THEN 1 ELSE 0 END) AS harsh_brake_cnt,
    SUM(CASE WHEN alert_type = 'idling' THEN 1 ELSE 0 END) AS idle_cnt
  FROM TABLE(
    HOP(
      TABLE alerts_outbound,
      DESCRIPTOR(event_time),
      INTERVAL '1' SECOND,
      INTERVAL '15' SECOND
    )
  )
  GROUP BY vehicle_id, window_start, window_end
);


INSERT INTO fleet_utilization_metrics
SELECT
  window_start,
  window_end,
  SUM(CASE WHEN speed_kmph > 5 THEN 1 ELSE 0 END) AS active_count,
  SUM(CASE WHEN speed_kmph <= 5 THEN 1 ELSE 0 END) AS idle_count,
  0 AS offline_count
FROM TABLE(
  HOP(
    TABLE telemetry_raw_session_window,
    DESCRIPTOR(event_time),
    INTERVAL '1' SECOND,   -- hop interval
    INTERVAL '5' SECOND    -- window size
  )
)
GROUP BY window_start, window_end;

  INSERT INTO vehicle_health_alerts
  SELECT
    window_start,
    window_end,
    vehicle_id,
    'high_engine_temp' AS alert_type,
    CONCAT('temp=', CAST(MAX(engine_temp_c) AS STRING)) AS details,
    MAX(`raw_timestamp`) AS time_stamp
  FROM TABLE(
    TUMBLE(
      TABLE vehicle_status,
      DESCRIPTOR(`raw_timestamp`),
      INTERVAL '1' MINUTE
    )
  )
  WHERE engine_temp_c > 90
  GROUP BY window_start, window_end, vehicle_id;