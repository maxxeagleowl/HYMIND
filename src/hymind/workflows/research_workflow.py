"""HYMIND research workflow — sequential LangGraph pipeline.

Nodes run in a fixed linear order for reliability and ease of debugging.
The state schema is compatible with future parallel fan-out (LangGraph Send())
without requiring redesign: each source node writes to its own isolated field.

Node order:
    initialize_state → collect_serper → collect_news → collect_rss
    → merge_and_deduplicate → crawl_selected → finalize_state → END
"""

import operator
import os
from datetime import datetime, timezone
from typing import Any

from langgraph.graph import END, START, StateGraph

from hymind.tools.rss_reader import DEFAULT_HYDROGEN_FEEDS, read_feeds
from hymind.tools.serper_search import search as serper_search
from hymind.tools.news_api import search as news_search
from hymind.tools.web_crawler import crawl_many
from hymind.utils.logger import get_logger
from hymind.workflows.state import AgentState

logger = get_logger(__name__)

_MAX_CRAWL_URLS: int = 5


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _normalize_url(url: str) -> str:
    """Return a canonical form of the URL for deduplication keying."""
    return url.strip().rstrip("/").lower()


# ---------------------------------------------------------------------------
# Nodes
# ---------------------------------------------------------------------------

def initialize_state(state: AgentState) -> dict:
    logger.info("Node: initialize_state | topic=%r", state["topic"])
    return {
        "run_metadata": {
            "topic": state["topic"],
            "start_time": _now_iso(),
            "end_time": None,
            "duration_seconds": None,
        }
    }


def collect_serper(state: AgentState) -> dict:
    logger.info("Node: collect_serper | topic=%r", state["topic"])

    if not os.getenv("SERPER_API_KEY", "").strip():
        logger.warning("collect_serper skipped | SERPER_API_KEY not configured")
        return {
            "serper_results": [],
            "warnings": ["collect_serper: SERPER_API_KEY not set — Serper skipped"],
        }

    try:
        results = serper_search(state["topic"])
        logger.info("Node: collect_serper complete | results=%d", len(results))
        return {"serper_results": results}
    except Exception as exc:
        logger.error("Node: collect_serper failed | error=%s", exc)
        return {
            "serper_results": [],
            "errors": [f"collect_serper: {type(exc).__name__}: {exc}"],
        }


def collect_news(state: AgentState) -> dict:
    logger.info("Node: collect_news | topic=%r", state["topic"])

    if not os.getenv("NEWS_API_KEY", "").strip():
        logger.warning("collect_news skipped | NEWS_API_KEY not configured")
        return {
            "news_results": [],
            "warnings": ["collect_news: NEWS_API_KEY not set — NewsAPI skipped"],
        }

    try:
        results = news_search(state["topic"])
        logger.info("Node: collect_news complete | results=%d", len(results))
        return {"news_results": results}
    except Exception as exc:
        logger.error("Node: collect_news failed | error=%s", exc)
        return {
            "news_results": [],
            "errors": [f"collect_news: {type(exc).__name__}: {exc}"],
        }


def collect_rss(state: AgentState) -> dict:
    logger.info("Node: collect_rss | feeds=%d", len(DEFAULT_HYDROGEN_FEEDS))
    try:
        results = read_feeds(DEFAULT_HYDROGEN_FEEDS, topic=state["topic"])
        logger.info("Node: collect_rss complete | results=%d", len(results))
        return {"rss_results": results}
    except Exception as exc:
        logger.error("Node: collect_rss failed | error=%s", exc)
        return {
            "rss_results": [],
            "errors": [f"collect_rss: {type(exc).__name__}: {exc}"],
        }


def merge_and_deduplicate(state: AgentState) -> dict:
    logger.info("Node: merge_and_deduplicate")

    all_results: list[dict] = (
        state.get("serper_results", [])
        + state.get("news_results", [])
        + state.get("rss_results", [])
    )

    seen: set[str] = set()
    deduplicated: list[dict] = []

    for item in all_results:
        url = item.get("url", "")
        if not url:
            continue
        key = _normalize_url(url)
        if key not in seen:
            seen.add(key)
            deduplicated.append(item)

    logger.info(
        "Node: merge_and_deduplicate complete | total=%d | unique=%d | removed=%d",
        len(all_results),
        len(deduplicated),
        len(all_results) - len(deduplicated),
    )
    return {"merged_results": deduplicated}


