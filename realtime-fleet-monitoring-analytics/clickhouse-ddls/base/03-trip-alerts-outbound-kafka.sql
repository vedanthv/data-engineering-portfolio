CREATE DATABASE IF NOT EXISTS telemetry;
USE telemetry;

-- 1) Kafka engine table reading from Redpanda topic
CREATE TABLE IF NOT EXISTS trip_alerts_outbound_kafka (
    raw String
)
ENGINE = Kafka
SETTINGS
    kafka_broker_list = 'redpanda-1:29092,redpanda-2:29093',
    kafka_topic_list = 'fleet.prod.alerts.outbound',
    kafka_group_name = 'ch_telemetry_consumer_v3',
    kafka_format = 'LineAsString';