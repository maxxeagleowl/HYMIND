"""RSS feed reader for HYMIND with timeout, graceful failure, and normalization.

Result schema matches serper_search.py and news_api.py so outputs from all three
tools can be merged into a single list by downstream workflow nodes.
"""

import logging
import re
from urllib.parse import urlparse

import feedparser
import requests
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_fixed,
    before_sleep_log,
)

from utils.logger import get_logger

logger = get_logger(__name__)

_TIMEOUT: int = 20
_MAX_RETRIES: int = 2
_RETRY_WAIT: int = 3
_USER_AGENT: str = "HYMIND/0.1 (hydrogen market intelligence)"

_HTML_TAG_RE = re.compile(r"<[^>]+>")
_WHITESPACE_RE = re.compile(r"\s+")

DEFAULT_HYDROGEN_FEEDS: list[str] = [
    "https://www.hydrogeninsight.com/rss",
    "https://www.h2-view.com/feed/",
    "https://fuelcellsworks.com/feed/",
]


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _strip_html(text: str) -> str:
    """Remove HTML tags and collapse whitespace from a text string."""
    text = _HTML_TAG_RE.sub(" ", text or "")
    return _WHITESPACE_RE.sub(" ", text).strip()


def _source_name(parsed: feedparser.FeedParserDict, url: str) -> str:
    """Return the feed title, falling back to the URL domain."""
    title = (getattr(parsed.feed, "title", None) or "").strip()
    if title:
        return title
    try:
        return urlparse(url).netloc or url
    except Exception:
        return url


def _normalize_entry(
    entry: feedparser.FeedParserDict,
    query: str,
    source: str,
    rank: int,
) -> dict:
    """Map a feedparser entry to the HYMIND shared result schema."""
    snippet_raw = entry.get("summary") or entry.get("description") or ""
    published_at = entry.get("published") or entry.get("updated") or None

    return {
        "title": (entry.get("title") or "").strip(),
        "url": entry.get("link") or "",
        "snippet": _strip_html(snippet_raw)[:500],  # cap to avoid huge blobs
        "published_at": published_at,
        "source": source,
        "source_type": "rss",
        "search_query": query,
        "author": entry.get("author") or None,
        "rank": rank,
    }


@retry(
    retry=retry_if_exception_type((requests.Timeout, requests.ConnectionError)),
    stop=stop_after_attempt(_MAX_RETRIES),
    wait=wait_fixed(_RETRY_WAIT),
    before_sleep=before_sleep_log(logger, logging.WARNING),
    reraise=True,
)
def _fetch_content(url: str) -> bytes:
    """Fetch raw feed bytes with explicit timeout.

    Using requests rather than feedparser.parse(url) so that timeout is
    enforced at the HTTP layer and not left to feedparser's defaults.

    Raises:
        requests.Timeout: If the server does not respond within _TIMEOUT seconds.
        requests.ConnectionError: On network failure.
        requests.HTTPError: On non-2xx responses (not retried).
    """
    response = requests.get(
        url,
        timeout=_TIMEOUT,
        headers={"User-Agent": _USER_AGENT},
    )
    response.raise_for_status()
    return response.content


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def read_feed(
    url: str,
    topic: str = "",
    max_entries: int | None = None,
    rank_offset: int = 0,
) -> list[dict]:
    """Read a single RSS feed and return normalized entries.

    Failures are contained: network errors and parse errors are logged and an
    empty list is returned so callers (including read_feeds) can continue with
    other feeds.

    Malformed feeds (feedparser bozo=True) are logged as warnings but still
    processed — feedparser is resilient and usually extracts valid entries even
    from technically invalid XML.

    Args:
        url: RSS/Atom feed URL.
        topic: Label written into the search_query field. Defaults to the URL.
        max_entries: Cap on entries per feed. None means no limit.
        rank_offset: Starting offset for rank values (rank_offset + 1 is rank 1).
            Used by read_feeds to maintain global ranks across multiple feeds.

    Returns:
        Normalized entry list. Returns [] if the feed is unavailable or empty.
    """
    query = topic or url
    logger.info("RSS feed start | url=%s", url)

    # --- Fetch ---
    try:
        content = _fetch_content(url)
    except requests.Timeout:
        logger.error("RSS fetch timeout | url=%s", url)
        return []
    except requests.ConnectionError as exc:
        logger.error("RSS fetch connection error | url=%s | error=%s", url, exc)
        return []
    except requests.HTTPError as exc:
        logger.error("RSS fetch HTTP error | url=%s | status=%s", url, exc.response.status_code if exc.response is not None else "?")
        return []
    except Exception as exc:
        logger.error("RSS fetch unexpected error | url=%s | error=%s", url, exc)
        return []

    # --- Parse ---
    try:
        parsed = feedparser.parse(content)
    except Exception as exc:
        logger.error("RSS parse error | url=%s | error=%s", url, exc)
        return []

    if parsed.bozo:
        logger.warning(
            "RSS malformed feed (bozo) | url=%s | reason=%s",
            url,
            type(parsed.bozo_exception).__name__ if parsed.bozo_exception else "unknown",
        )

    source = _source_name(parsed, url)
    entries = parsed.entries or []

    if max_entries is not None:
        entries = entries[:max_entries]

    # --- Normalize ---
    results: list[dict] = []
    for i, entry in enumerate(entries):
        normalized = _normalize_entry(entry, query, source, rank=rank_offset + i + 1)
        if not normalized["title"] and not normalized["url"]:
            logger.debug("RSS skipped entry with no title and no url | url=%s | i=%d", url, i)
            continue
        results.append(normalized)

    logger.info(
        "RSS feed complete | url=%s | source=%r | entries_parsed=%d | results=%d",
        url,
        source,
        len(entries),
        len(results),
    )

    if not results:
        logger.warning("RSS feed returned zero usable entries | url=%s", url)

    return results


def read_feeds(
    feed_urls: list[str],
    topic: str = "",
    max_per_feed: int | None = None,
) -> list[dict]:
    """Read multiple RSS feeds and return a single combined, globally ranked list.

    Feeds are processed in order. If a feed fails, it is skipped and processing
    continues with the remaining feeds. Global rank is maintained across all feeds.

    Args:
        feed_urls: List of RSS/Atom feed URLs.
        topic: Label written into the search_query field for all entries.
        max_per_feed: Cap on entries per individual feed. None means no limit.

    Returns:
        Combined normalized list from all feeds. Empty list if all feeds fail.
    """
    if not feed_urls:
        logger.warning("RSS read_feeds called with empty feed list")
        return []

    logger.info("RSS multi-feed start | feeds=%d", len(feed_urls))

    all_results: list[dict] = []
    for url in feed_urls:
        feed_results = read_feed(
            url,
            topic=topic,
            max_entries=max_per_feed,
            rank_offset=len(all_results),
        )
        all_results.extend(feed_results)

    logger.info(
        "RSS multi-feed complete | feeds=%d | total_results=%d",
        len(feed_urls),
        len(all_results),
    )
    return all_results
