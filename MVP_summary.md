# MVP Summary

## HYMIND
### Hydrogen Market Intelligence & Data

---

# Overview

HYMIND is an autonomous AI-powered research and reporting system focused on the hydrogen and fuel cell industry.

The MVP demonstrates a complete end-to-end autonomous workflow that:

1. Collects intelligence from multiple external sources (Serper, NewsAPI, RSS feeds, web crawling)
2. Normalizes, validates, and deduplicates all collected data
3. Stores and retrieves historical findings via Pinecone vector database (RAG)
4. Synthesizes executive reports using OpenAI GPT-4o-mini
5. Delivers reports automatically via a FastAPI HTTP wrapper and n8n workflow with Gmail delivery

The project was designed to satisfy the autonomous agent requirements of Project 3, including:

- Multi-source research
- Autonomous workflow execution (LangGraph)
- Structured report generation
- Error handling, validation, and reliability hardening
- Real API tool usage
- Distribution automation (n8n, Gmail)

---

# What Was Built — Phase Summary

## Phase 1 — Core Pipeline

| Component | File | Description |
|---|---|---|
| OpenAI client | `src/tools/openai_client.py` | Synthesis with tenacity retry |
| Serper search | `src/tools/serper_search.py` | Google-based web research |
| NewsAPI | `src/tools/news_api.py` | Structured news retrieval |
| RSS ingestion | `src/tools/rss_reader.py` | Hydrogen industry feeds |
| Web crawler | `src/tools/web_crawler.py` | Article content extraction |
| LangGraph workflow | `src/workflows/research_workflow.py` | 9-node state machine |
| Report generator | `src/reporting/report_generator.py` | Markdown executive reports |
| Logger | `src/utils/logger.py` | Rich console + file logging |
| Entry point | `src/main.py` | CLI runner |

## Phase 2 — Collector Abstraction

- `CollectorProtocol` (structural typing.Protocol) in `src/tools/collector.py`
- Input validation layer: `validate_result()`, `validate_results()`
- HTML stripping in NewsAPI normalization
- 60-test NewsAPI test suite

## Phase 3 — Pinecone RAG

- `src/rag/` — embeddings, pinecone_store, retriever, schemas
- Two new LangGraph nodes: `store_findings_in_pinecone`, `retrieve_context_from_pinecone`
- Historical context injected into report synthesis as `=== HISTORICAL CONTEXT ===`
- Graceful degradation — pipeline continues if Pinecone is not configured
- 46 new RAG tests

## Phase 4 — Reliability Hardening

- `src/reporting/validator.py` — `validate_findings()`, `check_state_quality()`
- `=== Node START/END ===` logging markers on all 9 workflow nodes
- 73 failure-scenario tests (timeouts, malformed feeds, degraded pipeline, node isolation)
- 34 validator unit tests
- 243 total tests — all pass
- 3 sample reports in `outputs/sample_reports/`

## Phase 5 — Distribution Automation

- `src/api/server.py` — FastAPI with `POST /run-hymind` and `GET /health`
- `scripts/run_api.py` — uvicorn convenience script
- `start_hymind_api.py` — starts FastAPI + ngrok + prints n8n config
- `n8n/HYMIND.json` — full n8n workflow (Schedule → HTTP → Markdown→HTML → Gmail → Sheets)
- `n8n/Global Error Handler.json` — n8n error handler
- Delivery logging via Google Sheets
- PDF descoped: Markdown→HTML conversion handles email delivery

---

# LangGraph Workflow

The 9-node pipeline executes in sequence:

```text
initialize_state
  ↓
collect_serper        ← Serper API (organic + news results)
  ↓
collect_news          ← NewsAPI (structured news)
  ↓
collect_rss           ← RSS/Atom feeds (hydrogen industry)
  ↓
merge_and_deduplicate ← normalised URL deduplication
  ↓
crawl_selected        ← top 5 non-PDF URLs crawled
  ↓
store_findings_in_pinecone    ← embed + upsert to Pinecone (optional)
  ↓
retrieve_context_from_pinecone ← top-5 historical findings (optional)
  ↓
finalize_state        ← counts, duration, error summary
  ↓
generate_report       ← OpenAI synthesis + Markdown output
```

Each collection node (Serper, NewsAPI, RSS) fails gracefully: missing keys or network errors append to `state["errors"]` and the pipeline continues with partial results.

---

# Normalized Result Schema

All collection tools share a single schema:

