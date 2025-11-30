CREATE TABLE prod_metrics_raw
(
    window_start   DateTime64(6, 'UTC'),
    window_end     DateTime64(6, 'UTC'),
    active_count   UInt32,
    idle_count     UInt32,
    offline_count  UInt32
)
ENGINE = MergeTree
ORDER BY (window_start, window_end);