def crawl_selected(state: AgentState) -> dict:
    logger.info("Node: crawl_selected")

    merged = state.get("merged_results", [])
    urls: list[str] = []

    for item in merged:
        url = item.get("url", "").strip()
        if not url:
            continue
        if url.lower().endswith(".pdf"):
            logger.debug("crawl_selected: skipping PDF | url=%s", url)
            continue
        urls.append(url)
        if len(urls) >= _MAX_CRAWL_URLS:
            break

    if not urls:
        logger.warning("Node: crawl_selected — no crawlable URLs found in merged results")
        return {
            "crawled_results": [],
            "warnings": ["crawl_selected: no crawlable URLs available"],
        }

    logger.info("Node: crawl_selected | urls_selected=%d", len(urls))
    try:
        results = crawl_many(urls)
        success = sum(1 for r in results if r.get("extraction_success"))
        logger.info(
            "Node: crawl_selected complete | crawled=%d | successful=%d",
            len(results),
            success,
        )
        return {"crawled_results": results}
    except Exception as exc:
        logger.error("Node: crawl_selected failed | error=%s", exc)
        return {
            "crawled_results": [],
            "errors": [f"crawl_selected: {type(exc).__name__}: {exc}"],
        }


def finalize_state(state: AgentState) -> dict:
    logger.info("Node: finalize_state")

    meta: dict = state.get("run_metadata", {})
    end_time = datetime.now(timezone.utc)

    duration: float | None = None
    start_str = meta.get("start_time")
    if start_str:
        try:
            start = datetime.fromisoformat(start_str)
            duration = round((end_time - start).total_seconds(), 2)
        except Exception:
            pass

    crawled = state.get("crawled_results", [])
    crawl_success = sum(1 for r in crawled if r.get("extraction_success"))
    errors = state.get("errors", [])

    updated_meta = {
        **meta,
        "end_time": end_time.isoformat(),
        "duration_seconds": duration,
        "serper_count": len(state.get("serper_results", [])),
        "news_count": len(state.get("news_results", [])),
        "rss_count": len(state.get("rss_results", [])),
        "merged_count": len(state.get("merged_results", [])),
        "crawled_count": len(crawled),
        "crawl_success_count": crawl_success,
        "error_count": len(errors),
        "warning_count": len(state.get("warnings", [])),
    }

    logger.info(
        "Node: finalize_state | topic=%r | serper=%d | news=%d | rss=%d"
        " | merged=%d | crawled=%d | crawl_ok=%d | errors=%d | duration=%.1fs",
        state.get("topic", ""),
        updated_meta["serper_count"],
        updated_meta["news_count"],
        updated_meta["rss_count"],
        updated_meta["merged_count"],
        updated_meta["crawled_count"],
        updated_meta["crawl_success_count"],
        updated_meta["error_count"],
        duration or 0.0,
    )

    return {"run_metadata": updated_meta}


# ---------------------------------------------------------------------------
# Graph assembly
# ---------------------------------------------------------------------------

def build_workflow():
    """Build and compile the HYMIND research workflow graph.

    Returns a compiled LangGraph application ready for .invoke() calls.
    """
    graph: StateGraph = StateGraph(AgentState)

    graph.add_node("initialize_state", initialize_state)
    graph.add_node("collect_serper", collect_serper)
    graph.add_node("collect_news", collect_news)
    graph.add_node("collect_rss", collect_rss)
    graph.add_node("merge_and_deduplicate", merge_and_deduplicate)
    graph.add_node("crawl_selected", crawl_selected)
    graph.add_node("finalize_state", finalize_state)

    graph.add_edge(START, "initialize_state")
    graph.add_edge("initialize_state", "collect_serper")
    graph.add_edge("collect_serper", "collect_news")
    graph.add_edge("collect_news", "collect_rss")
    graph.add_edge("collect_rss", "merge_and_deduplicate")
    graph.add_edge("merge_and_deduplicate", "crawl_selected")
    graph.add_edge("crawl_selected", "finalize_state")
    graph.add_edge("finalize_state", END)

    return graph.compile()


def run_research(topic: str) -> AgentState:
    """Run the full research workflow for a topic and return the final state.

    Args:
        topic: Research topic string passed to all collection nodes.

    Returns:
        Final AgentState dict with all collected, merged, and crawled results.
    """
    from hymind.workflows.state import initial_state
    app = build_workflow()
    return app.invoke(initial_state(topic))
