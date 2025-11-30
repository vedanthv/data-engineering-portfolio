CREATE MATERIALIZED VIEW trip_alerts_mv
TO trip_alerts_outbound_raw
AS
SELECT
    JSONExtractString(js, 'alert_id')   AS alert_id,
    JSONExtractString(js, 'ts')         AS ts,
    JSONExtractString(js, 'vehicle_id') AS vehicle_id,
    JSONExtractString(js, 'trip_id')    AS trip_id,

    parseDateTime64BestEffort(
        JSONExtractString(js, 'ts')
    ) AS timestamp,

    JSONExtractString(js, 'alert_type') AS alert_type,
    toUInt8(JSONExtractInt(js, 'severity')) AS severity,
    JSONExtractString(js, 'details')    AS details
FROM
(
    SELECT
        concat(
            '{',
            replaceAll(
                substring(trim(raw), 2, length(trim(raw)) - 2),
                '\n',
                ','
            ),
            '}'
        ) AS js
    FROM trip_alerts_outbound_kafka
);

SELECT * FROM trip_alerts_mv limit 1;