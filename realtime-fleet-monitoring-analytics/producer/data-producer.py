#!/usr/bin/env python3
"""
JSON Fake Fleet Data Producer for Redpanda/Kafka.

Produces JSON messages to topics:
- fleet.prod.telemetry.raw
- fleet.prod.trip.events
- fleet.prod.vehicle.status
- fleet.prod.events.driver
- fleet.prod.alerts.outbound

Usage:
  python producer_json.py --brokers localhost:9092 --num-vehicles 10 --telemetry-rate 1.0 --run-seconds 3600 --create-topics
"""

import argparse
import json
import math
import random
import time
import uuid
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor
from confluent_kafka import Producer, Consumer
from confluent_kafka.admin import AdminClient, NewTopic

# ---------------------------
# Topics & utils
# ---------------------------
TOPICS = [
    ("fleet.prod.telemetry.raw", 12, 1),
    ("fleet.prod.trip.events", 6, 1),
    ("fleet.prod.vehicle.status", 6, 1),
    ("fleet.prod.events.driver", 3, 1),
    ("fleet.prod.alerts.outbound", 3, 1),
    ("fleet.prod.commands", 1, 1),
]

def now_iso():
    return datetime.now(timezone.utc).isoformat()

def haversine_m(lat1, lon1, lat2, lon2):
    R = 6371000.0
    phi1 = math.radians(lat1); phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1); dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

def bearing(lat1, lon1, lat2, lon2):
    phi1 = math.radians(lat1); phi2 = math.radians(lat2)
    dlambda = math.radians(lon2 - lon1)
    x = math.sin(dlambda) * math.cos(phi2)
    y = math.cos(phi1)*math.sin(phi2) - math.sin(phi1)*math.cos(phi2)*math.cos(dlambda)
    theta = math.atan2(x, y)
    deg = (math.degrees(theta) + 360) % 360
    return deg

def interpolate(lat1, lon1, lat2, lon2, frac):
    return lat1 + (lat2 - lat1) * frac, lon1 + (lon2 - lon1) * frac

# ---------------------------
# Create topics (optional)
# ---------------------------
def create_topics(brokers, topics):
    admin = AdminClient({"bootstrap.servers": brokers})
    existing = admin.list_topics(timeout=5).topics
    new_topics = []
    for name, partitions, rf in topics:
        if name not in existing:
            new_topics.append(NewTopic(topic=name, num_partitions=partitions, replication_factor=rf))
    if new_topics:
        fs = admin.create_topics(new_topics)
        for topic, f in fs.items():
            try:
                f.result(timeout=10)
                print(f"Created topic {topic}")
            except Exception as e:
                print(f"Failed to create topic {topic}: {e}")
    else:
        print("Topics already exist (or were present).")

# ---------------------------
# Fleet generator
# ---------------------------
def generate_fleet(num_vehicles):
    vehicles = []
    for i in range(num_vehicles):
        vid = f"veh_{1000 + i}"
        driver_id = f"drv_{2000 + (i % max(1, num_vehicles//2))}"
        base_lat = 12.9 + random.uniform(-0.5, 0.5)
        base_lon = 77.6 + random.uniform(-0.7, 0.7)
        vehicles.append({
            "vehicle_id": vid,
            "driver_id": driver_id,
            "vin": str(uuid.uuid4())[:12],
            "make": random.choice(["Volvo", "Tata", "Mahindra", "Mercedes", "AshokLeyland"]),
            "model": random.choice(["A1","B2","C3","D4"]),
            "base_lat": base_lat,
            "base_lon": base_lon
        })
    return vehicles

# ---------------------------
# JSON builders
# ---------------------------
def build_telemetry_json(vehicle, lat, lon, speed_kmph, heading, ts=None, trip_id=""):
    return {
        "event_id": str(uuid.uuid4()),
        "vehicle_id": vehicle["vehicle_id"],
        "driver_id": vehicle["driver_id"],
        "trip_id": trip_id or "",
        "timestamp": ts or now_iso(),
        "lat": round(lat, 7),
        "lon": round(lon, 7),
        "speed_kmph": round(speed_kmph, 2),
        "heading": round(heading, 2),
        "sat_count": random.randint(5, 12),
        "battery_v": round(random.uniform(11.0, 13.0), 2)
    }

