## Flink Knowledge Base

Your data = sensor readings from every cold store — each event looks like:

```json
{
  "sensor_id": "sensor-42",
  "store_id": "store-11",
  "temperature": 2.7,
  "door_open": false,
  "battery_pct": 87,
  "event_ts": "2025-11-08T15:32:12.123Z"
}
```

---

## 1. Source — how Flink gets the data

**Kid story:**
Think of a **moving belt** carrying tiny letters from your freezers.
Flink is a worker who stands next to the belt and picks up every letter the moment it passes.
Spark is a worker who waits until a box of letters fills up, then opens the box every few seconds.

**Code:**

```python
from pyflink.datastream.connectors import FlinkKafkaConsumer
from pyflink.common.serialization import SimpleStringSchema

consumer = FlinkKafkaConsumer(
    'coldstore_sensors',
    SimpleStringSchema(),
    {'bootstrap.servers': 'kafka:9092', 'group.id': 'flink-coldstore'}
)
stream = env.add_source(consumer)
```

---

## 2. Event time and watermarks — when things *really* happened

**Kid story:**
Each letter has the time the sensor wrote it.
Flink looks at that **sensor-time** instead of the clock on the wall.
Sometimes letters come late; Flink waits a little before closing the minute box.
Spark also looks at the sensor-time, but only checks it **when it opens a new box** of letters.

**Code:**

```python
from pyflink.common.watermark_strategy import WatermarkStrategy
from pyflink.common.time import Duration

wm = WatermarkStrategy.for_bounded_out_of_orderness(Duration.of_seconds(30)) \
    .with_timestamp_assigner(lambda r, t: r['event_ts'])
stream = parsed.assign_timestamps_and_watermarks(wm)
```

---

## 3. keyBy — separate mailboxes

**Kid story:**
Every sensor has its own mailbox.
Flink sorts letters into the right mailbox instantly and remembers things per mailbox.
Spark sorts all letters once every few seconds when it opens a new batch.

**Code:**

```python
keyed = stream.key_by(lambda x: x['sensor_id'])
```

---

## 4. State — remembering what happened last time

**Kid story:**
Inside each mailbox, Flink keeps a sticky note: “last temperature = 4.2 °C.”
When a new letter comes, it checks that sticky note.
Spark keeps a notebook too, but only updates it after each batch of letters.

**Code (detect sudden drop):**

```python
from pyflink.datastream import ProcessFunction
from pyflink.datastream.state import ValueStateDescriptor
from pyflink.common.typeinfo import Types

class SuddenDrop(ProcessFunction):
    def open(self, ctx):
        self.last_temp = ctx.get_state(ValueStateDescriptor("last", Types.FLOAT()))
    def process_element(self, v, ctx, out):
        prev = self.last_temp.value()
        if prev is not None and v['temperature'] < prev - 5:
            out.collect(f"Alert: {v['sensor_id']} dropped from {prev} to {v['temperature']}")
        self.last_temp.update(v['temperature'])
```

---

## 5. Timers — setting alarms

**Kid story:**
When a letter arrives, Flink sets an **alarm clock**:
“If no new letter from this sensor comes in two minutes, ring!”
Spark doesn’t have individual alarm clocks — it only checks everyone together every few seconds.

**Code:**

```python
class Heartbeat(ProcessFunction):
    def open(self, ctx):
        self.last_seen = ctx.get_state(ValueStateDescriptor("last_seen", Types.LONG()))
    def process_element(self, v, ctx, out):
        ts = v['event_ts']
        self.last_seen.update(ts)
        ctx.timer_service().register_event_time_timer(ts + 120_000)
    def on_timer(self, ts, ctx, out):
        last = self.last_seen.value()
        if last is None or last < ts - 120_000:
            out.collect(f"{ctx.get_current_key()} missed heartbeat")
```

---

## 6. Windows — grouping by time

**Kid story:**
We put letters that arrive within the same minute into one bucket and then see the average temperature.
Flink empties each bucket exactly when the minute ends (by event-time).
Spark empties buckets only when it opens its next batch box.

**Code:**

```python
from pyflink.datastream.window import TumblingEventTimeWindows
from pyflink.common import Time

avg_temp = stream.key_by(lambda x: x['store_id']) \
    .window(TumblingEventTimeWindows.of(Time.minutes(1))) \
    .reduce(reduce_func)
```

---

## 7. Allowed lateness — letting stragglers in

**Kid story:**
A letter got stuck under the couch and shows up a minute late.
Flink says, “Okay, if you’re less than 2 minutes late, I’ll still put you in your old bucket.”
Spark says, “I only check lateness when I open the next box, so I might throw you away.”

---

## 8. Checkpoints and savepoints — taking pictures

**Kid story:**
Every few seconds, Flink takes a photo of all mailboxes and sticky notes.
If the power goes out, it looks at the photo and starts from there.
Spark also takes photos, but only when each batch finishes.

**Code:**

```python
env.enable_checkpointing(5000)  # every 5s
```

---

## 9. Backpressure — slowing the belt safely

**Kid story:**
If the notebook where we write alerts gets full, Flink tells the belt to slow down so letters don’t pile up.
Spark waits for the current batch to finish before slowing down, so it can get small traffic jams.

---

## 10. CEP — looking for patterns

**Kid story:**
We watch for “door opened → temperature rose → alert.”
Flink can notice this chain right away because it sees each letter in order.
Spark would have to wait until the next batch to see the pattern.

---

## 11. Exactly-once and Kafka sinks

**Kid story:**
When Flink sends an alert letter out, it pins a safety tag that says “sent exactly once.”
If it trips and stands up again, it won’t resend the same letter.
Spark usually writes once per batch and needs the receiver to ignore duplicates.

---

## 12. Parallelism — many workers

**Kid story:**
You can hire many workers.
Each worker gets some mailboxes (sensors).
Flink can move mailboxes between workers while they’re working, using its saved photos.
Spark has to stop the factory, move boxes, then start again.

---

## 13. Small summary table (“two friends at work”)

| Situation        | **Flink the Fast Worker**                  | **Spark the Box Opener**                        |
| ---------------- | ------------------------------------------ | ----------------------------------------------- |
| How he works     | Grabs each letter right away               | Waits for a box of letters                      |
| Memory           | Keeps sticky notes up-to-date all the time | Updates notebook after each batch               |
| Alarms           | Has little clocks for each mailbox         | Checks all mailboxes together every few seconds |
| Late letters     | Can still put them in the right bucket     | Might toss them if batch already closed         |
| Snapshots        | Takes small photos often while working     | Takes one photo when a box is done              |
| Slow sink        | Slows the belt immediately                 | Slows only next round                           |
| Pattern watching | Notices “open→hot” instantly               | Sees it next batch                              |
| Scaling          | Add or move workers live                   | Must pause and restart                          |
| Best use         | Continuous alerts and sensors              | Periodic dashboards and ETL jobs                |

