"""Schema consistency tests — all collection tools must produce identical field sets."""

import feedparser
import pytest

from tools.serper_search import _normalize as serper_normalize
from tools.news_api import _normalize as news_normalize
from tools.rss_reader import _normalize_entry as rss_normalize

EXPECTED_KEYS = frozenset({
    "title", "url", "snippet", "published_at",
    "source", "source_type", "search_query", "author", "rank",
})


# ---------------------------------------------------------------------------
# Individual schema checks
# ---------------------------------------------------------------------------

def test_serper_schema_keys():
    result = serper_normalize(
        {"title": "T", "link": "https://x.com", "snippet": "S"},
        query="hydrogen", rank=1, source_type="organic",
    )
    assert set(result.keys()) == EXPECTED_KEYS


def test_news_api_schema_keys():
    result = news_normalize(
        {
            "title": "T", "url": "https://x.com", "description": "S",
            "publishedAt": "2026-01-01T00:00:00Z",
            "source": {"name": "Reuters"}, "author": "Jane Doe",
        },
        query="hydrogen", rank=1,
    )
    assert set(result.keys()) == EXPECTED_KEYS


def test_rss_schema_keys():
    entry = feedparser.FeedParserDict(
        {"title": "T", "link": "https://x.com", "summary": "S"}
    )
    result = rss_normalize(entry, query="hydrogen", source="TestFeed", rank=1)
    assert set(result.keys()) == EXPECTED_KEYS


def test_all_three_schemas_identical():
    """The core contract: all three tools produce exactly the same field set."""
    serper = set(
        serper_normalize({"title": "T", "link": "U"}, "q", 1, "organic").keys()
    )
    news = set(
        news_normalize({"title": "T", "url": "U", "description": "S"}, "q", 1).keys()
    )
    rss_entry = feedparser.FeedParserDict({"title": "T", "link": "U"})
    rss = set(rss_normalize(rss_entry, "q", "Feed", 1).keys())

    assert serper == news == rss == EXPECTED_KEYS


# ---------------------------------------------------------------------------
# source_type values
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("source_type", ["organic", "news"])
def test_serper_source_type_passthrough(source_type):
    result = serper_normalize({"title": "T", "link": "U"}, "q", 1, source_type)
    assert result["source_type"] == source_type


def test_news_api_source_type_is_news():
    result = news_normalize({"title": "T", "url": "U"}, "q", 1)
    assert result["source_type"] == "news"


def test_rss_source_type_is_rss():
    entry = feedparser.FeedParserDict({"title": "T", "link": "U"})
    result = rss_normalize(entry, "q", "Feed", 1)
    assert result["source_type"] == "rss"


# ---------------------------------------------------------------------------
# Field value mapping
# ---------------------------------------------------------------------------

def test_serper_maps_link_to_url():
    result = serper_normalize({"link": "https://example.com"}, "q", 1, "organic")
    assert result["url"] == "https://example.com"


def test_serper_author_is_always_none():
    result = serper_normalize({"title": "T", "link": "U", "author": "someone"}, "q", 1, "organic")
    assert result["author"] is None


def test_serper_maps_date_to_published_at():
    result = serper_normalize({"title": "T", "link": "U", "date": "2026-05-01"}, "q", 1, "organic")
    assert result["published_at"] == "2026-05-01"


def test_news_api_maps_description_to_snippet():
    result = news_normalize({"title": "T", "url": "U", "description": "Desc"}, "q", 1)
    assert result["snippet"] == "Desc"


def test_news_api_extracts_source_name():
    result = news_normalize(
        {"title": "T", "url": "U", "source": {"name": "BBC", "id": "bbc"}}, "q", 1
    )
    assert result["source"] == "BBC"


def test_news_api_source_missing_returns_empty_string():
    result = news_normalize({"title": "T", "url": "U"}, "q", 1)
    assert result["source"] == ""


def test_rss_strips_html_from_snippet():
    entry = feedparser.FeedParserDict(
        {"title": "T", "link": "U", "summary": "<p>Clean text.</p>"}
    )
    result = rss_normalize(entry, "q", "Feed", 1)
    assert "<p>" not in result["snippet"]
    assert "Clean text." in result["snippet"]


def test_rss_rank_offset_applied():
    entry = feedparser.FeedParserDict({"title": "T", "link": "U"})
    result = rss_normalize(entry, "q", "Feed", rank=7)
    assert result["rank"] == 7
