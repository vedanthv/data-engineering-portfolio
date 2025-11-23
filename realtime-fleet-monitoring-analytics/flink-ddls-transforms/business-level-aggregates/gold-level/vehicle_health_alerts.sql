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