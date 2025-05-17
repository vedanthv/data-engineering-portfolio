# Realtime Cricket Analytics With Redpanda and ClickHouse

This project ingests real-time cricket data from the SportMonks API, streams it via Redpanda (Kafka-compatible), and stores it in ClickHouse for analytics.

## Features
- Redpanda for Kafka-compatible streaming
- Redpanda Console UI (localhost:8080)
- ClickHouse ingestion via Kafka engine
- Dockerized deployment
- Supports multiple API endpoints and Kafka topics
- Uses `ReplacingMergeTree` engine with `updated_at` for deterministic deduplication
- ClickHouse UI via Tabix (localhost:8124)

## How to Run
1. Replace `YOUR_API_KEY` in the `.env` file
2. Run the pipeline:
   ```bash
   docker-compose up --build -d
   ```
3. Access Redpanda Console UI:
   [http://localhost:8080](http://localhost:8080)
4. Access ClickHouse UI:
   [http://localhost:8124](http://localhost:8124)
5. Query ClickHouse:
   ```sql
   SELECT * FROM cricket_standings ORDER BY position ASC LIMIT 10;
   SELECT * FROM cricket_seasons ORDER BY starting_at DESC LIMIT 10;
   ```

## Extending
- Add more endpoints and map data in the producer.
- Update ClickHouse schema and Kafka topics accordingly.
- `ReplacingMergeTree(updated_at)` ensures the newest version of rows replaces older duplicates deterministically.