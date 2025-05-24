import os
import time
import json
import clickhouse_connect
from clickhouse_connect import get_client
from kafka import KafkaProducer

CLICKHOUSE_HOST = os.getenv("CLICKHOUSE_HOST", "localhost")
CLICKHOUSE_PORT = int(os.getenv("CLICKHOUSE_PORT", "8123"))
CLICKHOUSE_DB = os.getenv("CLICKHOUSE_DB", "default")
CLICKHOUSE_TABLE = os.getenv("CLICKHOUSE_TABLE", "fixtures_with_team_names_mv")

KAFKA_BROKER = os.getenv("KAFKA_BROKER", "redpanda:9092")
KAFKA_TOPIC = os.getenv("KAFKA_TOPIC", "fixtures_joined_teams_pub")

producer = KafkaProducer(
    bootstrap_servers=KAFKA_BROKER,
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

def fetch_clickhouse_rows():
    client = clickhouse_connect.get_client(
            host=CLICKHOUSE_HOST,
            port=8123,
            username="readonly_user",
            password="YourReadOnlyPassword"
        )
    query = f"SELECT * FROM {CLICKHOUSE_TABLE}"
    result = client.query(query)
    return result.result_rows, result.column_names

def publish_to_kafka(rows, columns):
    for row in rows:
        msg = dict(zip(columns, row))
        producer.send(KAFKA_TOPIC, msg)
    producer.flush()
    print(f"Published {len(rows)} rows to topic {KAFKA_TOPIC}")

if __name__ == "__main__":
    while True:
        try:
            rows, columns = fetch_clickhouse_rows()
            if rows:
                publish_to_kafka(rows, columns)
            else:
                print("No data found in ClickHouse table.")
        except Exception as e:
            print(f"Error: {e}")

        time.sleep(600)  # 10 minutes
    