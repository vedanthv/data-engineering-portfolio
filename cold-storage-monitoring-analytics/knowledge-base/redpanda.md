# 1. What Redpanda Is

Redpanda is a **Kafka-API compatible streaming engine**.
It is a drop-in replacement for Kafka, but:

* no ZooKeeper
* single binary
* much faster (C++ + Seastar engine)
* lower latency
* much simpler to operate
* works great on Docker, EC2, Kubernetes

You use it like Kafka:

* Topics
* Partitions
* Producers
* Consumers
* Consumer groups
* Offsets
* Retention

Every Flink or generator process sees it as normal Kafka.

---

# 2. Single-Node vs Multi-Node

Redpanda can run as:

### Single node (your current setup)

* one broker
* good for dev/local
* you use `--overprovisioned`, `--smp=1`, `--memory=1G`

### Multi node (production)

* multiple brokers
* partition replication
* Raft consensus
* fault tolerance
* operators or Helm charts manage it

---

# 3. Major Components You Use in the Compose

## 3.1 Redpanda Broker

This is the main server. It handles:

* Kafka API on port **9092**
* RPC API
* Storage of segments
* Metadata
* Raft consensus engine
* Partition management

This is what your producer and Flink connect to.

---

## 3.2 Redpanda Console

A web UI to manage:

* Topics
* Partitions
* Lag
* Messages
* Groups
* Brokers

You open it at:

```
http://localhost:8080
```

---

## 3.3 Pandaproxy

Kafka over HTTP.

Redpanda exposes an optional REST proxy on port **8082**, useful for:

* sending messages via HTTP
* debugging
* interacting without Kafka clients

You’re not using it heavily, but it’s enabled.

---

# 4. Core Kafka Concepts that Redpanda Implements

## 4.1 Topics

A stream of messages.

Examples in your setup:

* `cc.temp_readings`
* `cc.door_events`
* `cc.alerts`

These must exist before Flink reads them (or auto-create can be turned on).

---

## 4.2 Partitions

Each topic is split into partitions to scale throughput.

Example:

* Topic `cc.temp_readings` could have 6 partitions
* Flink will spin multiple parallel consumers
* More partitions = more throughput and parallelism

Redpanda stores *each partition* as a folder on disk.

---

## 4.3 Offsets

Redpanda tracks where a consumer has read up to.
Offsets are per:

```
topic → partition → consumer group
```

Flink stores its offsets in the consumer group metadata, and checkpoints in its state backend.

---

## 4.4 Consumer Groups

Multiple consumers reading the same topic as a group.

Example:

```
flink_cc_job_group
```

Redpanda ensures that:

* each partition goes to only one consumer instance
* but instances can scale horizontally
* if a consumer dies, another takes over automatically

---

# 5. Storage Engine Internals (why it’s fast)

Redpanda uses:

* **Segmented log files**
* **Index + batch headers**
* **Zero-copy reads** (via memory mapped files)
* **C++ Seastar engine** for asynchronous execution

Everything is append-only, giving very high write throughput.

Segment retention is controlled by:

* time (`retention.ms`)
* size (`retention.bytes`)

---

# 6. Networking Concepts in Your Compose

## 6.1 kafka-addr

```
--kafka-addr=PLAINTEXT://0.0.0.0:9092
```

Where the broker listens internally.

## 6.2 advertise-kafka-addr

```
--advertise-kafka-addr=PLAINTEXT://redpanda:9092
```

What Redpanda tells clients to use.

Important:
**In Docker, the advertised name must be the service name (`redpanda`).**

Otherwise, clients won't connect.

---

# 7. Resource Tuning Flags You Used

## 7.1 --overprovisioned

Tells Redpanda to relax hardware expectations for containers.

## 7.2 --smp

How many CPU threads to use.

You set:

```
--smp=1
```

Because EC2 instance isn’t dedicated for Redpanda.

## 7.3 --memory

Limit internal allocator, preventing Redpanda from using too much RAM.

## 7.4 --reserve-memory

Internal safety buffer.
You set it to zero for containers.

---

# 8. Health Checks

Your healthcheck:

```yaml
test: ["CMD", "bash", "-c", "rpk cluster info --brokers=localhost:9092 || exit 1"]
```

* runs inside container
* uses `rpk` (Redpanda’s CLI) to validate broker health
* ensures Redpanda is ready before Flink starts consuming

This avoids race conditions.

---

