CREATE TABLE IF NOT EXISTS trip_events_kafka
(
    raw String
)
ENGINE = Kafka
SETTINGS
    kafka_broker_list = 'redpanda-1:29092',
    kafka_topic_list = 'fleet.prod.trip.events',
    kafka_group_name = 'ch_trip_events_group',
    kafka_format = 'LineAsString',
    kafka_num_consumers = 1;
