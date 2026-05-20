"""Lightweight web crawler for HYMIND — article content extraction via requests + BeautifulSoup.

Designed for extracting article text from URLs discovered by Serper, NewsAPI, or RSS.
No browser automation. No JavaScript rendering. Graceful failure on all error conditions.
"""

import logging
import re
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup
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
_SNIPPET_LENGTH: int = 300
_MIN_PARAGRAPH_CHARS: int = 40
_MIN_CONTENT_CHARS: int = 100

_USER_AGENT: str = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)

_BOILERPLATE_TAGS: list[str] = [
    "script", "style", "noscript", "nav", "footer",
    "header", "aside", "form", "iframe",
]

# Tried in order — first match wins
_CONTENT_SELECTORS: list[str] = [
    "article",
    "main",
    '[role="main"]',
    ".article-body",
    ".article-content",
    ".entry-content",
    ".post-content",
    ".story-body",
    ".content-body",
]

_WHITESPACE_RE = re.compile(r"\n{3,}")


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _domain(url: str) -> str:
    """Return the netloc (host) portion of a URL, or the full URL on parse failure."""
    try:
        return urlparse(url).netloc or url
    except Exception:
        return url


def _meta_content(soup: BeautifulSoup, *attrs: str) -> str:
    """Return the content attribute of the first matching meta tag.

    Tries each attr as `property=` first, then as `name=`.
    """
    for attr in attrs:
        tag = soup.find("meta", property=attr) or soup.find("meta", attrs={"name": attr})
        if tag and tag.get("content"):
            return tag["content"].strip()
    return ""


def _page_title(soup: BeautifulSoup) -> str:
    """Extract the page title, preferring og:title over h1 over <title>."""
    og = _meta_content(soup, "og:title")
    if og:
        return og

    h1 = soup.find("h1")
    if h1:
        return h1.get_text(separator=" ").strip()

    title_tag = soup.find("title")
    if title_tag:
        return title_tag.get_text().strip()

    return ""


def _canonical_url(soup: BeautifulSoup, fallback: str) -> str:
    """Return the canonical URL from <link rel="canonical">, or fallback."""
    link = soup.find("link", rel="canonical")
    if link and link.get("href"):
        return link["href"].strip()
    return fallback


def _published_at(soup: BeautifulSoup) -> str | None:
    """Try to extract the article publication date from common meta patterns."""
    pub = _meta_content(soup, "article:published_time", "datePublished", "pubdate")
    if pub:
        return pub

    time_tag = soup.find("time", attrs={"datetime": True})
    if time_tag:
        return time_tag["datetime"]

    return None


def _remove_boilerplate(soup: BeautifulSoup) -> None:
    """Decompose known boilerplate elements in-place before extraction."""
    for tag_name in _BOILERPLATE_TAGS:
        for el in soup.find_all(tag_name):
            el.decompose()


def _paragraphs_from(element) -> str:
    """Extract paragraph-level text from an element, filtering noise.

    Tries structured paragraph tags first. Falls back to raw get_text() on the
    element if no qualifying paragraphs are found — handles sites that wrap
    content in <div> blocks without explicit <p> tags.
    """
    chunks: list[str] = []
    for tag in element.find_all(["p", "h1", "h2", "h3", "h4", "h5", "li"]):
        text = tag.get_text(separator=" ").strip()
        if len(text) >= _MIN_PARAGRAPH_CHARS:
            chunks.append(text)

    if chunks:
        return _WHITESPACE_RE.sub("\n\n", "\n\n".join(chunks)).strip()

    # Fallback for div-heavy layouts
    raw = _WHITESPACE_RE.sub("\n\n", element.get_text(separator="\n").strip())
    return raw


def _extract_content(soup: BeautifulSoup) -> str:
    """Find the main content region and return clean paragraph text."""
    for selector in _CONTENT_SELECTORS:
        element = soup.select_one(selector)
        if element:
            text = _paragraphs_from(element)
            if text:
                return text

    # Fallback: all paragraphs from body
    body = soup.find("body")
    if body:
        return _paragraphs_from(body)

    return ""


def _empty_result(url: str, reason: str = "") -> dict:
    """Return a failed-extraction result dict."""
    return {
        "title": "",
        "url": url,
        "content": "",
        "snippet": reason,
        "source": _domain(url),
        "source_type": "crawler",
        "published_at": None,
        "extraction_success": False,
        "content_length": 0,
    }


# ---------------------------------------------------------------------------
# HTTP fetch with retry
# ---------------------------------------------------------------------------