# 9. File Descriptors (ULimits)

```yaml
ulimits:
  nofile:
    soft: 65536
    hard: 65536
```

Redpanda opens a lot of files because:

* each topic partition is a directory
* each segment is a file
* logs roll over frequently

Low ulimit = data loss risk or errors.

---

# 10. Persistence

You mapped:

```
rpdata:/var/lib/redpanda
```

This stores:

* topic logs
* metadata
* partitions
* raft state
* snapshots
* offsets

If you delete the volume, all Kafka data disappears.

---

# 11. How Redpanda Behaves in Your Pipeline

### Producers:

* generator.py writes to Redpanda on port 9092
* writes at ~5s intervals per asset
* uses JSON

### Stream Processing:

* Flink reads from Redpanda as if it was Kafka
* Flink checkpoints control offset commits
* you can scale TaskManagers to consume partitions in parallel

### Storage:

* all events stored in Redpanda logs
* ClickHouse ingests processed aggregates from Flink

---

# 12. Operational Behavior

### Restart strategy:

`restart: unless-stopped`

Survives:

* EC2 restart
* Docker daemon restart
* container crash

### Redpanda Admin API:

Port:

```
9644
```

Allows:

* cluster introspection
* metrics scrapers
* monitoring

### Segment retention:

Defaults to Redpanda policy until tuned.

Here is a **clear, engineering-grade explanation** of the **Raft consensus algorithm** and **how it differs from Kafka’s replication model**.
This is the exact level of depth a data engineer should know when working with Redpanda, Flink, Kafka, ClickHouse, or distributed systems.

---

# 1. What is Raft?

**Raft** is a **distributed consensus algorithm** designed to ensure that **multiple nodes agree on the same log entries** even in the presence of failures.

Consensus =
All nodes agree on

* what the current state is
* what the next steps are
* which writes are committed

Raft’s goal:
**Make a replicated log behave like a single reliable machine.**

It guarantees:

* Strong consistency
* Leader-based replication
* Fault tolerance
* Deterministic behavior under failures

Raft was designed to be **understandable** and is used in many systems:

* etcd
* Consul
* CockroachDB
* TiKV
* Redpanda (for all metadata + data partitions)

---

# 2. Core Concepts of Raft

### 2.1 Leader Election

Only **one leader** at a time.
All writes go to the leader.

If the leader dies:

* followers hold an election
* new leader continues safely
* elections are fast and deterministic

### 2.2 Log Replication

When the leader gets a write:

1. Leader appends to its log
2. Sends AppendEntries RPC to followers
3. When majority (quorum) acknowledge → entry is **committed**
4. Leader applies the entry to the state machine
5. Followers apply it too

### 2.3 Commitment & Durability

Commit happens only after **majority** of nodes store the entry.
If leader dies right after commit, followers still have the operation.

---

# 3. Why Redpanda Uses Raft

Redpanda uses Raft for:

### partition replication

Each topic partition is a Raft group.

### metadata consistency

Cluster configuration, brokers, controller state.

### no ZooKeeper needed

Kafka requires ZooKeeper (until KIP-500), but Redpanda never did.

Main benefits:

* predictable behavior
* no split-brain
* fast failover
* correctness by design

---

# 4. Kafka’s traditional replication model (pre-KIP-500)

Kafka **did not use Raft** originally.
It uses a simpler approach:

### 4.1 One leader per partition

Same as Raft.

### 4.2 Followers replicate log

Same as Raft.

### 4.3 BUT commit semantics differ

Kafka commit =
**when the leader writes the message to its local log**
(not when followers have it)

Unless you enable:

* **min.insync.replicas**
* **acks=all**

If you don’t configure these, Kafka can lose committed messages during failover.

### 4.4 ZooKeeper manages cluster metadata

ZooKeeper tracks:

* leaders
* partitions
* brokers
* ACLs

If ZooKeeper fails or is slow, Kafka becomes unstable.

---

# 5. Kafka vs Raft: Key Differences

Below is the practical, real-world comparison:

---

## Difference 1: Metadata storage

**Kafka (classic)**
Uses **ZooKeeper** for metadata storage, elections, and cluster configuration.

**Redpanda (Raft)**
Leader election and metadata replicated via native Raft.
No external dependency.

---

## Difference 2: Strong consistency

**Kafka default writes:**

* write to leader only
* commit immediately
* data may be lost on leader failover
* requires strict configs to be safe

**Raft writes:**

