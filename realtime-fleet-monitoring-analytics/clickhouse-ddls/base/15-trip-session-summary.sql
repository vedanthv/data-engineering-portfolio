CREATE TABLE trip_summary_kafka
(
    raw String
)
ENGINE = Kafka
SETTINGS
    kafka_broker_list = 'redpanda-1:29092',
    kafka_topic_list = 'fleet.prod.trip.sessionsummary',
    kafka_group_name = 'ch_trip_summary_group',
    kafka_format = 'LineAsString',
    kafka_num_consumers = 1;
