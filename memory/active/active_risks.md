# Active Risks

## RISK-001 - OpenAI API Cost Overrun

**Severity:** Medium  
**Status:** Open

No per-run token budget is enforced. Synthesis calls with large merged_results contexts could consume significant tokens.

**Mitigation:** max_tokens is capped in the report generator. Monitor usage manually.
**Action needed:** Add a token budget guard in the report synthesis path.

---

## RISK-002 - NewsAPI Rate Limits

**Severity:** Medium  
**Status:** Open - mitigated at integration level

NewsAPI free tier limits can trigger HTTP 429 responses on repeated runs.
Tenacity retry with exponential back-off is implemented in `news_api.py`.

**Mitigation:** Retry is already implemented. `MAX_ARTICLES_PER_RUN=10` limits per-call volume.
**Action needed:** Add run deduplication/caching if scheduling frequency increases.

---

## RISK-003 - Serper Query Cost

**Severity:** Low  
**Status:** Open

Serper charges per query. Each workflow run consumes at least one search query.

**Mitigation:** Query volume is currently manual.
**Action needed:** Add query deduplication/caching before automation grows.

---

## RISK-004 - Automated Test Coverage Drift

**Severity:** Medium  
**Status:** Resolved

The repository now has an automated test suite covering the core workflow, collectors, crawler, report generation, and RAG layer. This risk is retained only as a reminder to keep coverage current as Phase 4 and Phase 6 expand.

**Mitigation:** 170 tests currently pass. Add new tests for any Phase 4 or Phase 6 changes.
**Action needed:** Keep the suite updated when the distribution layer is implemented.

---

## RISK-005 - JS-Rendered Sites in Crawler

**Severity:** Low  
**Status:** Known limitation, accepted

Sites using React/Next.js can return shell HTML. `crawl()` returns `extraction_success=False` correctly. Workflow continues, but crawl success rate depends on URL mix.

**Mitigation:** `extraction_success` allows downstream filtering.
**No action needed** until crawler capabilities are expanded.

---

## RISK-006 - LangGraph sys.exit Propagation

**Severity:** Low  
**Status:** Resolved

Tool clients previously called `sys.exit(1)` when API keys were missing. Inside LangGraph nodes this could kill the process. The workflow now pre-checks API keys before calling tools, so missing keys become warnings rather than exits.

---

## RISK-007 - Pinecone Index Not Created

**Severity:** Medium  
**Status:** Open - mitigated by graceful degradation

The Pinecone index (`hymind-research`, 1536 dimensions, cosine metric) must be created manually before the RAG layer can activate. The pipeline degrades gracefully if the index or credentials are missing, but the vector layer will not store or retrieve history.

**Mitigation:** Pipeline continues with warning. Clear README instructions provided.
**Action needed:** Create the Pinecone index manually before activating RAG.

---

## RISK-008 - OpenAI Embedding Cost (Phase 3)

**Severity:** Low  
**Status:** Open - accepted

Each run with ~20 findings embeds ~5,000 tokens via `text-embedding-3-small`. Daily usage remains low at the current scale.

**Mitigation:** Default model is `text-embedding-3-small`. Monitor usage if run frequency increases significantly.
**Action needed:** None at MVP scale.

---

## RISK-009 - Duplicate Vector Upserts

**Severity:** Low  
**Status:** Mitigated

Vector IDs are derived from a hash of the URL. Re-running the pipeline for the same topic re-upserts the same IDs with updated metadata. Pinecone treats this as an idempotent overwrite.

**Mitigation:** Idempotent by design. No action needed.

---

## RISK-010 - Phase 6 Delivery Automation Regression

**Severity:** Medium  
**Status:** Open

The Phase 6 n8n/PDF/Gmail/Telegram delivery layer introduces new failure modes around file generation, workflow triggers, and external delivery APIs.

**Mitigation:** Keep Phase 6 isolated from the core LangGraph pipeline and require logging, retries, and archive checks in the workflow design.
**Action needed:** Validate delivery retries, PDF generation, and report archiving before enabling production use.