```python
{
    "title": str,
    "url": str,
    "snippet": str,
    "published_at": str | None,
    "source": str,
    "source_type": str,   # "organic", "news", or "rss"
    "search_query": str,
    "author": str | None,
    "rank": int
}
```

---

# Reliability Features

| Feature | Implementation |
|---|---|
| Per-node graceful failure | Each node catches all exceptions, appends to errors, continues |
| API key pre-checking | Missing keys → warning, not sys.exit |
| Tenacity retry | All HTTP calls: Timeout, ConnectionError, 429, 5xx |
| Output validation | validate_findings() removes missing-URL and duplicate entries |
| URL deduplication | Normalised lowercase + trailing-slash-stripped URL comparison |
| PDF filtering | PDF URLs excluded from crawl queue automatically |
| Boilerplate removal | Crawler strips nav/footer/header/script/style/aside/iframe |
| Node-level logging | START/END markers + counts on every node |
| No secrets in logs | Keys sent via headers only, never logged |

---

# Test Coverage

| Test File | Tests | Coverage |
|---|---|---|
| test_schemas.py | 15 | Schema normalization and field validation |
| test_deduplication.py | 12 | URL normalization and merge deduplication |
| test_web_crawler.py | 20 | Crawler extraction, error handling, PDF filtering |
| test_missing_api_keys.py | 8 | Missing key behavior across all collectors |
| test_news_api_collector.py | 60 | NewsAPI full coverage including all failure modes |
| test_rag.py | 46 | RAG embeddings, store, retriever, graceful degradation |
| test_report_generator.py | ~15 | Report generation, RAG context injection |
| test_reliability.py | 73 | All failure scenarios: timeouts, malformed feeds, degraded pipeline |
| test_validator.py | 34 | validate_findings and check_state_quality |
| **Total** | **243** | All pass — no live API calls required |

---

# Report Structure

Each generated report contains:

1. Research Topic
2. Executive Summary (150–250 words)
3. Key Developments (source-backed bullets)
4. Market Implications
5. Technology Signals
6. Policy and Funding Signals
7. Competitive Notes
8. Risks and Watchouts
9. Source Traceability (all URLs with source type labels)
10. Workflow Metadata (pipeline statistics table)

Sample reports: `outputs/sample_reports/`

---

# Distribution Layer (Phase 5)

```text
FastAPI POST /run-hymind
  ↓
n8n Schedule Trigger (Monday 08:00)
  ↓
HTTP Request → ngrok → FastAPI server
  ↓
IF status == success
  ↓
Markdown → HTML (n8n built-in)
  ↓
Gmail send (HTML report)
  ↓
Google Sheets log (timestamp, title, status, channel)
```

---

# Technical Stack

| Component | Technology |
|---|---|
| Language | Python 3.11+ |
| Agent Framework | LangGraph |
| LLM | OpenAI GPT-4o-mini |
| Search API | Serper API |
| News Aggregation | NewsAPI |
| RSS Processing | feedparser + requests |
| Crawling | requests + BeautifulSoup + lxml |
| Vector Database | Pinecone (text-embedding-3-small) |
| Retry Logic | tenacity |
| Logging | Python logging + Rich |
| HTTP API | FastAPI + uvicorn |
| Distribution | n8n |
| Testing | pytest (243 tests) |
| Output Format | Markdown (HTML delivery via n8n) |

---

# Architecture Decisions

## Why LangGraph

LangGraph provides stateful multi-step orchestration with explicit node boundaries. Each node is isolated — one failure does not cascade. State accumulates across nodes. The graph is deterministic, testable, and extensible.

## Why Pinecone

The system needs persistent memory to track hydrogen market trends across weeks. Pinecone provides managed vector search, metadata filtering, and graceful degradation — the pipeline works without it configured.

## Why FastAPI + n8n

The distribution layer is intentionally decoupled from the core intelligence pipeline. FastAPI exposes a clean HTTP interface. n8n handles scheduling, delivery, and logging without coupling into the Python codebase.

## Why no PDF

PDF generation adds a rendering dependency (headless Chrome or weasyprint). n8n's built-in Markdown node produces HTML directly — sufficient for email delivery without an extra tool.

---

# Repository

https://github.com/maxxeagleowl/HYMIND

---

# Current State

**Phase 1–5 complete. Phase 6 (documentation and submission) in progress.**

- 243 tests pass
- 3 sample reports generated
- Full n8n workflow exported and documented
- All architecture docs updated to match current `src/` layout
- Demo runbook at `docs/operations/demo_runbook.md`
