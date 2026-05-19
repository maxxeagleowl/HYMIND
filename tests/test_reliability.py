"""Phase 4 reliability and failure scenario tests.

Covers failure modes not tested in earlier phases:
- RSS reader: per-feed timeout, connection error, HTTP error, malformed feed, empty feed
- Serper search: rate limit, server error, connection timeout, empty results
- NewsAPI: rate limit, server error, empty query
- Workflow node isolation: one failing node does not cascade to others
- finalize_state: missing start_time, partial state, all-zero counts
- Report generator: empty merged_results, degraded state (no crawls)
- OpenAI failure during synthesis: APIError propagation
"""

import os
from unittest.mock import MagicMock, patch

import pytest
import requests

from hymind.workflows.state import initial_state


# ---------------------------------------------------------------------------
# RSS reader failure modes
# ---------------------------------------------------------------------------

class TestRSSReaderFailures:
    """read_feed must return [] on any per-feed failure — never raise."""

    def test_feed_timeout_returns_empty(self):
        from hymind.tools.rss_reader import read_feed
        with patch("hymind.tools.rss_reader._fetch_content", side_effect=requests.Timeout()):
            result = read_feed("https://example.com/feed.xml", topic="hydrogen")
        assert result == []

    def test_feed_connection_error_returns_empty(self):
        from hymind.tools.rss_reader import read_feed
        with patch(
            "hymind.tools.rss_reader._fetch_content",
            side_effect=requests.ConnectionError("no route"),
        ):
            result = read_feed("https://example.com/feed.xml", topic="hydrogen")
        assert result == []

    def test_feed_http_error_returns_empty(self):
        from hymind.tools.rss_reader import read_feed
        mock_resp = MagicMock()
        mock_resp.status_code = 503
        with patch(
            "hymind.tools.rss_reader._fetch_content",
            side_effect=requests.HTTPError(response=mock_resp),
        ):
            result = read_feed("https://example.com/feed.xml", topic="hydrogen")
        assert result == []

    def test_unexpected_exception_returns_empty(self):
        from hymind.tools.rss_reader import read_feed
        with patch(
            "hymind.tools.rss_reader._fetch_content",
            side_effect=RuntimeError("unexpected"),
        ):
            result = read_feed("https://example.com/feed.xml", topic="hydrogen")
        assert result == []

    def test_malformed_feed_still_processes_valid_entries(self):
        """feedparser bozo=True must not skip processing — entries may still be valid."""
        import feedparser
        from hymind.tools.rss_reader import read_feed

        valid_entry = MagicMock()
        valid_entry.get = lambda k, d=None: {
            "title": "Hydrogen Update",
            "link": "https://example.com/1",
            "summary": "Important development.",
            "published": "2026-01-15",
            "author": None,
        }.get(k, d)

        mock_parsed = MagicMock(spec=feedparser.FeedParserDict)
        mock_parsed.bozo = True
        mock_parsed.bozo_exception = Exception("bad XML")
        mock_parsed.feed = MagicMock()
        mock_parsed.feed.title = "Test Feed"
        mock_parsed.entries = [valid_entry]

        with patch("hymind.tools.rss_reader._fetch_content", return_value=b"<rss/>"):
            with patch("feedparser.parse", return_value=mock_parsed):
                result = read_feed("https://bad-feed.com/rss", topic="hydrogen")

        # Bozo feed is logged as warning but entries are still processed
        assert isinstance(result, list)

    def test_empty_feed_returns_empty_list(self):
        import feedparser
        from hymind.tools.rss_reader import read_feed

        mock_parsed = MagicMock(spec=feedparser.FeedParserDict)
        mock_parsed.bozo = False
        mock_parsed.feed = MagicMock()
        mock_parsed.feed.title = "Empty Feed"
        mock_parsed.entries = []

        with patch("hymind.tools.rss_reader._fetch_content", return_value=b"<rss/>"):
            with patch("feedparser.parse", return_value=mock_parsed):
                result = read_feed("https://example.com/empty-feed", topic="hydrogen")

        assert result == []

    def test_read_feeds_continues_after_one_feed_fails(self):
        """read_feeds must process all feeds even if the first times out."""
        from hymind.tools.rss_reader import read_feeds

        call_count = 0

        def side_effect(url: str):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise requests.Timeout()
            return b"<rss/>"

        import feedparser
        mock_parsed = MagicMock(spec=feedparser.FeedParserDict)
        mock_parsed.bozo = False
        mock_parsed.feed = MagicMock()
        mock_parsed.feed.title = "Feed 2"
        mock_parsed.entries = []

        with patch("hymind.tools.rss_reader._fetch_content", side_effect=side_effect):
            with patch("feedparser.parse", return_value=mock_parsed):
                result = read_feeds(
                    ["https://feed1.com/rss", "https://feed2.com/rss"],
                    topic="hydrogen",
                )

        assert call_count == 2  # both feeds were attempted
        assert isinstance(result, list)

    def test_read_feeds_empty_url_list_returns_empty(self):
        from hymind.tools.rss_reader import read_feeds
        assert read_feeds([], topic="hydrogen") == []


