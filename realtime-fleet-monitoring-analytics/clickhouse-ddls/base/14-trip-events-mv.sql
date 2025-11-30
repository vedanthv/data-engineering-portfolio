CREATE MATERIALIZED VIEW trip_events_mv
TO trip_events_raw
AS
SELECT
    JSONExtractString(replaceAll(raw, '""', '","'), 'trip_id')    AS trip_id,
    JSONExtractString(replaceAll(raw, '""', '","'), 'vehicle_id') AS vehicle_id,
    JSONExtractString(replaceAll(raw, '""', '","'), 'driver_id')  AS driver_id,
    JSONExtractString(replaceAll(raw, '""', '","'), 'event_type') AS event_type,

    parseDateTime64BestEffort(
        JSONExtractString(replaceAll(raw, '""', '","'), 'timestamp')
    ) AS timestamp,

    -- origin (nullable)
    toFloat64OrNull(
        nullIf(JSONExtractString(replaceAll(raw, '""', '","'), 'origin_lat'), '')
    ) AS origin_lat,

    toFloat64OrNull(
        nullIf(JSONExtractString(replaceAll(raw, '""', '","'), 'origin_lon'), '')
    ) AS origin_lon,

    -- end (nullable)
    toFloat64OrNull(
        nullIf(JSONExtractString(replaceAll(raw, '""', '","'), 'end_lat'), '')
    ) AS end_lat,

    toFloat64OrNull(
        nullIf(JSONExtractString(replaceAll(raw, '""', '","'), 'end_lon'), '')
    ) AS end_lon,

    toUInt32OrNull(
        nullIf(JSONExtractString(replaceAll(raw, '""', '","'), 'distance_m'), '')
    ) AS distance_m,

    toUInt32OrNull(
        nullIf(JSONExtractString(replaceAll(raw, '""', '","'), 'duration_sec'), '')
    ) AS duration_sec,

    nullIf(JSONExtractString(replaceAll(raw, '""', '","'), 'status'), '') AS status,

    now64(6) AS ingestion_ts
FROM trip_events_kafka;
