# Active Risks

## RISK-001 — OpenAI API Cost Overrun

**Severity:** Medium
**Status:** Open

No per-run token budget or cost guard is implemented. Synthesis calls with large
research contexts could consume significant tokens.

**Mitigation:** `max_tokens` is capped at 2000 per call. Monitor usage during testing.
**Action needed:** Add token budget enforcement when LangGraph workflow is built (HYM-011).

---

## RISK-002 — NewsAPI Rate Limits

**Severity:** Medium
**Status:** Open — integration not yet built

NewsAPI free tier allows 100 requests per day. High-frequency runs will hit HTTP 429.

**Mitigation:** Exponential back-off retry is already the established pattern.
Fallback to RSS feeds when NewsAPI fails.
**Action needed:** Implement in HYM-008.

---

## RISK-003 — Serper Query Cost

**Severity:** Low
**Status:** Open

Serper charges per query. Uncontrolled query volume across runs could consume
monthly quota unexpectedly.

**Mitigation:** `MAX_SEARCH_RESULTS` cap is enforced. Query volume is currently manual.
**Action needed:** Add query deduplication when LangGraph workflow is built (HYM-011).

---

## RISK-004 — No Integration Tests

**Severity:** Medium
**Status:** Open

No automated tests exist. Manual smoke testing only at this stage.

**Action needed:** Add a tests/ directory with minimal integration tests before HYM-018.

---

## RISK-005 — Missing pyproject.toml Previously (Resolved)

**Severity:** Low
**Status:** Resolved

The `src/` layout package was not installable. Now resolved via `pyproject.toml`.
