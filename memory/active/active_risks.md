# Active Risks

## RISK-001 — OpenAI API Cost Overrun

**Severity:** Medium  
**Status:** Open

No per-run token budget enforced. Synthesis calls with large merged_results
contexts could consume significant tokens.

**Mitigation:** max_tokens capped at 2000 per call. Monitor usage manually.
**Action needed:** Add token budget guard in HYM-012 (report generator).

---

## RISK-002 — NewsAPI Rate Limits

**Severity:** Medium  
**Status:** Open — mitigated at integration level

NewsAPI free tier: 100 requests/day. High-frequency runs will hit HTTP 429.
Tenacity retry with exponential back-off is implemented in news_api.py.

**Mitigation:** Retry implemented. MAX_ARTICLES_PER_RUN=10 limits per-call volume.
**Action needed:** Add run deduplication/caching in HYM-011 follow-up.

---

## RISK-003 — Serper Query Cost

**Severity:** Low  
**Status:** Open

Serper charges per query. Each workflow run consumes one Serper query.

**Mitigation:** Query volume is currently manual (one run at a time).
**Action needed:** Add query deduplication/caching before scheduling automation.

---

## RISK-004 — No Integration Tests

**Severity:** Medium  
**Status:** Open

No automated test suite. All verification is manual smoke testing.

**Action needed:** Add tests/ directory before HYM-018 (final testing).

---

## RISK-005 — JS-Rendered Sites in Crawler

**Severity:** Low  
**Status:** Known limitation, accepted

Sites using React/Next.js return shell HTML. crawl() returns extraction_success=False
correctly. Workflow continues — crawled_results may have low success rate depending
on URL mix.

**Mitigation:** extraction_success flag allows downstream filtering.
**No action needed** until Phase 3 (advanced orchestration).

---

## RISK-006 — LangGraph sys.exit Propagation

**Severity:** Low  
**Status:** Resolved

Tool clients call sys.exit(1) when API keys are missing. Inside LangGraph nodes,
this would kill the process. Fixed by pre-checking API keys via os.getenv() in
each node before calling the tool — missing keys become warnings, not exits.
