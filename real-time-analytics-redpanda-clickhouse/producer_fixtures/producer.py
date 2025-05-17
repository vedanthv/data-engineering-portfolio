import requests
import json
import time
import os
from datetime import datetime
from kafka import KafkaProducer

API_TOKEN = os.getenv('API_TOKEN', 'YOUR_API_KEY')
KAFKA_SERVER = os.getenv('KAFKA_BROKER', 'redpanda:9092')

producer = KafkaProducer(
    bootstrap_servers=KAFKA_SERVER,
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

FIXTURES_ENDPOINT = f"https://cricket.sportmonks.com/api/v2.0/fixtures?api_token={API_TOKEN}"
TEAMS_ENDPOINT = f"https://cricket.sportmonks.com/api/v2.0/teams?api_token={API_TOKEN}"

def fetch_fixtures():
    try:
        resp = requests.get(FIXTURES_ENDPOINT)
        if resp.status_code == 200:
            data = resp.json().get('data', [])
            for entry in data:
                updated_at = int(time.time())
                row = {
                    "fixture_id": entry.get("id", 0),
                    "league_id": entry.get("league_id", 0),
                    "season_id": entry.get("season_id", 0),
                    "stage_id": entry.get("stage_id", 0),
                    "round": entry.get("round", ""),
                    "localteam_id": entry.get("localteam_id", 0),
                    "visitorteam_id": entry.get("visitorteam_id", 0),
                    "starting_at": entry.get("starting_at", ""),
                    "type": entry.get("type", ""),
                    "live": 1 if entry.get("live", False) else 0,
                    "status": entry.get("status", ""),
                    "note": entry.get("note", ""),
                    "venue_id": entry.get("venue_id", 0),
                    "toss_won_team_id": entry.get("toss_won_team_id", 0),
                    "winner_team_id": entry.get("winner_team_id", 0),
                    "man_of_match_id": entry.get("man_of_match_id", 0),
                    "total_overs_played": entry.get("total_overs_played", 0) or 0,
                    "elected": entry.get("elected", ""),
                    "super_over": 1 if entry.get("super_over", False) else 0,
                    "follow_on": 1 if entry.get("follow_on", False) else 0,
                    "updated_at": updated_at
                }
                print(f"Sending to cricket_fixtures_v2: {row}")
                producer.send("cricket_fixtures_v2", row)
            producer.flush()  # flush after sending all fixtures

        else:
            print(f"Failed to fetch fixtures: Status code {resp.status_code}")
    except Exception as e:
        print(f"Error fetching fixtures: {e}")

if __name__ == "__main__":
    while True:
        fetch_fixtures()
        time.sleep(30)