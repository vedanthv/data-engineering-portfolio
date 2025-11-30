DROP TABLE IF EXISTS driver_events_kafka;
CREATE TABLE IF NOT EXISTS driver_events_kafka
(
    raw String
)
ENGINE = Kafka
SETTINGS
    kafka_broker_list = 'redpanda-1:29092',
    kafka_topic_list = 'fleet.prod.events.driver',
    kafka_group_name = 'ch_driver_events_group',
    kafka_format = 'LineAsString',
    kafka_num_consumers = 1;