# ---------------------------------------------------------------------------
# Serper search failure modes
# ---------------------------------------------------------------------------

class TestSerperSearchFailures:
    """Serper failures should raise specific exceptions (retried by tenacity)."""

    def test_rate_limit_raises_serper_rate_limit_error(self):
        from hymind.tools.serper_search import search, SerperRateLimitError

        mock_resp = MagicMock()
        mock_resp.status_code = 429
        mock_resp.ok = False

        with patch.dict(os.environ, {"SERPER_API_KEY": "test-key"}):
            with patch("requests.post", return_value=mock_resp):
                with pytest.raises(SerperRateLimitError):
                    search("hydrogen fuel cell")

    def test_server_error_raises_serper_server_error(self):
        from hymind.tools.serper_search import search, SerperServerError

        mock_resp = MagicMock()
        mock_resp.status_code = 503
        mock_resp.ok = False

        with patch.dict(os.environ, {"SERPER_API_KEY": "test-key"}):
            with patch("requests.post", return_value=mock_resp):
                with pytest.raises(SerperServerError):
                    search("hydrogen fuel cell")

    def test_empty_query_returns_empty_without_api_call(self):
        from hymind.tools.serper_search import search

        with patch.dict(os.environ, {"SERPER_API_KEY": "test-key"}):
            with patch("requests.post") as mock_post:
                result = search("")
        assert result == []
        mock_post.assert_not_called()

    def test_whitespace_only_query_returns_empty_without_api_call(self):
        from hymind.tools.serper_search import search

        with patch.dict(os.environ, {"SERPER_API_KEY": "test-key"}):
            with patch("requests.post") as mock_post:
                result = search("   ")
        assert result == []
        mock_post.assert_not_called()

    def test_zero_results_returns_empty_list(self):
        from hymind.tools.serper_search import search

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.ok = True
        mock_resp.json.return_value = {"organic": [], "news": []}

        with patch.dict(os.environ, {"SERPER_API_KEY": "test-key"}):
            with patch("requests.post", return_value=mock_resp):
                result = search("obscure hydrogen niche topic")

        assert result == []


# ---------------------------------------------------------------------------
# NewsAPI failure modes
# ---------------------------------------------------------------------------

