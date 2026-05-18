"""High-level RAG retriever for HYMIND.

Provides two public entry points:
  - findings_from_state(): converts AgentState results to StoredFinding objects
  - store_from_state(): embeds and upserts merged findings into Pinecone
  - retrieve_context(): embeds a query and returns ranked RetrievedFinding objects

Both store_from_state() and retrieve_context() degrade gracefully when
Pinecone or OpenAI credentials are absent — they return 0 / [] rather than raising.
"""

import os
from datetime import datetime, timezone
from typing import Any, Optional

from hymind.rag.embeddings import create_embeddings
from hymind.rag.pinecone_store import is_pinecone_configured, query_index, upsert_findings
from hymind.rag.schemas import RetrievedFinding, StoredFinding
from hymind.utils.logger import get_logger

logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# State → StoredFinding conversion
# ---------------------------------------------------------------------------

def findings_from_state(state: dict, topic: str) -> list[StoredFinding]:
    """Convert AgentState merged_results to StoredFinding objects.

    Crawled page content is merged in by URL when available so that embeddings
    carry full-text signal rather than just snippets.

    Args:
        state: AgentState dict with merged_results and crawled_results.
        topic: Research topic string stored as metadata on each finding.

    Returns:
        List of StoredFinding objects (skips items without a URL).
    """
    crawled_by_url: dict[str, str] = {}
    for r in state.get("crawled_results", []):
        if r.get("extraction_success") and r.get("url") and r.get("content"):
            key = r["url"].strip().rstrip("/").lower()
            crawled_by_url[key] = r["content"]

    collected_at = datetime.now(timezone.utc).isoformat()
    findings: list[StoredFinding] = []

    for item in state.get("merged_results", []):
        url = item.get("url", "").strip()
        if not url:
            continue
        url_key = url.rstrip("/").lower()
        content = crawled_by_url.get(url_key, "")

        findings.append(
            StoredFinding(
                title=item.get("title", ""),
                url=url,
                source=item.get("source", ""),
                source_type=item.get("source_type", ""),
                published_at=item.get("published_at"),
                snippet=item.get("snippet", ""),
                content=content,
                topic=topic,
                category=None,
                collected_at=collected_at,
            )
        )

    logger.debug("findings_from_state: %d findings built | topic=%r", len(findings), topic)
    return findings


# ---------------------------------------------------------------------------
# Store
# ---------------------------------------------------------------------------

def store_from_state(
    state: dict,
    topic: str,
    openai_client: Optional[Any] = None,
    pinecone_index: Optional[Any] = None,
) -> int:
    """Embed merged findings and upsert them into Pinecone.

    Args:
        state: AgentState dict with merged_results and crawled_results.
        topic: Research topic — stored as metadata on each vector.
        openai_client: Injected OpenAI client (for testing).
        pinecone_index: Injected Pinecone index (for testing).

    Returns:
        Number of vectors upserted (0 if no findings or on error).
    """
    findings = findings_from_state(state, topic)
    if not findings:
        logger.info("store_from_state: no findings to embed or store")
        return 0

    # Embed title + snippet (snippet is the primary search-quality signal)
    texts = [f"{f.title}. {f.snippet}".strip() for f in findings]
    embeddings = create_embeddings(texts, client=openai_client)

    return upsert_findings(findings, embeddings, pinecone_index=pinecone_index)


# ---------------------------------------------------------------------------
# Retrieve
# ---------------------------------------------------------------------------

def retrieve_context(
    topic: str,
    query: str,
    top_k: int = 5,
    filter_: Optional[dict] = None,
    openai_client: Optional[Any] = None,
    pinecone_index: Optional[Any] = None,
) -> list[RetrievedFinding]:
    """Retrieve semantically relevant historical findings from Pinecone.

    Returns an empty list (never raises) when:
      - Pinecone is not configured
      - OPENAI_API_KEY is not set
      - Any embedding or query error occurs

    Args:
        topic: Research topic (for logging).
        query: Semantic query string to embed and search with.
        top_k: Maximum number of results to return.
        filter_: Optional Pinecone metadata filter dict.
        openai_client: Injected OpenAI client (for testing).
        pinecone_index: Injected Pinecone index (for testing).

    Returns:
        List of RetrievedFinding objects ordered by similarity score.
    """
    if not is_pinecone_configured():
        logger.warning("retrieve_context: Pinecone not configured — skipping")
        return []

    if not os.getenv("OPENAI_API_KEY", "").strip():
        logger.warning("retrieve_context: OPENAI_API_KEY not set — skipping")
        return []

    try:
        embeddings = create_embeddings([query], client=openai_client)
        if not embeddings:
            return []

        matches = query_index(
            query_embedding=embeddings[0],
            top_k=top_k,
            filter_=filter_,
            pinecone_index=pinecone_index,
        )

        results: list[RetrievedFinding] = []
        for match in matches:
            if isinstance(match, dict):
                meta = match.get("metadata", {}) or {}
                score = float(match.get("score", 0.0))
            else:
                meta = getattr(match, "metadata", {}) or {}
                score = float(getattr(match, "score", 0.0))

            results.append(
                RetrievedFinding(
                    title=meta.get("title", ""),
                    url=meta.get("url", ""),
                    source=meta.get("source", ""),
                    source_type=meta.get("source_type", ""),
                    published_at=meta.get("published_at") or None,
                    snippet=meta.get("snippet", ""),
                    score=score,
                    metadata=meta,
                )
            )

        logger.info(
            "retrieve_context complete | topic=%r | results=%d",
            topic,
            len(results),
        )
        return results

    except Exception as exc:
        logger.error("retrieve_context failed | topic=%r | error=%s", topic, exc)
        return []
