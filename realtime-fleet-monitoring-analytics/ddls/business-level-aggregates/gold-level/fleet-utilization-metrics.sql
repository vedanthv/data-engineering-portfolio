
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