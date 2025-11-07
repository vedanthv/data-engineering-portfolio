# Setup Instructions

## Docker

All commands are in ```docker.sh```

Here is a detailed guide:

---

### Script

```sh
#!/bin/sh
```

This specifies that the script should be executed using the `sh` shell.

```sh
set -e
```

This instructs the script to stop execution immediately if any command returns a non-zero exit status. This prevents partial or corrupted installations.

---

### Operating System Detection

```sh
if [ -f /etc/os-release ]; then
    . /etc/os-release
else
    echo "Cannot detect OS. Exiting."
    exit 1
fi
```

* `/etc/os-release` contains OS identity information in key-value format.
* The script checks if the file exists.
* If it exists, it is sourced using `. /etc/os-release`, which loads variables like `ID` and `VERSION_CODENAME`.
* If it does not exist, the script exits because it cannot determine the correct Docker repository.

```sh
echo "Detected OS: $ID $VERSION_CODENAME"
```

Prints the detected OS and version for validation.

---

### Package System Update

```sh
sudo apt-get update -y
```

Updates the list of available packages. The `-y` flag automatically answers "yes" to prompts.

---

### Removal of Old Docker Versions

```sh
sudo apt-get remove -y docker docker-engine docker.io containerd runc || true
```

* Removes older Docker components if they exist.
* `|| true` ensures the script continues even if none of these packages are installed.

---

### Dependencies Installation

```sh
sudo apt-get install -y \
    ca-certificates \
    curl \
    gnupg \
    lsb-release
```

Installs packages required for accessing secure repositories and handling keys.

* `ca-certificates`: enables HTTPS communication.
* `curl`: used to download Docker GPG key.
* `gnupg`: processes GPG keys.
* `lsb-release`: helps in identifying the distribution codename.

---

### Create Keyring Directory

```sh
sudo mkdir -p /etc/apt/keyrings
```

Creates the directory where trusted keys are stored.
The `-p` flag prevents errors if the directory already exists.

---

### Docker GPG Key

```sh
curl -fsSL https://download.docker.com/linux/$ID/gpg | \
    sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
```

* Downloads Docker’s official GPG key.
* `-f` fails silently on server errors.
* `-s` makes curl silent.
* `-S` shows errors.
* `-L` follows redirects.
* Pipe sends output to `gpg --dearmor` which converts the ASCII-armored key to binary format and stores it under `/etc/apt/keyrings/docker.gpg`.

---

### Set Permissions on Key

```sh
sudo chmod a+r /etc/apt/keyrings/docker.gpg
```

Ensures the key file is readable by the package manager.

---

### Add Docker Repository

```sh
echo \
  "deb [arch=$(dpkg --print-architecture) \
  signed-by=/etc/apt/keyrings/docker.gpg] \
  https://download.docker.com/linux/$ID \
  $VERSION_CODENAME stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
```

Explanation:

* Constructs a Debian repository entry using:

  * System architecture.
  * Docker GPG key to verify packages.
  * Distribution ID (`ubuntu` or `debian`).
  * Codename (e.g. `jammy`, `bullseye`).
  * The `stable` Docker channel.
* Writes it into `/etc/apt/sources.list.d/docker.list`.
* `> /dev/null` suppresses tee’s output.

---

### Update Package Index Again

```sh
sudo apt-get update -y
```

Loads metadata from the newly added Docker repository.

---

### Install Docker Engine Packages

```sh
sudo apt-get install -y \
  docker-ce \
  docker-ce-cli \
  containerd.io \
  docker-buildx-plugin \
  docker-compose-plugin
```

Packages:

* `docker-ce`: Docker Community Edition engine.
* `docker-ce-cli`: Command-line tools.
* `containerd.io`: Container runtime required by Docker.
* `docker-buildx-plugin`: Advanced build tool.
* `docker-compose-plugin`: Enables the `docker compose` command.

---

### Start and Enable Docker

```sh
sudo systemctl enable docker
sudo systemctl start docker
```

* Enables Docker to automatically start on boot.
* Starts the Docker daemon immediately.

---

### Add Current User to Docker Group

```sh
sudo usermod -aG docker "$USER"
```

* Adds the logged-in user to the `docker` group.
* Enables running Docker without using `sudo`.

---

### Completion Message

```sh
echo "Docker installation completed."
echo "Logout and login again for group changes to take effect."
```

Confirms installation and reminds the user to re-login so group membership is applied.

---

### How to Run the Script

1. Create the file:

```
nano install_docker.sh
```

2. Paste the script.

3. Make it executable:

```
chmod +x install_docker.sh
```

4. Run it:

```
./install_docker.sh
```

5. Re-login or reboot to activate group changes:

```
reboot
```

## Main Containers

### Redpanda

---

#### Breakdown of the `redpanda` service

```yaml
redpanda:
  image: redpandadata/redpanda:v24.2.10
```

**image**

* Pulls the official Redpanda container image from Docker Hub.
* Version pinned to `v24.2.10` to ensure consistent behavior and avoid breaking changes.

Redpanda is a Kafka-API compatible streaming engine that replaces Kafka but is simpler, faster, and single-binary.

---

```yaml
  command:
    - redpanda start
```

