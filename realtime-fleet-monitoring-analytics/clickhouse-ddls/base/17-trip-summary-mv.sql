DROP VIEW IF EXISTS trip_summary_mv;

CREATE MATERIALIZED VIEW trip_summary_mv
TO trip_summary_raw
AS
SELECT
    JSONExtractString(fixed, 'trip_id')     AS trip_id,
    JSONExtractString(fixed, 'vehicle_id')  AS vehicle_id,
    JSONExtractString(fixed, 'driver_id')   AS driver_id,

    parseDateTime64BestEffort(JSONExtractString(fixed, 'trip_start')) AS trip_start,
    parseDateTime64BestEffort(JSONExtractString(fixed, 'trip_end'))   AS trip_end,

    toUInt32OrNull(nullIf(JSONExtractString(fixed, 'trip_duration_sec'), '')) AS trip_duration_sec,
    toUInt32OrNull(nullIf(JSONExtractString(fixed, 'event_count'),       '')) AS event_count,

    toFloat64OrNull(nullIf(JSONExtractString(fixed, 'distance_m'), ''))  AS distance_m,
    toFloat64OrNull(nullIf(JSONExtractString(fixed, 'distance_km'), '')) AS distance_km,
    toFloat64OrNull(nullIf(JSONExtractString(fixed, 'avg_speed'), ''))   AS avg_speed,
    toFloat64OrNull(nullIf(JSONExtractString(fixed, 'min_speed'), ''))   AS min_speed,
    toFloat64OrNull(nullIf(JSONExtractString(fixed, 'max_speed'), ''))   AS max_speed,

    now64(6) AS ingestion_ts
FROM
(
    SELECT replaceAll(raw, '""', '","') AS fixed
    FROM trip_summary_kafka
);
