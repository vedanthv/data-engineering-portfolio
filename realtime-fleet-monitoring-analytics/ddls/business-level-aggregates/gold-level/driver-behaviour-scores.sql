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