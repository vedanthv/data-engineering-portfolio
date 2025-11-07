## How does Docker Networking work? How do clients resolve service names?

# 1. kafka-addr vs advertise-kafka-addr
## kafka-addr

This defines **where the Redpanda broker listens inside the container or host**.

Example:

```
--kafka-addr=PLAINTEXT://0.0.0.0:9092
```

Meaning:
Redpanda binds to port 9092 on all internal network interfaces.
This is the actual socket the broker opens.

Key point:
kafka-addr must always refer to a valid local interface on that machine or container.

---

## advertise-kafka-addr

This defines **what Redpanda tells clients to connect to**.
This is the address placed into metadata responses returned to producers and consumers.

Example:

```
--advertise-kafka-addr=PLAINTEXT://redpanda:9092
```

Meaning:
When a Kafka client requests metadata, the broker responds by saying:
“Connect to redpanda:9092 for this partition.”

Clients then always use the advertised address, not the listening address.

This is necessary because the broker’s internal IP might differ from what other services must use to contact it.

---

# 2. Why They Differ in Docker Compose

In Docker:

* Each container has its own network namespace.
* Localhost refers to itself, not other containers.
* Containers communicate through an internal virtual network.
* Docker Compose automatically creates DNS names for each service.

Therefore:

* kafka-addr must listen on 0.0.0.0 inside the Redpanda container.
* advertise-kafka-addr must be the service name so that other containers can reach it.

---

# 3. How Clients Resolve the Service Name

**“If we use `redpanda` as the advertised address, how does the client resolve it?”**

Answer:

When using Docker Compose, Docker automatically creates an internal network and a DNS server for that network. All services declared in `docker-compose.yml` are assigned DNS names matching the service name.

For example:

```
services:
  redpanda:
    ...
  flink-jobmanager:
    ...
  generator:
    ...
```

Docker will automatically provide DNS entries:

```
redpanda
flink-jobmanager
generator
```

Inside any container in the same Compose network, you can:

* ping redpanda
* curl redpanda:8082
* connect to redpanda:9092

Redpanda’s advertised address is therefore resolvable because Docker automatically maintains a DNS mapping.

This DNS mapping points:

```
redpanda  →  <internal container IP> (for example 172.18.0.2)
```

Kafka clients inside Docker use this address to reach the broker.

This is why using `redpanda:9092` as the advertised Kafka address is the correct approach in Compose.

---

# 4. Why Localhost Will Not Work

A common mistake:

```
--advertise-kafka-addr=PLAINTEXT://localhost:9092
```

This fails because:

* Kafka clients inside Flink or the generator container see localhost as their own container.
* They attempt to connect to themselves, not the broker.
* All connections fail.

Thus you must advertise the service name.

---

# 5. Summary Table

| Setting              | Purpose                           | Should Point To                                     |
| -------------------- | --------------------------------- | --------------------------------------------------- |
| kafka-addr           | Where Redpanda listens internally | Local container IP or 0.0.0.0                       |
| advertise-kafka-addr | Address sent to clients           | Service name (Docker), Pod DNS (K8s), or public URL |

---

# 6. In Simple Form

* kafka-addr = “bind here”
* advertise-kafka-addr = “tell others to reach me here”
* Docker Compose resolves service names using its internal DNS server.

This allows:

```
advertise-kafka-addr = redpanda:9092
```

to work reliably for all other services.

