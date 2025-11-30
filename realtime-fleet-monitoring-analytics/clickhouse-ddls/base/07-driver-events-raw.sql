DROP TABLE IF EXISTS driver_events_raw;
CREATE TABLE IF NOT EXISTS driver_events_raw
(
    driver_id   String,
    vehicle_id  String,
    event_type  String,
    timestamp   DateTime64(6, 'UTC')
)
ENGINE = MergeTree
ORDER BY (timestamp);