def build_trip_event_json(vehicle, trip_id, event_type, extra=None, ts=None):
    obj = {
        "trip_id": trip_id,
        "vehicle_id": vehicle["vehicle_id"],
        "driver_id": vehicle["driver_id"],
        "event_type": event_type,
        "timestamp": ts or now_iso()
    }
    if extra:
        obj.update(extra)
    return obj

def build_vehicle_status_json(vehicle, ts=None):
    return {
        "vehicle_id": vehicle["vehicle_id"],
        "timestamp": ts or now_iso(),
        "fuel_pct": round(random.uniform(10, 100), 1),
        "engine_temp_c": round(random.uniform(70, 95), 1),
        "odometer_km": int(random.uniform(20000, 400000)),
        "fault_codes": [] if random.random() > 0.98 else [random.choice(["P0420","P0171","P0300"])]
    }

def build_driver_event_json(vehicle, event_type, ts=None):
    return {
        "driver_id": vehicle["driver_id"],
        "vehicle_id": vehicle["vehicle_id"],
        "event_type": event_type,
        "timestamp": ts or now_iso()
    }

def build_alert_json(vehicle, trip_id, alert_type, severity, details):
    return {
        "alert_id": str(uuid.uuid4()),
        "ts": now_iso(),
        "vehicle_id": vehicle["vehicle_id"],
        "trip_id": trip_id or "",
        "alert_type": alert_type,
        "severity": severity,
        "details": details
    }

# ---------------------------
# Simulation loop per vehicle
# ---------------------------
def run_vehicle_loop(vehicle, producer, telemetry_rate, run_seconds):
    start_time = time.time()
    routes = []
    for _ in range(3):
        wp = []
        lat0 = vehicle["base_lat"] + random.uniform(-0.1, 0.1)
        lon0 = vehicle["base_lon"] + random.uniform(-0.1, 0.1)
        for i in range(4):
            wp.append((lat0 + random.uniform(-0.05, 0.05), lon0 + random.uniform(-0.05, 0.05)))
        routes.append(wp)

    in_trip = False
    trip_id = None
    trip_route = None
    route_idx = 0
    route_pos = 0.0
    seg_speed = random.uniform(20, 60)
    last_status_ts = 0
    last_driver_event = 0

    while time.time() - start_time < run_seconds:
        loop_start = time.time()

        # start trip
        if not in_trip and random.random() < 0.02:
            in_trip = True
            trip_id = f"trip_{vehicle['vehicle_id']}_{int(time.time())}"
            trip_route = random.choice(routes)
            route_idx = 0
            route_pos = 0.0
            seg_speed = random.uniform(20, 80)
            evt = build_trip_event_json(vehicle, trip_id, "trip_start", extra={
                "origin_lat": trip_route[0][0],
                "origin_lon": trip_route[0][1]
            })
            producer.produce(topic="fleet.prod.trip.events", key=vehicle["vehicle_id"].encode("utf-8"), value=json.dumps(evt).encode("utf-8"))
            # small chance driver_login
            if random.random() < 0.5:
                producer.produce(topic="fleet.prod.events.driver", key=vehicle["driver_id"].encode("utf-8"), value=json.dumps(build_driver_event_json(vehicle, "driver_login")).encode("utf-8"))

        # if in trip, move and emit telemetry
        if in_trip:
            if route_idx >= len(trip_route) - 1:
                lat, lon = trip_route[-1]
                speed = 0.0
                heading_val = 0.0
                producer.produce(topic="fleet.prod.telemetry.raw", key=vehicle["vehicle_id"].encode("utf-8"), value=json.dumps(build_telemetry_json(vehicle, lat, lon, speed, heading_val, trip_id=trip_id)).encode("utf-8"))
                summary = {
                    "end_lat": lat, "end_lon": lon,
                    "distance_m": int(random.uniform(1000, 50000)),
                    "duration_sec": int(random.uniform(300, 7200)),
                    "status": random.choice(["completed","cancelled"])
                }
                producer.produce(topic="fleet.prod.trip.events", key=vehicle["vehicle_id"].encode("utf-8"), value=json.dumps(build_trip_event_json(vehicle, trip_id, "trip_end", extra=summary)).encode("utf-8"))
                in_trip = False
                trip_id = None
                trip_route = None
                if random.random() < 0.3:
                    producer.produce(topic="fleet.prod.events.driver", key=vehicle["driver_id"].encode("utf-8"), value=json.dumps(build_driver_event_json(vehicle, "driver_logout")).encode("utf-8"))
            else:
                lat1, lon1 = trip_route[route_idx]
                lat2, lon2 = trip_route[route_idx + 1]
                advance = (seg_speed * 1000 / 3600) * (1.0/ max(telemetry_rate, 0.1))
                seg_length_m = haversine_m(lat1, lon1, lat2, lon2)
                frac_inc = advance / seg_length_m if seg_length_m > 0 else 1.0
                route_pos += frac_inc
                if route_pos >= 1.0:
                    route_idx += 1
                    route_pos = 0.0
                    seg_speed = max(5.0, seg_speed + random.uniform(-10, 10))
                lat, lon = interpolate(lat1, lon1, lat2, lon2, min(route_pos, 1.0))
                heading_val = bearing(lat1, lon1, lat2, lon2)
                speed = max(0.0, random.gauss(seg_speed, seg_speed * 0.05))
                producer.produce(topic="fleet.prod.telemetry.raw", key=vehicle["vehicle_id"].encode("utf-8"), value=json.dumps(build_telemetry_json(vehicle, lat, lon, speed, heading_val, trip_id=trip_id)).encode("utf-8"))
                if speed > 80 and random.random() < 0.1:
                    alert = build_alert_json(vehicle, trip_id, "overspeed", 2, f"speed={round(speed,1)}")
                    producer.produce(topic="fleet.prod.alerts.outbound", key=vehicle["vehicle_id"].encode("utf-8"), value=json.dumps(alert).encode("utf-8"))
        else:
            jitter_lat = vehicle["base_lat"] + random.uniform(-0.01, 0.01)
            jitter_lon = vehicle["base_lon"] + random.uniform(-0.01, 0.01)
            speed = random.uniform(0, 10)
            heading_val = random.uniform(0, 360)
            producer.produce(topic="fleet.prod.telemetry.raw", key=vehicle["vehicle_id"].encode("utf-8"), value=json.dumps(build_telemetry_json(vehicle, jitter_lat, jitter_lon, speed, heading_val)).encode("utf-8"))

        # periodic vehicle status
        if time.time() - last_status_ts > max(30, 60 + random.uniform(-10, 10)):
            producer.produce(topic="fleet.prod.vehicle.status", key=vehicle["vehicle_id"].encode("utf-8"), value=json.dumps(build_vehicle_status_json(vehicle)).encode("utf-8"))
            last_status_ts = time.time()

        # periodic driver events
        if time.time() - last_driver_event > max(60, 300 * random.random()):
            if random.random() < 0.05:
                producer.produce(topic="fleet.prod.events.driver", key=vehicle["driver_id"].encode("utf-8"), value=json.dumps(build_driver_event_json(vehicle, random.choice(["break_start", "break_end", "driver_incident"]))).encode("utf-8"))
            last_driver_event = time.time()

        # flush callbacks and sleep to maintain rate
        producer.poll(0)
        elapsed = time.time() - loop_start
        to_sleep = max(0.0, (1.0 / telemetry_rate) - elapsed)
        time.sleep(to_sleep)

