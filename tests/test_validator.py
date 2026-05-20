"""Tests for the HYMIND output validation layer (reporting/validator.py).

Covers validate_findings() and check_state_quality() with a full range of
input conditions: clean data, missing URLs, duplicate URLs, empty snippets,
missing titles, and complete/partial/empty state dicts.
"""

import pytest

from reporting.validator import (
    ValidationResult,
    check_state_quality,
    validate_findings,
)
from workflows.state import initial_state


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _finding(
    url: str = "https://example.com/article",
    title: str = "Hydrogen Update",
    snippet: str = "Electrolyzer deployment accelerated in Europe.",
    source_type: str = "news",
) -> dict:
    return {
        "title": title,
        "url": url,
        "snippet": snippet,
        "published_at": "2026-01-01",
        "source": "HydrogenInsight",
        "source_type": source_type,
        "search_query": "hydrogen",
        "author": None,
        "rank": 1,
    }


# ---------------------------------------------------------------------------
# validate_findings — clean input
# ---------------------------------------------------------------------------

class TestValidateFindingsClean:
    def test_all_valid_findings_returned_unchanged(self):
        findings = [
            _finding("https://a.com", "Title A"),
            _finding("https://b.com", "Title B"),
            _finding("https://c.com", "Title C"),
        ]
        valid, result = validate_findings(findings)
        assert len(valid) == 3
        assert result.valid_count == 3
        assert result.invalid_count == 0
        assert result.can_generate_report is True

    def test_validation_result_type(self):
        valid, result = validate_findings([_finding()])
        assert isinstance(result, ValidationResult)
        assert isinstance(valid, list)

    def test_total_input_reflects_original_count(self):
        findings = [_finding(f"https://example.com/{i}") for i in range(5)]
        _, result = validate_findings(findings)
        assert result.total_input == 5

    def test_empty_input_returns_empty_list_and_cannot_generate(self):
        valid, result = validate_findings([])
        assert valid == []
        assert result.valid_count == 0
        assert result.can_generate_report is False

    def test_single_valid_finding_can_generate_report(self):
        valid, result = validate_findings([_finding()])
        assert result.can_generate_report is True


# ---------------------------------------------------------------------------
# validate_findings — missing URL
# ---------------------------------------------------------------------------

class TestValidateFindingsMissingURL:
    def test_finding_with_empty_url_is_excluded(self):
        findings = [_finding(url=""), _finding(url="https://ok.com")]
        valid, result = validate_findings(findings)
        assert len(valid) == 1
        assert valid[0]["url"] == "https://ok.com"
        assert result.missing_url_count == 1

    def test_finding_with_none_url_is_excluded(self):
        finding = _finding()
        finding["url"] = None
        valid, result = validate_findings([finding])
        assert valid == []
        assert result.missing_url_count == 1

    def test_all_missing_urls_produces_cannot_generate(self):
        findings = [_finding(url=""), _finding(url="   ")]
        valid, result = validate_findings(findings)
        assert result.can_generate_report is False
        assert result.missing_url_count == 2

    def test_missing_url_count_tracked_correctly(self):
        findings = [
            _finding(url=""),
            _finding(url="https://a.com"),
            _finding(url=""),
        ]
        _, result = validate_findings(findings)
        assert result.missing_url_count == 2
        assert result.valid_count == 1


# ---------------------------------------------------------------------------
# validate_findings — duplicate URLs
# ---------------------------------------------------------------------------

