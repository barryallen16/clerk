# Clerk

An offline HR assistant that answers policy questions with semantic retrieval and manages leave balances through procedural tool calling.
Runs locally against LM Studio with zero external cloud dependencies.

[![CI](https://github.com/barryallen16/clerk/actions/workflows/ci.yml/badge.svg)](https://github.com/barryallen16/clerk/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/python-3.11%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Local](https://img.shields.io/badge/inference-fully%20offline-orange)

| CLI Terminal Interface | Web Browser UI |
| :---: | :---: |
| ![CLI Interface](docs/demo.gif) | ![Web Interface](docs/ui-demo.gif) |

## Why Clerk Exists

Most internal HR bots are either brittle keyword searchers or ungrounded LLM wrappers that hallucinate policies and commit arbitrary database writes.
Clerk divides the workload into two distinct operational domains.
Unstructured company policies stay in a vector store queried via semantic section chunking.
Structured employee records and state changes run through deterministic SQL transactions protected by procedural Python guardrails.

## Architecture & Mechanism

```mermaid
flowchart TD
    User["User Query (CLI / Web UI)"] --> API["FastAPI (/query)"]
    API --> AuthGuard["Caller Identity Verification (X-Employee-ID)"]
    AuthGuard --> Orchestrator["Orchestrator Loop (agent/orchestrator.py)"]
    
    subgraph Guardrails ["Procedural Guardrails in Python"]
        IntentCheck["Multi-Turn Intent & Date Pattern Regex"]
        WindowCap["Sliding Context Cap (Max 20 Messages)"]
    end
    
    Orchestrator --> WindowCap
    WindowCap --> LLM["Local Inference (LM Studio on :1234/v1)"]
    
    LLM -- "vector_search_hr_policy" --> Chroma["ChromaDB (Hierarchical Markdown Chunks)"]
    Chroma --> LLM
    
    LLM -- "submit_leave_request" --> IntentCheck
    IntentCheck -- "Rejected" --> ErrorFeedback["Tool Error: Ask User for Missing Details"]
    ErrorFeedback --> LLM
    IntentCheck -- "Approved" --> SQLite["SQLite (Balance Verification & Transaction)"]
    SQLite --> LLM
    
    LLM --> Response["Final Synthesized Answer"]
```

## Quick Start

Install dependencies with `uv` in one block:

```bash
git clone https://github.com/barryallen16/clerk.git
cd clerk
uv venv && uv pip install -e ".[dev,serve]"
cp .env.example .env
```

Start LM Studio on `http://localhost:1234/v1` with any function-calling model (such as Llama-3-8B-Instruct or Mistral-7B).

### Interactive CLI

```bash
uv run python main.py
```

Run a one-shot query:

```bash
uv run python main.py "What is the notice period during probation?"
```

Run the demo query flow:

```bash
uv run python main.py --demo
```

### Web Interface

Start the API service:

```bash
uv run uvicorn api:app --reload
```

Open `ui/index.html` in your browser.
The interface communicates with the backend on `http://localhost:8000/query`.

## Verification & Evaluation

Run the automated test suite across all unit, vector, orchestrator, and API tests:

```bash
uv run pytest
```

Run the deterministic golden evaluation harness:

```bash
uv run python eval/run_eval.py
```

Results are saved to `eval/results.json`.

Current live benchmark results against local model inference (`lfm3-1.7b`):
- **Policy Retrieval Accuracy**: 10/10 (100%) across all handbook queries.
- **Overall Tool Selection**: 12/14 (85.7%).
- **Execution Traces**: On medical leave, the agent queries policy constraints before executing the booking. On requests exceeding annual allowances (100 days), it inspects policy ceilings before initiating database deductions.

| Category | Test Scenario | Dispatched Tool | Answer Grounding |
|---|---|---|---|
| Policy | Doctor certificate requirement (>2 days sick leave) | `vector_search_hr_policy` | Pass |
| Policy | Annual casual leave allowance (12 days) | `vector_search_hr_policy` | Pass |
| Policy | Remote work monthly allowance (4 days) | `vector_search_hr_policy` | Pass |
| Policy | Maternity leave duration (26 weeks) | `vector_search_hr_policy` | Pass |
| Policy | Paternity leave duration (15 days) | `vector_search_hr_policy` | Pass |
| Policy | Probation resignation notice (14 calendar days) | `vector_search_hr_policy` | Pass |
| Policy | Probation WFH restriction (on-site requirement) | `vector_search_hr_policy` | Pass |
| Policy | Sabbatical service threshold (3 continuous years) | `vector_search_hr_policy` | Pass |
| Policy | Home office equipment allowance ($500 stipend) | `vector_search_hr_policy` | Pass |
| Policy | Bereavement leave for immediate family (5 days) | `vector_search_hr_policy` | Pass |
| Action | Approved casual leave balance deduction | `submit_leave_request` | Pass |
| Action | Approved medical leave balance deduction | `vector_search_hr_policy` + `submit_leave_request` | Pass |
| Action | Leave request exceeding annual allowance (100 days) | `vector_search_hr_policy` (Policy ceiling lookup) | Refusal |
| Guardrail | Rejection on missing date arguments | None (Procedural block) | Pass |

## Works With / Doesn't Work With Yet

| Subsystem | Works With Today | Doesn't Work With Yet | Production Migration Path |
|---|---|---|---|
| **Relational Storage** | SQLite (`enterprise_hr.db`) for local workloads | High-concurrency simultaneous write traffic | Migrate to PostgreSQL with connection pooling |
| **Leave Application** | Direct balance deduction after checks | Multi-tier manager approval hierarchies | Implement a pending leave state machine with approval hooks |
| **Document Search** | Semantic chunking over Markdown handbooks (top-3 results) | Scanned multi-column PDF tables and images | Add PyMuPDF extraction, BM25 hybrid search, and cross-encoder reranking |
| **Caller Security** | Header-based identity verification (`X-Employee-ID`) | Direct LDAP or Active Directory synchronization | Validate cryptographically signed JWT claims at an API Gateway |
| **Context Memory** | Sliding window bounded to the latest 20 turns | Cross-month long-term episodic user memory | Offload expired turns to an external session archive store |

## License

MIT License.
Free for commercial and personal modification.
