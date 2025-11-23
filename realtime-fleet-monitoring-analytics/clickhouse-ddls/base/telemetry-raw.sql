-- 2) Real storage table
CREATE TABLE IF NOT EXISTS telemetry_raw (
    event_id    String,
    vehicle_id  String,
    driver_id   String,
    trip_id     String,
    timestamp   DateTime64(3, 'UTC'),
    lat         Float64,
    lon         Float64,
    speed_kmph  Float64,
    heading     Float64,
    sat_count   UInt8,
    battery_v   Float64
)
ENGINE = MergeTree()
PARTITION BY toDate(timestamp)
ORDER BY (vehicle_id, timestamp);