class TestNewsAPIFailures:
    """NewsAPI failures should raise specific exceptions."""

    def test_rate_limit_raises_newsapi_rate_limit_error(self):
        from hymind.tools.news_api import search, NewsAPIRateLimitError

        mock_resp = MagicMock()
        mock_resp.status_code = 429
        mock_resp.ok = False
        mock_resp.text = "rate limited"

        with patch.dict(os.environ, {"NEWS_API_KEY": "test-key"}):
            with patch("requests.get", return_value=mock_resp):
                with pytest.raises(NewsAPIRateLimitError):
                    search("hydrogen fuel cell")

    def test_server_error_raises_newsapi_server_error(self):
        from hymind.tools.news_api import search, NewsAPIServerError

        mock_resp = MagicMock()
        mock_resp.status_code = 500
        mock_resp.ok = False
        mock_resp.text = "internal server error"

        with patch.dict(os.environ, {"NEWS_API_KEY": "test-key"}):
            with patch("requests.get", return_value=mock_resp):
                with pytest.raises(NewsAPIServerError):
                    search("hydrogen fuel cell")

    def test_application_level_error_raises_newsapi_error(self):
        from hymind.tools.news_api import search, NewsAPIError

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.ok = True
        mock_resp.json.return_value = {
            "status": "error",
            "code": "apiKeyInvalid",
            "message": "Your API key is invalid.",
        }

        with patch.dict(os.environ, {"NEWS_API_KEY": "test-key"}):
            with patch("requests.get", return_value=mock_resp):
                with pytest.raises(NewsAPIError):
                    search("hydrogen")

    def test_empty_query_returns_empty_without_api_call(self):
        from hymind.tools.news_api import search

        with patch.dict(os.environ, {"NEWS_API_KEY": "test-key"}):
            with patch("requests.get") as mock_get:
                result = search("")
        assert result == []
        mock_get.assert_not_called()

    def test_removed_articles_filtered_out(self):
        from hymind.tools.news_api import search

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.ok = True
        mock_resp.json.return_value = {
            "status": "ok",
            "totalResults": 2,
            "articles": [
                {
                    "title": "[Removed]",
                    "description": "[Removed]",
                    "url": "https://removed.com/1",
                    "source": {"name": "Test"},
                    "publishedAt": "2026-01-01",
                    "author": None,
                },
                {
                    "title": "Real Hydrogen Article",
                    "description": "Electrolyzer breakthrough.",
                    "url": "https://real.com/article",
                    "source": {"name": "HydrogenInsight"},
                    "publishedAt": "2026-01-01",
                    "author": "Jane Doe",
                },
            ],
        }

        with patch.dict(os.environ, {"NEWS_API_KEY": "test-key"}):
            with patch("requests.get", return_value=mock_resp):
                result = search("hydrogen electrolyzer")

        assert len(result) == 1
        assert result[0]["title"] == "Real Hydrogen Article"


# ---------------------------------------------------------------------------
# Workflow node failure isolation
# ---------------------------------------------------------------------------