* committed only after **majority** replication
* no acknowledged write is ever lost
* correctness always on by design

---

## Difference 3: Failover behavior

**Kafka:**

* Failover can cause data divergence
* Followers may have stale logs
* Leader recovery requires truncation / reconciliation

**Raft:**

* Log is always consistent
* Followers truncate automatically to leader
* No divergent histories
* Fast recovery

---

## Difference 4: Partition replication

**Kafka:**
Uses ISR (in-sync replicas).
Leader decides if a follower is in sync.

**Raft:**
Replicas are synchronized by the log index.
Leader drives consistency with AppendEntries RPC.

---

## Difference 5: Complexity

**Kafka:**

* Requires ZK for coordination
* More moving parts
* More operational overhead
* Harder to reason about failovers

**Raft:**

* Simple
* Easily understood
* Self-contained
* Fewer failure modes

---

## Difference 6: Multi-node consistency

**Kafka:**
Can have:

* unclean leader elections
* inconsistent writes
* data loss if misconfigured

**Raft:**
Guarantees:

* no split brain
* no unclean failover
* no committed write loss

---

# 6. Real-world example to illustrate

Imagine writing message #100 to partition P0.

### Kafka default:

* Leader writes it locally
* Returns success
* Followers replicate later
* Leader crashes
* Follower was behind (only up to 95)
* New leader takes over at offset 95
* **Messages 96–100 are lost**

### Raft:

* Leader writes #100
* Followers persist #100
* Majority acknowledges
* Leader commits
* Leader crashes
* Followers elect a new leader
* Log stays at #100
* **Message 100 is NEVER lost**

This reliability is why Redpanda uses Raft.

---

# 7. How Redpanda implements Raft internally

Redpanda creates:

* A Raft log for each partition
* A Raft group for cluster metadata
* A Raft group for controller operations

Each group elects:

* **Leader**
* **Followers**

Everything is consistent across the cluster.

---

# 8. Summary Table

| Feature      | Kafka (classic)   | Redpanda / Raft           |
| ------------ | ----------------- | ------------------------- |
| Consensus    | ZooKeeper + Kafka | Pure Raft                 |
| Write safety | Optional          | Always safe               |
| Commit rule  | Leader write      | Majority confirmation     |
| Failover     | Can lose data     | Zero data loss            |
| Metadata     | ZooKeeper         | Internal Raft group       |
| Complexity   | Higher            | Lower                     |
| Ease of ops  | Harder            | Easier                    |
| Performance  | Good              | Very high (C++ + Seastar) |

---

# 9. What You Should Remember

Raft gives you:

* Leader-based replication
* Majority commit
* No data loss
* Fast failover
* No ZooKeeper
* Consistent logs
* Deterministic behavior

Kafka’s older architecture is:

* More flexible but more dangerous
* Requires careful settings to achieve safety
* Depends on ZooKeeper
* More operational overhead

Below is a **deep, step-by-step**, engineering-grade explanation of the failure scenario you asked about and exactly **why Kafka (default settings) can lose committed messages**, and **why Raft (and Redpanda) cannot**.

This is the most important difference between Kafka-style replication and Raft-style consensus.

---

# 1. The Setup

We have a topic with **one leader** and **two followers**.

### Kafka cluster

```
Partition P0
 Leader:  Broker L
 Followers: F1, F2
```

### Raft cluster

```
Raft Group (P0)
 Leader:  Broker L
 Followers: F1, F2
(Majority = 2 of 3)
```

We write message 100.

---

# 2. Kafka Default Behavior (acks=1)

By default, Kafka producer uses:

```
acks=1       <-- THE IMPORTANT PART
```

Meaning:

* Leader writes message to its own disk
* Leader immediately returns success to the producer
* Followers replicate later in the background (asynchronously)

This is NOT a majority-based commit.

---

# 3. Kafka Failure Scenario Explained Step-by-Step

Here is the exact flow:

---

## Step 1: Producer sends message #96–100 to leader

Leader appends:

| Message | Written on Leader? | Written on Followers? |
| ------- | ------------------ | --------------------- |
| 96      | Yes                | Maybe                 |
| 97      | Yes                | Maybe                 |
| 98      | Yes                | Maybe                 |
| 99      | Yes                | Maybe                 |
| 100     | Yes                | Maybe                 |

Followers often lag behind.

### Example:

