"""Output validation for HYMIND report generation.

Validates collected findings before report synthesis to detect common data
quality issues: missing URLs, duplicate entries, empty titles, empty summaries.

Used by report_generator.py before calling OpenAI to ensure the context
passed to the LLM is clean and meaningful.
"""

from __future__ import annotations

import dataclasses

from hymind.utils.logger import get_logger

logger = get_logger(__name__)

_MIN_SNIPPET_CHARS: int = 5


@dataclasses.dataclass
class ValidationResult:
    """Summary of a validation pass over a list of findings."""

    total_input: int
    valid_count: int
    issues: list[str]
    duplicate_count: int
    missing_url_count: int
    missing_title_count: int
    empty_snippet_count: int
    can_generate_report: bool

    @property
    def invalid_count(self) -> int:
        return self.total_input - self.valid_count


def validate_findings(findings: list[dict]) -> tuple[list[dict], ValidationResult]:
    """Validate and filter a list of research findings before report generation.

    Removes entries with missing URLs and de-duplicates by normalized URL.
    Entries with missing titles or very short snippets are flagged as warnings
    but are kept in the valid set — they may still contribute context.

    Args:
        findings: Raw finding dicts from AgentState['merged_results'].

    Returns:
        Tuple of (valid_findings, ValidationResult).
    """
    issues: list[str] = []
    valid: list[dict] = []
    seen_urls: set[str] = set()

    missing_url = 0
    missing_title = 0
    empty_snippet = 0
    duplicate = 0

    for i, finding in enumerate(findings):
        url = (finding.get("url") or "").strip()
        title = (finding.get("title") or "").strip()
        snippet = (finding.get("snippet") or "").strip()

        if not url:
            missing_url += 1
            issues.append(f"finding[{i}]: skipped — missing URL (title={title[:60]!r})")
            continue

        url_key = url.rstrip("/").lower()
        if url_key in seen_urls:
            duplicate += 1
            issues.append(f"finding[{i}]: skipped — duplicate URL ({url[:80]})")
            continue

        if not title:
            missing_title += 1
            issues.append(f"finding[{i}]: warning — missing title ({url[:80]})")

        if len(snippet) < _MIN_SNIPPET_CHARS:
            empty_snippet += 1
            issues.append(f"finding[{i}]: warning — empty/very short snippet ({url[:80]})")

        seen_urls.add(url_key)
        valid.append(finding)

    result = ValidationResult(
        total_input=len(findings),
        valid_count=len(valid),
        issues=issues,
        duplicate_count=duplicate,
        missing_url_count=missing_url,
        missing_title_count=missing_title,
        empty_snippet_count=empty_snippet,
        can_generate_report=len(valid) > 0,
    )

    if result.duplicate_count or result.missing_url_count:
        logger.warning(
            "validate_findings | total=%d | valid=%d | duplicates=%d | missing_url=%d"
            " | missing_title=%d | empty_snippet=%d",
            result.total_input,
            result.valid_count,
            result.duplicate_count,
            result.missing_url_count,
            result.missing_title_count,
            result.empty_snippet_count,
        )
    else:
        logger.info(
            "validate_findings | total=%d | valid=%d | missing_title=%d | empty_snippet=%d",
            result.total_input,
            result.valid_count,
            result.missing_title_count,
            result.empty_snippet_count,
        )

    for issue in issues:
        if "skipped" in issue:
            logger.warning("Validation: %s", issue)
        else:
            logger.debug("Validation: %s", issue)

    return valid, result


def check_state_quality(state: dict) -> dict[str, object]:
    """Assess research state quality before report generation.

    Inspects the completed AgentState and returns a quality summary with
    warnings, errors, and a can_generate_report flag. Does not modify state.

    Args:
        state: Completed AgentState dict from the research workflow.

    Returns:
        Dict with keys:
            total_findings (int), crawl_success_count (int),
            rag_context_count (int), source_types (list[str]),
            warnings (list[str]), errors (list[str]),
            can_generate_report (bool).
    """
    merged = state.get("merged_results", [])
    crawled = state.get("crawled_results", [])
    rag = state.get("rag_context", [])

    crawl_success = sum(1 for r in crawled if r.get("extraction_success"))
    source_types = sorted({r.get("source_type", "unknown") for r in merged})

    warnings: list[str] = []
    errors: list[str] = []

    if not merged:
        errors.append("No findings collected — report will have no source material")
    elif len(merged) < 3:
        warnings.append(
            f"Very few findings collected ({len(merged)}) — report quality may be limited"
        )

    if not crawl_success and not rag:
        warnings.append(
            "No successful crawls and no RAG context — report based on snippets only"
        )

    if len(source_types) == 1:
        warnings.append(
            f"Only one source type in results ({source_types[0]}) — limited source diversity"
        )

    if merged:
        no_snippet = sum(1 for r in merged if not (r.get("snippet") or "").strip())
        if no_snippet / len(merged) > 0.5:
            warnings.append(
                f"{no_snippet}/{len(merged)} findings have empty snippets — context may be thin"
            )

    can_generate = len(errors) == 0

    quality = {
        "total_findings": len(merged),
        "crawl_success_count": crawl_success,
        "rag_context_count": len(rag),
        "source_types": source_types,
        "warnings": warnings,
        "errors": errors,
        "can_generate_report": can_generate,
    }

    if errors:
        for err in errors:
            logger.error("State quality: %s", err)
    if warnings:
        for w in warnings:
            logger.warning("State quality: %s", w)

    logger.info(
        "check_state_quality | findings=%d | crawl_ok=%d | rag=%d"
        " | sources=%s | can_generate=%s",
        quality["total_findings"],
        quality["crawl_success_count"],
        quality["rag_context_count"],
        quality["source_types"],
        quality["can_generate_report"],
    )

    return quality