class TestValidateFindingsDuplicates:
    def test_exact_duplicate_url_removed(self):
        findings = [
            _finding(url="https://example.com/article", title="First"),
            _finding(url="https://example.com/article", title="Duplicate"),
        ]
        valid, result = validate_findings(findings)
        assert len(valid) == 1
        assert valid[0]["title"] == "First"
        assert result.duplicate_count == 1

    def test_trailing_slash_variants_deduplicated(self):
        findings = [
            _finding(url="https://example.com/path/"),
            _finding(url="https://example.com/path"),
        ]
        valid, result = validate_findings(findings)
        assert len(valid) == 1
        assert result.duplicate_count == 1

    def test_case_insensitive_deduplication(self):
        findings = [
            _finding(url="https://EXAMPLE.com/article"),
            _finding(url="https://example.com/article"),
        ]
        valid, result = validate_findings(findings)
        assert len(valid) == 1
        assert result.duplicate_count == 1

    def test_multiple_duplicates_counted(self):
        findings = [
            _finding(url="https://shared.com"),
            _finding(url="https://shared.com"),
            _finding(url="https://shared.com"),
            _finding(url="https://unique.com"),
        ]
        valid, result = validate_findings(findings)
        assert len(valid) == 2  # shared.com once + unique.com
        assert result.duplicate_count == 2

    def test_no_duplicates_returns_zero_duplicate_count(self):
        findings = [
            _finding(url="https://a.com"),
            _finding(url="https://b.com"),
        ]
        _, result = validate_findings(findings)
        assert result.duplicate_count == 0


# ---------------------------------------------------------------------------
# validate_findings — missing title and empty snippet
# ---------------------------------------------------------------------------

class TestValidateFindingsWarningFields:
    def test_missing_title_is_kept_but_flagged(self):
        finding = _finding(title="")
        valid, result = validate_findings([finding])
        assert len(valid) == 1  # kept
        assert result.missing_title_count == 1

    def test_none_title_is_kept_but_flagged(self):
        finding = _finding()
        finding["title"] = None
        valid, result = validate_findings([finding])
        assert len(valid) == 1
        assert result.missing_title_count == 1

    def test_very_short_snippet_is_kept_but_flagged(self):
        finding = _finding(snippet="Hi")  # below _MIN_SNIPPET_CHARS threshold
        valid, result = validate_findings([finding])
        assert len(valid) == 1
        assert result.empty_snippet_count == 1

    def test_empty_snippet_is_kept_but_flagged(self):
        finding = _finding(snippet="")
        valid, result = validate_findings([finding])
        assert len(valid) == 1
        assert result.empty_snippet_count == 1

    def test_sufficient_snippet_not_flagged(self):
        finding = _finding(snippet="Electrolyzer deployment reached 5 GW in 2026.")
        _, result = validate_findings([finding])
        assert result.empty_snippet_count == 0

    def test_issues_list_contains_descriptions(self):
        findings = [
            _finding(url=""),  # skipped
            _finding(title=""),  # kept, warned
        ]
        _, result = validate_findings(findings)
        assert len(result.issues) >= 2
        assert any("missing URL" in i for i in result.issues)
        assert any("missing title" in i for i in result.issues)


# ---------------------------------------------------------------------------
# validate_findings — combined edge cases
# ---------------------------------------------------------------------------

class TestValidateFindingsMixed:
    def test_mix_of_valid_missing_url_and_duplicate(self):
        findings = [
            _finding(url="https://good.com/a"),
            _finding(url=""),
            _finding(url="https://good.com/a"),  # duplicate of first
            _finding(url="https://good.com/b"),
        ]
        valid, result = validate_findings(findings)
        assert result.valid_count == 2
        assert result.missing_url_count == 1
        assert result.duplicate_count == 1
        assert result.invalid_count == 2

    def test_can_generate_true_with_at_least_one_valid(self):
        findings = [_finding(url=""), _finding(url="https://valid.com")]
        _, result = validate_findings(findings)
        assert result.can_generate_report is True

    def test_invalid_count_property(self):
        findings = [_finding(url=""), _finding(url="https://a.com")]
        _, result = validate_findings(findings)
        assert result.invalid_count == result.total_input - result.valid_count


# ---------------------------------------------------------------------------
# check_state_quality
# ---------------------------------------------------------------------------

