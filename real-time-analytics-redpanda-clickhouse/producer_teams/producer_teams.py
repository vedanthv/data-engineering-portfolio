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

TEAMS_ENDPOINT = f"https://cricket.sportmonks.com/api/v2.0/teams?api_token={API_TOKEN}"

def fetch_teams():
    try:
        resp = requests.get(TEAMS_ENDPOINT)
        if resp.status_code == 200:
            data = resp.json().get('data', [])
            for team in data:
                updated_at = int(time.time())
                row = {
                    "team_id": team.get("id", 0),
                    "name": team.get("name", ""),
                    "code": team.get("code", ""),
                    "image_path": team.get("image_path", ""),
                    "country_id": team.get("country_id", 0),
                    "national_team": 1 if team.get("national_team", False) else 0,
                    "updated_at": updated_at
                }
                print(f"Sending to cricket_teams_v2: {row}")
                producer.send("cricket_teams_v2", row)
            producer.flush()
        else:
            print(f"Failed to fetch teams: Status code {resp.status_code}")
    except Exception as e:
        print(f"Error fetching teams: {e}")

if __name__ == "__main__":
    print("Starting Teams Producer...")
    while True:
        fetch_teams()
        time.sleep(800)