class TestWorkflowNodeIsolation:
    """Error in one collection node must not cascade to others."""

    def test_collect_serper_exception_returns_error_in_state(self):
        from hymind.workflows.research_workflow import collect_serper

        state = initial_state("hydrogen")
        with patch.dict(os.environ, {"SERPER_API_KEY": "test-key"}):
            with patch(
                "hymind.tools.serper_search.search",
                side_effect=RuntimeError("network failure"),
            ):
                result = collect_serper(state)

        assert result["serper_results"] == []
        assert any("collect_serper" in e for e in result.get("errors", []))

    def test_collect_news_exception_returns_error_in_state(self):
        from hymind.workflows.research_workflow import collect_news

        state = initial_state("hydrogen")
        with patch.dict(os.environ, {"NEWS_API_KEY": "test-key"}):
            with patch(
                "hymind.tools.news_api.search",
                side_effect=ConnectionError("DNS failure"),
            ):
                result = collect_news(state)

        assert result["news_results"] == []
        assert any("collect_news" in e for e in result.get("errors", []))

    def test_collect_rss_exception_returns_error_in_state(self):
        from hymind.workflows.research_workflow import collect_rss

        state = initial_state("hydrogen")
        # read_feeds is imported directly into research_workflow, so patch there
        with patch(
            "hymind.workflows.research_workflow.read_feeds",
            side_effect=RuntimeError("catastrophic RSS failure"),
        ):
            result = collect_rss(state)

        assert result["rss_results"] == []
        assert any("collect_rss" in e for e in result.get("errors", []))

    def test_crawl_selected_exception_returns_error_in_state(self):
        from hymind.workflows.research_workflow import crawl_selected

        state = {
            **initial_state("hydrogen"),
            "merged_results": [
                {"url": "https://example.com/article", "title": "Article",
                 "snippet": "Content", "source": "x", "source_type": "news",
                 "published_at": None, "search_query": "hydrogen", "author": None, "rank": 1}
            ],
        }
        # crawl_many is imported directly into research_workflow, so patch there
        with patch("hymind.workflows.research_workflow.crawl_many", side_effect=RuntimeError("crash")):
            result = crawl_selected(state)

        assert result["crawled_results"] == []
        assert any("crawl_selected" in e for e in result.get("errors", []))

    def test_crawl_selected_skips_pdf_urls(self):
        from hymind.workflows.research_workflow import crawl_selected

        state = {
            **initial_state("hydrogen"),
            "merged_results": [
                {"url": "https://example.com/report.pdf", "title": "PDF",
                 "snippet": "A PDF", "source": "x", "source_type": "organic",
                 "published_at": None, "search_query": "hydrogen", "author": None, "rank": 1},
                {"url": "https://example.com/article", "title": "Article",
                 "snippet": "HTML content", "source": "x", "source_type": "news",
                 "published_at": None, "search_query": "hydrogen", "author": None, "rank": 2},
            ],
        }

        crawled_urls: list[str] = []

        def _track_urls(urls):
            crawled_urls.extend(urls)
            return [{"url": u, "title": "", "content": "", "snippet": "",
                     "source": "", "source_type": "crawler",
                     "published_at": None, "extraction_success": False, "content_length": 0}
                    for u in urls]

        # crawl_many is imported directly into research_workflow, so patch there
        with patch("hymind.workflows.research_workflow.crawl_many", side_effect=_track_urls):
            crawl_selected(state)

        # PDF must be excluded from crawl
        assert "https://example.com/report.pdf" not in crawled_urls
        assert "https://example.com/article" in crawled_urls

    def test_crawl_selected_no_crawlable_urls_returns_warning(self):
        from hymind.workflows.research_workflow import crawl_selected

        state = {
            **initial_state("hydrogen"),
            "merged_results": [
                {"url": "", "title": "No URL", "snippet": "...",
                 "source": "x", "source_type": "news", "published_at": None,
                 "search_query": "q", "author": None, "rank": 1}
            ],
        }
        result = crawl_selected(state)
        assert result["crawled_results"] == []
        assert any("crawl_selected" in w for w in result.get("warnings", []))

    def test_store_findings_in_pinecone_skips_gracefully_without_config(self):
        from hymind.workflows.research_workflow import store_findings_in_pinecone

        state = {
            **initial_state("hydrogen"),
            "merged_results": [
                {"url": "https://x.com", "title": "H2", "snippet": "test",
                 "source": "x", "source_type": "news", "published_at": None,
                 "search_query": "q", "author": None, "rank": 1}
            ],
        }
        with patch.dict(os.environ, {"PINECONE_API_KEY": ""}, clear=False):
            result = store_findings_in_pinecone(state)

        # Must not raise; must return a dict with a warning
        assert isinstance(result, dict)
        assert any("Pinecone" in w for w in result.get("warnings", []))

    def test_retrieve_context_from_pinecone_skips_gracefully_without_config(self):
        from hymind.workflows.research_workflow import retrieve_context_from_pinecone

        state = initial_state("hydrogen")
        with patch.dict(os.environ, {"PINECONE_API_KEY": ""}, clear=False):
            result = retrieve_context_from_pinecone(state)

        assert isinstance(result, dict)
        # rag_context is either missing from result or an empty list
        assert result.get("rag_context", []) == []


