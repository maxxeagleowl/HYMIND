"""Phase 2 NewsAPI collector tests — all HTTP mocked, no live API calls.

Tests tools.news_api.search() against all relevant failure and success
modes. Complements the existing schema checks in test_schemas.py and the
missing-key tests in test_missing_api_keys.py with full HTTP-level coverage.

Also tests the Phase 2 validation module (tools.collector).
"""

import json
import os
from unittest.mock import MagicMock, patch

import pytest
import requests

from tools.news_api import (
    NewsAPIError,
    NewsAPIRateLimitError,
    NewsAPIServerError,
    search,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _mock_response(
    status_code: int = 200,
    json_body: dict | None = None,
    raise_json: Exception | None = None,
) -> MagicMock:
    """Build a mock requests.Response for use with patch('...requests.get')."""
    mock = MagicMock()
    mock.status_code = status_code
    mock.ok = status_code < 400
    mock.text = json.dumps(json_body or {})
    if raise_json is not None:
        mock.json.side_effect = raise_json
    else:
        mock.json.return_value = json_body or {}
    return mock


def _article(
    title: str = "Hydrogen Breakthrough",
    url: str = "https://example.com/hydrogen",
    description: str = "Major news about hydrogen fuel cells.",
    published_at: str = "2026-05-18T12:00:00Z",
    source_name: str = "Reuters",
    author: str = "Jane Doe",
) -> dict:
    """Build a minimal realistic NewsAPI article dict."""
    return {
        "title": title,
        "url": url,
        "description": description,
        "publishedAt": published_at,
        "source": {"name": source_name},
        "author": author,
    }


def _ok_response(articles: list[dict] | None = None) -> MagicMock:
    """Build a successful HTTP 200 mock with the given article list."""
    return _mock_response(
        status_code=200,
        json_body={
            "status": "ok",
            "totalResults": len(articles or []),
            "articles": articles or [],
        },
    )


# ---------------------------------------------------------------------------
# Successful HTTP 200 response
# ---------------------------------------------------------------------------

class TestSuccessfulResponse:
    def test_returns_normalized_list(self):
        with patch("tools.news_api.requests.get", return_value=_ok_response([_article()])):
            with patch.dict(os.environ, {"NEWS_API_KEY": "test-key"}):
                results = search("hydrogen fuel cells")
        assert len(results) == 1

    def test_title_mapped_correctly(self):
        with patch("tools.news_api.requests.get", return_value=_ok_response([_article(title="PEM Breakthrough")])):
            with patch.dict(os.environ, {"NEWS_API_KEY": "test-key"}):
                results = search("hydrogen")
        assert results[0]["title"] == "PEM Breakthrough"

    def test_url_preserved(self):
        with patch("tools.news_api.requests.get", return_value=_ok_response([_article(url="https://news.example.com/h2")])):
            with patch.dict(os.environ, {"NEWS_API_KEY": "test-key"}):
                results = search("hydrogen")
        assert results[0]["url"] == "https://news.example.com/h2"

    def test_source_type_is_news(self):
        with patch("tools.news_api.requests.get", return_value=_ok_response([_article()])):
            with patch.dict(os.environ, {"NEWS_API_KEY": "test-key"}):
                results = search("hydrogen")
        assert results[0]["source_type"] == "news"

    def test_published_at_preserved(self):
        with patch("tools.news_api.requests.get", return_value=_ok_response([_article(published_at="2026-05-18T12:00:00Z")])):
            with patch.dict(os.environ, {"NEWS_API_KEY": "test-key"}):
                results = search("hydrogen")
        assert results[0]["published_at"] == "2026-05-18T12:00:00Z"

    def test_search_query_field_set(self):
        with patch("tools.news_api.requests.get", return_value=_ok_response([_article()])):
            with patch.dict(os.environ, {"NEWS_API_KEY": "test-key"}):
                results = search("green hydrogen")
        assert results[0]["search_query"] == "green hydrogen"

    def test_rank_starts_at_one(self):
        articles = [_article(), _article(title="Second", url="https://second.com")]
        with patch("tools.news_api.requests.get", return_value=_ok_response(articles)):
            with patch.dict(os.environ, {"NEWS_API_KEY": "test-key"}):
                results = search("hydrogen")
        assert results[0]["rank"] == 1
        assert results[1]["rank"] == 2

    def test_all_nine_schema_fields_present(self):
        from tools.collector import REQUIRED_FIELDS
        with patch("tools.news_api.requests.get", return_value=_ok_response([_article()])):
            with patch.dict(os.environ, {"NEWS_API_KEY": "test-key"}):
                results = search("hydrogen")
        assert set(results[0].keys()) == REQUIRED_FIELDS

    def test_html_stripped_from_snippet(self):
        article = _article(description="<p>Clean <b>hydrogen</b> content.</p>")
        with patch("tools.news_api.requests.get", return_value=_ok_response([article])):
            with patch.dict(os.environ, {"NEWS_API_KEY": "test-key"}):
                results = search("hydrogen")
        assert "<p>" not in results[0]["snippet"]
        assert "Clean" in results[0]["snippet"]
        assert "hydrogen" in results[0]["snippet"]

    def test_source_name_extracted_from_nested_dict(self):
        article = _article(source_name="BBC News")
        with patch("tools.news_api.requests.get", return_value=_ok_response([article])):
            with patch.dict(os.environ, {"NEWS_API_KEY": "test-key"}):
                results = search("hydrogen")
        assert results[0]["source"] == "BBC News"

    def test_author_preserved(self):
        article = _article(author="Dr. Smith")
        with patch("tools.news_api.requests.get", return_value=_ok_response([article])):
            with patch.dict(os.environ, {"NEWS_API_KEY": "test-key"}):
                results = search("hydrogen")
        assert results[0]["author"] == "Dr. Smith"

    def test_multiple_articles_all_returned(self):
        articles = [
            _article(title="A", url="https://a.com"),
            _article(title="B", url="https://b.com"),
            _article(title="C", url="https://c.com"),
        ]
        with patch("tools.news_api.requests.get", return_value=_ok_response(articles)):
            with patch.dict(os.environ, {"NEWS_API_KEY": "test-key"}):
                results = search("hydrogen")
        assert len(results) == 3

    def test_from_and_to_dates_passed_to_api_request(self):
        """from_date and to_date must appear in the params sent to the NewsAPI endpoint."""
        with patch("tools.news_api.requests.get", return_value=_ok_response([_article()])) as mock_get:
            with patch.dict(os.environ, {"NEWS_API_KEY": "test-key"}):
                search("hydrogen", from_date="2026-05-01", to_date="2026-05-18")
        _, call_kwargs = mock_get.call_args
        params = call_kwargs.get("params", {})
        assert params.get("from") == "2026-05-01"
        assert params.get("to") == "2026-05-18"


# ---------------------------------------------------------------------------
# Empty and missing results
# ---------------------------------------------------------------------------

class TestEmptyResponse:
    def test_empty_articles_list_returns_empty(self):
        with patch("tools.news_api.requests.get", return_value=_ok_response([])):
            with patch.dict(os.environ, {"NEWS_API_KEY": "test-key"}):
                results = search("hydrogen")
        assert results == []

    def test_missing_articles_key_returns_empty(self):
        """Response body with no 'articles' key must not crash."""
        resp = _mock_response(200, {"status": "ok", "totalResults": 0})
        with patch("tools.news_api.requests.get", return_value=resp):
            with patch.dict(os.environ, {"NEWS_API_KEY": "test-key"}):
                results = search("hydrogen")
        assert results == []

    def test_empty_query_returns_empty_without_api_call(self):
        with patch("tools.news_api.requests.get") as mock_get:
            with patch.dict(os.environ, {"NEWS_API_KEY": "test-key"}):
                results = search("   ")
        assert results == []
        mock_get.assert_not_called()

    def test_whitespace_only_query_returns_empty(self):
        with patch("tools.news_api.requests.get") as mock_get:
            with patch.dict(os.environ, {"NEWS_API_KEY": "test-key"}):
                results = search("\t\n")
        assert results == []
        mock_get.assert_not_called()


# ---------------------------------------------------------------------------
# HTTP authentication errors — not retried
# ---------------------------------------------------------------------------

class TestHTTPAuthErrors:
    def test_http_401_raises_http_error(self):
        resp = _mock_response(401, {"status": "error", "code": "apiKeyInvalid", "message": "Your API key is invalid."})
        resp.ok = False
        with patch("tools.news_api.requests.get", return_value=resp):
            with patch.dict(os.environ, {"NEWS_API_KEY": "bad-key"}):
                with pytest.raises(requests.HTTPError):
                    search("hydrogen")

    def test_http_403_raises_http_error(self):
        resp = _mock_response(403, {"status": "error", "code": "apiKeyDisabled", "message": "Your API key has been disabled."})
        resp.ok = False
        with patch("tools.news_api.requests.get", return_value=resp):
            with patch.dict(os.environ, {"NEWS_API_KEY": "disabled-key"}):
                with pytest.raises(requests.HTTPError):
                    search("hydrogen")

    def test_http_401_does_not_continue_silently(self):
        """A 401 must not return an empty list — it must raise so callers know the key is broken."""
        resp = _mock_response(401, {})
        resp.ok = False
        with patch("tools.news_api.requests.get", return_value=resp):
            with patch.dict(os.environ, {"NEWS_API_KEY": "bad-key"}):
                with pytest.raises(requests.HTTPError):
                    search("hydrogen")


# ---------------------------------------------------------------------------
# Rate limiting (HTTP 429 and application-level) — patched past retry loop
# ---------------------------------------------------------------------------

class TestRateLimiting:
    def test_rate_limit_error_propagates(self):
        """HTTP 429 raises NewsAPIRateLimitError after retry exhaustion."""
        with patch("tools.news_api._call_newsapi", side_effect=NewsAPIRateLimitError("HTTP 429")):
            with patch.dict(os.environ, {"NEWS_API_KEY": "test-key"}):
                with pytest.raises(NewsAPIRateLimitError):
                    search("hydrogen")

    def test_application_rate_limit_propagates(self):
        """Application-level rateLimited status in response body propagates."""
        with patch("tools.news_api._call_newsapi", side_effect=NewsAPIRateLimitError("rateLimited")):
            with patch.dict(os.environ, {"NEWS_API_KEY": "test-key"}):
                with pytest.raises(NewsAPIRateLimitError):
                    search("hydrogen")

    def test_rate_limit_is_not_swallowed(self):
        """Rate limit must never silently return [] — the caller must know."""
        with patch("tools.news_api._call_newsapi", side_effect=NewsAPIRateLimitError("rate limited")):
            with patch.dict(os.environ, {"NEWS_API_KEY": "test-key"}):
                with pytest.raises(NewsAPIRateLimitError):
                    search("hydrogen")


# ---------------------------------------------------------------------------
# Network timeout — patched past retry loop
# ---------------------------------------------------------------------------

class TestTimeout:
    def test_timeout_propagates_after_retries(self):
        """Persistent timeout after all retry attempts is re-raised to caller."""
        with patch("tools.news_api._call_newsapi", side_effect=requests.Timeout("timed out")):
            with patch.dict(os.environ, {"NEWS_API_KEY": "test-key"}):
                with pytest.raises(requests.Timeout):
                    search("hydrogen")

    def test_timeout_is_not_swallowed(self):
        """Timeout must never silently return [] — the caller must know."""
        with patch("tools.news_api._call_newsapi", side_effect=requests.Timeout()):
            with patch.dict(os.environ, {"NEWS_API_KEY": "test-key"}):
                with pytest.raises(requests.Timeout):
                    search("hydrogen")


# ---------------------------------------------------------------------------
# Malformed payloads
# ---------------------------------------------------------------------------

class TestMalformedPayloads:
    def test_json_decode_error_raises(self):
        """Non-JSON body on a 200 response raises ValueError."""
        resp = _mock_response(200, raise_json=ValueError("malformed json"))
        with patch("tools.news_api.requests.get", return_value=resp):
            with patch.dict(os.environ, {"NEWS_API_KEY": "test-key"}):
                with pytest.raises(ValueError):
                    search("hydrogen")

    def test_removed_sentinel_title_filtered(self):
        """Articles with [Removed] title are excluded from results."""
        articles = [
            _article(title="[Removed]", description="[Removed]"),
            _article(title="Real Article", url="https://real.com/article"),
        ]
        with patch("tools.news_api.requests.get", return_value=_ok_response(articles)):
            with patch.dict(os.environ, {"NEWS_API_KEY": "test-key"}):
                results = search("hydrogen")
        assert len(results) == 1
        assert results[0]["url"] == "https://real.com/article"

    def test_removed_sentinel_description_filtered(self):
        """Articles with [Removed] description are excluded even if title looks valid."""
        articles = [
            _article(title="Looks Valid", description="[Removed]"),
            _article(title="Second", url="https://second.com"),
        ]
        with patch("tools.news_api.requests.get", return_value=_ok_response(articles)):
            with patch.dict(os.environ, {"NEWS_API_KEY": "test-key"}):
                results = search("hydrogen")
        assert len(results) == 1
        assert results[0]["url"] == "https://second.com"

    def test_url_missing_articles_dropped(self):
        """Articles with empty URL are excluded from results."""
        articles = [
            {"title": "No URL", "url": "", "description": "Desc",
             "publishedAt": None, "source": {"name": "Test"}, "author": None},
            _article(title="Has URL", url="https://has-url.com"),
        ]
        with patch("tools.news_api.requests.get", return_value=_ok_response(articles)):
            with patch.dict(os.environ, {"NEWS_API_KEY": "test-key"}):
                results = search("hydrogen")
        assert len(results) == 1
        assert results[0]["url"] == "https://has-url.com"

    def test_title_missing_articles_dropped(self):
        """Articles with empty title are excluded from results."""
        articles = [
            {"title": "", "url": "https://no-title.com", "description": "Desc",
             "publishedAt": None, "source": {}, "author": None},
            _article(title="Has Title", url="https://with-title.com"),
        ]
        with patch("tools.news_api.requests.get", return_value=_ok_response(articles)):
            with patch.dict(os.environ, {"NEWS_API_KEY": "test-key"}):
                results = search("hydrogen")
        assert len(results) == 1
        assert results[0]["title"] == "Has Title"

    def test_all_removed_returns_empty(self):
        """If every article is a [Removed] placeholder, return []."""
        articles = [
            _article(title="[Removed]", description="[Removed]"),
            _article(title="[Removed]", url="https://b.com", description="[Removed]"),
        ]
        with patch("tools.news_api.requests.get", return_value=_ok_response(articles)):
            with patch.dict(os.environ, {"NEWS_API_KEY": "test-key"}):
                results = search("hydrogen")
        assert results == []


# ---------------------------------------------------------------------------
# Schema compatibility with Phase 1 workflow
# ---------------------------------------------------------------------------

class TestSchemaCompatibility:
    """Verify that search() output is directly usable by Phase 1 workflow nodes."""

    def test_results_feed_merge_and_deduplicate(self):
        """search() output can be passed directly to merge_and_deduplicate."""
        from workflows.research_workflow import merge_and_deduplicate
        from workflows.state import initial_state

        articles = [
            _article(title="A", url="https://a.com"),
            _article(title="B", url="https://b.com"),
        ]
        with patch("tools.news_api.requests.get", return_value=_ok_response(articles)):
            with patch.dict(os.environ, {"NEWS_API_KEY": "test-key"}):
                news_results = search("hydrogen")

        state = {**initial_state("hydrogen"), "news_results": news_results}
        merged = merge_and_deduplicate(state)
        assert len(merged["merged_results"]) == 2

    def test_results_deduplication_removes_duplicate_url(self):
        """Duplicate URLs across news and serper results are deduplicated."""
        from workflows.research_workflow import merge_and_deduplicate
        from workflows.state import initial_state

        shared_url = "https://shared.com/article"
        articles = [_article(url=shared_url)]
        with patch("tools.news_api.requests.get", return_value=_ok_response(articles)):
            with patch.dict(os.environ, {"NEWS_API_KEY": "test-key"}):
                news_results = search("hydrogen")

        # Simulate the same URL also appearing in serper results
        serper_result = {
            "title": "Shared", "url": shared_url, "snippet": "S",
            "published_at": None, "source": "Test", "source_type": "organic",
            "search_query": "hydrogen", "author": None, "rank": 1,
        }
        state = {
            **initial_state("hydrogen"),
            "serper_results": [serper_result],
            "news_results": news_results,
        }
        merged = merge_and_deduplicate(state)
        assert len(merged["merged_results"]) == 1

    def test_results_pass_validation_layer(self):
        """All fields returned by search() satisfy the Phase 2 validation layer."""
        from tools.collector import validate_results

        articles = [
            _article(),
            _article(title="Second", url="https://second.com"),
        ]
        with patch("tools.news_api.requests.get", return_value=_ok_response(articles)):
            with patch.dict(os.environ, {"NEWS_API_KEY": "test-key"}):
                news_results = search("hydrogen")

        validated = validate_results(news_results)
        assert len(validated) == len(news_results)


# ---------------------------------------------------------------------------
# Validation module — validate_result
# ---------------------------------------------------------------------------

class TestValidateResult:
    def test_valid_result_passes(self):
        from tools.collector import validate_result
        result = {
            "title": "T", "url": "https://x.com", "snippet": "S",
            "published_at": "2026-01-01", "source": "Reuters",
            "source_type": "news", "search_query": "hydrogen",
            "author": None, "rank": 1,
        }
        ok, issues = validate_result(result)
        assert ok is True
        assert issues == []

    def test_empty_url_is_invalid(self):
        from tools.collector import validate_result
        result = {
            "title": "T", "url": "", "snippet": "S",
            "published_at": None, "source": "S",
            "source_type": "news", "search_query": "q",
            "author": None, "rank": 1,
        }
        ok, issues = validate_result(result)
        assert ok is False
        assert any("url" in i for i in issues)

    def test_missing_fields_are_invalid(self):
        from tools.collector import validate_result
        result = {"title": "T", "url": "https://x.com"}  # missing 7 of 9 fields
        ok, issues = validate_result(result)
        assert ok is False
        assert any("missing fields" in i for i in issues)

    def test_html_snippet_flagged(self):
        from tools.collector import validate_result
        result = {
            "title": "T", "url": "https://x.com",
            "snippet": "<p>Has <b>HTML</b> tags.</p>",
            "published_at": None, "source": "S",
            "source_type": "news", "search_query": "q",
            "author": None, "rank": 1,
        }
        ok, issues = validate_result(result)
        assert ok is False
        assert any("HTML" in i for i in issues)

    def test_empty_source_type_is_invalid(self):
        from tools.collector import validate_result
        result = {
            "title": "T", "url": "https://x.com", "snippet": "S",
            "published_at": None, "source": "S",
            "source_type": "", "search_query": "q",
            "author": None, "rank": 1,
        }
        ok, issues = validate_result(result)
        assert ok is False
        assert any("source_type" in i for i in issues)

    def test_none_published_at_is_valid(self):
        from tools.collector import validate_result
        result = {
            "title": "T", "url": "https://x.com", "snippet": "S",
            "published_at": None, "source": "S",
            "source_type": "news", "search_query": "q",
            "author": None, "rank": 1,
        }
        ok, issues = validate_result(result)
        assert ok is True

    def test_none_author_is_valid(self):
        from tools.collector import validate_result
        result = {
            "title": "T", "url": "https://x.com", "snippet": "S",
            "published_at": "2026-01-01", "source": "S",
            "source_type": "rss", "search_query": "q",
            "author": None, "rank": 1,
        }
        ok, issues = validate_result(result)
        assert ok is True

    def test_multiple_failures_reported(self):
        from tools.collector import validate_result
        result = {"url": ""}  # missing fields AND empty URL
        ok, issues = validate_result(result)
        assert ok is False
        assert len(issues) >= 2


# ---------------------------------------------------------------------------
# Validation module — validate_results (batch)
# ---------------------------------------------------------------------------

class TestValidateResults:
    def _valid(self, url: str = "https://x.com", rank: int = 1) -> dict:
        return {
            "title": "T", "url": url, "snippet": "S",
            "published_at": None, "source": "S",
            "source_type": "news", "search_query": "q",
            "author": None, "rank": rank,
        }

    def test_all_valid_results_returned(self):
        from tools.collector import validate_results
        results = [self._valid("https://a.com", 1), self._valid("https://b.com", 2)]
        assert len(validate_results(results)) == 2

    def test_invalid_results_dropped(self):
        from tools.collector import validate_results
        results = [
            {**self._valid(), "url": ""},  # invalid — empty URL
            self._valid("https://b.com"),  # valid
        ]
        validated = validate_results(results)
        assert len(validated) == 1
        assert validated[0]["url"] == "https://b.com"

    def test_empty_list_returns_empty(self):
        from tools.collector import validate_results
        assert validate_results([]) == []

    def test_all_invalid_returns_empty(self):
        from tools.collector import validate_results
        assert validate_results([{"url": ""}]) == []

    def test_order_preserved_after_filtering(self):
        from tools.collector import validate_results
        results = [
            self._valid("https://a.com", 1),
            {**self._valid(), "url": ""},  # invalid — dropped
            self._valid("https://c.com", 3),
        ]
        validated = validate_results(results)
        assert len(validated) == 2
        assert validated[0]["url"] == "https://a.com"
        assert validated[1]["url"] == "https://c.com"


# ---------------------------------------------------------------------------
# strip_html utility
# ---------------------------------------------------------------------------

class TestStripHtml:
    def test_removes_tags(self):
        from tools.collector import strip_html
        assert strip_html("<p>Hello world.</p>") == "Hello world."

    def test_collapses_whitespace(self):
        from tools.collector import strip_html
        result = strip_html("  too   many   spaces  ")
        assert "  " not in result

    def test_empty_string_returns_empty(self):
        from tools.collector import strip_html
        assert strip_html("") == ""

    def test_plain_text_unchanged(self):
        from tools.collector import strip_html
        assert strip_html("No HTML here.") == "No HTML here."

    def test_nested_tags_removed(self):
        from tools.collector import strip_html
        result = strip_html("<div><p><b>Bold</b> text.</p></div>")
        assert "<" not in result
        assert "Bold" in result
        assert "text." in result
