DROP VIEW IF EXISTS driver_events_mv;
CREATE MATERIALIZED VIEW driver_events_mv
TO driver_events_raw
AS
SELECT
    JSONExtractString(replaceAll(raw, '""', '","'), 'driver_id')   AS driver_id,
    JSONExtractString(replaceAll(raw, '""', '","'), 'vehicle_id')  AS vehicle_id,
    JSONExtractString(replaceAll(raw, '""', '","'), 'event_type')  AS event_type,
    parseDateTime64BestEffort(
        JSONExtractString(replaceAll(raw, '""', '","'), 'timestamp')
    ) AS timestamp
FROM driver_events_kafka;

