CREATE TABLE IF NOT EXISTS prod_metrics_kafka
(
    raw String
)
ENGINE = Kafka
SETTINGS
    kafka_broker_list = 'redpanda-1:29092',
    kafka_topic_list = 'fleet.prod.metrics.live',
    kafka_group_name = 'ch_prod_events_group',
    kafka_format = 'LineAsString',
    kafka_num_consumers = 1;