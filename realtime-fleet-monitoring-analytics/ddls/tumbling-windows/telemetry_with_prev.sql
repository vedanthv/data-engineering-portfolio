-- 2) previous row per vehicle (use LAG without explicit ROWS/RANGE frame)
CREATE VIEW telemetry_with_prev AS
SELECT vehicle_id, driver_id, lat, lon, speed_kmph, event_time, 
LAG(lat) OVER (PARTITION BY vehicle_id ORDER BY event_time) AS prev_lat, 
LAG(lon) OVER (PARTITION BY vehicle_id ORDER BY event_time) AS prev_lon, 
LAG(event_time) OVER (PARTITION BY vehicle_id ORDER BY event_time) AS prev_ts 
FROM telemetry_raw;