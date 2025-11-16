#!/usr/bin/env python3
"""
Trip sessionizer (PyFlink) - event-time using KafkaSource (robust imports)

This version tries multiple import locations for KafkaSource/KafkaOffsetsInitializer
to support different PyFlink builds. If KafkaSource is not available it will raise
a helpful error instructing you to either install a newer PyFlink or fallback to
FlinkKafkaConsumer (older API).

Saves trip summaries to topic: fleet.prod.trip.summary
"""

import json
import math
import uuid
import sys
from datetime import datetime

from pyflink.common import Duration, Types
from pyflink.common.serialization import SimpleStringSchema
from pyflink.datastream import StreamExecutionEnvironment
from pyflink.common.watermark_strategy import WatermarkStrategy

# Try robust imports for KafkaSource + offsets initializer across PyFlink versions
KafkaSource = None
KafkaOffsetsInitializer = None
KafkaSourceBuilder = None
use_kafka_source = True

# First attempt: modern PyFlink (typical)
try:
    from pyflink.datastream.connectors import KafkaSource, KafkaOffsetsInitializer
    # if import succeeds, good
except Exception:
    try:
        # Some distributions expose helpers under a kafka submodule
        from pyflink.datastream.connectors.kafka import KafkaSource, KafkaOffsetsInitializer
    except Exception:
        # Some older PyFlink builds only expose KafkaSource (no offsets helper)
        try:
            from pyflink.datastream.connectors import KafkaSource
            KafkaOffsetsInitializer = None
        except Exception:
            KafkaSource = None
            KafkaOffsetsInitializer = None

# If KafkaSource is not available, we'll instruct user to use FlinkKafkaConsumer fallback
if KafkaSource is None:
    print("ERROR: KafkaSource class not available in this PyFlink. "
          "Your PyFlink version may be too old. Falling back will require using FlinkKafkaConsumer instead.",
          file=sys.stderr)
    # Stop here with a clear message — fallback code is below as commented instructions.
    raise ImportError("KafkaSource not available in pyflink.datastream.connectors; use FlinkKafkaConsumer fallback or upgrade PyFlink.")

# -------------------------
# Utility: haversine distance
# -------------------------
def haversine_m(lat1, lon1, lat2, lon2):
    R = 6371000.0
    import math
    phi1 = math.radians(lat1); phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1); dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

# -------------------------
# Map function: parse JSON str -> dict
# -------------------------
def parse_json(s):
    try:
        return json.loads(s)
    except Exception:
        return None

# -------------------------
# ProcessFunction (Keyed) for sessionization
# -------------------------
from pyflink.datastream.functions import KeyedProcessFunction, RuntimeContext
from pyflink.datastream.state import ValueStateDescriptor

class TripSessionizer(KeyedProcessFunction):

    def open(self, runtime_context: RuntimeContext):
        # keyed state descriptors
        self.current_trip = runtime_context.get_state(ValueStateDescriptor("current_trip", Types.STRING()))
        # store last point as JSON string (lat, lon, ts)
        self.last_point = runtime_context.get_state(ValueStateDescriptor("last_point", Types.STRING()))
        self.accum_dist = runtime_context.get_state(ValueStateDescriptor("accum_dist", Types.FLOAT()))
        self.last_speed_ts = runtime_context.get_state(ValueStateDescriptor("last_speed_ts", Types.LONG()))
        # timer for end-detection
        self.end_timer_ts = runtime_context.get_state(ValueStateDescriptor("end_timer_ts", Types.LONG()))

    def process_element(self, value, ctx: 'KeyedProcessFunction.Context'):
        """
        value: dict parsed JSON telemetry
        """
        if value is None:
            return

        vehicle = value.get("vehicle_id")
        speed = float(value.get("speed_kmph", 0.0))
        ts = int(datetime.fromisoformat(value.get("timestamp")).timestamp() * 1000) if value.get("timestamp") else int(ctx.timestamp())
        # current state
        trip_id = self.current_trip.value()
        last_point_s = self.last_point.value()
        dist = self.accum_dist.value() or 0.0

        if trip_id is None:
            # detect trip start
            if speed > 2.0:
                trip_id = f"trip_{vehicle}_{uuid.uuid4().hex[:8]}"
                self.current_trip.update(trip_id)
                self.accum_dist.update(0.0)
                # set last point
                p = {"lat": value.get("lat"), "lon": value.get("lon"), "ts": ts}
                self.last_point.update(json.dumps(p))
                self.last_speed_ts.update(ts)
            else:
                # update last point only (idle)
                p = {"lat": value.get("lat"), "lon": value.get("lon"), "ts": ts}
                self.last_point.update(json.dumps(p))
        else:
            # in-trip: accumulate distance using last_point
            if last_point_s:
                last_p = json.loads(last_point_s)
                try:
                    delta = haversine_m(last_p["lat"], last_p["lon"], value.get("lat"), value.get("lon"))
                except Exception:
                    delta = 0.0
                dist = (dist or 0.0) + delta
                self.accum_dist.update(dist)
            # update last point/time
            p = {"lat": value.get("lat"), "lon": value.get("lon"), "ts": ts}
            self.last_point.update(json.dumps(p))
            self.last_speed_ts.update(ts)

            # detect trip end: speed < 2 -> schedule a short timer to confirm stop (handle jitter)
            if speed < 2.0:
                # schedule timer 20s later in event time to confirm stop
                timer_ts = ts + 20_000
                prev_timer = self.end_timer_ts.value()
                if prev_timer is None or timer_ts > prev_timer:
                    # register event time timer
                    ctx.timer_service().register_event_time_timer(timer_ts)
                    self.end_timer_ts.update(timer_ts)
            else:
                # clear pending end timer if moving again
                if self.end_timer_ts.value() is not None:
                    try:
                        ctx.timer_service().delete_event_time_timer(self.end_timer_ts.value())
                    except Exception:
                        pass
                    self.end_timer_ts.clear()

    def on_timer(self, timestamp: int, ctx: 'KeyedProcessFunction.OnTimerContext', out):
        # This timer confirms the vehicle stayed stopped -> end trip
        trip_id = self.current_trip.value()
        if trip_id is None:
            return
        vehicle = ctx.get_current_key()
        dist = self.accum_dist.value() or 0.0
        # produce trip summary
        summary = {
            "trip_id": trip_id,
            "vehicle_id": vehicle,
            "end_ts": timestamp,
            "distance_m": dist
        }
        # emit summary downstream as JSON string
        out.collect(json.dumps({"event": "trip_end", "summary": summary}))
        # clear state
        self.current_trip.clear()
        self.accum_dist.clear()
        self.last_point.clear()
        self.last_speed_ts.clear()
        self.end_timer_ts.clear()


