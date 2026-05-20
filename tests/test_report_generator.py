"""Report generator tests — empty-source handling, missing key, and mocked generation."""

import os
from unittest.mock import patch

import pytest

from reporting.report_generator import (
    DEFAULT_OUTPUT_DIR,
    _MAX_CONTEXT_CHARS,
    build_context,
    generate_report,
)
from workflows.state import initial_state

# ---------------------------------------------------------------------------
# build_context — context assembly and limits
# ---------------------------------------------------------------------------

class TestBuildContext:
    def test_empty_state_returns_empty_string_and_zero_count(self):
        ctx, count = build_context(initial_state("hydrogen"))
        assert ctx == ""
        assert count == 0

    def test_successful_crawl_included_in_context(self):
        state = {
            **initial_state("hydrogen"),
            "crawled_results": [{
                "title": "Hydrogen Article", "url": "https://x.com/art",
                "content": "Long extracted article content.", "extraction_success": True,
                "source": "x.com", "source_type": "crawler",
                "snippet": "", "published_at": None, "content_length": 30,
            }],
        }
        ctx, count = build_context(state)
        assert count == 1
        assert "Hydrogen Article" in ctx
        assert "https://x.com/art" in ctx

    def test_failed_crawl_excluded_from_context(self):
        state = {
            **initial_state("hydrogen"),
            "crawled_results": [{
                "title": "Failed Page", "url": "https://x.com",
                "content": "", "extraction_success": False,
                "source": "x.com", "source_type": "crawler",
                "snippet": "fetch timeout", "published_at": None, "content_length": 0,
            }],
        }
        ctx, count = build_context(state)
        assert count == 0
        assert ctx == ""

    def test_merged_result_snippet_included(self):
        state = {
            **initial_state("hydrogen"),
            "merged_results": [{
                "title": "Hydrogen News", "url": "https://news.com/1",
                "snippet": "Important snippet.", "published_at": "2026-01-01",
                "source": "News Corp", "source_type": "news",
                "search_query": "hydrogen", "author": None, "rank": 1,
            }],
        }
        ctx, count = build_context(state)
        assert count == 1
        assert "Hydrogen News" in ctx
        assert "Important snippet." in ctx

    def test_crawled_url_not_duplicated_from_merged(self):
        """A URL crawled successfully must not also appear as a merged snippet."""
        url = "https://x.com/article"
        state = {
            **initial_state("hydrogen"),
            "crawled_results": [{
                "title": "Article", "url": url, "content": "Content here.",
                "extraction_success": True, "source": "x.com",
                "source_type": "crawler", "snippet": "", "published_at": None,
                "content_length": 13,
            }],
            "merged_results": [{
                "title": "Article", "url": url, "snippet": "Snippet.",
                "published_at": None, "source": "x.com", "source_type": "organic",
                "search_query": "q", "author": None, "rank": 1,
            }],
        }
        ctx, count = build_context(state)
        # Only counted once — crawled version takes priority
        assert count == 1

    def test_context_truncated_at_character_limit(self):
        long_content = "hydrogen " * 10_000  # well over the limit
        state = {
            **initial_state("hydrogen"),
            "crawled_results": [{
                "title": "Big Article", "url": "https://x.com",
                "content": long_content, "extraction_success": True,
                "source": "x.com", "source_type": "crawler",
                "snippet": "", "published_at": None, "content_length": len(long_content),
            }],
        }
        ctx, _ = build_context(state)
        # Allow a small overhead for the truncation marker string
        assert len(ctx) <= _MAX_CONTEXT_CHARS + 200

    def test_crawled_content_capped_per_item(self):
        from reporting.report_generator import _MAX_CRAWLED_CONTENT_CHARS
        long_content = "x" * (_MAX_CRAWLED_CONTENT_CHARS + 5000)
        state = {
            **initial_state("hydrogen"),
            "crawled_results": [{
                "title": "Article", "url": "https://x.com",
                "content": long_content, "extraction_success": True,
                "source": "x.com", "source_type": "crawler",
                "snippet": "", "published_at": None, "content_length": len(long_content),
            }],
        }
        ctx, count = build_context(state)
        assert count == 1
        # The full content (5000 chars over cap) must not be in the context
        assert len(ctx) < len(long_content)

    def test_source_count_reflects_both_crawled_and_merged(self):
        state = {
            **initial_state("hydrogen"),
            "crawled_results": [{
                "title": "A", "url": "https://a.com", "content": "Content.",
                "extraction_success": True, "source": "a.com",
                "source_type": "crawler", "snippet": "", "published_at": None,
                "content_length": 8,
            }],
            "merged_results": [
                {
                    "title": "B", "url": "https://b.com", "snippet": "Snip.",
                    "published_at": None, "source": "B", "source_type": "news",
                    "search_query": "q", "author": None, "rank": 1,
                },
                {
                    "title": "C", "url": "https://c.com", "snippet": "Snip.",
                    "published_at": None, "source": "C", "source_type": "rss",
                    "search_query": "q", "author": None, "rank": 2,
                },
            ],
        }
        _, count = build_context(state)
        assert count == 3  # 1 crawled + 2 merged


