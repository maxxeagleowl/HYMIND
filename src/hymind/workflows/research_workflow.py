"""HYMIND research workflow — sequential LangGraph pipeline.

Nodes run in a fixed linear order for reliability and ease of debugging.
The state schema is compatible with future parallel fan-out (LangGraph Send())
without requiring redesign: each source node writes to its own isolated field.

Node order:
    initialize_state → collect_serper → collect_news → collect_rss
    → merge_and_deduplicate → crawl_selected
    → store_findings_in_pinecone → retrieve_context_from_pinecone
    → finalize_state → END
"""

import os
from datetime import datetime, timezone

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
    """Return the current UTC time as an ISO 8601 string."""
    return datetime.now(timezone.utc).isoformat()


def _normalize_url(url: str) -> str:
    """Return a canonical form of the URL for deduplication keying."""
    return url.strip().rstrip("/").lower()


# ---------------------------------------------------------------------------
# Nodes
# ---------------------------------------------------------------------------

def initialize_state(state: AgentState) -> dict:
    """Set up run_metadata with topic and start timestamp."""
    logger.info("=== Node START: initialize_state | topic=%r ===", state["topic"])
    result = {
        "run_metadata": {
            "topic": state["topic"],
            "start_time": _now_iso(),
            "end_time": None,
            "duration_seconds": None,
        }
    }
    logger.info("=== Node END: initialize_state ===")
    return result


def collect_serper(state: AgentState) -> dict:
    """Run a Serper web search for the topic and store results in state."""
    logger.info("=== Node START: collect_serper | topic=%r ===", state["topic"])

    if not os.getenv("SERPER_API_KEY", "").strip():
        logger.warning("collect_serper: SERPER_API_KEY not configured — source skipped")
        logger.info("=== Node END: collect_serper | skipped (no key) ===")
        return {
            "serper_results": [],
            "warnings": ["collect_serper: SERPER_API_KEY not set — Serper skipped"],
        }

    try:
        results = serper_search(state["topic"])
        logger.info("=== Node END: collect_serper | results=%d ===", len(results))
        return {"serper_results": results}
    except Exception as exc:
        logger.error("collect_serper: failed | error_type=%s | error=%s", type(exc).__name__, exc)
        logger.info("=== Node END: collect_serper | failed, continuing ===")
        return {
            "serper_results": [],
            "errors": [f"collect_serper: {type(exc).__name__}: {exc}"],
        }


def collect_news(state: AgentState) -> dict:
    """Query NewsAPI for recent articles matching the topic."""
    logger.info("=== Node START: collect_news | topic=%r ===", state["topic"])

    if not os.getenv("NEWS_API_KEY", "").strip():
        logger.warning("collect_news: NEWS_API_KEY not configured — source skipped")
        logger.info("=== Node END: collect_news | skipped (no key) ===")
        return {
            "news_results": [],
            "warnings": ["collect_news: NEWS_API_KEY not set — NewsAPI skipped"],
        }

    try:
        results = news_search(state["topic"])
        logger.info("=== Node END: collect_news | results=%d ===", len(results))
        return {"news_results": results}
    except Exception as exc:
        logger.error("collect_news: failed | error_type=%s | error=%s", type(exc).__name__, exc)
        logger.info("=== Node END: collect_news | failed, continuing ===")
        return {
            "news_results": [],
            "errors": [f"collect_news: {type(exc).__name__}: {exc}"],
        }


def collect_rss(state: AgentState) -> dict:
    """Fetch entries from all configured hydrogen RSS feeds."""
    logger.info("=== Node START: collect_rss | feeds=%d ===", len(DEFAULT_HYDROGEN_FEEDS))
    try:
        results = read_feeds(DEFAULT_HYDROGEN_FEEDS, topic=state["topic"])
        logger.info("=== Node END: collect_rss | results=%d ===", len(results))
        return {"rss_results": results}
    except Exception as exc:
        logger.error("collect_rss: failed | error_type=%s | error=%s", type(exc).__name__, exc)
        logger.info("=== Node END: collect_rss | failed, continuing ===")
        return {
            "rss_results": [],
            "errors": [f"collect_rss: {type(exc).__name__}: {exc}"],
        }


def merge_and_deduplicate(state: AgentState) -> dict:
    """Combine all source results and remove duplicates by normalised URL."""
    logger.info("=== Node START: merge_and_deduplicate ===")

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
        "=== Node END: merge_and_deduplicate | total=%d | unique=%d | removed=%d ===",
        len(all_results),
        len(deduplicated),
        len(all_results) - len(deduplicated),
    )
    return {"merged_results": deduplicated}


def crawl_selected(state: AgentState) -> dict:
    """Crawl the top N non-PDF URLs from merged_results for full content extraction."""
    logger.info("=== Node START: crawl_selected ===")

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
        logger.warning("crawl_selected: no crawlable URLs found in merged results — skipping")
        logger.info("=== Node END: crawl_selected | skipped (no URLs) ===")
        return {
            "crawled_results": [],
            "warnings": ["crawl_selected: no crawlable URLs available"],
        }

    logger.info("crawl_selected: selected %d URLs for crawling", len(urls))
    try:
        results = crawl_many(urls)
        success = sum(1 for r in results if r.get("extraction_success"))
        logger.info(
            "=== Node END: crawl_selected | crawled=%d | successful=%d | failed=%d ===",
            len(results),
            success,
            len(results) - success,
        )
        return {"crawled_results": results}
    except Exception as exc:
        logger.error("crawl_selected: failed | error_type=%s | error=%s", type(exc).__name__, exc)
        logger.info("=== Node END: crawl_selected | failed, continuing ===")
        return {
            "crawled_results": [],
            "errors": [f"crawl_selected: {type(exc).__name__}: {exc}"],
        }