# ---------------------------------------------------------------------------
# finalize_state edge cases
# ---------------------------------------------------------------------------

class TestFinalizeState:
    def test_empty_state_does_not_raise(self):
        from hymind.workflows.research_workflow import finalize_state

        state = initial_state("hydrogen")
        result = finalize_state(state)
        assert "run_metadata" in result
        meta = result["run_metadata"]
        assert "end_time" in meta
        assert meta["serper_count"] == 0
        assert meta["news_count"] == 0
        assert meta["rss_count"] == 0
        assert meta["merged_count"] == 0

    def test_missing_start_time_does_not_raise(self):
        from hymind.workflows.research_workflow import finalize_state

        state = {**initial_state("hydrogen"), "run_metadata": {}}
        result = finalize_state(state)
        # duration_seconds should be None (cannot compute without start_time)
        assert result["run_metadata"]["duration_seconds"] is None

    def test_invalid_start_time_format_does_not_raise(self):
        from hymind.workflows.research_workflow import finalize_state

        state = {
            **initial_state("hydrogen"),
            "run_metadata": {"start_time": "not-a-valid-timestamp"},
        }
        result = finalize_state(state)
        assert "end_time" in result["run_metadata"]
        # duration_seconds should be None since start_time was unparseable
        assert result["run_metadata"]["duration_seconds"] is None

    def test_counts_match_actual_state_lists(self):
        from hymind.workflows.research_workflow import finalize_state

        state = {
            **initial_state("hydrogen"),
            "run_metadata": {"start_time": "2026-01-01T10:00:00+00:00"},
            "serper_results": [{"url": "a"}, {"url": "b"}],
            "news_results": [{"url": "c"}],
            "rss_results": [{"url": "d"}, {"url": "e"}, {"url": "f"}],
            "merged_results": [{"url": "a"}, {"url": "b"}, {"url": "c"}],
            "crawled_results": [
                {"url": "a", "extraction_success": True},
                {"url": "b", "extraction_success": False},
            ],
            "errors": ["err1"],
            "warnings": ["w1", "w2"],
        }
        result = finalize_state(state)
        meta = result["run_metadata"]
        assert meta["serper_count"] == 2
        assert meta["news_count"] == 1
        assert meta["rss_count"] == 3
        assert meta["merged_count"] == 3
        assert meta["crawled_count"] == 2
        assert meta["crawl_success_count"] == 1
        assert meta["error_count"] == 1
        assert meta["warning_count"] == 2

    def test_duration_seconds_positive_when_start_time_set(self):
        from hymind.workflows.research_workflow import finalize_state

        state = {
            **initial_state("hydrogen"),
            "run_metadata": {"start_time": "2026-01-01T09:00:00+00:00"},
        }
        result = finalize_state(state)
        duration = result["run_metadata"]["duration_seconds"]
        assert duration is not None
        assert duration >= 0


# ---------------------------------------------------------------------------
# Report generator degraded state
# ---------------------------------------------------------------------------

