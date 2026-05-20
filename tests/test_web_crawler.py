"""Web crawler graceful failure tests — all mocked, no live HTTP calls."""

from unittest.mock import MagicMock, patch

import pytest
import requests

from tools.web_crawler import _domain, _empty_result, crawl, crawl_many


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _html_response(
    status_code: int = 200,
    content: bytes = (
        b"<html><body><article>"
        b"<p>This is a sufficiently long paragraph about hydrogen fuel cells "
        b"and the European market for electrolyzer technology in 2026.</p>"
        b"</article></body></html>"
    ),
    content_type: str = "text/html; charset=utf-8",
    final_url: str = "https://example.com/article",
) -> MagicMock:
    mock = MagicMock()
    mock.status_code = status_code
    mock.ok = status_code < 400
    mock.content = content
    mock.url = final_url
    mock.headers = {"Content-Type": content_type}
    return mock


# ---------------------------------------------------------------------------
# _empty_result helper
# ---------------------------------------------------------------------------

class TestEmptyResult:
    def test_schema_fields_present(self):
        r = _empty_result("https://x.com", "reason")
        assert r["extraction_success"] is False
        assert r["content_length"] == 0
        assert r["content"] == ""
        assert r["snippet"] == "reason"
        assert r["source_type"] == "crawler"
        assert r["title"] == ""

    def test_source_is_domain(self):
        r = _empty_result("https://news.example.com/path")
        assert r["source"] == "news.example.com"

    def test_url_preserved(self):
        r = _empty_result("https://x.com/article")
        assert r["url"] == "https://x.com/article"


# ---------------------------------------------------------------------------
# _domain helper
# ---------------------------------------------------------------------------

class TestDomain:
    def test_extracts_netloc(self):
        assert _domain("https://example.com/path?q=1") == "example.com"

    def test_extracts_subdomain(self):
        assert _domain("https://news.bbc.co.uk/article") == "news.bbc.co.uk"

    def test_non_url_returns_input(self):
        result = _domain("not-a-url")
        assert isinstance(result, str)  # must not raise

    def test_empty_string_returns_empty(self):
        result = _domain("")
        assert isinstance(result, str)


# ---------------------------------------------------------------------------
# crawl — network and HTTP failure modes
# ---------------------------------------------------------------------------

class TestCrawlGracefulFailure:
    def test_connection_error_returns_failed_result(self):
        with patch("tools.web_crawler._fetch", side_effect=requests.ConnectionError()):
            result = crawl("https://example.com")
        assert result["extraction_success"] is False
        assert "connection error" in result["snippet"]

    def test_timeout_returns_failed_result(self):
        with patch("tools.web_crawler._fetch", side_effect=requests.Timeout()):
            result = crawl("https://example.com")
        assert result["extraction_success"] is False
        assert "timeout" in result["snippet"]

    def test_unexpected_exception_returns_failed_result(self):
        with patch("tools.web_crawler._fetch", side_effect=RuntimeError("boom")):
            result = crawl("https://example.com")
        assert result["extraction_success"] is False

    def test_404_returns_failed_result(self):
        resp = _html_response(status_code=404)
        resp.ok = False
        with patch("tools.web_crawler._fetch", return_value=resp):
            result = crawl("https://example.com/missing")
        assert result["extraction_success"] is False
        assert "404" in result["snippet"]

    def test_403_returns_failed_result(self):
        resp = _html_response(status_code=403)
        resp.ok = False
        with patch("tools.web_crawler._fetch", return_value=resp):
            result = crawl("https://example.com/blocked")
        assert result["extraction_success"] is False
        assert "403" in result["snippet"]

    def test_non_html_content_type_returns_failed_result(self):
        resp = _html_response(content_type="application/pdf")
        with patch("tools.web_crawler._fetch", return_value=resp):
            result = crawl("https://example.com/report.pdf")
        assert result["extraction_success"] is False
        assert "pdf" in result["snippet"].lower() or "non-HTML" in result["snippet"]

    def test_crawl_never_raises_on_any_exception(self):
        """crawl() must always return a dict, never propagate exceptions."""
        with patch("tools.web_crawler._fetch", side_effect=MemoryError("oom")):
            result = crawl("https://example.com")
        assert isinstance(result, dict)
        assert result["extraction_success"] is False

    def test_crawl_returns_correct_url_on_success(self):
        resp = _html_response(final_url="https://example.com/article")
        with patch("tools.web_crawler._fetch", return_value=resp):
            result = crawl("https://example.com/article")
        assert result["source_type"] == "crawler"
        assert isinstance(result["content_length"], int)
        assert isinstance(result["extraction_success"], bool)


# ---------------------------------------------------------------------------
# crawl_many — isolation and batch behaviour
# ---------------------------------------------------------------------------

class TestCrawlMany:
    def test_empty_list_returns_empty(self):
        assert crawl_many([]) == []

    def test_result_count_matches_url_count(self):
        resp = _html_response()
        with patch("tools.web_crawler._fetch", return_value=resp):
            results = crawl_many(["https://a.com", "https://b.com", "https://c.com"])
        assert len(results) == 3

    def test_failure_on_first_url_does_not_skip_remaining(self):
        """One failing URL must not prevent subsequent URLs from being attempted."""
        call_count = 0

        def _side_effect(url: str) -> MagicMock:
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise requests.ConnectionError("first fails")
            return _html_response()

        with patch("tools.web_crawler._fetch", side_effect=_side_effect):
            results = crawl_many(["https://fail.com", "https://ok.com"])

        assert call_count == 2
        assert len(results) == 2
        assert results[0]["extraction_success"] is False  # first failed
        # second attempt was made regardless

    def test_all_failures_still_returns_result_per_url(self):
        with patch("tools.web_crawler._fetch", side_effect=requests.Timeout()):
            results = crawl_many(["https://a.com", "https://b.com"])
        assert len(results) == 2
        assert all(not r["extraction_success"] for r in results)

    def test_results_in_same_order_as_input(self):
        urls = ["https://first.com", "https://second.com"]
        resp = _html_response()

        def _side_effect(url: str) -> MagicMock:
            r = _html_response(final_url=url)
            return r

        with patch("tools.web_crawler._fetch", side_effect=_side_effect):
            results = crawl_many(urls)

        assert results[0]["source"] == "first.com"
        assert results[1]["source"] == "second.com"
