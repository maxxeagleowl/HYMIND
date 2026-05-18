"""NewsAPI client wrapper for HYMIND with retry, timeout, and normalization.

Result schema matches src/hymind/tools/serper_search.py so outputs from both
tools can be merged into a single list by downstream workflow nodes.
"""

import logging
import os
import re
import sys

import requests
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
    before_sleep_log,
)

from hymind.utils.logger import get_logger

logger = get_logger(__name__)

_TIMEOUT: int = 20
_MAX_RETRIES: int = 3
_BASE_URL: str = "https://newsapi.org/v2"
_REMOVED_SENTINEL: str = "[Removed]"

_HTML_TAG_RE = re.compile(r"<[^>]+>")
_WHITESPACE_RE = re.compile(r"\s+")


def _strip_html(text: str) -> str:
    """Remove HTML tags and collapse whitespace from a snippet string."""
    text = _HTML_TAG_RE.sub(" ", text or "")
    return _WHITESPACE_RE.sub(" ", text).strip()


class NewsAPIRateLimitError(Exception):
    """HTTP 429 or application-level rate limit — retried by tenacity."""


class NewsAPIServerError(Exception):
    """HTTP 5xx from NewsAPI — retried by tenacity."""


class NewsAPIError(Exception):
    """Non-retryable NewsAPI application error (bad key, source not found, etc.)."""


def _get_api_key() -> str:
    """Return NEWS_API_KEY or exit with a clear message if it is missing."""
    key = os.getenv("NEWS_API_KEY", "").strip()
    if not key:
        logger.error(
            "NEWS_API_KEY is not set. "
            "Copy .env.example to .env and add your NewsAPI key, "
            "then re-run the application."
        )
        sys.exit(1)
    return key


def _is_removed(article: dict) -> bool:
    """Return True if NewsAPI has removed this article (placeholder content)."""
    return (
        (article.get("title") or "") == _REMOVED_SENTINEL
        or (article.get("description") or "") == _REMOVED_SENTINEL
    )


def _normalize(article: dict, query: str, rank: int) -> dict:
    """Map a raw NewsAPI article to the HYMIND shared result schema."""
    source_name = ""
    if isinstance(article.get("source"), dict):
        source_name = article["source"].get("name") or ""

    return {
        "title": (article.get("title") or "").strip(),
        "url": article.get("url") or "",
        "snippet": _strip_html(article.get("description") or ""),
        "published_at": article.get("publishedAt"),
        "source": source_name,
        "source_type": "news",
        "search_query": query,
        "author": article.get("author"),
        "rank": rank,
    }


@retry(
    retry=retry_if_exception_type((
        requests.Timeout,
        requests.ConnectionError,
        NewsAPIRateLimitError,
        NewsAPIServerError,
    )),
    stop=stop_after_attempt(_MAX_RETRIES),
    wait=wait_exponential(multiplier=1, min=2, max=15),
    before_sleep=before_sleep_log(logger, logging.WARNING),
    reraise=True,
)
def _call_newsapi(
    api_key: str,
    query: str,
    page_size: int,
    language: str,
    sort_by: str,
) -> dict:
    """Execute one NewsAPI GET request. Retried by tenacity on transient failures.

    The API key is sent as a header (X-Api-Key) rather than a query parameter
    so it does not appear in server access logs or debug output.

    Raises:
        NewsAPIRateLimitError: On HTTP 429 or application-level rateLimited code.
        NewsAPIServerError: On HTTP 5xx.
        NewsAPIError: On non-retryable application errors (bad key, invalid query, etc.).
        requests.HTTPError: On other unexpected HTTP errors.
        requests.Timeout: On request timeout (retried).
        requests.ConnectionError: On network failure (retried).
    """
    base = os.getenv("NEWS_API_BASE_URL", _BASE_URL)
    url = f"{base}/everything"

    headers = {"X-Api-Key": api_key}
    params = {
        "q": query,
        "language": language,
        "sortBy": sort_by,
        "pageSize": page_size,
    }

    logger.debug(
        "NewsAPI GET /everything | query=%r | pageSize=%d | language=%s | sortBy=%s",
        query,
        page_size,
        language,
        sort_by,
    )

    response = requests.get(url, params=params, headers=headers, timeout=_TIMEOUT)

    if response.status_code == 429:
        logger.warning("NewsAPI rate limit | status=429 | query=%r", query)
        raise NewsAPIRateLimitError("NewsAPI rate limit exceeded (HTTP 429)")

    if response.status_code >= 500:
        logger.warning(
            "NewsAPI server error | status=%d | query=%r", response.status_code, query
        )
        raise NewsAPIServerError(f"NewsAPI server error (HTTP {response.status_code})")

    if not response.ok:
        logger.error(
            "NewsAPI HTTP error | status=%d | query=%r | body=%.200s",
            response.status_code,
            query,
            response.text,
        )
        raise requests.HTTPError(
            f"NewsAPI returned HTTP {response.status_code}", response=response
        )

    try:
        data = response.json()
    except ValueError as exc:
        logger.error(
            "NewsAPI JSON decode error | status=%d | query=%r | error=%s",
            response.status_code,
            query,
            exc,
        )
        raise

    # NewsAPI signals application errors via the response body even on HTTP 200
    if data.get("status") == "error":
        code = data.get("code", "unknown")
        message = data.get("message", "no message")
        logger.error("NewsAPI application error | code=%s | message=%s", code, message)
        if code in ("rateLimited", "maximumResultsReached"):
            raise NewsAPIRateLimitError(f"NewsAPI rate limit: {message}")
        raise NewsAPIError(f"NewsAPI error [{code}]: {message}")

    return data


