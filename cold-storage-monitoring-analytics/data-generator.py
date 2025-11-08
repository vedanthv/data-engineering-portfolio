import os
import json
import random
import time
import uuid
import datetime
from decimal import Decimal, ROUND_HALF_UP
from confluent_kafka import Producer
from confluent_kafka.admin import AdminClient, NewTopic

# ---- config via env ----
BOOTSTRAP = "redpanda:9092"
TEMP_TOPIC = os.getenv("TEMP_TOPIC", "cc.temp_readings")
DOOR_TOPIC = os.getenv("DOOR_TOPIC", "cc.door_events")
SLEEP_SECS = float(os.getenv("SLEEP_SECS", "5.0"))
NUM_PARTITIONS = int(os.getenv("NUM_PARTITIONS", "6"))
REPLICATION_FACTOR = int(os.getenv("REPLICATION_FACTOR", "1"))

ASSET_COUNT = int(os.getenv("ASSET_COUNT", "50"))
DOOR_EVENT_PROB = float(os.getenv("DOOR_EVENT_PROB", "0.05"))
EXCURSION_PROB = float(os.getenv("EXCURSION_PROB", "0.02"))
FREEZER_RATIO = float(os.getenv("FREEZER_RATIO", "0.2"))
SETPOINT_MEAN = float(os.getenv("SETPOINT_MEAN", "4.5"))
SETPOINT_JITTER = float(os.getenv("SETPOINT_JITTER", "0.8"))
AMBIENT_MEAN = float(os.getenv("AMBIENT_MEAN", "22.0"))
AMBIENT_JITTER = float(os.getenv("AMBIENT_JITTER", "2.0"))
NOISE_STD = float(os.getenv("NOISE_STD", "0.15"))

# producer tuning
LINGER_MS = int(os.getenv("LINGER_MS", "50"))
ENABLE_IDEMPOTENCE = os.getenv("ENABLE_IDEMPOTENCE", "true").lower() in ("1", "true", "yes")
ACKS = os.getenv("ACKS", "all") 

SEED = os.getenv("SEED")
# new random number generator object

rnd = random.Random()
if SEED is not None:
    rnd.seed(int(SEED))

# ---- helpers ----
def dround(x, places=2):
    q = Decimal(f'1.{"0"*places}')
    return float(Decimal(x).quantize(q, rounding=ROUND_HALF_UP))

def iso_now():
    return datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc).isoformat()

def ensure_topic(admin_bootstrap, topic, partitions, repl):
    admin = AdminClient({"bootstrap.servers": admin_bootstrap})
    # check existing topics
    md = admin.list_topics(timeout=10)
    if topic in md.topics and not md.topics[topic].error:
        print(f"Topic '{topic}' exists")
        return
    print(f"Creating topic '{topic}' (p={partitions}, r={repl})")
    fs = admin.create_topics([NewTopic(topic, num_partitions=partitions, replication_factor=repl)])
    try:
        fs[topic].result()
        print(f"Created topic '{topic}'")
    except Exception as e:
        if "exists" in str(e).lower():
            print("Topic already exists (race)")
        else:
            print(f"Topic creation error for {topic}: {e}")

# ---- asset model ----
class Asset:
    def __init__(self, idx: int):
        self.idx = idx
        self.asset_id = f"STORE_{1 + (idx // 5)}_A{idx%5:02d}"
        self.site_id = f"STORE_{1 + (idx // 5)}"
        self.is_freezer = rnd.random() < FREEZER_RATIO

        if self.is_freezer:
            self.spec_low = float(os.getenv("FREEZER_SPEC_LOW", "-25.0"))
            self.spec_high = float(os.getenv("FREEZER_SPEC_HIGH", "-18.0"))
            self.setpoint = float(os.getenv("FREEZER_SETPOINT", "-20.5")) + rnd.uniform(-0.5, 0.5)
            self.temp = self.setpoint + rnd.uniform(-0.7, 0.7)
        else:
            self.spec_low = float(os.getenv("SPEC_LOW", "2.0"))
            self.spec_high = float(os.getenv("SPEC_HIGH", "8.0"))
            self.setpoint = SETPOINT_MEAN + rnd.uniform(-SETPOINT_JITTER, SETPOINT_JITTER)
            self.temp = self.setpoint + rnd.uniform(-0.7, 0.7)

        self.ambient = AMBIENT_MEAN + rnd.uniform(-AMBIENT_JITTER, AMBIENT_JITTER)
        self.sensor_id = f"SEN-{rnd.randint(1000,9999)}"
        self.door_open = False

    def maybe_toggle_door(self):
        if rnd.random() < DOOR_EVENT_PROB:
            self.door_open = not self.door_open
            return {
                "asset_id": self.asset_id,
                "site_id": self.site_id,
                "ts": iso_now(),
                "state": "OPEN" if self.door_open else "CLOSE"
            }
        return None

    def step_temperature(self):
    """
    Simulates how the internal temperature of this refrigeration asset (fridge or freezer)
    changes over time based on door state, environment, and random effects.
    """

    # 1. Determine the target temperature
    #    - If the door is closed, the fridge aims for its normal setpoint (cooling mode)
    #    - If the door is open, the internal temperature tends toward the ambient (room) temperature
    target = self.setpoint if not self.door_open else self.ambient

    # 2. Determine how quickly the temperature moves toward the target
    #    - 'response' controls how fast temperature adjusts each step
    #    - When the door is closed: slower response (e.g., 0.10)
    #    - When open: faster warming response (e.g., 0.30)
    response = (
        float(os.getenv("RESPONSE_CLOSED", "0.10"))
        if not self.door_open
        else float(os.getenv("RESPONSE_OPEN", "0.30"))
    )

    # 3. Introduce occasional temperature excursions (faults or anomalies)
    #    - With small probability EXCURSION_PROB, increase the target temperature temporarily
    #    - Simulates events like compressor delay, power interruption, or door left open too long
    if rnd.random() < EXCURSION_PROB:
        # Add a larger excursion for freezers (e.g., +3.5°C) vs coolers (+2.5°C)
        target += (2.5 if not self.is_freezer else 3.5)

    # 4. Move current temperature slightly toward the target temperature
    #    - Formula: new_temp = old_temp + response * (target - old_temp)
    #    - Creates smooth, gradual temperature change instead of sudden jumps
    self.temp = self.temp + response * (target - self.temp)

    # 5. Add small random Gaussian (bell-curve) noise to simulate sensor variation
    #    - NOISE_STD defines how much random fluctuation to apply (e.g., ±0.15°C)
    self.temp += rnd.gauss(0.0, NOISE_STD)

    # 6. Let the ambient (room) temperature drift slightly as well
    #    - Small random walk to simulate environmental fluctuations (e.g., ±0.02°C)
    self.ambient += rnd.gauss(0, 0.02)

    # 7. Return the updated internal temperature, rounded to 2 decimal places
    return round(self.temp, 2)

# ---- main record builders ----
def make_temp_record(asset: Asset, ingest_ts: str):
    return {
        "asset_id": asset.asset_id,
        "site_id": asset.site_id,
        "ts": iso_now(),
        "temp_c": asset.step_temperature(),
        "spec_low": asset.spec_low,
        "spec_high": asset.spec_high,
        "sensor_id": asset.sensor_id,
        "ingest_ts": ingest_ts,
        "source": "confluent_python_generator_v1",
        "version": 1
    }

# ---- producer setup ----
def make_producer(bootstrap):
    conf = {
        "bootstrap.servers": bootstrap,
        "linger.ms": LINGER_MS,
        "enable.idempotence": ENABLE_IDEMPOTENCE,
        "acks": ACKS,
    }
    print(f"Producer config: {conf}")
    return Producer(conf)

# ---- program flow ----
def main():
    # ensure topics exist
    ensure_topic(BOOTSTRAP, TEMP_TOPIC, NUM_PARTITIONS, REPLICATION_FACTOR)
    ensure_topic(BOOTSTRAP, DOOR_TOPIC, NUM_PARTITIONS, REPLICATION_FACTOR)

    producer = make_producer(BOOTSTRAP)
    assets = [Asset(i) for i in range(ASSET_COUNT)]

    print(f"Producing temp & door events to '{TEMP_TOPIC}'/'{DOOR_TOPIC}' on {BOOTSTRAP} every {SLEEP_SECS}s … Ctrl+C to stop.")

    try:
        while True:
            ingest_ts = iso_now()
            for a in assets:
                # door event
                try:
                    door_evt = a.maybe_toggle_door()
                    if door_evt:
                        key = a.asset_id.encode("utf-8")
                        val = json.dumps(door_evt).encode("utf-8")
                        producer.produce(DOOR_TOPIC, val, key=key)
                        # pump the delivery queue
                        producer.poll(0)
                        print(f"[gen] produced door event for {a.asset_id}")
                except Exception as e:
                    print(f"[gen] door produce error: {e}")

                # temperature event
                try:
                    temp_evt = make_temp_record(a, ingest_ts)
                    key = a.asset_id.encode("utf-8")
                    val = json.dumps(temp_evt).encode("utf-8")
                    producer.produce(TEMP_TOPIC, val, key=key)
                    producer.poll(0)
                    print(f"[gen] produced temp event for {a.asset_id}")
                except Exception as e:
                    print(f"[gen] temp produce error: {e}")

            time.sleep(SLEEP_SECS)
    except KeyboardInterrupt:
        print("Interrupted – flushing producer")
    finally:
        # flush outstanding messages
        producer.flush()
        print("Producer flushed, exiting.")

if __name__ == "__main__":
    main()