```
L has:    1,2,3,...,95,96,97,98,99,100
F1 has:   1,2,3,...,95 (lagging)
F2 has:   1,2,3,...,95,96,97 (slightly ahead)
```

---

## Step 2: Leader immediately acknowledges to the producer

Producer sees:

```
SUCCESS: message 100 written
```

**But only Leader has it**, followers have NOT replicated it yet.

---

## Step 3: Leader crashes abruptly

Now followers must elect a new leader.

Both followers attempt to elect themselves.

---

## Step 4: Kafka elects a follower as the new leader

Let’s assume follower F1 becomes the new leader.

F1 has logs only up to:

```
1..95
```

Because F1 did not replicate messages 96–100 yet.

---

## Step 5: New leader’s log becomes the truth

Kafka’s rule (without strict settings):

**The new leader's log becomes the authoritative log.**

This means:

```
L(backup)   had 96..100
F1(leader)  has only up to 95
--> 96..100 are LOST FOREVER
```

F2 will truncate its tail to match F1.

---

## Step 6: Followers truncate messages they previously had

F2 had 96–97.
F2 now sees F1 as leader and performs log truncation.

It removes 96–97 to match new leader’s log.

---

## Final Outcome in Kafka default mode

### LOST MESSAGES:

```
96, 97, 98, 99, 100
```

Even though the original leader explicitly acknowledged them to the producer.

This is called:
**Data Loss on Unclean Failover**
and it happens when:

* producer uses `acks=1`
* `unclean.leader.election` is allowed (default in older Kafka)
* follower lag exists (very common)

---

# 4. Why Raft NEVER Loses These Messages

Raft has a completely different commit model:

> A message is **not committed** until it has been replicated to a **majority** of nodes.

With 3 nodes:

```
Majority = 2
```

Let’s walk the same scenario under Raft.

---

# 5. Raft Scenario Step-by-Step

## Step 1: Leader receives message 96–100

Leader appends entries (uncommitted).

## Step 2: Leader sends AppendEntries RPC to followers

Followers store messages persistently.

### In Raft:

A write is considered “committed” only if:

```
Leader + at least 1 follower store the entry.
```

---

## Step 3: Majority acknowledges message 100

Assume replication looks like:

| Message | Leader | F1  | F2  | Majority replicated? |
| ------- | ------ | --- | --- | -------------------- |
| 96      | Yes    | Yes | No  | Yes                  |
| 97      | Yes    | Yes | No  | Yes                  |
| 98      | Yes    | Yes | Yes | Yes                  |
| 99      | Yes    | Yes | Yes | Yes                  |
| 100     | Yes    | Yes | No  | Yes                  |

Majority = Leader + F1

**Message 100 becomes COMMITTED.**

---

## Step 4: Leader crashes

What happens?

Followers hold an election.

---

## Step 5: Only a node with the COMMITTED entry can win leadership

Raft enforces the **log matching property**:

> A follower cannot become leader unless it has the most up-to-date committed log.

In this case:

* F1 has entries 1..100 → eligible to become leader
* F2 has up to 99 → **not allowed**
* Any node missing committed entries cannot win

**F1 becomes leader.**

---

## Step 6: New leader’s log is the longest valid log

New leader log:

```
1..100
```

F2 truncates and syncs to:

```
1..100
```

---

# Final Outcome in Raft

### NOTHING IS LOST:

```
96, 97, 98, 99, 100
```

They were majority-committed before failure.

---

# 6. Why This Matters in Practice

In Kafka default configuration:

* Data loss happens whenever leader acknowledges a write before followers replicate it
* Followers can be behind
* New leader discards unreplicated messages
* Application thinks the messages were written—but they disappear

In Raft:

* Leader cannot acknowledge before replication
* Every committed write survives leader failure
* System is always consistent
* No truncation of committed data
* No split-brain
* No “stale” leader

This is why Redpanda, CockroachDB, TiKV, and Etcd all use **Raft**.

---

# 7. Summary Table

| Step                        | Kafka default                 | Raft (Redpanda)                    |
| --------------------------- | ----------------------------- | ---------------------------------- |
| How is a write committed?   | Leader local write            | Majority replication               |
| Acknowledgement to producer | Immediate                     | After majority                     |
| If leader dies              | New leader may have stale log | Only fully caught-up node can lead |
| Message loss possible?      | Yes                           | No                                 |
| Log truncation likely?      | Yes                           | Rare & safe                        |
| Consistency                 | Eventual                      | Strong                             |

