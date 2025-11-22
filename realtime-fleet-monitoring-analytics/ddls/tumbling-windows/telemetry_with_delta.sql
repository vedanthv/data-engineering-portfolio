-- 3) compute delta distance (meters) using Haversine; prev null -> 0
CREATE VIEW telemetry_with_delta AS
SELECT
  vehicle_id,
  driver_id,
  lat,
  lon,
  speed_kmph,
  event_time,
  prev_lat,
  prev_lon,
  prev_ts,
  CASE
    WHEN prev_lat IS NULL OR prev_lon IS NULL THEN 0.0
    ELSE
      6371000.0 * 2 * ASIN(
        SQRT(
          POWER(SIN(RADIANS((lat - prev_lat)/2)),2)
          + COS(RADIANS(prev_lat)) * COS(RADIANS(lat)) * POWER(SIN(RADIANS((lon - prev_lon)/2)),2)
        )
      )
  END AS delta_m
FROM telemetry_with_prev;