# HYMIND Workflow Documentation

## n8n + FastAPI Integration (Phase 5)

This document describes the HTTP API wrapper added in Phase 5 that allows
n8n to trigger the HYMIND Python agent via HTTP and receive the generated
Markdown report content in the response.

---

## Architecture

```
n8n Schedule Trigger
  ↓
HTTP Request node  →  POST /run-hymind  →  FastAPI server (local)
                                               ↓
                                         run_hymind_agent()
                                               ↓
                                         run_research(topic)       ← LangGraph pipeline
                                               ↓
                                         generate_report(state)    ← OpenAI synthesis
                                               ↓
                                         Read Markdown file
                                               ↓
                   ←  JSON response with report_content  ←
  ↓
Gmail node  →  report_content sent as email body
```

---

## Files Added

| File | Purpose |
|---|---|
| `src/hymind/api/server.py` | FastAPI server with `/run-hymind` and `/health` endpoints |
| `src/hymind/api/__init__.py` | Package marker |
| `scripts/run_api.py` | Convenience start script |

---

## Starting the Server

```powershell
# Install dependencies (one-time)
C:\Users\nest\.conda\envs\hymind\python.exe -m pip install fastapi "uvicorn[standard]"

# Start server
uvicorn src.hymind.api.server:app --host 0.0.0.0 --port 8000 --reload

# Or via script
C:\Users\nest\.conda\envs\hymind\python.exe scripts/run_api.py
```

Interactive API docs: `http://localhost:8000/docs`

---

## Endpoint Reference

### GET /health

Liveness check. Returns immediately with `{"status": "ok"}`.

### POST /run-hymind

Triggers a full research + report run.

**Request headers:**

| Header | Required | Description |
|---|---|---|
| `Content-Type` | Yes | `application/json` |
| `x-api-key` | Conditional | Required if `HYMIND_API_KEY` env var is set |

**Request body:**

```json
{
  "topic": "weekly hydrogen and fuel cell market intelligence",
  "report_type": "weekly_executive",
  "run_mode": "scheduled"
}
```

| Field | Type | Default | Description |
|---|---|---|---|
| `topic` | string | required | Research topic passed to all collection nodes |
| `report_type` | string | `"weekly_executive"` | Report type label (informational only) |
| `run_mode` | string | `"manual"` | Trigger context: `manual` or `scheduled` |

**Success response (HTTP 200):**

```json
{
  "status": "success",
  "report_title": "HYMIND Executive Intelligence Report",
  "report_content": "# Markdown report content...",
  "report_path": "outputs/reports/20260519_080500_hymind_report.md",
  "generated_at": "2026-05-19T08:05:00+00:00"
}
```

**Failure response (HTTP 200, status field = "failed"):**

```json
{
  "status": "failed",
  "error": "OPENAI_API_KEY is not set — report generation requires OpenAI.",
  "generated_at": "2026-05-19T08:05:00+00:00"
}
```

Note: failures return HTTP 200 with `status: failed` so n8n can read the error
message without triggering its own HTTP error handling. Use an IF node to check
`{{$json.status}} equals success`.

---

## ngrok Setup

n8n cloud cannot reach `localhost`. Use ngrok to expose the local port:

```powershell
# Download and install ngrok from https://ngrok.com/download
ngrok http 8000
```

ngrok prints a forwarding URL like:

```
Forwarding  https://abc123.ngrok-free.app -> http://localhost:8000
```

Use the `https://...ngrok-free.app` URL in the n8n HTTP Request node.

The ngrok free tier URL changes each time ngrok restarts. For a stable URL,
use a fixed ngrok domain (free on ngrok's free plan with an account).

---

## n8n Workflow Configuration

### HTTP Request node settings

| Field | Value |
|---|---|
| Method | POST |
| URL | `https://YOUR-NGROK-URL.ngrok-free.app/run-hymind` |
| Body Content Type | JSON |
| Body | See below |

Request body:

```json
{
  "topic": "weekly hydrogen and fuel cell market intelligence",
  "report_type": "weekly_executive",
  "run_mode": "scheduled"
}
```

### IF node — success check

Condition: `{{$json.status}}` equals `success`

- True branch → Gmail send node
- False branch → error alert or stop

### Gmail node — body expression

```
{{$json.report_content}}
```

The `report_content` field contains the full Markdown report. Gmail renders
plain text; for formatted HTML, add a Markdown-to-HTML conversion node.

---

## Authentication

Set `HYMIND_API_KEY` in `.env` to require authentication:

```env
HYMIND_API_KEY=your-secret-value
```

When set, all requests to `/run-hymind` must include:

```
x-api-key: your-secret-value
```

In n8n: use a **Header Auth** credential with name `x-api-key`.

Leave `HYMIND_API_KEY` empty for open local development access.

---

## Timing

A full HYMIND run typically takes 2–5 minutes depending on:
- Number of API sources configured
- Crawl success rate
- OpenAI response time

n8n's HTTP Request node default timeout is 300 seconds. Increase it in
**Settings → Workflow Settings → HTTP Request Timeout** if runs take longer.

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| `status: failed` — OPENAI_API_KEY not set | Missing env var | Add `OPENAI_API_KEY` to `.env` and restart server |
| n8n gets connection refused | ngrok not running | Start ngrok before triggering n8n |
| `401 Unauthorized` | Wrong or missing API key | Check `HYMIND_API_KEY` in `.env` and n8n Header Auth |
| n8n timeout | Run took >300s | Increase n8n HTTP timeout; check logs for slow nodes |
| Report has no sources | All API keys missing | Add at least `SERPER_API_KEY` or `NEWS_API_KEY` |