@retry(
    retry=retry_if_exception_type((requests.Timeout, requests.ConnectionError)),
    stop=stop_after_attempt(_MAX_RETRIES),
    wait=wait_fixed(_RETRY_WAIT),
    before_sleep=before_sleep_log(logger, logging.WARNING),
    reraise=True,
)
def _fetch(url: str) -> requests.Response:
    """Fetch a URL with timeout and a browser-like User-Agent.

    Follows redirects automatically. Raises on network failure (retried by
    tenacity). HTTP error codes are NOT raised here — handled by the caller.
    """
    return requests.get(
        url,
        timeout=_TIMEOUT,
        headers={
            "User-Agent": _USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
        },
    )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def crawl(url: str) -> dict:
    """Crawl a single URL and extract article content.

    Always returns a result dict — never raises. Set extraction_success=False
    on any failure so callers can continue processing without try/except.

    Returned fields:
        title (str), url (str), content (str), snippet (str),
        source (str), source_type ("crawler"), published_at (str|None),
        extraction_success (bool), content_length (int)

    Args:
        url: Article page URL to crawl.

    Returns:
        Result dict. content and title are empty strings on failure.
        snippet contains a short failure reason on extraction failure.
    """
    logger.info("Crawler request | url=%s", url)

    # --- Fetch ---
    try:
        response = _fetch(url)
    except requests.Timeout:
        logger.error("Crawler timeout | url=%s", url)
        return _empty_result(url, "fetch timeout")
    except requests.ConnectionError as exc:
        logger.error("Crawler connection error | url=%s | error=%s", url, exc)
        return _empty_result(url, "connection error")
    except Exception as exc:
        logger.error("Crawler unexpected fetch error | url=%s | error=%s", url, exc)
        return _empty_result(url, "unexpected fetch error")

    final_url = response.url

    # --- HTTP status ---
    if response.status_code == 404:
        logger.warning("Crawler 404 | url=%s", url)
        return _empty_result(final_url, "HTTP 404 not found")

    if response.status_code == 403:
        logger.warning("Crawler 403 blocked | url=%s", url)
        return _empty_result(final_url, "HTTP 403 access blocked")

    if not response.ok:
        logger.warning(
            "Crawler HTTP error | url=%s | status=%d", url, response.status_code
        )
        return _empty_result(final_url, f"HTTP {response.status_code}")

    # --- Content-type guard ---
    content_type = response.headers.get("Content-Type", "")
    if content_type and "html" not in content_type.lower():
        logger.warning(
            "Crawler non-HTML content | url=%s | content_type=%s", url, content_type
        )
        return _empty_result(final_url, f"non-HTML content ({content_type.split(';')[0].strip()})")

    # --- Parse ---
    try:
        soup = BeautifulSoup(response.content, "lxml")
    except Exception as exc:
        logger.error("Crawler parse error | url=%s | error=%s", url, exc)
        return _empty_result(final_url, "HTML parse error")

    _remove_boilerplate(soup)

    title = _page_title(soup)
    canonical = _canonical_url(soup, final_url)
    meta_desc = _meta_content(soup, "og:description", "description")
    published_at = _published_at(soup)
    content = _extract_content(soup)

    extraction_success = len(content) >= _MIN_CONTENT_CHARS
    snippet = content[:_SNIPPET_LENGTH] if content else meta_desc[:_SNIPPET_LENGTH]

    logger.info(
        "Crawler result | url=%s | title=%.50r | content_length=%d | success=%s",
        url,
        title,
        len(content),
        extraction_success,
    )

    if not extraction_success:
        logger.warning(
            "Crawler low content | url=%s | content_length=%d", url, len(content)
        )

    return {
        "title": title,
        "url": canonical,
        "content": content,
        "snippet": snippet,
        "source": _domain(final_url),
        "source_type": "crawler",
        "published_at": published_at,
        "extraction_success": extraction_success,
        "content_length": len(content),
    }


def crawl_many(urls: list[str]) -> list[dict]:
    """Crawl multiple URLs sequentially and return all results including failures.

    All results are included in the return value. Callers should filter by
    extraction_success if they need only successfully extracted pages.

    Args:
        urls: List of article page URLs to crawl.

    Returns:
        List of result dicts in the same order as the input URLs.
    """
    if not urls:
        logger.warning("crawl_many called with empty URL list")
        return []

    logger.info("Crawler batch start | urls=%d", len(urls))
    results = [crawl(url) for url in urls]
    successful = sum(1 for r in results if r["extraction_success"])
    logger.info(
        "Crawler batch complete | urls=%d | successful=%d | failed=%d",
        len(urls),
        successful,
        len(urls) - successful,
    )
    return results
