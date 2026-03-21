# To Do List

## AWS

- [x] Multi threaded producer code setup for all services
- [x] Orders - Eventbridge -> Lamda
- [ ] Payments - Eventbridge -> Lamda
- [x] User Activity - Eventbridge -> Firehose -> S3 (Parquet setup with glue for schema)
- [ ] Shipment - Eventbridge -> Lamda
- [ ] Tickets - Eventbridge -> Lamda

## Databricks

- [x] Orders Autoloader Pipeline Setup
- [x] User Activity Autoloader Pipeline Setup
- [x] RAG Agent Design PoC
- [x] Orders vector embeddings + vector search index setup

## Frontend / Backend / UX

- [x] NextJS -> Databricks SQL Warehouse Connection PoC
- [x] Initial frontend setup for orders data
- [x] Backend route for chat -> OpenAI embeddings + databricks hybrid search

## Misc

- [ ] Architecture Diagram
- [ ] Mermaid Process Flows