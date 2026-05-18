"""Pinecone vector store for HYMIND RAG layer.

All Pinecone interactions use dependency injection so that tests never touch a
real index. The pinecone SDK import is deferred to connection time — missing the
package is only an error when Pinecone is actually configured.

Index setup (manual, one-time):
    The HYMIND index must be created before ingestion. Example using the SDK:

        from pinecone import Pinecone, ServerlessSpec
        pc = Pinecone(api_key="...")
        pc.create_index(
            name="hymind-research",
            dimension=1536,          # matches text-embedding-3-small
            metric="cosine",
            spec=ServerlessSpec(cloud="aws", region="us-east-1"),
        )

    Alternatively, create it in the Pinecone console and set
    PINECONE_INDEX_NAME to match.
"""

import hashlib
import os
from datetime import datetime, timezone
from typing import Any, Optional

from hymind.rag.schemas import StoredFinding
from hymind.utils.logger import get_logger

logger = get_logger(__name__)

_METADATA_STR_LIMIT: int = 500
_SNIPPET_LIMIT: int = 1000


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

def get_pinecone_config() -> dict:
    """Read Pinecone configuration from environment variables."""
    return {
        "api_key": os.getenv("PINECONE_API_KEY", "").strip(),
        "index_name": os.getenv("PINECONE_INDEX_NAME", "hymind-research"),
        "cloud": os.getenv("PINECONE_CLOUD", "aws"),
        "region": os.getenv("PINECONE_REGION", "us-east-1"),
    }


def is_pinecone_configured() -> bool:
    """Return True if the minimum Pinecone credentials are present in env."""
    cfg = get_pinecone_config()
    return bool(cfg["api_key"] and cfg["index_name"])


# ---------------------------------------------------------------------------
# Vector ID and metadata helpers
# ---------------------------------------------------------------------------

def make_vector_id(url: str, title: str = "") -> str:
    """Generate a stable, deterministic vector ID from a URL.

    Uses SHA-256 of the stripped URL. Falls back to title when URL is empty.
    Truncated to 48 hex chars (192 bits) — well within Pinecone's 512-byte limit.
    """
    base = url.strip() if url.strip() else (title.strip() + ":no-url")
    return hashlib.sha256(base.encode()).hexdigest()[:48]


def finding_to_metadata(finding: StoredFinding) -> dict:
    """Convert a StoredFinding to a Pinecone-compatible metadata dict.

    String values are truncated to stay within Pinecone metadata limits.
    """
    return {
        "title": (finding.title or "")[:_METADATA_STR_LIMIT],
        "url": (finding.url or "")[:_METADATA_STR_LIMIT],
        "source": (finding.source or "")[:200],
        "source_type": (finding.source_type or "")[:50],
        "published_at": finding.published_at or "",
        "snippet": (finding.snippet or "")[:_SNIPPET_LIMIT],
        "content_preview": (finding.content or "")[:_METADATA_STR_LIMIT],
        "topic": (finding.topic or "")[:200],
        "category": finding.category or "",
        "collected_at": finding.collected_at or datetime.now(timezone.utc).isoformat(),
    }


# ---------------------------------------------------------------------------
# Upsert
# ---------------------------------------------------------------------------

def upsert_findings(
    findings: list[StoredFinding],
    embeddings: list[list[float]],
    pinecone_index: Optional[Any] = None,
) -> int:
    """Upsert findings with their embeddings into Pinecone.

    Args:
        findings: StoredFinding objects to store.
        embeddings: Embedding vectors, one per finding (must match length).
        pinecone_index: Injected Pinecone index object (for testing).
                        If None, connects using environment variables.

    Returns:
        Number of vectors upserted (0 for empty input).

    Raises:
        ValueError: On configuration error or findings/embeddings length mismatch.
    """
    if not findings:
        logger.info("upsert_findings: empty input — nothing to upsert")
        return 0

    if len(findings) != len(embeddings):
        raise ValueError(
            f"findings and embeddings length mismatch: "
            f"{len(findings)} findings vs {len(embeddings)} embeddings"
        )

    if pinecone_index is None:
        cfg = get_pinecone_config()
        if not cfg["api_key"]:
            raise ValueError("PINECONE_API_KEY is not configured")
        from pinecone import Pinecone
        pc = Pinecone(api_key=cfg["api_key"])
        pinecone_index = pc.Index(cfg["index_name"])

    vectors = [
        {
            "id": make_vector_id(f.url, f.title),
            "values": emb,
            "metadata": finding_to_metadata(f),
        }
        for f, emb in zip(findings, embeddings)
    ]

    try:
        pinecone_index.upsert(vectors=vectors)
        logger.info("upsert_findings: upserted %d vectors", len(vectors))
        return len(vectors)
    except Exception as exc:
        logger.error("upsert_findings failed | count=%d | error=%s", len(vectors), exc)
        raise


# ---------------------------------------------------------------------------
# Query
# ---------------------------------------------------------------------------

def query_index(
    query_embedding: list[float],
    top_k: int = 5,
    filter_: Optional[dict] = None,
    pinecone_index: Optional[Any] = None,
) -> list[Any]:
    """Query Pinecone for the top_k most similar vectors.

    Args:
        query_embedding: Query vector (must match index dimension).
        top_k: Number of results to return.
        filter_: Optional Pinecone metadata filter dict.
        pinecone_index: Injected Pinecone index object (for testing).

    Returns:
        List of match objects. Each has .id, .score, and .metadata attributes,
        or is a dict with the same keys when using dict-based mocks.

    Raises:
        ValueError: If Pinecone credentials are missing.
    """
    if pinecone_index is None:
        cfg = get_pinecone_config()
        if not cfg["api_key"]:
            raise ValueError("PINECONE_API_KEY is not configured")
        from pinecone import Pinecone
        pc = Pinecone(api_key=cfg["api_key"])
        pinecone_index = pc.Index(cfg["index_name"])

    kwargs: dict = {
        "vector": query_embedding,
        "top_k": top_k,
        "include_metadata": True,
    }
    if filter_:
        kwargs["filter"] = filter_

    try:
        response = pinecone_index.query(**kwargs)
        # Handle both dict (mock) and SDK QueryResponse object
        if isinstance(response, dict):
            matches = response.get("matches", [])
        else:
            matches = getattr(response, "matches", []) or []
        logger.info("query_index: got %d matches | top_k=%d", len(matches), top_k)
        return matches
    except Exception as exc:
        logger.error("query_index failed | top_k=%d | error=%s", top_k, exc)
        raise
