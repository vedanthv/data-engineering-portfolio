CREATE MATERIALIZED VIEW prod_metrics_mv
TO prod_metrics_raw
AS
SELECT
    parseDateTime64BestEffort(
        JSONExtractString(replaceAll(raw, '""', '","'), 'window_start')
    ) AS window_start,

    parseDateTime64BestEffort(
        JSONExtractString(replaceAll(raw, '""', '","'), 'window_end')
    ) AS window_end,

    toUInt32(JSONExtractString(replaceAll(raw, '""', '","'), 'active_count'))   AS active_count,
    toUInt32(JSONExtractString(replaceAll(raw, '""', '","'), 'idle_count'))     AS idle_count,
    toUInt32(JSONExtractString(replaceAll(raw, '""', '","'), 'offline_count'))  AS offline_count
FROM prod_metrics_kafka;