# ---------------------------
# Main
# ---------------------------
def main():
    parser = argparse.ArgumentParser()
    # modify to redpanda-1:29092 when deploying with k8s
    parser.add_argument("--brokers", default="localhost:9092")
    parser.add_argument("--num-vehicles", type=int, default=10)
    parser.add_argument("--telemetry-rate", type=float, default=1.0)
    parser.add_argument("--run-seconds", type=int, default=3600)
    parser.add_argument("--create-topics", action="store_true")
    args = parser.parse_args()

    if args.create_topics:
        create_topics(args.brokers, TOPICS)

    conf = {"bootstrap.servers": args.brokers}
    producer = Producer(conf)

    vehicles = generate_fleet(args.num_vehicles)
    print(f"Simulating {len(vehicles)} vehicles -> brokers={args.brokers}, telemetry_rate={args.telemetry_rate}/s per vehicle")
    with ThreadPoolExecutor(max_workers=min(64, len(vehicles))) as exe:
        futures = []
        for v in vehicles:
            futures.append(exe.submit(run_vehicle_loop, v, producer, args.telemetry_rate, args.run_seconds))
        try:
            for f in futures:
                f.result()
        except KeyboardInterrupt:
            print("Interrupted by user, exiting...")

    producer.flush()
    print("Producer stopped.")

if __name__ == "__main__":
    main()
