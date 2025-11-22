  INSERT INTO vehicle_health_alerts
  SELECT
    window_start,
    window_end,
    vehicle_id,
    'high_engine_temp' AS alert_type,
    CONCAT('temp=', CAST(MAX(engine_temp_c) AS STRING)) AS details,
    MAX(`timestamp`) AS raw_timestamp
  FROM TABLE(
    TUMBLE(
      TABLE vehicle_status,
      DESCRIPTOR(`timestamp`),
      INTERVAL '1' MINUTE
    )
  )
  WHERE engine_temp_c > 90
  GROUP BY window_start, window_end, vehicle_id;