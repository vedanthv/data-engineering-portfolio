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