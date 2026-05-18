# Phase 2 — Research Foundation

## Overview

Phase 2 establishes the research integration layer that Phase 3 LangGraph orchestration will depend on.

It delivers:
- The first production-ready API integration (NewsAPI) with full reliability handling
- A collector abstraction that standardizes how all future sources plug in
- A validation layer that ensures only traceable, well-formed results enter the pipeline
- A complete mocked test suite for the NewsAPI collector

---

## Why NewsAPI Was Chosen First

NewsAPI was selected as the first integration for three reasons:

1. **Structured output** — NewsAPI returns JSON with predictable fields (title, url, description, publishedAt, source, author). No scraping or parsing required.

2. **Hydrogen coverage** — The `/everything` endpoint searches across thousands of publishers and can be narrowed to `language=en` and sorted by `publishedAt`, giving current industry news with minimal noise.

3. **Simple authentication** — A single header (`X-Api-Key`) with no OAuth flow. This makes it straightforward to validate the integration in isolation before adding more complex sources.

Serper and RSS were already integrated in Phase 1. NewsAPI completes the three-source research foundation needed before Phase 3 LangGraph workflow refinement.

---

## How NEWS_API_KEY Is Configured

```
# .env (never commit this file)
NEWS_API_KEY=your_key_here
```

The key is read from the environment by `_get_api_key()` in `src/hymind/tools/news_api.py`.

- If the key is absent at the tool level (`news_api.search()`), the function calls `sys.exit(1)` with an actionable error message.
- If the key is absent at the workflow node level (`collect_news` in `research_workflow.py`), the node logs a warning and returns `[]` so the pipeline continues using Serper and RSS results.

The dual behavior preserves flexibility: standalone tool use fails fast; workflow use degrades gracefully.

---

## What the Collector Returns

The `search()` function in `news_api.py` returns a list of dicts using the shared 9-field normalized schema:

| Field | Type | Description |
|---|---|---|
| `title` | str | Article headline, whitespace-stripped |
| `url` | str | Canonical article URL |
| `snippet` | str | Description field, HTML-stripped |
| `published_at` | str \| None | ISO 8601 publish date from `publishedAt` |
| `source` | str | Publisher name from nested `source.name` |
| `source_type` | str | Always `"news"` for NewsAPI results |
| `search_query` | str | The query string passed to `search()` |
| `author` | str \| None | Author field, or `None` if absent |
| `rank` | int | 1-based position in the result list |

This schema matches Serper and RSS outputs so all three can be merged directly.

---

## Collector Abstraction

`src/hymind/tools/collector.py` provides:

### CollectorProtocol

A `typing.Protocol` that any callable with signature `(query: str, **kwargs) -> list[dict]` satisfies structurally. No subclassing required.

```python
from hymind.tools.collector import CollectorProtocol

# Both of these satisfy CollectorProtocol:
from hymind.tools.news_api import search as news_search
from hymind.tools.serper_search import search as serper_search
```

This allows workflow nodes to accept any collector as a dependency without coupling to a specific implementation. It is the interface that Phase 3 orchestration will use when adding a second integration.

### Validation Functions

```python
from hymind.tools.collector import validate_result, validate_results

# Single item
ok, issues = validate_result(result)

# Batch — drops and logs invalid items
clean_results = validate_results(raw_results)
```

`validate_result` checks:
- All 9 required fields are present
- `url` is non-empty (result must be traceable)
- `source_type` is non-empty
- `snippet` is free of raw HTML tags

`validate_results` wraps `validate_result` for batch use and logs each dropped item as a WARNING.

---

## Known Limitations

### NewsAPI Developer Plan

On the free Developer plan:
- **100 requests per day** maximum
- Results are **delayed 24 hours** (no real-time news)
- Maximum **100 articles per request** (pageSize parameter)
- No access to sources blocked by the terms of service

For production use, the Business or Enterprise plan is required for real-time results and higher rate limits.

### source_type Value

The `source_type` field is set to `"news"` (not `"newsapi"`) for NewsAPI results. This matches the value already used in the RSS (`"rss"`) and Serper (`"organic"`, `"news"`) normalizers and is consistent across the Phase 1 test suite. Changing it would require updating 5 existing tests; the current value is correct and unambiguous.

### Date Range

The free plan only allows queries over the past 30 days. The `from` and `to` query parameters are supported in the API but not yet wired into `search()`. This can be added in Phase 3 when the workflow needs time-bounded queries.

---

## Cost and Rate Limit Considerations

| Plan | Price | Requests/day | Delay |
|---|---|---|---|
| Developer (free) | $0 | 100 | 24h |
| Business | $449/month | 250,000 | Real-time |
| Enterprise | Custom | Unlimited | Real-time |

The Developer plan is sufficient for weekly automated report generation (which makes at most 5–10 requests per run). Monitor usage at https://newsapi.org/account.

Rate limit responses (HTTP 429 and application-level `rateLimited` code) are handled by the tenacity retry decorator with exponential backoff (min 2s, max 15s, 3 attempts). After exhaustion, `NewsAPIRateLimitError` is re-raised.

---

## Failure Mode Reference

| Failure | HTTP Status | Handling |
|---|---|---|
| Invalid API key | 401 | `requests.HTTPError` raised immediately (not retried) |
| Disabled API key | 403 | `requests.HTTPError` raised immediately (not retried) |
| Rate limit | 429 | `NewsAPIRateLimitError` raised, retried 3x then re-raised |
| Server error | 5xx | `NewsAPIServerError` raised, retried 3x then re-raised |
| Network timeout | — | `requests.Timeout` raised, retried 3x then re-raised |
| Connection failure | — | `requests.ConnectionError` raised, retried 3x then re-raised |
| Malformed JSON | 200 | `ValueError` raised with logged error context |
| Empty results | 200 | `[]` returned, WARNING logged |
| `[Removed]` articles | 200 | Filtered out silently during normalization |
| Articles without URL | 200 | Filtered out with DEBUG log |
| Articles without title | 200 | Filtered out with DEBUG log |

---

## How This Prepares Phase 3

Phase 3 will:
1. Wire the collector abstraction into the LangGraph workflow so nodes accept `CollectorProtocol` arguments
2. Add `validate_results` as a post-collection node to enforce schema integrity before deduplication
3. Add a second API integration (Serper news type or a dedicated hydrogen source) using the same `CollectorProtocol` interface
4. Add date-range parameters to `news_api.search()` for time-bounded weekly queries
5. Add ChromaDB or FAISS for duplicate detection across runs (persistent deduplication beyond URL matching)
