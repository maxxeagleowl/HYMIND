"""Serper search API wrapper for HYMIND with retry, timeout, and normalization."""

import logging
import os
import sys

import requests
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
    before_sleep_log,
)

from utils.logger import get_logger

logger = get_logger(__name__)

_TIMEOUT: int = 20
_MAX_RETRIES: int = 3
_DEFAULT_URL: str = "https://google.serper.dev/search"


class SerperRateLimitError(Exception):
    """HTTP 429 from Serper — retried by tenacity."""


class SerperServerError(Exception):
    """HTTP 5xx from Serper — retried by tenacity."""


def _get_api_key() -> str:
    """Return SERPER_API_KEY or exit with a clear message if it is missing."""
    key = os.getenv("SERPER_API_KEY", "").strip()
    if not key:
        logger.error(
            "SERPER_API_KEY is not set. "
            "Copy .env.example to .env and add your Serper key, "
            "then re-run the application."
        )
        sys.exit(1)
    return key


def _normalize(item: dict, query: str, rank: int, source_type: str) -> dict:
    """Map a raw Serper result item to the HYMIND shared result schema."""
    return {
        "title": (item.get("title") or "").strip(),
        "url": item.get("link") or "",
        "snippet": item.get("snippet") or "",
        "published_at": item.get("date"),
        "source": item.get("source") or "",
        "source_type": source_type,
        "search_query": query,
        "author": None,
        "rank": rank,
    }


@retry(
    retry=retry_if_exception_type((
        requests.Timeout,
        requests.ConnectionError,
        SerperRateLimitError,
        SerperServerError,
    )),
    stop=stop_after_attempt(_MAX_RETRIES),
    wait=wait_exponential(multiplier=1, min=2, max=15),
    before_sleep=before_sleep_log(logger, logging.WARNING),
    reraise=True,
)
def _call_serper(api_key: str, query: str, num_results: int, search_type: str) -> dict:
    """Execute one Serper POST request. Retried by tenacity on transient failures.

    Raises:
        SerperRateLimitError: On HTTP 429.
        SerperServerError: On HTTP 5xx.
        requests.HTTPError: On other non-2xx responses.
        requests.Timeout: On request timeout (retried).
        requests.ConnectionError: On network failure (retried).
    """
    url = os.getenv("SERPER_SEARCH_URL", _DEFAULT_URL)

    headers = {
        "X-API-KEY": api_key,
        "Content-Type": "application/json",
    }
    payload: dict = {"q": query, "num": num_results}
    if search_type != "search":
        payload["type"] = search_type

    logger.debug(
        "Serper HTTP POST | url=%s | query=%r | num=%d | type=%s",
        url,
        query,
        num_results,
        search_type,
    )

    response = requests.post(url, json=payload, headers=headers, timeout=_TIMEOUT)

    if response.status_code == 429:
        logger.warning("Serper rate limit | status=429 | query=%r", query)
        raise SerperRateLimitError("Serper API rate limit exceeded (HTTP 429)")

    if response.status_code >= 500:
        logger.warning("Serper server error | status=%d | query=%r", response.status_code, query)
        raise SerperServerError(f"Serper API server error (HTTP {response.status_code})")

    if not response.ok:
        logger.error(
            "Serper API error | status=%d | query=%r | body=%.200s",
            response.status_code,
            query,
            response.text,
        )
        raise requests.HTTPError(
            f"Serper API returned HTTP {response.status_code}", response=response
        )

    return response.json()


def search(
    query: str,
    num_results: int | None = None,
    search_type: str = "search",
) -> list[dict]:
    """Search Serper and return a normalized list of results.

    Normalized fields per result:
        title (str), url (str), snippet (str), published_at (str | None),
        source (str), source_type (str), search_query (str),
        author (None), rank (int)

    Args:
        query: Search query string. Empty queries return [] without an API call.
        num_results: Number of results to request. Defaults to MAX_SEARCH_RESULTS
            env var, or 10 if not set.
        search_type: Serper type — 'search' for organic, 'news' for news results.

    Returns:
        Normalized result list. Returns [] on empty query or zero API results.

    Raises:
        SystemExit: If SERPER_API_KEY is not configured.
        SerperRateLimitError: Re-raised after max retries on HTTP 429.
        SerperServerError: Re-raised after max retries on HTTP 5xx.
        requests.HTTPError: On non-retryable HTTP errors.
    """
    if not query or not query.strip():
        logger.warning("Serper search called with empty query — skipping")
        return []

    effective_num = num_results if num_results is not None else int(
        os.getenv("MAX_SEARCH_RESULTS", "10")
    )
    api_key = _get_api_key()
    clean_query = query.strip()

    logger.info(
        "Serper search | query=%r | num_results=%d | type=%s",
        clean_query,
        effective_num,
        search_type,
    )

    try:
        data = _call_serper(api_key, clean_query, effective_num, search_type)
    except (SerperRateLimitError, SerperServerError, requests.RequestException) as exc:
        logger.error("Serper search failed | query=%r | error=%s", clean_query, exc)
        raise

    results: list[dict] = []

    for rank, item in enumerate(data.get("organic") or [], start=1):
        results.append(_normalize(item, clean_query, rank, "organic"))

    # news type responses use a "news" key instead of "organic"
    news_start_rank = len(results) + 1
    for rank, item in enumerate(data.get("news") or [], start=news_start_rank):
        results.append(_normalize(item, clean_query, rank, "news"))

    logger.info(
        "Serper search complete | query=%r | results=%d",
        clean_query,
        len(results),
    )

    if not results:
        logger.warning("Serper returned zero results | query=%r", clean_query)

    return results
