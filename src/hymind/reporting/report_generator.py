"""Executive Markdown report generator for HYMIND.

Accepts a completed AgentState from the research workflow, builds a compact
research context, calls OpenAI to synthesize a structured intelligence report,
appends a programmatic metadata section, and saves the result to disk.
"""

import os
from datetime import datetime
from pathlib import Path

from hymind.tools.openai_client import complete
from hymind.utils.logger import get_logger
from hymind.workflows.state import AgentState

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

DEFAULT_OUTPUT_DIR: Path = Path("outputs/reports")

_MAX_CONTEXT_CHARS: int = 15_000
_MAX_CRAWLED_CONTENT_CHARS: int = 600
_MAX_SNIPPET_CHARS: int = 280
_MAX_MERGED_IN_CONTEXT: int = 25

# ---------------------------------------------------------------------------
# Prompts
# ---------------------------------------------------------------------------

_SYSTEM_PROMPT = """\
You are a senior hydrogen industry intelligence analyst producing structured executive intelligence reports.

Your role is to transform collected research into clear, strategic, executive-readable intelligence.

Rules you must follow:
- Only state facts that are supported by the research provided.
- Where source coverage is thin or unclear, explicitly note the uncertainty.
- Clearly separate confirmed findings from analytical interpretation.
- Do not invent statistics, quotes, company names, or claims not present in the research.
- Do not use filler phrases such as "in today's rapidly evolving landscape" or "it is important to note".
- Write in concise, professional executive language — not academic language.
- Lead each section with the most strategically relevant point.
- The Source Traceability section must list only sources that appear in the provided research context.\
"""

_USER_PROMPT_TEMPLATE = """\
Topic: {topic}
Report Date: {date}

--- RESEARCH CONTEXT ---
{context}
--- END RESEARCH CONTEXT ---

Generate a complete structured Markdown executive intelligence report using EXACTLY the section headers below.
Do not add or remove sections. Do not add commentary outside the sections.
Leave the "## Workflow Metadata" section body as a single line: [System-generated]

# HYMIND Executive Intelligence Report

## Research Topic
[One concise sentence describing the research scope and topic]

## Executive Summary
[150–250 words. Summarise the most important developments, their strategic significance, and what decision-makers should prioritise. Separate confirmed facts from interpretation.]

## Key Developments
[4–7 bullet points. Each bullet: **Headline.** Source-backed fact. Strategic implication in one sentence.]

## Market Implications
[2–4 short paragraphs. Market trends, sizing signals, demand shifts, competitive dynamics. Cite sources where possible.]

## Technology Signals
[Bullet points. Engineering advances, efficiency improvements, deployment milestones, R&D directions from the research.]

## Policy and Funding Signals
[Bullet points. Government programs, regulations, subsidies, funding announcements visible in the research. If none found, state that clearly.]

## Competitive Notes
[Bullet points. Company announcements, partnerships, expansion activity, hiring signals from the research. If none found, state that clearly.]

## Risks and Watchouts
[Bullet points. Supply chain risks, policy uncertainty, technology gaps, market risks visible in the research. Include at least two even if the research is limited.]

## Source Traceability
[List every source that contributed to this report. Format exactly as:
- **Title**: URL (source_type)]

## Workflow Metadata
[System-generated]
"""

# ---------------------------------------------------------------------------
# Context builder
# ---------------------------------------------------------------------------

def build_context(state: AgentState) -> tuple[str, int]:
    """Build a compact research context string from the workflow state.

    Context is assembled in priority order:
      1. Successfully crawled pages — highest signal quality (full content excerpt)
      2. Merged search / news / RSS results — snippet-level signal

    Total context is capped at _MAX_CONTEXT_CHARS to control token cost.

    Returns:
        Tuple of (context_string, total_source_count_in_context)
    """
    parts: list[str] = []
    source_count: int = 0

    # --- Priority 1: crawled pages with successful extraction ---
    for r in state.get("crawled_results", []):
        if not r.get("extraction_success"):
            continue
        content_excerpt = (r.get("content") or "")[:_MAX_CRAWLED_CONTENT_CHARS]
        parts.append(
            f"[CRAWLED | {r.get('source', '')}]\n"
            f"Title: {r.get('title', '')}\n"
            f"URL: {r.get('url', '')}\n"
            f"Content excerpt:\n{content_excerpt}"
        )
        source_count += 1

    # --- Priority 2: merged results (search + news + rss) ---
    added_urls: set[str] = {r.get("url", "") for r in state.get("crawled_results", []) if r.get("extraction_success")}
    for r in state.get("merged_results", [])[:_MAX_MERGED_IN_CONTEXT]:
        url = r.get("url", "")
        if url in added_urls:
            continue  # already included via crawled content above
        snippet = (r.get("snippet") or "")[:_MAX_SNIPPET_CHARS]
        pub = r.get("published_at") or ""
        parts.append(
            f"[{r.get('source_type', '').upper()} | {r.get('source', '')}]\n"
            f"Title: {r.get('title', '')}\n"
            f"URL: {url}\n"
            f"Published: {pub}\n"
            f"{snippet}"
        )
        source_count += 1

    context = "\n\n---\n\n".join(parts)

    if len(context) > _MAX_CONTEXT_CHARS:
        context = context[:_MAX_CONTEXT_CHARS] + "\n\n[Context truncated at character limit]"
        logger.warning(
            "build_context: context truncated | original_chars=%d | limit=%d",
            len("\n\n---\n\n".join(parts)),
            _MAX_CONTEXT_CHARS,
        )

    logger.debug("build_context | chars=%d | sources=%d", len(context), source_count)
    return context, source_count