def main():
    env = StreamExecutionEnvironment.get_execution_environment()
    env.set_parallelism(4)
    # enable checkpointing
    env.enable_checkpointing(30_000)  # 30s
    env.get_checkpoint_config().set_min_pause_between_checkpoints(10_000)
    env.get_checkpoint_config().set_checkpoint_timeout(600_000)
    # NOTE: state backend (RocksDB) should be configured via flink-conf.yaml for cluster-level setup

    # Use KafkaSource (modern source API) with robust offsets initializer handling
    use_kafka = True

    if use_kafka:
        # Build KafkaSource robustly depending on available KafkaOffsetsInitializer symbol
        kafka_bootstrap = "redpanda-1:29092"
        topic_name = "fleet.prod.telemetry.raw"

        # If we have KafkaOffsetsInitializer available, use it; otherwise try to call with starting offsets parameter
        try:
            if KafkaOffsetsInitializer is not None:
                kafka_source = KafkaSource.builder() \
                    .set_bootstrap_servers(kafka_bootstrap) \
                    .set_group_id("trip-sessionizer-group") \
                    .set_topics(topic_name) \
                    .set_value_only_deserializer(SimpleStringSchema()) \
                    .set_starting_offsets(KafkaOffsetsInitializer.earliest()) \
                    .build()
            else:
                # Some PyFlink variants accept a string 'earliest' through a different API.
                kafka_source = KafkaSource.builder() \
                    .set_bootstrap_servers(kafka_bootstrap) \
                    .set_group_id("trip-sessionizer-group") \
                    .set_topics(topic_name) \
                    .set_value_only_deserializer(SimpleStringSchema()) \
                    .build()
                # In this branch, starting offsets default to whatever the source chooses (often 'latest' or connector default).
        except Exception as e:
            print("Failed to construct KafkaSource with KafkaOffsetsInitializer:", e, file=sys.stderr)
            raise

        # assign timestamps & watermarks (bounded out-of-orderness 30s)
        ws = WatermarkStrategy.for_bounded_out_of_orderness(Duration.of_seconds(30)) \
            .with_timestamp_assigner(lambda elem, ts: int(datetime.fromisoformat(json.loads(elem)['timestamp']).timestamp() * 1000))

        # from_source returns a DataStream
        stream = env.from_source(kafka_source, ws, "kafka-source")
    else:
        # local dev via nc -lk 9000 -> send JSON lines
        ws = WatermarkStrategy.for_bounded_out_of_orderness(Duration.of_seconds(30)) \
            .with_timestamp_assigner(lambda elem, ts: int(datetime.fromisoformat(json.loads(elem)['timestamp']).timestamp() * 1000))
        stream = env.socket_text_stream("localhost", 9000, '\n').assign_timestamps_and_watermarks(ws)

    parsed = stream.map(lambda s: parse_json(s), output_type=Types.MAP(Types.STRING(), Types.PYOBJECT()))
    keyed = parsed.key_by(lambda d: d.get("vehicle_id"))
    # apply process function
    result = keyed.process(TripSessionizer(), output_type=Types.STRING())

    # Kafka sink — FlinkKafkaProducer (producer API class is expected to be available as a Java class)
    # We import lazily to avoid import errors if module unavailable in some PyFlink builds
    try:
        from pyflink.datastream.connectors import FlinkKafkaProducer
    except Exception:
        try:
            from pyflink.datastream.connectors.kafka import FlinkKafkaProducer
        except Exception:
            raise ImportError("FlinkKafkaProducer not found in pyflink.datastream.connectors. "
                              "Ensure the Flink Kafka connector JAR is on the classpath (/opt/flink/lib).")

    kafka_producer_props = {
        'bootstrap.servers': 'redpanda-1:29092'
    }
    kafka_producer = FlinkKafkaProducer(
        topic='fleet.prod.trip.summary',
        serialization_schema=SimpleStringSchema(),
        producer_config=kafka_producer_props
    )
    result.add_sink(kafka_producer)

    env.execute("Trip Sessionizer (PyFlink) -> Kafka")

if __name__ == "__main__":
    main()
