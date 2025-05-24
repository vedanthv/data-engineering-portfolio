import requests
import json
import time
import os
from kafka import KafkaProducer

API_TOKEN = os.getenv('API_TOKEN', 'YOUR_API_KEY')
KAFKA_SERVER = os.getenv('KAFKA_BROKER', 'redpanda:9092')

producer = KafkaProducer(
    bootstrap_servers=KAFKA_SERVER,
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

BASE_PLAYERS_ENDPOINT = "https://cricket.sportmonks.com/api/v2.0/players"
TOPIC = "cricket_players_v2"

def fetch_players():
    endpoint = f"{BASE_PLAYERS_ENDPOINT}?api_token={API_TOKEN}&filter[country_id]=153732"
    print(f"Fetching from: {endpoint}")
    try:
        resp = requests.get(endpoint)
        if resp.status_code == 200:
            json_data = resp.json()
            data = json_data.get('data', [])
            for entry in data:
                row = {
                    "player_id": entry.get("id", 0),
                    "country_id": entry.get("country_id", 0),
                    "firstname": entry.get("firstname", ""),
                    "lastname": entry.get("lastname", ""),
                    "fullname": entry.get("fullname", ""),
                    "image_path": entry.get("image_path", ""),
                    "dateofbirth": entry.get("dateofbirth", ""),
                    "gender": entry.get("gender", ""),
                    "battingstyle": entry.get("battingstyle", ""),
                    "bowlingstyle": entry.get("bowlingstyle", ""),
                    "position_id": entry.get("position", {}).get("id", 0),
                    "position_name": entry.get("position", {}).get("name", ""),
                    "updated_at": entry.get("updated_at", "")
                }
                print(f"Sending to {TOPIC}: {row}")
                producer.send(TOPIC, row)

            producer.flush()

        else:
            print(f"Failed to fetch players: Status code {resp.status_code}")
    except Exception as e:
        print(f"Error fetching players: {e}")

if __name__ == "__main__":
    while True:
        fetch_players()
        print("Sleeping for 10 minutes...")
        time.sleep(600000)  # 10 minutes
