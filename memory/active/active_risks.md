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

---

## RISK-007 — Pinecone Index Not Created

**Severity:** Medium  
**Status:** Open — mitigated by graceful degradation

The Pinecone index (`hymind-research`, 1536 dimensions, cosine metric) must be
created manually before the RAG layer can activate. The pipeline degrades gracefully
if the index does not exist or credentials are absent — both RAG nodes emit a
warning and continue. However, if the API key is set but the index does not exist,
Pinecone will raise an exception caught by the node's try/except.

**Mitigation:** Pipeline continues with warning. Clear README instructions provided.
**Action needed:** Create Pinecone index manually before activating RAG.

---

## RISK-008 — OpenAI Embedding Cost (Phase 3)

**Severity:** Low  
**Status:** Open — accepted

Each run with ~20 findings embeds ~5,000 tokens via text-embedding-3-small
($0.02/1M tokens). Daily runs: ~$0.10/month. Negligible at current scale.

**Mitigation:** Default model is text-embedding-3-small (lowest cost). Monitor via
OpenAI usage dashboard if run frequency increases significantly.
**Action needed:** None at MVP scale.

---

## RISK-009 — Duplicate Vector Upserts

**Severity:** Low  
**Status:** Mitigated

Vector IDs are derived from SHA-256 of the URL (48 hex chars). Re-running the
pipeline for the same topic will re-upsert the same vector IDs with potentially
updated metadata. Pinecone treats this as an overwrite (idempotent upsert).

**Mitigation:** Idempotent by design. No action needed.
