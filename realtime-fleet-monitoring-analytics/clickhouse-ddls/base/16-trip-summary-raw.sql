CREATE TABLE IF NOT EXISTS trip_summary_raw
(
    trip_id            String,
    vehicle_id         String,
    driver_id          String,
    trip_start         DateTime64(6, 'UTC'),
    trip_end           DateTime64(6, 'UTC'),
    trip_duration_sec  Nullable(UInt32),
    event_count        Nullable(UInt32),
    distance_m         Nullable(Float64),
    distance_km        Nullable(Float64),
    avg_speed          Nullable(Float64),
    min_speed          Nullable(Float64),
    max_speed          Nullable(Float64),
    ingestion_ts       DateTime64(6, 'UTC') DEFAULT now64(6)
)
ENGINE = MergeTree
ORDER BY (trip_start, trip_id);