def store_findings_in_pinecone(state: AgentState) -> dict:
    """Embed merged findings and upsert them into Pinecone.

    Skips gracefully with a warning when Pinecone or OpenAI credentials are absent.
    Never raises — a storage failure must not block report generation.
    """
    logger.info("=== Node START: store_findings_in_pinecone | topic=%r ===", state["topic"])

    from hymind.rag.pinecone_store import is_pinecone_configured

    if not is_pinecone_configured():
        logger.warning("store_findings_in_pinecone: Pinecone not configured — RAG storage skipped")
        logger.info("=== Node END: store_findings_in_pinecone | skipped (not configured) ===")
        return {"warnings": ["store_findings_in_pinecone: Pinecone not configured — RAG storage skipped"]}

    if not os.getenv("OPENAI_API_KEY", "").strip():
        logger.warning("store_findings_in_pinecone: OPENAI_API_KEY missing — RAG storage skipped")
        logger.info("=== Node END: store_findings_in_pinecone | skipped (no OpenAI key) ===")
        return {"warnings": ["store_findings_in_pinecone: OPENAI_API_KEY missing — RAG storage skipped"]}

    try:
        from hymind.rag.retriever import store_from_state
        count = store_from_state(state, topic=state["topic"])
        logger.info("=== Node END: store_findings_in_pinecone | stored=%d vectors ===", count)
        return {}
    except Exception as exc:
        logger.error(
            "store_findings_in_pinecone: failed | error_type=%s | error=%s",
            type(exc).__name__, exc,
        )
        logger.info("=== Node END: store_findings_in_pinecone | failed, continuing ===")
        return {"warnings": [f"store_findings_in_pinecone: {type(exc).__name__}: {exc}"]}


def retrieve_context_from_pinecone(state: AgentState) -> dict:
    """Retrieve historical context from Pinecone for the current topic.

    Skips gracefully when Pinecone is not configured. Returns rag_context as a
    list of plain dicts (dataclasses serialized via dataclasses.asdict) so that
    downstream nodes can use .get() without importing the RAG schema.
    """
    import dataclasses

    logger.info("=== Node START: retrieve_context_from_pinecone | topic=%r ===", state["topic"])

    try:
        from hymind.rag.retriever import retrieve_context
        results = retrieve_context(topic=state["topic"], query=state["topic"], top_k=5)
        rag_dicts = [dataclasses.asdict(r) for r in results]
        logger.info(
            "=== Node END: retrieve_context_from_pinecone | historical_results=%d ===",
            len(rag_dicts),
        )
        return {"rag_context": rag_dicts}
    except Exception as exc:
        logger.error(
            "retrieve_context_from_pinecone: failed | error_type=%s | error=%s",
            type(exc).__name__, exc,
        )
        logger.info("=== Node END: retrieve_context_from_pinecone | failed, continuing ===")
        return {
            "rag_context": [],
            "warnings": [f"retrieve_context_from_pinecone: {type(exc).__name__}: {exc}"],
        }


def finalize_state(state: AgentState) -> dict:
    """Compute final run_metadata counters and elapsed duration."""
    logger.info("=== Node START: finalize_state ===")

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

    if errors:
        logger.warning("finalize_state: %d pipeline errors recorded", len(errors))

    logger.info(
        "=== Node END: finalize_state | topic=%r | serper=%d | news=%d | rss=%d"
        " | merged=%d | crawled=%d | crawl_ok=%d | errors=%d | warnings=%d | duration=%.1fs ===",
        state.get("topic", ""),
        updated_meta["serper_count"],
        updated_meta["news_count"],
        updated_meta["rss_count"],
        updated_meta["merged_count"],
        updated_meta["crawled_count"],
        updated_meta["crawl_success_count"],
        updated_meta["error_count"],
        updated_meta["warning_count"],
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
    graph.add_node("store_findings_in_pinecone", store_findings_in_pinecone)
    graph.add_node("retrieve_context_from_pinecone", retrieve_context_from_pinecone)
    graph.add_node("finalize_state", finalize_state)

    graph.add_edge(START, "initialize_state")
    graph.add_edge("initialize_state", "collect_serper")
    graph.add_edge("collect_serper", "collect_news")
    graph.add_edge("collect_news", "collect_rss")
    graph.add_edge("collect_rss", "merge_and_deduplicate")
    graph.add_edge("merge_and_deduplicate", "crawl_selected")
    graph.add_edge("crawl_selected", "store_findings_in_pinecone")
    graph.add_edge("store_findings_in_pinecone", "retrieve_context_from_pinecone")
    graph.add_edge("retrieve_context_from_pinecone", "finalize_state")
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
