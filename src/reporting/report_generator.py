"""Executive Markdown report generator for HYMIND.

Accepts a completed AgentState from the research workflow, builds a compact
research context, calls OpenAI to synthesize a structured intelligence report,
appends a programmatic metadata section, and saves the result to disk.
"""

import os
from datetime import datetime
from pathlib import Path

from tools.openai_client import complete
from reporting.validator import check_state_quality, validate_findings
from utils.logger import get_logger
from workflows.state import AgentState

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

DEFAULT_OUTPUT_DIR: Path = Path("outputs/reports")

_MAX_CONTEXT_CHARS: int = 30_000
_MAX_CRAWLED_CONTENT_CHARS: int = 1_200
_MAX_SNIPPET_CHARS: int = 400
_MAX_MERGED_IN_CONTEXT: int = 50

# ---------------------------------------------------------------------------
# Prompts
# ---------------------------------------------------------------------------

_SYSTEM_PROMPT = """\
You are a principal analyst at a top-tier strategy firm — the equivalent of a Roland Berger or McKinsey hydrogen practice lead — producing a weekly intelligence briefing for C-suite executives and investment committees in the European hydrogen and fuel cell industry.

Your output is a primary decision-making tool. It must be dense with specific facts, named companies, named programs, euro amounts, and dates drawn directly from the research provided. Vague or generic statements are a failure mode.

Hard rules:
- Every claim must trace to a source in the research context. Do not invent statistics, company names, program names, or figures.
- Where the research is thin on a topic, state the gap explicitly — do not pad with generic sector commentary.
- Separate confirmed facts from analytical interpretation. Label interpretation clearly.
- Do not use filler language: no "in today's rapidly evolving landscape", no "it is important to note", no "as the industry continues to grow".
- Write in the register of a senior strategy consultant: direct, precise, action-oriented.
- Lead every section and every bullet with the most strategically significant point — never bury the lede.
- Cover all application pillars present in the research: funding/policy, PEM fuel cell technology, stationary power, micro-grid and off-grid, backup/UPS power, and intralogistics.
- Name companies, name programs, name amounts. Anonymous claims have no value.
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

Write in depth. Each section must be substantive — executives use this report as their primary weekly briefing on the European hydrogen and fuel cell industry. Short or thin sections are not acceptable.

# HYMIND [brief topic phrase — 4–8 words, no punctuation, starting with "Weekly"]

## Executive Summary
[400–600 words. Provide a thorough summary of the most important developments across all research pillars: funding, policy, fuel cell technology, stationary power, micro-grid and backup power, and intralogistics. Highlight strategic significance and what decision-makers should prioritise this week. Separate confirmed facts from interpretation. This section stands alone — a reader who reads only this section must come away fully informed.]

## Key Developments
[10–14 bullet points. Each bullet must follow this format exactly: **Headline.** One or two source-backed sentences with specific facts, figures, or company names where available. Strategic implication in one sentence. Cover all research pillars — do not cluster on a single theme.]

## Market Implications
[5–7 paragraphs. Cover market trends, sizing signals, demand shifts, and competitive dynamics across Europe. Devote at least one paragraph each to: (1) stationary and backup power demand, (2) intralogistics and material handling, (3) micro-grid and off-grid applications, (4) funding and investment flows. Cite sources where possible.]

## Technology Signals
[8–12 bullet points. Cover engineering advances, efficiency improvements, cost reductions, stack and system performance milestones, deployment results, and R&D directions from the research. Include specific figures or company names where available.]

## Policy and Funding Signals
[8–12 bullet points. Cover EU-level, national, and regional funding programs, regulatory updates, subsidies, grants, and strategy announcements visible in the research. Include amounts, timelines, and eligibility criteria where available. If a specific funding pillar has no new signals, state that explicitly.]

## Competitive Notes
[8–12 bullet points. Cover company announcements, product launches, partnerships, expansion activity, contract wins, and strategic moves from the research. Organise by application area where possible — stationary power, intralogistics, backup/UPS, micro-grid. If a company appears in the research, include it here.]

## Risks and Watchouts
[6–10 bullet points. Cover supply chain risks, policy uncertainty, technology gaps, cost barriers, market risks, and execution risks visible in the research. Include at least one risk per major application area. Be specific — generic risk statements are not acceptable.]

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
    """Build a research context string from the workflow state.

    Priority order — highest value first so truncation cuts the least useful content:
      1. RSS items — freshest real news from industry publications
      2. Serper/NewsAPI snippets — current news after search_type="news" filtering
      3. Crawled pages — full article content from non-blocklisted sources
      4. RAG historical context — capped at 2 items, labelled clearly as background

    Returns:
        Tuple of (context_string, total_source_count_in_context)
    """
    parts: list[str] = []
    source_count: int = 0

    merged = state.get("merged_results", [])
    crawled_urls: set[str] = {
        r.get("url", "") for r in state.get("crawled_results", [])
        if r.get("extraction_success")
    }

    # --- Priority 1: RSS items (real industry news, no paywalls) ---
    rss_items = [r for r in merged if r.get("source_type") == "rss" and r.get("url") not in crawled_urls]
    for r in rss_items[:35]:
        snippet = (r.get("snippet") or "")[:_MAX_SNIPPET_CHARS]
        pub = r.get("published_at") or ""
        parts.append(
            f"[RSS | {r.get('source', '')}]\n"
            f"Title: {r.get('title', '')}\n"
            f"URL: {r.get('url', '')}\n"
            f"Published: {pub}\n"
            f"{snippet}"
        )
        source_count += 1

    # --- Priority 2: Serper / NewsAPI news snippets ---
    search_items = [
        r for r in merged
        if r.get("source_type") in ("organic", "news") and r.get("url") not in crawled_urls
    ]
    for r in search_items[:_MAX_MERGED_IN_CONTEXT]:
        snippet = (r.get("snippet") or "")[:_MAX_SNIPPET_CHARS]
        pub = r.get("published_at") or ""
        parts.append(
            f"[{r.get('source_type', '').upper()} | {r.get('source', '')}]\n"
            f"Title: {r.get('title', '')}\n"
            f"URL: {r.get('url', '')}\n"
            f"Published: {pub}\n"
            f"{snippet}"
        )
        source_count += 1

    # --- Priority 3: Crawled pages (blocklist already applied upstream) ---
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

    # --- Priority 4: RAG historical — capped at 2, background context only ---
    rag_context = state.get("rag_context", [])
    if rag_context:
        rag_parts: list[str] = []
        for r in rag_context[:2]:
            title = r.get("title", "") if isinstance(r, dict) else getattr(r, "title", "")
            url = r.get("url", "") if isinstance(r, dict) else getattr(r, "url", "")
            source = r.get("source", "") if isinstance(r, dict) else getattr(r, "source", "")
            snippet = r.get("snippet", "") if isinstance(r, dict) else getattr(r, "snippet", "")
            score = r.get("score", 0.0) if isinstance(r, dict) else getattr(r, "score", 0.0)
            rag_parts.append(
                f"[HISTORICAL BACKGROUND | {source}] (score: {score:.2f})\n"
                f"Title: {title}\nURL: {url}\n"
                f"{(snippet or '')[:_MAX_SNIPPET_CHARS]}"
            )
        if rag_parts:
            parts.append(
                "=== HISTORICAL BACKGROUND (for trend comparison only — not current news) ===\n\n"
                + "\n\n---\n\n".join(rag_parts)
            )
            source_count += len(rag_parts)
            logger.debug("build_context: added %d RAG items as background", len(rag_parts))

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

    lines += ["", "---", "_Generated by HYMIND — Hydrogen Market Intelligence & Data_"]
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Save
# ---------------------------------------------------------------------------

def _save(content: str, output_dir: Path) -> Path:
    """Write content to a timestamped Markdown file. Creates output_dir if needed."""
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

    logger.info("=== Report generation starting | topic=%r ===", topic)

    # --- Validate findings before synthesis ---
    raw_findings = state.get("merged_results", [])
    valid_findings, validation = validate_findings(raw_findings)

    quality = check_state_quality(state)
    if not quality["can_generate_report"]:
        logger.warning(
            "generate_report: state quality check failed | errors=%s",
            quality["errors"],
        )
    logger.info(
        "generate_report: validation complete | total=%d | valid=%d"
        " | duplicates=%d | missing_url=%d",
        validation.total_input,
        validation.valid_count,
        validation.duplicate_count,
        validation.missing_url_count,
    )

    # Use validated findings for context building
    validated_state: AgentState = {**state, "merged_results": valid_findings}

    # --- Build context ---
    context, source_count = build_context(validated_state)
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
        "Report: calling OpenAI | prompt_chars=%d | max_tokens=6000",
        len(prompt),
    )

    # --- Call OpenAI ---
    report_body = complete(
        prompt=prompt,
        system=_SYSTEM_PROMPT,
        max_tokens=6000,
        temperature=0.2,
    )

    logger.info("Report: OpenAI response received | response_chars=%d", len(report_body))

    # --- Replace the [System-generated] placeholder with real metadata ---
    # Save first so the path is available for the metadata section footer.
    temp_path = _save(report_body, output_dir)

    metadata = _metadata_section(state, source_count, temp_path)
    full_report = report_body.replace("[System-generated]", metadata)

    # Overwrite with final version
    temp_path.write_text(full_report, encoding="utf-8")

    char_count = len(full_report)
    logger.info(
        "=== Report generation complete | path=%s | chars=%d | sources=%d ===",
        temp_path,
        char_count,
        source_count,
    )

    return temp_path, char_count
