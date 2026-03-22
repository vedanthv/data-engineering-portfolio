# To Do List

## AWS

- [x] Multi threaded producer code setup for all services
- [x] Orders - Eventbridge -> Lamda
- [ ] Payments - Eventbridge -> Lamda
- [x] User Activity - Eventbridge -> Firehose -> S3 (Parquet setup with glue for schema)
- [ ] Shipment - Eventbridge -> Lamda
- [ ] Tickets - Eventbridge -> Lamda

## Databricks / AI Enhancements

- [x] Orders Autoloader Pipeline Setup
- [x] User Activity Autoloader Pipeline Setup
- [x] RAG Agent Design PoC
- [x] Orders vector embeddings + vector search index setup
- [x] User Activity / Analytics vector embeddings + vector search index setup
- [ ] Langsmith monitoring setup
- [ ] Guardrails in prompts

## Frontend / Backend / UX

- [x] NextJS -> Databricks SQL Warehouse Connection PoC
- [x] Initial frontend setup for orders data
- [x] Backend route for chat -> OpenAI embeddings + databricks hybrid search
- [x] UI Enhancements
    - [x] Add separate components for chat, message and sidebar
    - [x] Enhance Backend api to route between SQL and RAG using LLM as judge
    - [x] Generate chat history title route setup
    - [x] Normalization and scoring responses feat in vector search route
- [ ] Feedback on response feature
- [ ] Setup database for chat history
- [ ] Deploy on Vercel

## Misc

- [ ] Architecture Diagram
- [ ] Mermaid Process Flows