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