# ---------------------------------------------------------------------------
# Metadata section (programmatic — never passed to LLM)
# ---------------------------------------------------------------------------

def _metadata_section(state: AgentState, source_count: int, report_path: Path) -> str:
    meta = state.get("run_metadata", {})
    crawled = state.get("crawled_results", [])
    crawl_success = sum(1 for r in crawled if r.get("extraction_success"))
    errors = state.get("errors", [])
    warnings = state.get("warnings", [])

    lines = [
        f"| Field | Value |",
        f"|---|---|",
        f"| Topic | {meta.get('topic', state.get('topic', ''))} |",
        f"| Report generated | {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')} |",
        f"| Pipeline duration | {meta.get('duration_seconds', 'N/A')}s |",
        f"| Serper results | {meta.get('serper_count', 0)} |",
        f"| NewsAPI results | {meta.get('news_count', 0)} |",
        f"| RSS results | {meta.get('rss_count', 0)} |",
        f"| Merged unique | {meta.get('merged_count', 0)} |",
        f"| Crawled | {meta.get('crawled_count', 0)} |",
        f"| Crawl success | {crawl_success} |",
        f"| Sources in context | {source_count} |",
        f"| Errors | {len(errors)} |",
        f"| Warnings | {len(warnings)} |",
        f"| Report file | `{report_path.name}` |",
    ]

    if errors:
        lines += ["", "**Pipeline errors:**"]
        for err in errors:
            lines.append(f"- {err}")

    if warnings:
        lines += ["", "**Pipeline warnings:**"]
        for w in warnings:
            lines.append(f"- {w}")

    lines += ["", "---", "_Generated by HYMIND — Autonomous Hydrogen Engineering Intelligence Agent_"]
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Save
# ---------------------------------------------------------------------------

def _save(content: str, output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = output_dir / f"{timestamp}_hymind_report.md"
    path.write_text(content, encoding="utf-8")
    return path


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def generate_report(
    state: AgentState,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
) -> tuple[Path, int]:
    """Generate a structured Markdown executive report from a completed AgentState.

    Builds a compact research context from crawled and merged results, calls
    OpenAI to synthesize the report body, appends a programmatic metadata section,
    and saves the result to disk.

    Args:
        state: Completed AgentState from the research workflow.
        output_dir: Directory to write the report file. Created automatically.

    Returns:
        Tuple of (report_path, character_count).

    Raises:
        RuntimeError: If OPENAI_API_KEY is not configured.
        openai.APIError: On non-retryable OpenAI failures.
    """
    topic = state.get("topic", "hydrogen industry intelligence")

    if not os.getenv("OPENAI_API_KEY", "").strip():
        logger.error("generate_report: OPENAI_API_KEY not configured")
        raise RuntimeError(
            "OPENAI_API_KEY is not set — report generation requires OpenAI. "
            "Add it to your .env file."
        )

    logger.info("Report generation starting | topic=%r", topic)

    # --- Build context ---
    context, source_count = build_context(state)
    logger.info(
        "Report context built | chars=%d | sources_in_context=%d",
        len(context),
        source_count,
    )

    if not context.strip():
        logger.warning("generate_report: context is empty — report will have limited content")

    # --- Build prompt ---
    date_str = datetime.now().strftime("%Y-%m-%d")
    prompt = _USER_PROMPT_TEMPLATE.format(
        topic=topic,
        date=date_str,
        context=context if context.strip() else "[No research context available]",
    )

    logger.info(
        "Report: calling OpenAI | prompt_chars=%d | max_tokens=3000",
        len(prompt),
    )

    # --- Call OpenAI ---
    report_body = complete(
        prompt=prompt,
        system=_SYSTEM_PROMPT,
        max_tokens=3000,
        temperature=0.2,
    )

    logger.info("Report: OpenAI response received | response_chars=%d", len(report_body))

    # --- Replace the [System-generated] placeholder with real metadata ---
    # Save first (path needed for metadata section)
    placeholder_report = report_body
    temp_path = _save(placeholder_report, output_dir)

    # Build metadata and replace placeholder
    metadata = _metadata_section(state, source_count, temp_path)
    full_report = report_body.replace("[System-generated]", metadata)

    # Overwrite with final version
    temp_path.write_text(full_report, encoding="utf-8")

    char_count = len(full_report)
    logger.info(
        "Report saved | path=%s | chars=%d | sources=%d",
        temp_path,
        char_count,
        source_count,
    )

    return temp_path, char_count