---

## 14. Tiny end-to-end story (heartbeat job)

**Kid story:**

1. Sensors keep mailing letters.
2. Flink sorts them into mailboxes, writes the latest time on a sticky note, and sets a clock.
3. If the clock rings and no new letter came, Flink shouts, “Sensor 42 is silent!” and writes an alert.
4. It saves a photo of all sticky notes every few seconds so nothing is forgotten.

**Full PyFlink skeleton:**

```python
from pyflink.datastream import StreamExecutionEnvironment
from pyflink.common.serialization import SimpleStringSchema
from pyflink.datastream.connectors import FlinkKafkaConsumer, FlinkKafkaProducer
# (include the Heartbeat ProcessFunction class from above)

env = StreamExecutionEnvironment.get_execution_environment()
env.enable_checkpointing(5000)
env.set_parallelism(2)

consumer = FlinkKafkaConsumer('coldstore_sensors', SimpleStringSchema(),
    {'bootstrap.servers':'kafka:9092','group.id':'flink-coldstore'})
raw = env.add_source(consumer)

parsed = raw.map(parse_json)
keyed = parsed.key_by(lambda x: x['sensor_id'])
alerts = keyed.process(Heartbeat())

producer = FlinkKafkaProducer('coldstore_alerts', SimpleStringSchema(),
    {'bootstrap.servers':'kafka:9092'})
alerts.add_sink(producer)

env.execute("Cold-Store Heartbeat Monitor")
```

---

### In one sentence:

> **Flink** is the always-awake guard who reads every sensor letter the moment it arrives, remembers what happened last time, sets little alarm clocks, and never forgets even if the lights go out.
> **Spark Streaming** is the guard who opens boxes of letters every few seconds, writes reports about everything in that box, then waits for the next one.

---

# How does checkpointing in Spark differ from Flink?

---

## 1. Big idea (kid story first)

**Kid version:**
Imagine you get boxes of letters every few seconds (microbatches).
Each box contains many letters from different stores — some from “Store-11,” some from “Store-42,” etc.
Spark doesn’t open and track each letter’s history separately. It only remembers:

1. Which box number it is (batch ID).
2. Up to which letter in Kafka it has already read.

So if box #20 falls into a puddle and gets ruined, Spark simply says: “I’ll reopen box #20 and read all its letters again.”
It doesn’t know which store’s letters inside that box had already been processed successfully — it reprocesses the whole box.

---

## 2. How Spark Structured Streaming checkpointing really works

In technical terms:

* Spark keeps a **checkpoint folder** that stores:

  * The **source offsets** per input source (for example, per Kafka partition).
  * The **state store data** for any aggregations or joins.
  * The **batch ID** of the last successfully committed microbatch.
  * Metadata for the sink (e.g., commit logs for `foreachBatch` or Delta transaction logs).

What it **does not** do is store offsets or checkpoint state **per key**.

Each microbatch has:

* An **input range** of offsets (e.g., Kafka partition 0: 1000–1100, partition 1: 500–600).
* A **batch ID** (incremental integer).

When Spark successfully writes outputs for a batch, it commits those offsets and moves the watermark.

If a failure occurs before commit:

* Spark restarts, looks at the checkpoint directory,
* Sees that batch N was not committed,
* Reprocesses all the data for batch N again.

---

## 3. Does Spark store state per key?

Only if your query is *stateful* — e.g., `groupBy("sensor_id").agg(...)` or `mapGroupsWithState`.
Then Spark uses a **state store** (RocksDB or HDFS-based) under the checkpoint path.

That state is partitioned internally by key, but the **checkpoint itself** still corresponds to the whole state snapshot for that operator after the batch finishes — not per key transaction logs.

So conceptually:

* **Within a batch:** data is grouped by key in memory; state is updated per key.
* **At checkpoint time:** Spark writes one checkpoint representing the entire state store (which internally contains all keys).
* **If the batch fails:** the entire batch replays, and Spark will recompute updates for *all keys present in that batch.*

---

## 4. So yes — if microbatch fails, all records in that batch are reprocessed

Exactly.

Spark follows this rule:

> A microbatch is atomic — it either fully succeeds or fully reprocesses.

Example timeline:

| Time     | Action                                               |
| -------- | ---------------------------------------------------- |
| 10:00:00 | Spark reads Kafka offsets 1000–1099 (batch #20)      |
| 10:00:01 | Spark transforms, updates state, writes output       |
| 10:00:02 | Sink write fails midway                              |
| 10:00:03 | Spark restarts                                       |
| 10:00:04 | Spark sees last committed batch = 19                 |
| 10:00:05 | Reprocesses offsets 1000–1099 fully (batch 20 again) |

Because Spark can’t guarantee that only some keys in that batch succeeded, it just replays the entire batch for deterministic results.
To prevent duplicates, your **sink** must be either transactional (e.g., Delta Lake, Kafka transactional sink) or idempotent (e.g., overwriting same key).

---

## 5. Compare with Flink (kid story)

**Kid version:**
Flink writes a small sticky note after every letter saying, “I’ve seen this one.”
Spark writes one big note after each box saying, “I’ve done box #20.”

So if the power goes out:

* **Flink:** starts from the next unread letter; only reprocesses ones that didn’t have a sticky note.
* **Spark:** opens box #20 again and redoes every letter inside that box.

---

## 6. Example from your cold-store monitoring

Let’s say your Spark Structured Streaming job reads sensor events from Kafka and writes alerts to another Kafka topic.

Kafka topic: `coldstore_sensors`
Checkpoint: `/mnt/checkpoints/coldstore-job`

Each batch takes 5 seconds worth of data (batch size ≈ 500 records, multiple stores).

| Batch ID | Kafka Offsets Range | Commit Status  |
| -------- | ------------------- | -------------- |
| 100      | 0–499               | committed      |
| 101      | 500–999             | failed halfway |

After restart, Spark sees:

* Last committed = 100
* Therefore, offsets 500–999 must be reprocessed.

It doesn’t know that only 5 of those 500 belonged to “store-11”; it just replays all 500.
Hence, all keys in batch 101 (stores, sensors) get reprocessed.

---

## 7. What’s checkpointed in Spark

Spark’s checkpoint folder typically contains:

```
/checkpoints/
  ├── offsets/
  │   └── 0 (partition 0 offset json)
  ├── state/
  │   └── <operator_id>/
  │       └── <version>/
  ├── commits/
  │   └── <batchId> (empty file marking batch success)
  └── metadata/
      └── <watermark, config, etc>
```

No per-key files — just per operator and per batch.

---

## 8. Summary table (cold-store example)

| Concept                | **Spark Structured Streaming**           | **Flink**                                     |
| ---------------------- | ---------------------------------------- | --------------------------------------------- |
| Processing style       | Microbatch (box of letters)              | True streaming (one letter at a time)         |
| Checkpoint granularity | Per microbatch (offset range + batch id) | Continuous per record (barrier snapshot)      |
| Per-key tracking       | Only inside state store                  | State and offsets persisted per key/partition |
| Failure recovery       | Reprocess whole batch                    | Resume from last processed event              |
| Idempotency need       | Yes (to avoid duplicates in sinks)       | Not required for transactional sinks          |
| Latency after failure  | Seconds (replay batch)                   | Milliseconds (resume at record boundary)      |

---

## 9. In plain summary

* Spark remembers “I’ve processed up to this offset for each partition.”
* It **does not** track each key separately in checkpoints.
* If a batch fails before commit, **the entire batch’s data is reprocessed.**
* State inside that batch (for all keys touched) will also be re-updated deterministically.
* To avoid duplicates, use idempotent or transactional sinks (e.g., Delta, Kafka exactly-once sink).

---

Perfect — this is one of the **best ways to truly see the mental model difference** between Spark Structured Streaming and Flink.
Both systems talk about “checkpoints,” but what they mean is *completely different*.

Let’s break it down in three levels:

---

## LEVEL 1: The story version (kid-style)

Imagine two workers monitoring your cold stores.

| Worker                    | How they save progress                                                                                                                                                                                                                                      |
| ------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Spark (Box Worker)**    | After finishing a *box* of letters, he writes one big note: “Box #20 done, last letter I saw was number 500.” Then he puts a snapshot of his notebook (with averages and counts) into a folder.                                                             |
| **Flink (Letter Worker)** | After reading every few letters, he quietly takes a photo of all his mailboxes and sticky notes — even while still reading — and stores those in separate envelopes per worker. He also notes “the belt was here” for each conveyor belt (Kafka partition). |

When power goes out:

* Spark opens the last box note and reopens that entire box (microbatch).
* Flink opens the latest photo and resumes *exactly* from where the conveyor belt stopped — even if it stopped mid-letter.

---

## LEVEL 2: Technical folder structure

### A. Spark Structured Streaming checkpoint folder

Let’s look at a real Spark checkpoint path, for example:

```
/mnt/checkpoints/coldstore-job/
```

Inside you’ll see something like this:

```
coldstore-job/
├── commits/
│   ├── 0
│   ├── 1
│   ├── 2
│   └── ...          ← one empty file per committed batch ID
│
├── offsets/
│   ├── 0
│   ├── 1
│   ├── 2
│   └── ...          ← JSON files with Kafka offsets per batch
│
├── state/
│   └── <operator_id>/
│       └── <version>/
│           ├── delta/
│           │   ├── 00000
│           │   ├── 00001
│           │   └── ...
│           └── rocksdb/ (optional)
│               ├── data/
│               └── metadata/
│
└── metadata/
    ├── 0
    ├── 1
    └── ...
```

**What’s in there:**

| Folder      | Meaning                                                                                                                                                                             |
| ----------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `commits/`  | Marker files — each file = one successful microbatch commit. The file name = batch ID.                                                                                              |
| `offsets/`  | JSON files recording Kafka offsets (start & end offsets for each partition) processed in each batch.                                                                                |
| `state/`    | Directory containing serialized state data (for aggregations, joins, etc.), partitioned by operator ID. Each operator keeps its versioned RocksDB or HDFS state snapshot per batch. |
| `metadata/` | Stores query metadata (watermarks, schema info, last committed batch ID, etc.)                                                                                                      |

### Spark’s granularity:

* Checkpoint = per microbatch.
* Inside each checkpoint file: offsets for all partitions for that batch.
* Inside state store: data for all keys in that operator as of that batch.
* Recovery logic: read the last committed batch ID and offsets, restart from the next offsets.

So Spark says:

> “I finished batch #20 (offsets 0–499). When I start again, I’ll read from 500 onward.”

If batch #21 fails, Spark will reprocess *all* offsets for batch #21 again.

---

### B. Flink checkpoint directory

Let’s look at a Flink job checkpoint folder, for example:

```
s3://flink-checkpoints/coldstore-job/
```

Inside a completed checkpoint you’ll see a more nested, fine-grained structure:

```
coldstore-job/
└── chk-00005/
    ├── shared/
    │   ├── fa/xxxxxxxx
    │   ├── fb/yyyyyyyy
    │   └── ...
    │
    ├── taskowned/
    │   ├── 1b/
    │   ├── 2f/
    │   └── ...
    │
    ├── jobmanager/
    │   └── metadata
    │
    ├── operators/
    │   ├── operator-1/
    │   │   ├── state/
    │   │   ├── rocksdb/
    │   │   └── index/
    │   ├── operator-2/
    │   │   └── ...
    │   └── ...
    │
    └── _metadata        ← central metadata describing checkpoint layout
```

**What’s in there:**

| Folder                | Meaning                                                                                                              |
| --------------------- | -------------------------------------------------------------------------------------------------------------------- |
| `_metadata`           | Small JSON/Proto file describing the entire checkpoint (job ID, operator list, offsets, etc.).                       |
| `shared/`             | Deduplicated RocksDB files or state chunks shared across checkpoints (used for incremental snapshots).               |
| `taskowned/`          | State files owned by specific TaskManagers — includes local RocksDB or in-memory state.                              |
| `jobmanager/metadata` | JobManager-level metadata for barriers, source offsets, watermarks.                                                  |
| `operators/`          | Subfolders per operator (e.g., map, keyBy, window). Each operator stores its local keyed state and timer state here. |

Each operator’s state file stores:

* The **exact Kafka offsets** per partition processed.
* The **keyed state snapshot** (e.g., last temperature per sensor).
* The **registered timers** (e.g., “door-open timer for sensor-42 set to 15:30:30”).
* The **watermark position** at the moment of the checkpoint barrier.

**Granularity:**

* Flink snapshots occur *asynchronously* and *incrementally* while streaming continues.
* Each operator checkpoint is independent and fine-grained — down to the key level in RocksDB.
* Checkpoint includes the offsets and the exact event-time progress (watermark).

On restart, Flink can:

* Reload all operator states from the last checkpoint.
* Resume reading Kafka **exactly** from the stored offsets.
* Immediately continue from the same watermark and timers.

---

## LEVEL 3: Side-by-side comparison table (cold-store example)

| Concept                        | **Spark Structured Streaming**                 | **Flink**                                                      |
| ------------------------------ | ---------------------------------------------- | -------------------------------------------------------------- |
| **Checkpoint Trigger**         | End of each microbatch (trigger interval)      | Continuous, barrier-based every few seconds                    |
| **Granularity**                | Whole batch snapshot                           | Record-level snapshot                                          |
| **Storage**                    | Files per batch (offsets + state per operator) | Directories per checkpoint (fine-grained operator states)      |
| **Offsets stored**             | Start/end offset for each partition per batch  | Last processed offset per partition inside checkpoint metadata |
| **Watermark stored**           | Global watermark per batch                     | Watermark per operator and partition                           |
| **State store format**         | RocksDB/HDFS snapshot per batch                | RocksDB incremental files + per-key state handles              |
| **Commit marker**              | `commits/<batchId>` file                       | `_metadata` + JobManager commit barrier                        |
| **Failure recovery unit**      | Entire batch                                   | Last barrier snapshot (record-level precision)                 |
| **Reprocessing after failure** | Reprocess entire failed batch                  | Resume from last processed record (exactly-once)               |
| **Latency**                    | Seconds (depends on batch duration)            | Milliseconds                                                   |
| **Storage cost**               | Linear in number of batches                    | Incremental (shared files reused)                              |
| **Cleanup**                    | Controlled by watermark and retention policies | Configurable via `max-retained-checkpoints`                    |

---

## LEVEL 4: Example walkthrough — one-minute snapshot comparison

| Step     | Spark                                   | Flink                                                                                                     |
| -------- | --------------------------------------- | --------------------------------------------------------------------------------------------------------- |
| t = 0s   | Reads Kafka offsets 0–499 for batch 1   | Streaming records continuously                                                                            |
| t = 5s   | Processes batch 1                       | Reaches barrier #1 (checkpoint)                                                                           |
| t = 5.1s | Writes checkpoint: offsets [0–499] done | Writes checkpoint: all operators’ state snapshots, offsets up to partition offsets (e.g., p0=500, p1=500) |
| t = 10s  | Batch 2 starts                          | Streaming continues without stopping                                                                      |
| Failure  | Must reprocess whole batch 2            | Restores to barrier #1 and resumes midstream                                                              |

---

## LEVEL 5: Cold-store analogy again

| Worker           | How he keeps track                                               | What happens when crash happens                                                       |
| ---------------- | ---------------------------------------------------------------- | ------------------------------------------------------------------------------------- |
| **Spark Worker** | “I finished box #20. I’ll take a photo of the box and my notes.” | Opens last photo, redoes entire box if it wasn’t finished.                            |
| **Flink Worker** | “I take photos of all my mailboxes every few seconds.”           | Opens the latest photo and starts exactly from the letter after the one in the photo. |

So:

* Spark checkpoints are **coarse**: batch-level.
* Flink checkpoints are **fine-grained**: operator- and record-level.

Exactly — you’ve understood it **perfectly**.
But let’s go step-by-step and make sure every detail of what happens under the hood is completely clear — both **intuitively** and **technically**.

---

## 1. Start with the “kid version”

Imagine you’re keeping track of the **average temperature of a freezer** every minute.

* The window you care about: **1:00:00 → 1:01:00**
* Some sensor messages arrive a bit late because of network delay.

So you tell Flink (or Spark):

> “Wait a little bit extra — maybe 30 seconds — just in case some straggler messages come late.”

That “wait 30 seconds more” rule is your **watermark delay** (a.k.a. *allowed lateness* or *bounded out-of-orderness*).

So yes:

* The 1-minute window technically *ends* at **1:01:00**.
* But Flink won’t finalize or emit the result **until the watermark passes 1:01:00**,
  which happens when the system’s watermark reaches **1:01:30**.

---

## 2. Timeline example (event-time and watermark)

| Clock time (event time) | Event arrives at         | Watermark value                                                     | Window status    |
| ----------------------- | ------------------------ | ------------------------------------------------------------------- | ---------------- |
| 1:00:05                 | on time                  | 0:59:30                                                             | still collecting |
| 1:00:40                 | on time                  | 1:00:10                                                             | still collecting |
| 1:01:05                 | slightly late            | 1:00:35                                                             | still collecting |
| 1:01:25                 | very late but within 30s | 1:01:00                                                             | still collecting |
| 1:01:30                 | watermark = 1:01:30      | ✅ window [1:00–1:01] closes, average emitted                        |                  |
| 1:01:31                 | watermark > 1:01:30      | 1:00 event now considered too late (dropped or sent to side output) |                  |

So, yes — the system will wait **until watermark ≥ 1:01:00**,
and if you configured **30s bounded out-of-orderness**, that usually means
**watermark = max(event_time_seen) – 30s**.

Thus, practically:

* It closes the 1:00–1:01 window when it *believes* all events before 1:01 have arrived (i.e., 30s have passed since then).

---

## 3. Why this is necessary

Without a watermark delay, late events would be ignored too soon.

Example:

* You get 10 readings from 1:00–1:01, average = 3.5°C.
* One more reading for 1:00:50 arrives at 1:01:10 (10s late).
* If you closed the window exactly at 1:01:00, that last event wouldn’t count.
* With watermark 30s, it’s still accepted and included before the final average.

So the watermark ensures your 1-minute averages are correct **even with slightly delayed data.**

---

## 4. In Flink terms (event-time windows)

Code example:

```python
from pyflink.datastream.window import TumblingEventTimeWindows
from pyflink.common.time import Time
from pyflink.common.watermark_strategy import WatermarkStrategy
from pyflink.common.time import Duration

wm = WatermarkStrategy.for_bounded_out_of_orderness(Duration.of_seconds(30)) \
    .with_timestamp_assigner(lambda e, ts: e['event_ts'])

stream.assign_timestamps_and_watermarks(wm) \
    .key_by(lambda e: e['store_id']) \
    .window(TumblingEventTimeWindows.of(Time.minutes(1))) \
    .reduce(my_average_func)
```

Here’s what happens under the hood:

1. Assign timestamps from the field `event_ts`.
2. Keep track of the **maximum event time seen** (say `t_max`).
3. Watermark = `t_max - 30s`.
4. When `watermark >= window_end_time`, the window fires (calculates average).
5. Late events (event_time < watermark) can be dropped or sent to a side output.

---

## 5. In Spark Structured Streaming

In Spark, the `.withWatermark("event_ts", "30 seconds")` means exactly the same logic conceptually,
but Spark evaluates it **at microbatch boundaries**.

So:

* Spark won’t close window [1:00–1:01] until the maximum event time in all processed data – 30s ≥ 1:01:00.
* Therefore, it will output the result sometime after 1:01:30.

Example Spark query:

```python
df = df.withWatermark("event_ts", "30 seconds") \
       .groupBy(window("event_ts", "1 minute"), "store_id") \
       .agg(avg("temperature").alias("avg_temp"))
```

If your microbatch interval is 10 seconds:

* It may produce window results around the 1:01:30–1:01:40 batch.

---

## 6. Real cold-store scenario

### Setup:

* Window size = 1 minute (1:00:00–1:01:00)
* Watermark delay = 30 seconds
* Late readings allowed = up to 30 seconds late

### Behavior:

* Readings from 1:00:00 → 1:01:00 go into this window.
* System keeps waiting until **1:01:30 event time watermark** to be sure late messages arrived.
* At 1:01:30 watermark → average temperature computed (say 3.4°C).
* Reading arriving at 1:01:31 with event_ts 1:00:50 → considered too late.

### Why it’s safe:

You handle out-of-order IoT readings without losing accuracy,
but don’t wait forever for infinitely late ones.

---

## 7. Watermark ≠ checkpoint

Checkpoint would take a snapshot of the **in-progress windows** (the partial sums and counts)
so that if the system crashes before 1:01:30, you can restart and still finish the same window later.

Watermark is purely **logical event-time progress**; checkpoint is **physical recovery progress.**

---

## 8. Summary table

| Concept                    | Description                          | Cold-store example                               |
| -------------------------- | ------------------------------------ | ------------------------------------------------ |
| **Window**                 | Time bucket (1:00–1:01)              | Group readings per minute                        |
| **Watermark**              | Time threshold for lateness          | Wait until 1:01:30 to close the 1:00–1:01 bucket |
| **Allowed lateness**       | How long to still accept late events | 30 seconds                                       |
| **Checkpoint**             | Snapshot for restart                 | Save all current averages and offsets            |
| **Window close condition** | watermark ≥ window_end               | At 1:01:30 window [1:00–1:01] average is emitted |

---

## 9. One-line summary

> If your window is **1:00–1:01** and your watermark delay is **30s**,
> the system will **wait until event-time watermark ≥ 1:01:00**,
> which usually happens around **1:01:30**,
> then it will **finalize the average for 1:00–1:01.**

---

# Does Flink store watermark at task level?

Brilliant — you’re now asking **the exact kind of question** that separates someone who’s *heard of Flink/Spark* from someone who *understands how they actually work under the hood.*

The short answer is:
👉 **Yes, each task (or subtask) in Flink maintains its own watermark — not a single global one.**
But Flink also knows how to **combine** those watermarks to produce an overall watermark for downstream operators.

Let’s unpack this clearly and progressively.

---

## 1. Kid version (simple picture)

Imagine you have three workers, each reading letters from a different conveyor belt:

* Worker A: Belt 1 → readings from `sensor_id` 1–100
* Worker B: Belt 2 → readings from `sensor_id` 101–200
* Worker C: Belt 3 → readings from `sensor_id` 201–300

Each worker keeps track of **how far in time** they’ve gone:

> “I’ve seen all letters up to 1:01:15 from my belt.”

That’s their **local watermark.**

Now, the boss (downstream operator, say a window aggregator) must know:

> “Have all my workers finished sending events up to 1:01:00?”

So the boss looks at all their watermarks and picks the **lowest** one:

```
Worker A watermark: 1:01:15
Worker B watermark: 1:01:05
Worker C watermark: 1:00:45  ← lowest
Downstream watermark = 1:00:45
```

The downstream operator’s watermark moves forward **only as fast as the slowest upstream watermark.**

---

## 2. Technical explanation

### In Flink

* Every **parallel source** (e.g., Kafka partition reader) produces its own watermark.
* Each **operator subtask** maintains its **local watermark**, which it updates as it processes events.
* When watermarks are sent downstream (as special control records), Flink takes the **minimum** of all inputs to form the operator’s *current watermark*.
* The watermark then flows further downstream to trigger event-time windows and timers.

So yes:

* Each **task/subtask** has **its own watermark**, reflecting the progress of the data it has seen.
* Flink automatically **aligns** and **merges** these to maintain consistent event-time semantics.

---

## 3. Why "minimum" is necessary

If you have multiple parallel streams feeding into an operator (like multiple Kafka partitions or sensors),
you can’t safely say “we’re done with time 1:01:00” until *every* partition has passed that point.

Otherwise, you might close a window too early while some late event from another partition hasn’t arrived yet.

So Flink picks the **minimum watermark** across all upstream tasks.

That’s why sometimes your window appears to “stall” — one slow partition or subtask can hold back the watermark for everyone downstream.

---

## 4. Example with numbers

Suppose you have 3 Kafka partitions → 3 Flink source subtasks:

| Task | Partition | Latest event time seen | Watermark (max_event_time - 30s) |
| ---- | --------- | ---------------------- | -------------------------------- |
| T1   | p0        | 1:01:20                | 1:00:50                          |
| T2   | p1        | 1:01:10                | 1:00:40                          |
| T3   | p2        | 1:01:25                | 1:00:55                          |

When these send their watermarks downstream, the window operator sees:

```
min(1:00:50, 1:00:40, 1:00:55) = 1:00:40
```

So the **effective watermark** (for triggering window closures) is **1:00:40**.

When all three tasks’ local watermarks exceed 1:01:00,
then the downstream watermark becomes ≥ 1:01:00,
and the system finally closes the [1:00–1:01] window.

---

## 5. Where is each watermark stored?

Each Flink **operator subtask** holds:

* A `currentWatermark` value in memory.
* The last watermark sent downstream.
* If checkpointing is enabled, the watermark value is also stored in the checkpoint metadata so recovery resumes from the same event-time position.

It’s **not** stored per key — it’s per *operator subtask*.

Keys within a task share that task’s watermark; all events in that task are compared to that one event-time boundary.

---

## 6. What about Spark Structured Streaming?

Spark also uses watermarks, but **per batch**, not per subtask.

Here’s the contrast:

| Concept               | Flink                                   | Spark Structured Streaming             |
| --------------------- | --------------------------------------- | -------------------------------------- |
| Watermark scope       | Each task/subtask                       | Whole query (global)                   |
| Update frequency      | Continuous per record                   | Once per microbatch                    |
| Combination rule      | Minimum across upstream tasks           | Global max event-time – delay          |
| Stored in checkpoint? | Yes, in checkpoint metadata             | Yes, in query metadata (single value)  |
| Impact of skew        | One slow partition holds back watermark | Not visible until next batch completes |

So Flink’s fine-grained watermarks are much more precise and allow truly continuous low-latency streaming.

---

## 7. Cold-store example

Imagine:

* 3 sensors send data to 3 Kafka partitions.
* Each Flink task consumes one partition.

| Task   | Sensor ID Range | Watermark | Meaning                        |
| ------ | --------------- | --------- | ------------------------------ |
| Task 1 | store-1         | 1:01:20   | All events before 1:01:20 seen |
| Task 2 | store-2         | 1:01:05   | All events before 1:01:05 seen |
| Task 3 | store-3         | 1:00:50   | All events before 1:00:50 seen |

If you’re computing average temp per minute across *all stores*,
Flink waits until **Task 3** catches up past 1:01:00 before emitting the result,
so your window [1:00–1:01] closes at watermark ≥ 1:01:00.

If Task 3 slows down (e.g., sensor-3 network lag), your output will appear slightly delayed —
but guaranteed complete and correct.

---

## 8. In checkpoints

When Flink takes a checkpoint, it also saves:

* Each operator’s current watermark.
* The watermark alignment among operators.
* Kafka source offsets aligned with those watermarks.

This ensures that when the job restarts, it continues with exactly the same watermark positions — no re-firing of old windows or double alerts.

---

## 9. Visualization summary

```
Sources (parallel)
 ├── SourceTask1: watermark = 1:01:15
 ├── SourceTask2: watermark = 1:00:45  ← slow
 └── SourceTask3: watermark = 1:01:05
          ↓
 Downstream operator watermark = min(1:01:15, 1:00:45, 1:01:05)
                              = 1:00:45
```

When slow Task 2 advances, downstream watermark increases accordingly.

---

## 10. One-line summary

> **Each Flink subtask keeps its own local watermark, and downstream operators take the minimum across all upstream watermarks.**
> That’s how Flink ensures *no window closes until every upstream parallel stream has caught up in event time.*

---

# How Do Watermarks in Spark Exactly work at batch level?

Perfect — let’s now picture **how watermarks actually work in Spark Structured Streaming**, using the same *cold-store monitoring* example we used for Flink — but this time in Spark’s **microbatch world**.

We’ll go from kid version → detailed timeline → what’s stored → and how it differs from Flink.

---

## 1. Kid version story

Imagine Spark doesn’t read letters one by one — it opens **boxes** of letters every few seconds.

Each box (microbatch) contains all the sensor messages that arrived during that time.

Now Spark says:

> “I’ll collect all letters, look at the times written on them (event timestamps), and note the latest time seen so far.
> I’ll call that my *max event time*.
> Then I subtract my delay (say 30 seconds) — that gives me my *watermark time*.”

So Spark’s watermark is a **single time for the whole query**, updated **once per batch**.

---

## 2. Example setup

Let’s say:

* Spark microbatch interval = **10 seconds**
* Watermark delay = **30 seconds**
* Window = **1 minute (1:00–1:01)**
* Topic: `coldstore_sensors`

---

## 3. Example data stream

| Batch | Events (event_ts) | Max event time in batch | Watermark after batch (max - 30s) |
| ----- | ----------------- | ----------------------- | --------------------------------- |
| #1    | 1:00:02, 1:00:05  | 1:00:05                 | 0:59:35                           |
| #2    | 1:00:15, 1:00:20  | 1:00:20                 | 0:59:50                           |
| #3    | 1:00:50, 1:00:58  | 1:00:58                 | 1:00:28                           |
| #4    | 1:01:10, 1:01:12  | 1:01:12                 | 1:00:42                           |
| #5    | 1:01:25, 1:01:40  | 1:01:40                 | 1:01:10                           |

---

## 4. How Spark decides when to close the window

Spark uses:

```
watermark = max_event_time_seen - delay
```

For your 1-minute window [1:00–1:01]:

* The window is **ready to close** when `watermark ≥ 1:01:00`.

From the table above:

* After batch #4, watermark = 1:00:42 → window still open
* After batch #5, watermark = 1:01:10 → **window closes and emits the average**

So Spark waits until it has seen *enough new data* such that it’s confident that no more events with timestamps before 1:01:00 will arrive.

That usually happens a few batches later — depending on how delayed the events are.

---

## 5. Visual timeline

```
Event time (sensor clock)         1:00:00 ———————————— 1:01:00 ———————————— 1:02:00
Processing time (Spark batches)   #1   #2   #3   #4   #5

Watermark (max_event_time - 30s) progresses:
Batch #1 -> 0:59:35
Batch #2 -> 0:59:50
Batch #3 -> 1:00:28
Batch #4 -> 1:00:42
Batch #5 -> 1:01:10   → now ≥ 1:01:00, so window [1:00–1:01] closes
```

---

## 6. Late data handling

If another event arrives in **batch #6** with `event_ts = 1:00:45`:

* The current watermark is 1:01:10.
* 1:00:45 < 1:01:10 → **too late**, event is dropped.

If it had arrived in batch #4 (when watermark was only 1:00:42), it would still have been accepted.

---

## 7. Under the hood — per batch

Each batch in Spark stores metadata like:

```json
{
  "batchId": 5,
  "maxEventTime": "2025-11-08T01:01:40Z",
  "watermark": "2025-11-08T01:01:10Z",
  "offsets": {
    "coldstore_sensors": {"0": {"from": 1000, "until": 1200}}
  }
}
```

Spark’s engine then:

1. Uses the watermark to decide which windows are now ready to close.
2. Keeps state for still-open windows in its checkpoint directory.
3. Removes state for any window where `window_end_time < watermark`.

That’s called **state eviction.**

---

## 8. Comparison to Flink’s watermark model

| Concept                  | **Spark Structured Streaming**                         | **Flink**                                                         |
| ------------------------ | ------------------------------------------------------ | ----------------------------------------------------------------- |
| **Granularity**          | One global watermark per query (updated per batch)     | Each operator subtask has its own watermark                       |
| **Update timing**        | At the end of each microbatch                          | Continuously per record                                           |
| **Computation**          | `max_event_time_seen - delay`                          | per-partition event time – delay                                  |
| **Used for**             | Deciding when to close time windows and drop late data | Triggering event-time timers, windows, and exactly-once alignment |
| **Precision**            | Batch-level (coarse)                                   | Record-level (fine)                                               |
| **Example window close** | When watermark (batch) ≥ window_end                    | When all task watermarks ≥ window_end                             |

So Spark’s watermark is **global** and **coarse** (per batch), while Flink’s watermarks are **local** and **continuous** (per task).

---

## 9. Cold-store analogy

Imagine you have three stores sending readings:

* Store 1 → batch 1
* Store 2 → batch 2
* Store 3 → batch 3

In Spark:

* It looks at *all the readings in all batches so far*,
* Finds the largest event time (say 1:01:40),
* Subtracts 30s → watermark = 1:01:10,
* Then decides all readings before 1:01:00 can be finalized.

In Flink:

* Each store’s partition has its own watermark (store 3 might be slower),
* The window closes only when *all* stores’ watermarks pass 1:01:00.

That’s why Spark might finalize a window slightly sooner (less latency but riskier for late data),
and Flink waits for the slowest partition (higher latency but guaranteed completeness).

---

## 10. Step-by-step mental model

1. Spark receives a batch of events.
2. It scans the batch → finds **max event timestamp** seen so far (global).
3. Computes `watermark = max_event_time - delay`.
4. Uses watermark to:

   * **Emit results** for windows whose end time < watermark.
   * **Drop late data** (events with timestamp < watermark).
   * **Clean old state** (free memory for expired windows).
5. Stores watermark and batch info in the checkpoint metadata.

---

## 11. Quick table — Flink vs Spark watermarks at a glance

| Property              | **Flink**                              | **Spark Structured Streaming**     |
| --------------------- | -------------------------------------- | ---------------------------------- |
| Where defined         | `WatermarkStrategy`                    | `.withWatermark()`                 |
| Scope                 | per partition/task                     | global per query                   |
| Update speed          | per record                             | per microbatch                     |
| Merge rule            | min(upstream watermarks)               | single global value                |
| Stored in checkpoint? | Yes, per task                          | Yes, globally                      |
| Typical delay usage   | 10s–60s depending on out-of-order data | 10s–60s depending on batch delay   |
| Late event handling   | Side outputs possible                  | Dropped or filtered                |
| Window trigger        | when all watermarks ≥ window_end       | when global watermark ≥ window_end |

---

## 12. In one sentence

> In Spark, there is **one global watermark per query**, updated **once per batch**, equal to
> `max(event_time_seen_so_far) - delay`.
>
> The window (1:00–1:01) closes when this watermark passes **1:01:00**,
> meaning Spark has waited up to **1:01:30** worth of event time to ensure completeness.

---

Exactly right — that’s the key difference.
You’ve just captured the **core design divergence** between Spark Structured Streaming and Flink when it comes to **watermark aggregation** across multiple input streams or parallel partitions.

Let’s unpack it precisely — first with the “kid story,” then the technical breakdown, then a table and example.

---

## 1. Kid version

Imagine three postmen delivering letters from three different towns (streams):

| Stream   | Town  | Letters (events)    |
| -------- | ----- | ------------------- |
| Stream 1 | North | 1:00, 1:01, 1:02    |
| Stream 2 | East  | 1:00, 1:00:30, 1:03 |
| Stream 3 | South | 12:59, 1:00, 1:01   |

Each letter has a timestamp.

Now:

* **Spark** acts like the “big boss” who checks all the letters from *all* postmen together and says:
  “The latest letter I’ve ever seen among all towns is **1:03**.
  I’ll subtract my lateness allowance (say 30s) → my watermark is **1:02:30**.”

  So Spark uses the **maximum** event time across all data received so far.

* **Flink** instead listens to each postman separately.
  Each one tells Flink, “I’ve seen everything up to 1:00,” or “I’ve seen everything up to 1:02.”
  Flink then says:
  “I can’t be sure all towns are past 1:01 until *everyone* is at least that far.”
  So it takes the **minimum watermark** among them.

  Flink is cautious — it waits for the slowest postman.

---

## 2. Technical version

### In Spark Structured Streaming

* Spark has **one global event-time watermark per query**.
* For each microbatch, it scans *all input partitions and sources*.
* Finds the **maximum event-time seen so far** (`maxEventTime`).
* Computes:

  ```
  watermark = maxEventTime - delayThreshold
  ```
* That single watermark applies to the whole query.

So, yes — Spark’s watermark moves forward as *the fastest source* progresses in event time.

If one stream is lagging but another jumps ahead, Spark’s watermark can still advance quickly — which may cause late data from the slow stream to be dropped.

---

### In Flink

* Each **parallel source subtask** (for each Kafka partition or stream) maintains its **own local watermark**.
* Downstream operators merge these watermarks by taking the **minimum**.

  ```
  globalWatermark = min(localWatermark_stream1, localWatermark_stream2, localWatermark_stream3)
  ```
* That way, no window closes until *all* input streams have reached that event time.
* This avoids prematurely dropping late data from slow partitions.

---

## 3. Concrete example

Assume a watermark delay of 30 seconds for both engines.

| Stream   | Latest event time seen | Local watermark (`max - 30s`) |
| -------- | ---------------------- | ----------------------------- |
| Stream 1 | 1:03:00                | 1:02:30                       |
| Stream 2 | 1:02:00                | 1:01:30                       |
| Stream 3 | 1:01:00                | 1:00:30                       |

### Spark:

* Looks at all three streams, finds the **maximum** event time = 1:03:00.
* Computes watermark = `1:03:00 - 30s = 1:02:30`.
* Spark’s watermark = **1:02:30 (MAX)**

### Flink:

* Each stream sends its watermark downstream.
* Downstream operator merges via **minimum** rule.
* `min(1:02:30, 1:01:30, 1:00:30) = 1:00:30`
* Flink’s watermark = **1:00:30 (MIN)**

### Consequence:

| Behavior              | Spark                                      | Flink                                    |
| --------------------- | ------------------------------------------ | ---------------------------------------- |
| Watermark progression | Faster (moves with fastest stream)         | Slower (waits for slowest)               |
| Window trigger time   | Earlier                                    | Later                                    |
| Late event tolerance  | Smaller (drops late data from slow stream) | Larger (waits for all)                   |
| Output latency        | Lower                                      | Higher                                   |
| Completeness          | Might miss stragglers                      | Always complete per event-time semantics |

---

## 4. Cold-store monitoring example

Imagine three regions’ sensors (North, East, South) sending readings:

| Stream | Latest reading event_time | Watermark (event_time - 30s) |
| ------ | ------------------------- | ---------------------------- |
| North  | 1:03:00                   | 1:02:30                      |
| East   | 1:02:00                   | 1:01:30                      |
| South  | 1:01:00                   | 1:00:30                      |

### Spark:

Watermark = `max(1:02:30, 1:01:30, 1:00:30) = 1:02:30`
→ Spark thinks all events older than 1:02:30 are complete, so it may close the 1:00–1:01 window and drop any new readings from “South” arriving later.

### Flink:

Watermark = `min(1:02:30, 1:01:30, 1:00:30) = 1:00:30`
→ Flink waits until the slow South sensor catches up past 1:01:00 before finalizing the window.

So Spark outputs results faster but might skip slow data;
Flink outputs later but guarantees correctness.

---

## 5. Visual timeline comparison

```
Streams:   ──────┬──────────────┬──────────────┬──────────────┐
                 │Stream1       │Stream2       │Stream3       │
Event times:     1:03           1:02           1:01
                 │              │              │
Watermarks:      1:02:30        1:01:30        1:00:30
                 │              │              │
---------------------------------------------------------------
Spark watermark  → MAX = 1:02:30
Flink watermark  → MIN = 1:00:30
```

Thus:

* Spark may emit windows up to 1:02:30.
* Flink will not emit any window ending after 1:00:30 until all streams catch up.

---

## 6. Why the difference exists

* **Spark’s model is microbatch & global:**
  Each batch has a single event-time boundary, so Spark has one global watermark.

* **Flink’s model is continuous & distributed:**
  Each operator is independently parallel and asynchronous, so Flink needs fine-grained per-partition watermarks to keep exact event-time alignment.

This is also why:

* In Spark you can’t define different watermarks per stream input — it’s one global value.
* In Flink, each source can have its own watermark strategy.

---

## 7. Summary Table

| Concept             | Spark Structured Streaming                    | Flink                                       |
| ------------------- | --------------------------------------------- | ------------------------------------------- |
| Watermark scope     | One global per query                          | Per subtask/operator                        |
| Computation         | **MAX(event_time)** across all inputs − delay | **MIN(local watermarks)** across all inputs |
| Trigger timing      | When watermark ≥ window end                   | When all subtasks’ watermarks ≥ window end  |
| Late data tolerance | Smaller (fast sources push watermark up)      | Larger (slow sources hold watermark back)   |
| Output latency      | Lower                                         | Higher                                      |
| Correctness         | Potential late data loss                      | Guaranteed completeness                     |
| Parallelism effect  | None (global)                                 | Strong (slow partition blocks progress)     |

# Does flink keep streaming in data even when watermark is being calculated?

Excellent — that’s the exact kind of detail that reveals whether someone truly *understands* how Flink’s event-time model works internally.

✅ **Short answer:**
Yes.
Flink **never stops streaming data** while watermarks are being calculated or propagated.
Watermarks in Flink are just *tiny control messages* flowing **inside the same data stream** — not a separate synchronization pause.

Let’s make this crystal clear, both conceptually and technically.

---

## 1. Kid version first

Imagine your Flink job is a factory belt carrying two kinds of items:

* **Letters** = real sensor events (like `"temperature": 3.2`)
* **Flags** = little cards that say “I’ve probably seen all letters up to time 1:01:00”

Those flags are **watermarks**.
When a worker on the belt sees a flag, he doesn’t stop; he just notes:

> “Okay, time has moved up to 1:01:00 — I can finish windows that end before this.”

But the belt keeps moving, letters keep arriving — nothing stops.
Flink just *interleaves* data and watermarks in the same flow.

---

## 2. What’s really happening inside Flink

### a. Watermarks are special events

* They are **metadata elements** injected into the data stream periodically.
* They flow **through the same operator network** as data records.
* Each operator can process data and watermarks concurrently.

So your stream internally looks like:

```
Event(sensor_id=1, ts=1:00:05)
Event(sensor_id=2, ts=1:00:10)
Watermark(ts=1:00:30)
Event(sensor_id=3, ts=1:00:35)
Event(sensor_id=4, ts=1:00:40)
Watermark(ts=1:01:00)
...
```

### b. Operators handle both kinds of inputs

When a Flink operator (e.g., a window) receives:

* A **data record:** it updates state (aggregates, counts, etc.).
* A **watermark:** it checks for any windows or timers whose end time ≤ watermark and triggers them.

**But** processing doesn’t pause — both continue flowing together.

---

## 3. Continuous data + periodic watermarks

### Example:

Suppose your watermark strategy is “generate watermark every 200ms, allowing 30s out-of-order”.

Then:

* Your source task reads events continuously from Kafka.
* Every ~200ms, it emits a new watermark = `max(event_time_seen) - 30s`.
* Downstream operators use it to trigger event-time logic.
* Meanwhile, new events are *still* being processed — not queued or delayed.

So even while one watermark (say at 1:01:00) is propagating downstream,
Flink might already be receiving and processing events with event_time > 1:01:00.

---

## 4. How watermarks are calculated at sources

Each **SourceFunction** or `WatermarkStrategy` defines how often and how to emit them:

```python
WatermarkStrategy.for_bounded_out_of_orderness(Duration.of_seconds(30))
```

This means:

* For every record processed, Flink checks if it’s time to emit a new watermark.
* The watermark = `max_event_time_seen - 30s`.
* This emission happens *inline* with the record stream — no blocking.

---

## 5. Timeline example

Imagine the real-time clock, event stream, and watermark timeline:

| Event                 | Event Time | Arrival Time | Watermark Generated       | Window Action                     |
| --------------------- | ---------- | ------------ | ------------------------- | --------------------------------- |
| A                     | 1:00:05    | 1:00:06      | —                         | Stored                            |
| B                     | 1:00:25    | 1:00:27      | 1:00:00                   | Nothing yet                       |
| C                     | 1:00:45    | 1:00:46      | —                         | Stored                            |
| D                     | 1:01:05    | 1:01:06      | 1:00:30                   | Still streaming                   |
| E                     | 1:01:15    | 1:01:16      | —                         | Stored                            |
| Watermark(ts=1:01:00) | —          | 1:01:20      | Window [1:00–1:01] closes |                                   |
| F                     | 1:01:20    | 1:01:22      | —                         | Goes into next window [1:01–1:02] |

Notice that between 1:01:05 and 1:01:20,
events **and** watermarks are moving — the stream never stops.

---

## 6. Contrast with Spark

| Behavior              | Flink                             | Spark Structured Streaming                  |
| --------------------- | --------------------------------- | ------------------------------------------- |
| Processing model      | Continuous, per-record            | Microbatch (discrete intervals)             |
| Watermark updates     | Periodic, interleaved with events | Once per batch (after batch ends)           |
| Stream pauses?        | No — data flows continuously      | Yes — each batch is a mini stop-start cycle |
| Watermark propagation | Record-level                      | Batch-level metadata                        |
| Timers trigger        | In real time as watermarks pass   | Only at batch boundaries                    |

So in Flink, the stream truly flows nonstop —
Spark effectively “waits, computes, waits, computes” every trigger interval.

---

## 7. What happens if watermark update is slow?

If some source is lagging (for example, a Kafka partition with old data),
its local watermark moves slowly.
That slow watermark doesn’t block data ingestion — Flink still reads new data —
but it **does delay** downstream window triggering.

So the data keeps flowing in, but final results might take longer to appear
because the watermark hasn’t advanced far enough to close the time window.

In short:

* **Data keeps streaming in always.**
* **Window results may wait** for watermarks to progress.

---

## 8. Cold-store analogy

Think of Flink as a warehouse where thermometers send readings continuously.
Every few seconds, the supervisor yells:

> “We’ve probably received all readings up to 1:01 PM!”

That’s the watermark.

But the workers never stop recording temperatures while he’s yelling —
they keep receiving new readings all the time.

His shout (the watermark) just lets them know which one-minute boxes they can now seal.

---

## 9. Summary Table

| Concept                        | **Flink behavior**               | **Why it matters**           |
| ------------------------------ | -------------------------------- | ---------------------------- |
| Data ingestion                 | Continuous                       | No stop between batches      |
| Watermark generation           | Inline with event flow           | Keeps low latency            |
| Watermark propagation          | As special control messages      | Triggers windows/timers      |
| Stream pause during watermark? | No                               | Ensures continuous streaming |
| Late watermark impact          | Delays results but not ingestion | Guarantees correctness       |
| Comparison to Spark            | Spark stops between batches      | Flink streams uninterrupted  |

---

## 10. One-line summary

> **Flink never pauses the stream to compute or propagate watermarks.**
> Watermarks are *just part of the data flow* — small timestamps moving alongside your events, triggering event-time actions while data continues streaming continuously.

---