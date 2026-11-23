# Design and Trade-offs

## Why local inference

The data is HR records.
Sending employee records and internal policy queries to a hosted cloud API introduces privacy and compliance risks for enterprise teams.
Running the model in-house keeps all data on the machine.
The operational cost is bounded model quality and reliance on local hardware.

## Why RAG instead of fine-tuning

Policies change frequently.
Re-training or fine-tuning weights for every policy amendment is slow and resource-intensive.
Storing policies in ChromaDB with semantic section chunking means an update is a single Markdown edit and re-index.

## Why structured tool calling instead of free-form SQL

The model never generates raw SQL.
It selects typed functions with strict JSON schemas.
This prevents prompt-injection attacks and hallucinated table queries.
The trade-off is that every new operational capability requires an explicit tool definition and handler.

## Trade-offs accepted

- Multi-turn context: Persistent session store in SQLite (`sessions` table) keyed by employee ID with a 20-message sliding window to prevent context window exhaustion.
- Caller identity verification: Strict `X-Employee-ID` header validation that rejects mismatched body requests with a `403 Forbidden` response.
- SQLite: Suitable for local dev and demo workloads. Move to PostgreSQL with connection pooling under concurrent multi-user load.
- Local model evaluation: Measured through a deterministic 14-scenario evaluation harness (`eval/cases.py`).

## What I would do next

- Hybrid search combining BM25 keyword matching with vector embeddings, paired with a cross-encoder reranker.
- Manager approval state machines for leave deductions rather than immediate commits.
- Cryptographically signed JWT validation at an API gateway.
