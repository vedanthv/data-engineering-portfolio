CREATE TABLE IF NOT EXISTS trip_events_raw
(
    trip_id       String,
    vehicle_id    String,
    driver_id     String,
    event_type    String,
    timestamp     DateTime64(6, 'UTC'),
    origin_lat    Nullable(Float64),
    origin_lon    Nullable(Float64),
    end_lat       Nullable(Float64),
    end_lon       Nullable(Float64),
    distance_m    Nullable(UInt32),
    duration_sec  Nullable(UInt32),
    status        Nullable(String),
    ingestion_ts  DateTime64(6, 'UTC') DEFAULT now64(6)
)
ENGINE = MergeTree
ORDER BY (timestamp, trip_id);

