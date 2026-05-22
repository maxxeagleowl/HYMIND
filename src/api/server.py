"""HYMIND FastAPI server — HTTP wrapper for the LangGraph research pipeline.

Exposes a single POST /run-hymind endpoint that n8n (or any HTTP client) can
call to trigger a full research + report run and receive the Markdown report
content in the JSON response.

Start locally:
    uvicorn src.api.server:app --host 0.0.0.0 --port 8000 --reload

Expose to n8n via ngrok:
    ngrok http 8000
"""

import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, Field

load_dotenv()

from utils.logger import get_logger
from workflows.research_workflow import run_research
from reporting.report_generator import generate_report

logger = get_logger("hymind.api")

# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

app = FastAPI(
    title="HYMIND API",
    description="HTTP wrapper for the HYMIND hydrogen market intelligence platform.",
    version="1.0.0",
)


# ---------------------------------------------------------------------------
# Request / response schemas
# ---------------------------------------------------------------------------

class HymindRequest(BaseModel):
    topic: str = Field(..., min_length=1, description="Research topic for the run")
    report_type: str = Field(default="weekly_executive", description="Report type label")
    run_mode: str = Field(default="manual", description="Trigger mode: manual or scheduled")


# ---------------------------------------------------------------------------
# Core agent wrapper
# ---------------------------------------------------------------------------

def run_hymind_agent(topic: str, report_type: str, run_mode: str) -> dict:
    """Run the full HYMIND pipeline and return a structured result dict.

    Calls run_research → generate_report, reads the saved Markdown file, and
    returns its content alongside path and metadata.  Raises on unrecoverable
    failures so the API endpoint can catch and format a clean error response.
    """
    logger.info(
        "run_hymind_agent | topic=%r | report_type=%r | run_mode=%r",
        topic, report_type, run_mode,
    )

    # Step 1: research workflow
    state = run_research(topic)
    errors = state.get("errors", [])
    if errors:
        logger.warning("run_hymind_agent: pipeline completed with %d errors", len(errors))

    # Step 2: report generation — may raise RuntimeError if OPENAI_API_KEY missing
    report_path, char_count = generate_report(state)

    # Step 3: read report content from disk
    content = report_path.read_text(encoding="utf-8")

    # Extract report title from first H1 line
    title = "Weekly Hydrogen and Fuel Cell Market Intelligence"
    for line in content.splitlines():
        stripped = line.strip()
        if stripped.startswith("# "):
            title = stripped[2:].strip()
            break

    logger.info(
        "run_hymind_agent complete | report=%s | chars=%d",
        report_path, char_count,
    )

    return {
        "status": "success",
        "report_title": title,
        "report_content": content,
        "report_path": str(report_path),
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }


# ---------------------------------------------------------------------------
# Optional API key check
# ---------------------------------------------------------------------------

def _check_api_key(x_api_key: Optional[str]) -> None:
    """Validate x-api-key header when HYMIND_API_KEY env var is set.

    If HYMIND_API_KEY is empty or unset, all requests are allowed (dev mode).
    """
    expected = os.getenv("HYMIND_API_KEY", "").strip()
    if not expected:
        return  # dev mode — no auth required
    if x_api_key != expected:
        raise HTTPException(status_code=401, detail="Invalid or missing x-api-key header")


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.get("/health")
def health() -> dict:
    """Lightweight liveness check — returns 200 immediately."""
    return {"status": "ok", "service": "hymind-api"}


@app.post("/run-hymind")
def run_hymind_endpoint(
    request: HymindRequest,
    x_api_key: Optional[str] = Header(default=None),
) -> dict:
    """Trigger a full HYMIND research and report run.

    n8n HTTP Request node should POST to this endpoint.  The response contains
    the full Markdown report content in the ``report_content`` field so n8n
    can pass it directly to a Gmail or Telegram node without accessing the
    local filesystem.

    The endpoint is defined as a plain ``def`` (not ``async def``) so FastAPI
    automatically runs it in a thread-pool executor, preventing the blocking
    LangGraph pipeline from stalling the event loop.
    """
    _check_api_key(x_api_key)

    logger.info(
        "/run-hymind called | topic=%r | report_type=%r | run_mode=%r",
        request.topic, request.report_type, request.run_mode,
    )

    try:
        result = run_hymind_agent(
            topic=request.topic,
            report_type=request.report_type,
            run_mode=request.run_mode,
        )
        return result

    except RuntimeError as exc:
        # Expected failure: missing API key, empty pipeline output, etc.
        logger.error("/run-hymind: RuntimeError | error=%s", exc)
        return {
            "status": "failed",
            "error": str(exc),
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }

    except Exception as exc:
        logger.error(
            "/run-hymind: unexpected error | error_type=%s | error=%s",
            type(exc).__name__, exc,
        )
        return {
            "status": "failed",
            "error": f"{type(exc).__name__}: {exc}",
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }
