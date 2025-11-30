CREATE MATERIALIZED VIEW telemetry_mv
TO telemetry_raw
AS
SELECT
    JSONExtractString(replaceAll(raw, '""', '","'), 'event_id')    AS event_id,
    JSONExtractString(replaceAll(raw, '""', '","'), 'vehicle_id')  AS vehicle_id,
    JSONExtractString(replaceAll(raw, '""', '","'), 'driver_id')   AS driver_id,
    JSONExtractString(replaceAll(raw, '""', '","'), 'trip_id')     AS trip_id,
    parseDateTime64BestEffort(JSONExtractString(replaceAll(raw, '""', '","'), 'timestamp')) AS timestamp,
    toFloat64(JSONExtractString(replaceAll(raw, '""', '","'), 'lat'))        AS lat,
    toFloat64(JSONExtractString(replaceAll(raw, '""', '","'), 'lon'))        AS lon,
    toFloat64(JSONExtractString(replaceAll(raw, '""', '","'), 'speed_kmph')) AS speed_kmph,
    toFloat64(JSONExtractString(replaceAll(raw, '""', '","'), 'heading'))    AS heading,
    toUInt8(JSONExtractString(replaceAll(raw, '""', '","'), 'sat_count'))    AS sat_count,
    toFloat64(JSONExtractString(replaceAll(raw, '""', '","'), 'battery_v'))  AS battery_v
FROM telemetry_kafka;