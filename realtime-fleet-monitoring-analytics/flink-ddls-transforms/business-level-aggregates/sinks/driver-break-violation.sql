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
