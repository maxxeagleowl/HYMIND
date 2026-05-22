"""Persistent URL tracker — prevents reprocessing articles across runs.

Strategy:
  filter_new  — Pinecone fetch by vector ID (primary) → SQLite fallback.
  mark_seen   — Pinecone already handles storage via the store_findings_in_pinecone
                workflow node (which runs before finalize_state). SQLite is written
                only when Pinecone is not configured.

Why fetch by vector ID and not metadata filter:
  Vector IDs are deterministic SHA-256 hashes of the URL (see pinecone_store.make_vector_id).
  fetch() checks existence by ID without needing a query embedding — fast, cheap, exact.
"""

import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from utils.logger import get_logger

logger = get_logger(__name__)

_DB_PATH: Path = Path("data/seen_urls.db")
_PINECONE_FETCH_BATCH: int = 100


def _normalize(url: str) -> str:
    return url.strip().rstrip("/").lower()


# ---------------------------------------------------------------------------
# SQLite
# ---------------------------------------------------------------------------

def _connect(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS seen_urls (
            url         TEXT PRIMARY KEY,
            first_seen  TEXT NOT NULL,
            source_type TEXT
        )
        """
    )
    conn.commit()
    return conn


def _filter_new_sqlite(results: list[dict], db_path: Path) -> tuple[list[dict], int]:
    if not results:
        return [], 0
    try:
        conn = _connect(db_path)
        keys = [_normalize(r.get("url", "")) for r in results]
        placeholders = ",".join("?" * len(keys))
        seen: set[str] = {
            row[0]
            for row in conn.execute(
                f"SELECT url FROM seen_urls WHERE url IN ({placeholders})", keys
            )
        }
        conn.close()
    except Exception as exc:
        logger.warning("url_tracker: SQLite filter error — skipped | error=%s", exc)
        return results, 0

    new_results = [r for r in results if _normalize(r.get("url", "")) not in seen]
    skipped = len(results) - len(new_results)
    if skipped:
        logger.info("url_tracker: SQLite filtered %d seen URLs | new=%d", skipped, len(new_results))
    return new_results, skipped


def _mark_seen_sqlite(results: list[dict], db_path: Path) -> int:
    if not results:
        return 0
    now = datetime.now(timezone.utc).isoformat()
    rows = [
        (_normalize(r.get("url", "")), now, r.get("source_type", ""))
        for r in results
        if r.get("url", "").strip()
    ]
    if not rows:
        return 0
    try:
        conn = _connect(db_path)
        conn.executemany(
            "INSERT OR IGNORE INTO seen_urls (url, first_seen, source_type) VALUES (?, ?, ?)",
            rows,
        )
        conn.commit()
        conn.close()
        logger.info("url_tracker: SQLite stored %d URLs", len(rows))
        return len(rows)
    except Exception as exc:
        logger.warning("url_tracker: SQLite store error | error=%s", exc)
        return 0


# ---------------------------------------------------------------------------
# Pinecone
# ---------------------------------------------------------------------------

def _filter_new_pinecone(
    results: list[dict],
    pinecone_index: Optional[Any],
) -> tuple[list[dict], int]:
    """Check which URLs already exist in Pinecone using fetch by vector ID.

    Does not embed anything — vector IDs are deterministic hashes so existence
    can be checked with fetch() alone.

    Raises on any Pinecone error so the caller can fall back to SQLite.
    """
    from rag.pinecone_store import get_pinecone_config, make_vector_id

    if pinecone_index is None:
        cfg = get_pinecone_config()
        from pinecone import Pinecone
        pinecone_index = Pinecone(api_key=cfg["api_key"]).Index(cfg["index_name"])

    # Build {vector_id: result} map — only for results that have a URL
    id_to_result: dict[str, dict] = {
        make_vector_id(r["url"].strip()): r
        for r in results
        if r.get("url", "").strip()
    }
    if not id_to_result:
        return results, 0

    # Batch fetch to check existence
    all_ids = list(id_to_result.keys())
    existing_ids: set[str] = set()

    for i in range(0, len(all_ids), _PINECONE_FETCH_BATCH):
        batch = all_ids[i : i + _PINECONE_FETCH_BATCH]
        response = pinecone_index.fetch(ids=batch)
        vectors = (
            response.get("vectors", {})
            if isinstance(response, dict)
            else getattr(response, "vectors", {})
        )
        existing_ids.update(vectors.keys())

    from rag.pinecone_store import make_vector_id as _vid
    new_results = [
        r for r in results
        if not r.get("url", "").strip() or _vid(r["url"].strip()) not in existing_ids
    ]
    skipped = len(results) - len(new_results)
    if skipped:
        logger.info(
            "url_tracker: Pinecone filtered %d seen URLs | new=%d",
            skipped,
            len(new_results),
        )
    return new_results, skipped


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def filter_new(
    results: list[dict],
    db_path: Path = _DB_PATH,
    pinecone_index: Optional[Any] = None,
) -> tuple[list[dict], int]:
    """Remove results whose URLs were seen in a previous run.

    Pinecone fetch is attempted first; falls back to SQLite on any error or
    when Pinecone is not configured.

    Args:
        results: Result dicts, each with a 'url' key.
        db_path: SQLite fallback database path.
        pinecone_index: Injected Pinecone index (for testing).

    Returns:
        Tuple of (new_results, skipped_count).
    """
    from rag.pinecone_store import is_pinecone_configured

    if is_pinecone_configured():
        try:
            return _filter_new_pinecone(results, pinecone_index=pinecone_index)
        except Exception as exc:
            logger.warning(
                "url_tracker: Pinecone check failed — falling back to SQLite | error=%s", exc
            )

    return _filter_new_sqlite(results, db_path)


def mark_seen(
    results: list[dict],
    db_path: Path = _DB_PATH,
) -> int:
    """Persist result URLs into SQLite.

    SQLite is always written regardless of Pinecone state so that the fallback
    is populated and useful if Pinecone becomes unavailable in a future run.

    Args:
        results: Result dicts, each with a 'url' key.
        db_path: SQLite database path.

    Returns:
        Number of URLs written to SQLite.
    """
    return _mark_seen_sqlite(results, db_path)
