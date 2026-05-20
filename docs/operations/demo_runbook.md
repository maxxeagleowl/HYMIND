# HYMIND Demo Runbook

## Overview

This runbook walks through a complete end-to-end demonstration of HYMIND in approximately 5–7 minutes. The demo covers:

1. Environment check
2. Running the core pipeline (research → report)
3. Reviewing the generated Markdown report
4. Starting the API server
5. Testing the HTTP endpoint manually
6. Explaining the n8n workflow

---

## Prerequisites

- Conda environment `hymind` activated (or equivalent)
- `.env` file populated with valid API keys:
  - `OPENAI_API_KEY` (required)
  - `SERPER_API_KEY` (required)
  - `NEWS_API_KEY` (recommended)
  - `PINECONE_API_KEY` (optional — enables historical context)
- Dependencies installed: `pip install -e .`

---

## Step 1 — Run the Core Pipeline (2–4 min)

```powershell
python -m main "weekly hydrogen and fuel cell market intelligence"
```

Expected output:

```
[HYMIND] Research topic: weekly hydrogen and fuel cell market intelligence

============================================================
  HYMIND — Full Pipeline Complete
============================================================
  Topic           : weekly hydrogen and fuel cell market intelligence
  Serper results  : 10
  News results    : 10
  RSS results     : 12
  Merged (unique) : 24
  Crawl success   : 4
  Report path     : outputs/reports/20260520_XXXXXX_hymind_report.md
  Report size     : ~8,000 characters
  Duration        : ~120s
============================================================
```

---

## Step 2 — Review the Generated Report

Open the output file in `outputs/reports/`. The report follows a structured executive format:

- Executive Summary
- Key Developments (source-backed bullets)
- Market Implications
- Technology Signals
- Policy and Funding Signals
- Competitive Notes
- Risks and Watchouts
- Source Traceability table
- Workflow Metadata table

Alternatively, open a sample report for immediate review (no API calls needed):

```powershell
# View a sample report
Get-Content outputs/sample_reports/20260519_120000_european_electrolyzer_market.md
```

---

## Step 3 — Run the Tests (30 seconds)

```powershell
# Full suite — no live API calls required
pytest tests/ -v --tb=short
```

Expected: **243 tests pass**.

---

## Step 4 — Start the API Server

```powershell
# Option A: uvicorn directly
uvicorn src.api.server:app --host 0.0.0.0 --port 8000 --reload

# Option B: convenience script
python scripts/run_api.py

# Option C: server + ngrok + configuration printout
python start_hymind_api.py
```

Verify liveness:

```powershell
curl http://localhost:8000/health
# Expected: {"status": "ok", "service": "hymind-api"}
```

Interactive API docs: [http://localhost:8000/docs](http://localhost:8000/docs)

---

## Step 5 — Trigger a Run via HTTP

```powershell
curl -X POST "http://localhost:8000/run-hymind" `
  -H "Content-Type: application/json" `
  -d "{\"topic\":\"hydrogen electrolyzer market 2026\",\"report_type\":\"weekly_executive\",\"run_mode\":\"manual\"}"
```

Expected response:

```json
{
  "status": "success",
  "report_title": "HYMIND Executive Intelligence Report",
  "report_content": "# HYMIND Executive Intelligence Report\n...",
  "report_path": "outputs/reports/20260520_XXXXXX_hymind_report.md",
  "generated_at": "2026-05-20T10:00:00+00:00"
}
```

---

## Step 6 — Explain the n8n Distribution Layer

Show the n8n workflow file at `n8n/HYMIND.json` and describe the flow:

1. **Schedule Trigger** — runs every Monday at 08:00
2. **HTTP Request** — calls `POST /run-hymind` via ngrok tunnel
3. **IF node** — routes on `status == success`
4. **Markdown node** — converts report Markdown to HTML
5. **Gmail node** — sends the HTML report to the recipient
6. **Google Sheets node** — logs the delivery (timestamp, title, status)
7. **Error Gmail node** — sends alert if the pipeline fails

See `docs/operations/n8n_workflow.md` for setup instructions.

---

## Key Points to Emphasize

### Architecture decisions
- **LangGraph** for stateful multi-step orchestration with graceful failure isolation per node
- **Pinecone RAG** for persistent memory and historical trend comparison across runs
- **FastAPI** wrapper keeps the distribution layer separate from the core intelligence pipeline
- **n8n** handles scheduling and delivery without coupling into the Python codebase

### Reliability
- All 9 workflow nodes have `=== Node START/END ===` log markers
- Missing API keys become warnings (not crashes) — pipeline completes with partial results
- Tenacity retry handles transient API failures (HTTP 429, 5xx, timeouts)
- 243 tests cover all collectors, workflow nodes, RAG layer, output validator, and failure scenarios

### Output quality
- Reports are executive-readable: structured sections, source-backed facts, strategic interpretation
- Source Traceability table links every claim back to a URL
- RAG historical context allows trend comparison across weeks

---

## Troubleshooting During Demo

| Problem | Fix |
|---|---|
| `OPENAI_API_KEY not set` | Add key to `.env` and restart |
| Pipeline produces 0 results | Check `SERPER_API_KEY` — it's the most reliable source |
| API server fails to start | Ensure `fastapi` and `uvicorn` are installed: `pip install fastapi "uvicorn[standard]"` |
| Tests fail with import error | Run `pip install -e .` from the project root |
| ngrok URL changed | Run `ngrok http 8000` again and update the n8n HTTP Request node URL |
