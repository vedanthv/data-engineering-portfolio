-- 2) Real storage table

CREATE TABLE IF NOT EXISTS trip_alerts_outbound_raw (
    alert_id    String,
    ts  String,
    vehicle_id   String,
    trip_id     String,
    timestamp   DateTime64(3, 'UTC'),
    alert_type  String,
    severity   UInt8,
    details   String
)
ENGINE = MergeTree()
PARTITION BY toDate(timestamp)
ORDER BY (alert_id, timestamp);