"""URL normalization and merge-deduplicate logic tests."""

import pytest

from workflows.research_workflow import _normalize_url, merge_and_deduplicate
from workflows.state import initial_state


# ---------------------------------------------------------------------------
# _normalize_url
# ---------------------------------------------------------------------------

def test_normalize_url_strips_trailing_slash():
    assert _normalize_url("https://example.com/path/") == "https://example.com/path"


def test_normalize_url_lowercases_scheme_and_host():
    assert _normalize_url("HTTPS://Example.COM/Path") == "https://example.com/path"


def test_normalize_url_strips_surrounding_whitespace():
    assert _normalize_url("  https://example.com  ") == "https://example.com"


def test_normalize_url_trailing_slash_and_lowercase_combined():
    assert _normalize_url("  HTTPS://Example.com/path/  ") == "https://example.com/path"


def test_normalize_url_empty_string():
    assert _normalize_url("") == ""


def test_normalize_url_no_path():
    assert _normalize_url("https://example.com") == "https://example.com"


# ---------------------------------------------------------------------------
# merge_and_deduplicate node
# ---------------------------------------------------------------------------

def _make_result(url: str, source_type: str = "organic") -> dict:
    return {
        "title": "Test", "url": url, "snippet": "S",
        "published_at": None, "source": "Test",
        "source_type": source_type, "search_query": "q",
        "author": None, "rank": 1,
    }


def test_exact_duplicate_urls_removed():
    state = {
        **initial_state("test"),
        "serper_results": [_make_result("https://example.com/a")],
        "news_results": [_make_result("https://example.com/a")],
        "rss_results": [],
    }
    result = merge_and_deduplicate(state)
    assert len(result["merged_results"]) == 1


def test_trailing_slash_variants_deduplicated():
    state = {
        **initial_state("test"),
        "serper_results": [_make_result("https://example.com/path/")],
        "news_results": [_make_result("https://example.com/path")],
        "rss_results": [],
    }
    result = merge_and_deduplicate(state)
    assert len(result["merged_results"]) == 1


def test_unique_urls_all_preserved():
    state = {
        **initial_state("test"),
        "serper_results": [_make_result("https://a.com")],
        "news_results": [_make_result("https://b.com")],
        "rss_results": [_make_result("https://c.com")],
    }
    result = merge_and_deduplicate(state)
    assert len(result["merged_results"]) == 3


def test_empty_url_items_dropped():
    state = {
        **initial_state("test"),
        "serper_results": [_make_result("")],
        "news_results": [_make_result("https://b.com")],
        "rss_results": [],
    }
    result = merge_and_deduplicate(state)
    # Empty URL item is discarded, only the valid URL survives
    assert len(result["merged_results"]) == 1
    assert result["merged_results"][0]["url"] == "https://b.com"


def test_all_empty_sources_returns_empty_list():
    state = initial_state("test")
    result = merge_and_deduplicate(state)
    assert result["merged_results"] == []


def test_source_order_preserved_serper_first():
    """Results from earlier sources appear before later sources in merged output."""
    state = {
        **initial_state("test"),
        "serper_results": [_make_result("https://serper.com")],
        "news_results": [_make_result("https://news.com")],
        "rss_results": [_make_result("https://rss.com")],
    }
    result = merge_and_deduplicate(state)
    urls = [r["url"] for r in result["merged_results"]]
    assert urls.index("https://serper.com") < urls.index("https://news.com")
    assert urls.index("https://news.com") < urls.index("https://rss.com")


def test_many_duplicates_across_all_sources():
    shared = "https://shared.com/article"
    state = {
        **initial_state("test"),
        "serper_results": [_make_result(shared), _make_result("https://unique-a.com")],
        "news_results": [_make_result(shared), _make_result("https://unique-b.com")],
        "rss_results": [_make_result(shared), _make_result("https://unique-c.com")],
    }
    result = merge_and_deduplicate(state)
    urls = [r["url"] for r in result["merged_results"]]
    # shared appears once + 3 unique = 4 total
    assert len(urls) == 4
    assert urls.count(shared) == 1


def test_first_occurrence_of_duplicate_is_kept():
    """When deduplicating, the first occurrence (Serper) should be in the result."""
    state = {
        **initial_state("test"),
        "serper_results": [_make_result("https://x.com", source_type="organic")],
        "news_results": [_make_result("https://x.com", source_type="news")],
        "rss_results": [],
    }
    result = merge_and_deduplicate(state)
    assert len(result["merged_results"]) == 1
    assert result["merged_results"][0]["source_type"] == "organic"