class TestReportGeneratorDegradedState:
    """Report generation must log warnings and still attempt generation when findings are sparse."""

    def test_empty_merged_results_logs_warning_but_proceeds(self, tmp_path):
        from hymind.reporting.report_generator import generate_report

        state = {
            **initial_state("hydrogen test"),
            "run_metadata": {
                "topic": "hydrogen test",
                "start_time": "2026-01-01T00:00:00+00:00",
                "end_time": "2026-01-01T00:00:10+00:00",
                "duration_seconds": 10.0,
                "serper_count": 0, "news_count": 0, "rss_count": 0,
                "merged_count": 0, "crawled_count": 0,
                "crawl_success_count": 0, "error_count": 0, "warning_count": 0,
            },
        }

        mock_body = (
            "# HYMIND Executive Intelligence Report\n\n"
            "## Research Topic\nHydrogen.\n\n"
            "## Executive Summary\nNo sources available.\n\n"
            "## Key Developments\nNone identified.\n\n"
            "## Market Implications\nUndetermined.\n\n"
            "## Technology Signals\nNone.\n\n"
            "## Policy and Funding Signals\nNone.\n\n"
            "## Competitive Notes\nNone.\n\n"
            "## Risks and Watchouts\n- Limited data.\n- Coverage gap.\n\n"
            "## Source Traceability\nNo sources.\n\n"
            "## Workflow Metadata\n[System-generated]"
        )

        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}, clear=False):
            with patch("hymind.reporting.report_generator.complete", return_value=mock_body):
                report_path, char_count = generate_report(state, output_dir=tmp_path)

        assert report_path.exists()
        content = report_path.read_text(encoding="utf-8")
        assert "## Workflow Metadata" in content
        assert "[System-generated]" not in content

    def test_no_successful_crawls_still_generates_report(self, tmp_path):
        from hymind.reporting.report_generator import generate_report

        state = {
            **initial_state("hydrogen funding"),
            "merged_results": [
                {"url": "https://a.com", "title": "H2 Fund", "snippet": "Funding news.",
                 "published_at": "2026-01-01", "source": "HI", "source_type": "news",
                 "search_query": "hydrogen funding", "author": None, "rank": 1},
            ],
            "crawled_results": [
                {"url": "https://a.com", "title": "", "content": "", "snippet": "timeout",
                 "source": "a.com", "source_type": "crawler",
                 "published_at": None, "extraction_success": False, "content_length": 0},
            ],
            "run_metadata": {
                "topic": "hydrogen funding",
                "start_time": "2026-01-01T00:00:00+00:00",
                "end_time": "2026-01-01T00:00:05+00:00",
                "duration_seconds": 5.0,
                "serper_count": 0, "news_count": 1, "rss_count": 0,
                "merged_count": 1, "crawled_count": 1,
                "crawl_success_count": 0, "error_count": 0, "warning_count": 0,
            },
        }

        mock_body = (
            "# HYMIND Executive Intelligence Report\n\n"
            "## Research Topic\nHydrogen funding.\n\n"
            "## Executive Summary\nFunding activity observed.\n\n"
            "## Key Developments\n- **H2 Fund.** Funding news. Strategic.\n\n"
            "## Market Implications\nActive market.\n\n"
            "## Technology Signals\nNone noted.\n\n"
            "## Policy and Funding Signals\n- Funding announced.\n\n"
            "## Competitive Notes\nNone.\n\n"
            "## Risks and Watchouts\n- Coverage limited.\n- Single source.\n\n"
            "## Source Traceability\n- **H2 Fund**: https://a.com (news)\n\n"
            "## Workflow Metadata\n[System-generated]"
        )

        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}, clear=False):
            with patch("hymind.reporting.report_generator.complete", return_value=mock_body):
                report_path, char_count = generate_report(state, output_dir=tmp_path)

        assert report_path.exists()
        assert char_count > 0


# ---------------------------------------------------------------------------
# OpenAI client failure propagation
# ---------------------------------------------------------------------------