**command**
Runs Redpanda in server mode using the built-in `redpanda` binary.

`redpanda start` launches the broker and enables all core subsystems: storage engine, Raft group, RPC endpoints, and Kafka API.

---

```yaml
    - --overprovisioned
```

**--overprovisioned**
Tells Redpanda to run in lightweight mode for containers/VMs.

* Disables heavy tuning intended for bare-metal.
* Intended for development or single-node setups.
  Mandatory for Docker Compose and EC2 non-dedicated nodes.

---

```yaml
    - --smp=1
```

**--smp=1**

* Sets number of CPU threads to 1.
* Seastar (Redpanda’s engine) normally runs one thread per CPU core.
* For a single-node EC2 dev machine, `1` reduces resource usage and avoids heavy I/O scheduling.

If your EC2 instance has more cores, you can raise this (e.g., `--smp=2`).

---

```yaml
    - --memory=1G
```

**--memory=1G**

* Limits Redpanda's internal memory allocator to 1GB.
* Ensures it won’t aggressively consume EC2 RAM.

Without this, it may reserve too much memory due to Seastar’s heuristics.

---

```yaml
    - --reserve-memory=0M
```

**--reserve-memory=0M**

* Prevents Redpanda from keeping extra memory untouched for itself.
* Defaults to several hundred MB if not set.
* Setting it to 0 makes it more container-friendly.

---

```yaml
    - --node-id=0
```

**--node-id=0**
Unique cluster node identifier.

Since this is a **single-node** docker-compose setup:

* `0` is fine.
* For multi-node clusters, each container would need a unique `node-id`.

---

```yaml
    - --check=false
```

**--check=false**
Disables "unsafe" configuration verification.
This is useful when running Redpanda inside Docker where CPU/memory discovery may not match native hardware.

---

```yaml
    - --kafka-addr=PLAINTEXT://0.0.0.0:9092
```

**--kafka-addr**
Defines the internal Kafka API listener.

* `PLAINTEXT` = no TLS
* `0.0.0.0` = listen on all interfaces inside the container
* `9092` = Kafka API port

This is what Kafka producers/consumers (Flink, generator, etc.) use.

---

```yaml
    - --advertise-kafka-addr=PLAINTEXT://redpanda:9092
```

**--advertise-kafka-addr**
This is the hostname advertised to clients.

* Must match the **service name** in docker-compose (`redpanda`)
* Ensures internal services can connect via Docker network DNS

You should **not** advertise the EC2 public IP, because internal services (Flink, generator) connect via Docker overlay network.

---

```yaml
    - --pandaproxy-addr=0.0.0.0:8082
```

**--pandaproxy-addr**
Pandaproxy is Redpanda’s REST-based Kafka proxy.

* Provides HTTP access to Kafka topics
* Useful for debugging and tools
* Binds to port 8082 inside the container

---

```yaml
    - --advertise-pandaproxy-addr=redpanda:8082
```

**--advertise-pandaproxy-addr**
Advertises proxy hostname for internal use.

---

#### Ports Section

```yaml
  ports:
    - "9092:9092"
    - "9644:9644"
    - "8082:8082"
```

Each port maps container → host:

| Port     | Purpose                                       |
| -------- | --------------------------------------------- |
| **9092** | Kafka API (used internally by other services) |
| **9644** | Redpanda Admin API & metrics endpoint         |
| **8082** | Pandaproxy REST API                           |

Security recommendation:
Keep 9092 closed to the internet (internal only).
9644 also should not be exposed publicly.

---

#### Volumes

```yaml
  volumes:
    - rpdata:/var/lib/redpanda
```

* Mounts persistent storage at `/var/lib/redpanda`.
* Ensures logs, metadata, segments, and topics survive container restarts or EC2 reboots.

`rpdata` is defined as a named Docker volume.

---

#### ulimits

```yaml
  ulimits:
    nofile:
      soft: 65536
      hard: 65536
```

Redpanda requires high file descriptor limits because each topic partition is backed by file segments.

Minimum recommended: **65536**.

If limits are too low, Redpanda logs will show warnings and throughput drops.

---

#### restart policy

```yaml
  restart: unless-stopped
```

Container restarts on:

* Crash
* Docker daemon restart
* EC2 reboot

But **does not** restart if explicitly stopped with `docker stop`.

This is preferred for most production-like dev setups.

---

#### healthcheck

```yaml
  healthcheck:
    test: ["CMD", "bash", "-c", "rpk cluster info --brokers=localhost:9092 || exit 1"]
    interval: 15s
    timeout: 5s
    retries: 10
```

**Purpose:**
Ensures Redpanda is healthy before dependent services (Flink, generator) start sending traffic.

**Explanation:**

* The test runs `rpk cluster info` inside the container.
* `--brokers=localhost:9092` checks the Kafka API.
* If the command fails, the container is considered **unhealthy**.
* Docker will retry:

| Parameter     | Meaning                                         |
| ------------- | ----------------------------------------------- |
| interval: 15s | run the test every 15 seconds                   |
| timeout: 5s   | fail if the command takes longer than 5 seconds |
| retries: 10   | after 10 failed attempts mark as unhealthy      |

This protects your Flink jobs from failing on startup because Kafka isn’t ready yet.