class TestCheckStateQuality:
    def test_empty_state_reports_cannot_generate(self):
        state = initial_state("hydrogen")
        quality = check_state_quality(state)
        assert quality["can_generate_report"] is False
        assert quality["total_findings"] == 0
        assert len(quality["errors"]) > 0

    def test_state_with_findings_can_generate(self):
        state = {
            **initial_state("hydrogen"),
            "merged_results": [
                _finding("https://a.com"),
                _finding("https://b.com"),
                _finding("https://c.com"),
            ],
        }
        quality = check_state_quality(state)
        assert quality["can_generate_report"] is True
        assert quality["total_findings"] == 3

    def test_few_findings_generates_warning(self):
        state = {
            **initial_state("hydrogen"),
            "merged_results": [_finding("https://a.com")],
        }
        quality = check_state_quality(state)
        # 1 finding < 3 → warning about limited quality
        assert any("few" in w.lower() for w in quality["warnings"])

    def test_no_crawl_success_and_no_rag_generates_warning(self):
        state = {
            **initial_state("hydrogen"),
            "merged_results": [_finding(), _finding("https://b.com"), _finding("https://c.com")],
            "crawled_results": [
                {"url": "https://example.com", "extraction_success": False}
            ],
            "rag_context": [],
        }
        quality = check_state_quality(state)
        assert any("crawl" in w.lower() or "snippet" in w.lower() for w in quality["warnings"])

    def test_single_source_type_generates_warning(self):
        state = {
            **initial_state("hydrogen"),
            "merged_results": [
                _finding("https://a.com", source_type="rss"),
                _finding("https://b.com", source_type="rss"),
                _finding("https://c.com", source_type="rss"),
            ],
        }
        quality = check_state_quality(state)
        assert any("source type" in w.lower() for w in quality["warnings"])

    def test_multiple_source_types_no_diversity_warning(self):
        state = {
            **initial_state("hydrogen"),
            "merged_results": [
                _finding("https://a.com", source_type="news"),
                _finding("https://b.com", source_type="rss"),
                _finding("https://c.com", source_type="organic"),
            ],
        }
        quality = check_state_quality(state)
        assert not any("source type" in w.lower() for w in quality["warnings"])

    def test_crawl_success_count_correct(self):
        state = {
            **initial_state("hydrogen"),
            "merged_results": [_finding(), _finding("https://b.com"), _finding("https://c.com")],
            "crawled_results": [
                {"url": "https://example.com/article", "extraction_success": True},
                {"url": "https://example.com/other", "extraction_success": False},
            ],
        }
        quality = check_state_quality(state)
        assert quality["crawl_success_count"] == 1

    def test_rag_context_count_reflected(self):
        state = {
            **initial_state("hydrogen"),
            "merged_results": [_finding(), _finding("https://b.com"), _finding("https://c.com")],
            "rag_context": [{"title": "old", "url": "x", "snippet": "y", "score": 0.8}],
        }
        quality = check_state_quality(state)
        assert quality["rag_context_count"] == 1

    def test_source_types_sorted(self):
        state = {
            **initial_state("hydrogen"),
            "merged_results": [
                _finding("https://a.com", source_type="rss"),
                _finding("https://b.com", source_type="news"),
                _finding("https://c.com", source_type="organic"),
            ],
        }
        quality = check_state_quality(state)
        assert quality["source_types"] == sorted(quality["source_types"])

    def test_majority_empty_snippets_generates_warning(self):
        state = {
            **initial_state("hydrogen"),
            "merged_results": [
                _finding("https://a.com", snippet=""),
                _finding("https://b.com", snippet=""),
                _finding("https://c.com", snippet="Good content here."),
            ],
        }
        quality = check_state_quality(state)
        assert any("snippet" in w.lower() for w in quality["warnings"])

    def test_return_dict_has_all_required_keys(self):
        quality = check_state_quality(initial_state("hydrogen"))
        required = {
            "total_findings", "crawl_success_count", "rag_context_count",
            "source_types", "warnings", "errors", "can_generate_report",
        }
        assert required.issubset(quality.keys())