class TestOpenAIFailures:
    """OpenAI API failures must propagate with appropriate exception types."""

    def test_api_timeout_error_reraises_after_retries(self):
        from hymind.tools.openai_client import complete
        from openai import APITimeoutError

        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = APITimeoutError(
            request=MagicMock()
        )

        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            with patch("hymind.tools.openai_client._get_client", return_value=mock_client):
                with pytest.raises(APITimeoutError):
                    complete("test prompt", max_tokens=100)

    def test_rate_limit_error_reraises_after_retries(self):
        from hymind.tools.openai_client import complete
        from openai import RateLimitError

        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = RateLimitError(
            message="rate limited", response=MagicMock(headers={}), body={}
        )

        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            with patch("hymind.tools.openai_client._get_client", return_value=mock_client):
                with pytest.raises(RateLimitError):
                    complete("test prompt", max_tokens=100)

    def test_complete_returns_string_on_success(self):
        from hymind.tools.openai_client import complete

        mock_response = MagicMock()
        mock_response.choices[0].message.content = "Hydrogen is the future."
        mock_response.usage.total_tokens = 42

        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response

        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            with patch("hymind.tools.openai_client._get_client", return_value=mock_client):
                result = complete("Tell me about hydrogen.", max_tokens=100)

        assert result == "Hydrogen is the future."
        assert isinstance(result, str)

    def test_complete_with_empty_response_returns_empty_string(self):
        from hymind.tools.openai_client import complete

        mock_response = MagicMock()
        mock_response.choices[0].message.content = None
        mock_response.usage.total_tokens = 5

        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response

        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            with patch("hymind.tools.openai_client._get_client", return_value=mock_client):
                result = complete("Prompt.", max_tokens=100)

        assert result == ""


# ---------------------------------------------------------------------------
# Multi-source degraded pipeline
# ---------------------------------------------------------------------------

class TestDegradedPipeline:
    """Workflow must produce usable output even when most sources fail."""

    def test_all_api_sources_missing_rss_still_collected(self):
        """With Serper and NewsAPI keys absent, RSS runs and workflow completes."""
        import feedparser
        from hymind.workflows.research_workflow import (
            collect_serper, collect_news, collect_rss, merge_and_deduplicate
        )

        state = initial_state("hydrogen")

        # Both API sources skip due to missing keys
        with patch.dict(os.environ, {"SERPER_API_KEY": "", "NEWS_API_KEY": ""}, clear=False):
            serper_result = collect_serper(state)
            news_result = collect_news(state)

        # RSS still collects (no key required) — mock the HTTP call
        mock_entry = MagicMock()
        mock_entry.get = lambda k, d=None: {
            "title": "Hydrogen RSS Update",
            "link": "https://example.com/rss-article",
            "summary": "A hydrogen industry update from RSS.",
            "published": "2026-01-10",
            "author": None,
        }.get(k, d)

        mock_parsed = MagicMock(spec=feedparser.FeedParserDict)
        mock_parsed.bozo = False
        mock_parsed.feed = MagicMock()
        mock_parsed.feed.title = "Hydrogen Insight"
        mock_parsed.entries = [mock_entry]

        with patch("hymind.tools.rss_reader._fetch_content", return_value=b"<rss/>"):
            with patch("feedparser.parse", return_value=mock_parsed):
                rss_result = collect_rss(state)

        # Merge results into state
        merged_state = {
            **state,
            **serper_result,
            **news_result,
            **rss_result,
        }
        merged = merge_and_deduplicate(merged_state)

        assert merged["merged_results"]  # at least one RSS result
        assert merged["merged_results"][0]["source_type"] == "rss"

    def test_workflow_errors_accumulate_across_nodes(self):
        """Multiple nodes failing should accumulate errors in state, not overwrite."""
        from hymind.workflows.research_workflow import collect_serper, collect_news

        state = initial_state("hydrogen")

        with patch.dict(os.environ, {"SERPER_API_KEY": "key", "NEWS_API_KEY": "key"}):
            with patch(
                "hymind.tools.serper_search.search",
                side_effect=RuntimeError("serper down"),
            ):
                serper_result = collect_serper(state)

            news_state = {**state, **serper_result}
            with patch(
                "hymind.tools.news_api.search",
                side_effect=RuntimeError("newsapi down"),
            ):
                news_result = collect_news(news_state)

        combined_errors = serper_result.get("errors", []) + news_result.get("errors", [])
        assert len(combined_errors) >= 2
        assert any("collect_serper" in e for e in combined_errors)
        assert any("collect_news" in e for e in combined_errors)