def search(
    query: str,
    num_results: int | None = None,
    language: str = "en",
    sort_by: str = "publishedAt",
) -> list[dict]:
    """Search NewsAPI and return a normalized list of articles.

    Normalized fields match the Serper schema so results can be merged:
        title (str), url (str), snippet (str), published_at (str | None),
        source (str), source_type (str), search_query (str),
        author (str | None), rank (int)

    Removed articles (NewsAPI placeholder content) are filtered out.
    Articles with no title or URL are skipped.

    Args:
        query: Search query string. Empty queries return [] without an API call.
        num_results: Number of articles to request. Defaults to MAX_ARTICLES_PER_RUN
            env var, or 10 if not set.
        language: ISO 639-1 language code. Defaults to 'en'.
        sort_by: NewsAPI sort order — 'publishedAt', 'relevancy', or 'popularity'.

    Returns:
        Normalized article list. Returns [] on empty query or zero results.

    Raises:
        SystemExit: If NEWS_API_KEY is not configured.
        NewsAPIRateLimitError: Re-raised after max retries.
        NewsAPIServerError: Re-raised after max retries.
        NewsAPIError: On non-retryable application errors.
        requests.HTTPError: On unexpected HTTP errors.
    """
    if not query or not query.strip():
        logger.warning("NewsAPI search called with empty query — skipping")
        return []

    effective_num = num_results if num_results is not None else int(
        os.getenv("MAX_ARTICLES_PER_RUN", "10")
    )
    api_key = _get_api_key()
    clean_query = query.strip()

    logger.info(
        "NewsAPI search | query=%r | num_results=%d | language=%s | sort=%s",
        clean_query,
        effective_num,
        language,
        sort_by,
    )

    try:
        data = _call_newsapi(api_key, clean_query, effective_num, language, sort_by)
    except (NewsAPIRateLimitError, NewsAPIServerError, requests.RequestException) as exc:
        logger.error("NewsAPI search failed | query=%r | error=%s", clean_query, exc)
        raise

    total_available = data.get("totalResults", 0)
    logger.debug("NewsAPI total available | query=%r | total=%d", clean_query, total_available)

    results: list[dict] = []
    rank = 1
    for article in data.get("articles") or []:
        if _is_removed(article):
            logger.debug("NewsAPI skipped removed article | rank=%d", rank)
            continue
        if not article.get("title") or not article.get("url"):
            logger.debug("NewsAPI skipped article with missing title or url | rank=%d", rank)
            continue
        results.append(_normalize(article, clean_query, rank))
        rank += 1

    logger.info(
        "NewsAPI search complete | query=%r | results=%d | total_available=%d",
        clean_query,
        len(results),
        total_available,
    )

    if not results:
        logger.warning("NewsAPI returned zero usable results | query=%r", clean_query)

    return results
