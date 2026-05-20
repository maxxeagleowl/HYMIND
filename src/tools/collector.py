"""Collector abstraction and shared validation for HYMIND research tools.

Provides:
  - CollectorProtocol: structural type interface for all source collectors
  - validate_result: single-item schema validator
  - validate_results: batch filter that drops invalid items
  - strip_html: shared HTML cleaning utility

All HYMIND search collectors (NewsAPI, Serper, RSS) satisfy CollectorProtocol
because they expose a callable with signature (query: str, **kwargs) -> list[dict].

The shared 9-field normalized schema:
    title (str), url (str), snippet (str), published_at (str | None),
    source (str), source_type (str), search_query (str),
    author (str | None), rank (int)
"""

import re
from typing import Any, Protocol, runtime_checkable

from utils.logger import get_logger

logger = get_logger(__name__)

_HTML_TAG_RE = re.compile(r"<[^>]+>")
_WHITESPACE_RE = re.compile(r"\s+")

# The shared normalized schema field set used by all collectors
REQUIRED_FIELDS = frozenset({
    "title", "url", "snippet", "published_at",
    "source", "source_type", "search_query", "author", "rank",
})


@runtime_checkable
class CollectorProtocol(Protocol):
    """Structural interface satisfied by all HYMIND research collector callables.

    Any callable with the signature (query: str, **kwargs) -> list[dict] satisfies
    this protocol without subclassing. Module-level search() functions are the
    primary implementors.

    Current implementors:
        tools.news_api.search
        tools.serper_search.search

    Planned future implementors:
        Serper news type, additional news sources, domain-specific crawlers.

    Contract: Each returned dict must contain exactly REQUIRED_FIELDS keys.
    Empty query, missing API key, or zero results must return [] (not raise).
    """

    def __call__(self, query: str, **kwargs: Any) -> list[dict]:
        """Collect research results for the given topic query.

        Args:
            query: Research topic or keyword string.
            **kwargs: Source-specific options such as page size, language,
                      sort order, or date range.

        Returns:
            Normalized result list where each item has REQUIRED_FIELDS keys.
            Returns [] on empty query, missing API key, or zero results.
        """
        ...


def strip_html(text: str) -> str:
    """Remove HTML tags and collapse whitespace from a text string.

    Args:
        text: Raw text that may contain HTML tags.

    Returns:
        Plain text with tags removed and whitespace normalized.
    """
    text = _HTML_TAG_RE.sub(" ", text or "")
    return _WHITESPACE_RE.sub(" ", text).strip()


def validate_result(result: dict) -> tuple[bool, list[str]]:
    """Validate one normalized result dict against the shared 9-field schema.

    Checks performed:
    - All 9 required fields are present
    - url is non-empty (results without URLs are not traceable)
    - source_type is non-empty
    - snippet does not contain raw HTML tags

    Args:
        result: A single normalized result dict from any collector.

    Returns:
        (is_valid, issues): (True, []) if all checks pass.
                            (False, [description, ...]) if any check fails.
    """
    issues: list[str] = []

    missing = REQUIRED_FIELDS - set(result.keys())
    if missing:
        issues.append(f"missing fields: {sorted(missing)}")

    if not result.get("url"):
        issues.append("url is empty — result is not traceable")

    if not result.get("source_type"):
        issues.append("source_type is empty")

    snippet = result.get("snippet") or ""
    if "<" in snippet and ">" in snippet:
        issues.append("snippet may contain HTML tags")

    return len(issues) == 0, issues


def validate_results(results: list[dict]) -> list[dict]:
    """Filter a result list, dropping and logging any invalid entries.

    Invalid entries (empty URL, missing required fields, HTML snippets) are
    logged as warnings and excluded from the returned list. Valid entries are
    returned in their original order.

    Args:
        results: List of normalized result dicts from any collector.

    Returns:
        Filtered list containing only results that pass validate_result.
    """
    valid: list[dict] = []
    for i, result in enumerate(results):
        ok, issues = validate_result(result)
        if ok:
            valid.append(result)
        else:
            logger.warning(
                "validate_results: dropping index=%d | url=%r | issues=%s",
                i,
                result.get("url", ""),
                "; ".join(issues),
            )

    dropped = len(results) - len(valid)
    if dropped:
        logger.info(
            "validate_results: %d/%d passed | %d dropped",
            len(valid),
            len(results),
            dropped,
        )

    return valid
