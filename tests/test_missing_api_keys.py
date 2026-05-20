"""Tests for API key validation — both sys.exit paths (tools) and warning paths (workflow nodes)."""

import os
from unittest.mock import patch

import pytest

from workflows.state import initial_state


# ---------------------------------------------------------------------------
# Tool-level: missing key → sys.exit(1)
# ---------------------------------------------------------------------------

class TestSerperMissingKey:
    def test_search_exits_when_key_absent(self):
        with patch.dict(os.environ, {"SERPER_API_KEY": ""}, clear=False):
            from tools.serper_search import search
            with pytest.raises(SystemExit) as exc:
                search("hydrogen")
        assert exc.value.code == 1

    def test_search_exits_with_whitespace_only_key(self):
        with patch.dict(os.environ, {"SERPER_API_KEY": "   "}, clear=False):
            from tools.serper_search import search
            with pytest.raises(SystemExit) as exc:
                search("hydrogen")
        assert exc.value.code == 1


class TestNewsAPIMissingKey:
    def test_search_exits_when_key_absent(self):
        with patch.dict(os.environ, {"NEWS_API_KEY": ""}, clear=False):
            from tools.news_api import search
            with pytest.raises(SystemExit) as exc:
                search("hydrogen")
        assert exc.value.code == 1


# ---------------------------------------------------------------------------
# Workflow node-level: missing key → warning, no sys.exit
# ---------------------------------------------------------------------------

class TestWorkflowNodesMissingKeys:
    """Workflow nodes must degrade gracefully — no sys.exit, workflow continues."""

    def test_collect_serper_returns_empty_results_and_warning(self):
        from workflows.research_workflow import collect_serper
        state = initial_state("hydrogen")
        with patch.dict(os.environ, {"SERPER_API_KEY": ""}, clear=False):
            result = collect_serper(state)
        assert result["serper_results"] == []
        assert any("SERPER_API_KEY" in w for w in result.get("warnings", []))

    def test_collect_serper_does_not_raise_or_exit(self):
        from workflows.research_workflow import collect_serper
        state = initial_state("hydrogen")
        with patch.dict(os.environ, {"SERPER_API_KEY": ""}, clear=False):
            # Must not raise SystemExit or any other exception
            result = collect_serper(state)
        assert isinstance(result, dict)

    def test_collect_news_returns_empty_results_and_warning(self):
        from workflows.research_workflow import collect_news
        state = initial_state("hydrogen")
        with patch.dict(os.environ, {"NEWS_API_KEY": ""}, clear=False):
            result = collect_news(state)
        assert result["news_results"] == []
        assert any("NEWS_API_KEY" in w for w in result.get("warnings", []))

    def test_collect_news_does_not_raise_or_exit(self):
        from workflows.research_workflow import collect_news
        state = initial_state("hydrogen")
        with patch.dict(os.environ, {"NEWS_API_KEY": ""}, clear=False):
            result = collect_news(state)
        assert isinstance(result, dict)

    def test_both_nodes_missing_keys_workflow_still_has_rss(self):
        """Even with Serper and News keys missing, RSS collection is unaffected."""
        from workflows.research_workflow import collect_serper, collect_news
        state = initial_state("hydrogen")
        with patch.dict(os.environ, {"SERPER_API_KEY": "", "NEWS_API_KEY": ""}, clear=False):
            serper_result = collect_serper(state)
            news_result = collect_news(state)
        # RSS has no key requirement — it's the only source left operational
        assert serper_result["serper_results"] == []
        assert news_result["news_results"] == []
        # Both return warnings, not errors
        assert "warnings" in serper_result
        assert "warnings" in news_result
        assert "errors" not in serper_result or not serper_result.get("errors")
        assert "errors" not in news_result or not news_result.get("errors")


# ---------------------------------------------------------------------------
# Report generator: missing OpenAI key → RuntimeError (not sys.exit)
# ---------------------------------------------------------------------------

class TestReportGeneratorMissingKey:
    def test_raises_runtime_error_not_system_exit(self, tmp_path):
        from reporting.report_generator import generate_report
        state = initial_state("hydrogen")
        with patch.dict(os.environ, {"OPENAI_API_KEY": ""}, clear=False):
            with pytest.raises(RuntimeError, match="OPENAI_API_KEY"):
                generate_report(state, output_dir=tmp_path)

    def test_error_message_is_actionable(self, tmp_path):
        from reporting.report_generator import generate_report
        state = initial_state("hydrogen")
        with patch.dict(os.environ, {"OPENAI_API_KEY": ""}, clear=False):
            with pytest.raises(RuntimeError) as exc_info:
                generate_report(state, output_dir=tmp_path)
        # Error message should tell the user what to do
        assert ".env" in str(exc_info.value)