# ---------------------------------------------------------------------------
# generate_report — key guard and file output
# ---------------------------------------------------------------------------

class TestGenerateReport:
    def test_raises_runtime_error_when_openai_key_missing(self, tmp_path):
        state = initial_state("hydrogen")
        with patch.dict(os.environ, {"OPENAI_API_KEY": ""}, clear=False):
            with pytest.raises(RuntimeError, match="OPENAI_API_KEY"):
                generate_report(state, output_dir=tmp_path)

    def test_creates_markdown_file_with_mocked_openai(self, tmp_path):
        """Full generate_report path with OpenAI mocked — verifies the file is written."""
        state = {
            **initial_state("hydrogen test"),
            "run_metadata": {
                "topic": "hydrogen test",
                "start_time": "2026-01-01T00:00:00+00:00",
                "end_time": "2026-01-01T00:00:30+00:00",
                "duration_seconds": 30.0,
                "serper_count": 0, "news_count": 0, "rss_count": 0,
                "merged_count": 0, "crawled_count": 0,
                "crawl_success_count": 0, "error_count": 0, "warning_count": 0,
            },
        }
        _mock_body = (
            "# HYMIND Executive Intelligence Report\n\n"
            "## Research Topic\nHydrogen test topic.\n\n"
            "## Executive Summary\nTest summary.\n\n"
            "## Key Developments\n- **Item.** Fact. Implication.\n\n"
            "## Market Implications\nMarket context.\n\n"
            "## Technology Signals\n- Signal one.\n\n"
            "## Policy and Funding Signals\nNo signals found.\n\n"
            "## Competitive Notes\nNo notes found.\n\n"
            "## Risks and Watchouts\n- Risk one.\n- Risk two.\n\n"
            "## Source Traceability\nNo sources.\n\n"
            "## Workflow Metadata\n[System-generated]"
        )

        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key-not-real"}, clear=False):
            with patch("reporting.report_generator.complete", return_value=_mock_body):
                report_path, char_count = generate_report(state, output_dir=tmp_path)

        assert report_path.exists()
        assert report_path.suffix == ".md"
        content = report_path.read_text(encoding="utf-8")
        assert "# HYMIND Executive Intelligence Report" in content
        assert "## Workflow Metadata" in content
        assert "[System-generated]" not in content
        assert char_count == len(content)

    def test_all_required_sections_present_after_generation(self, tmp_path):
        """Every mandatory report section must appear in the output file."""
        required_sections = [
            "## Research Topic",
            "## Executive Summary",
            "## Key Developments",
            "## Market Implications",
            "## Technology Signals",
            "## Policy and Funding Signals",
            "## Competitive Notes",
            "## Risks and Watchouts",
            "## Source Traceability",
            "## Workflow Metadata",
        ]
        state = {
            **initial_state("hydrogen"),
            "run_metadata": {
                "topic": "hydrogen", "start_time": "2026-01-01T00:00:00+00:00",
                "end_time": "2026-01-01T00:00:10+00:00", "duration_seconds": 10.0,
                "serper_count": 0, "news_count": 0, "rss_count": 0,
                "merged_count": 0, "crawled_count": 0, "crawl_success_count": 0,
                "error_count": 0, "warning_count": 0,
            },
        }
        # Build a mock response that includes all sections
        mock_body = "\n\n".join(
            [f"# HYMIND Executive Intelligence Report"]
            + [f"{s}\nContent for {s}." for s in required_sections]
        )
        mock_body = mock_body.replace(
            "## Workflow Metadata\nContent for ## Workflow Metadata.",
            "## Workflow Metadata\n[System-generated]",
        )

        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}, clear=False):
            with patch("reporting.report_generator.complete", return_value=mock_body):
                report_path, _ = generate_report(state, output_dir=tmp_path)

        content = report_path.read_text(encoding="utf-8")
        for section in required_sections:
            assert section in content, f"Missing section: {section}"

    def test_metadata_table_injected_into_workflow_metadata_section(self, tmp_path):
        state = {
            **initial_state("hydrogen"),
            "run_metadata": {
                "topic": "hydrogen", "start_time": "2026-01-01T00:00:00+00:00",
                "end_time": "2026-01-01T00:00:10+00:00", "duration_seconds": 10.0,
                "serper_count": 5, "news_count": 3, "rss_count": 10,
                "merged_count": 15, "crawled_count": 5, "crawl_success_count": 4,
                "error_count": 0, "warning_count": 0,
            },
        }
        mock_body = (
            "# HYMIND Executive Intelligence Report\n\n"
            "## Workflow Metadata\n[System-generated]"
        )
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}, clear=False):
            with patch("reporting.report_generator.complete", return_value=mock_body):
                report_path, _ = generate_report(state, output_dir=tmp_path)

        content = report_path.read_text(encoding="utf-8")
        # Serper and news counts come from run_metadata
        assert "| Serper results | 5 |" in content
        assert "| NewsAPI results | 3 |" in content
        # Crawl success is computed from crawled_results (empty in this state → 0)
        assert "| Crawl success | 0 |" in content
        # Pipeline duration comes from run_metadata
        assert "| Pipeline duration | 10.0s |" in content
