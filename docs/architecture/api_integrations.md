# API Integrations

## Active Integrations (Phase 1 + Phase 2)

| Integration | Purpose | Status | Module |
|---|---|---|---|
| NewsAPI | Structured news collection from thousands of publishers | Active | `src/hymind/tools/news_api.py` |
| Serper API | Google Search-based research for hydrogen topics | Active | `src/hymind/tools/serper_search.py` |
| RSS feeds | Monitor recurring industry sources | Active | `src/hymind/tools/rss_reader.py` |
| Web crawler | Extract full article content from URLs | Active | `src/hymind/tools/web_crawler.py` |
| OpenAI | Report synthesis and executive formatting | Active | `src/hymind/tools/openai_client.py` |

## Planned Integrations

| Integration | Purpose | Status | Notes |
|---|---|---|---|
| Telegram or Gmail | Send report alerts | Planned | For Phase 6 distribution automation |
| ChromaDB or FAISS | Cross-run duplicate detection and retrieval | Planned | For Phase 3 RAG and memory |
| n8n | Scheduling and orchestration | Planned | For Phase 6 automation |

---

## NewsAPI

### Authentication

NewsAPI uses a single header key:

```http
X-Api-Key: <NEWS_API_KEY>
```

The key is never passed as a query parameter to prevent exposure in server logs and debug output. Set `NEWS_API_KEY` in your local `.env` file (never commit it).

### Endpoint

```
GET https://newsapi.org/v2/everything
```

Overridable via `NEWS_API_BASE_URL` environment variable (used in tests to intercept requests).

### Parameters

| Parameter | Description | Default |
|---|---|---|
| `q` | Search query | Required |
| `language` | ISO 639-1 language code | `en` |
| `sortBy` | `publishedAt`, `relevancy`, or `popularity` | `publishedAt` |
| `pageSize` | Number of articles (1–100) | `MAX_ARTICLES_PER_RUN` env var or `10` |

### Rate Limits

| Plan | Requests/day | Article delay | Price |
|---|---|---|---|
| Developer (free) | 100 | 24 hours | $0 |
| Business | 250,000 | Real-time | $449/month |
| Enterprise | Unlimited | Real-time | Custom |

The Developer plan is sufficient for weekly automated runs (5–10 requests per pipeline execution).

### Failure Modes

| Condition | HTTP Status | Behaviour |
|---|---|---|
| Invalid API key | 401 | `requests.HTTPError` — not retried |
| Disabled API key | 403 | `requests.HTTPError` — not retried |
| Rate limit | 429 | `NewsAPIRateLimitError` — retried 3x with exponential backoff |
| Server error | 5xx | `NewsAPIServerError` — retried 3x with exponential backoff |
| Network timeout | — | `requests.Timeout` — retried 3x |
| Connection failure | — | `requests.ConnectionError` — retried 3x |
| Malformed JSON body | 200 | `ValueError` raised with error log |
| Empty results | 200 | Returns `[]`, logs WARNING |
| `[Removed]` placeholder | 200 | Filtered out silently |
| Missing URL or title | 200 | Filtered out with DEBUG log |

### Normalized Output Schema

All results use the shared 9-field schema:

```
title, url, snippet, published_at, source, source_type, search_query, author, rank
```

`source_type` is always `"news"` for NewsAPI results.

### Known Limitations

- Free plan results are delayed 24 hours — not suitable for real-time monitoring
- Free plan limited to the past 30 days of coverage
- Some publishers block or restrict access via NewsAPI terms
- `from` and `to` date parameters are not yet wired into `search()` (planned for Phase 3)

---

## Serper API

### Authentication

```http
X-API-KEY: <SERPER_API_KEY>
```

### Endpoint

```
POST https://google.serper.dev/search
```

### Normalized Output

Same 9-field schema. `source_type` is `"organic"` for web search results and `"news"` when using `search_type="news"`.

`author` is always `None` (Serper does not return author metadata).

---

## RSS Feeds

No API key required. Uses `requests` for HTTP with a 20-second timeout and `feedparser` for parsing.

Default hydrogen feeds:
- https://www.hydrogeninsight.com/rss
- https://www.h2-view.com/feed/
- https://fuelcellsworks.com/feed/

`source_type` is always `"rss"`. HTML is stripped from snippet fields during normalization.

---

## Integration Rules

- Each integration lives in its own module under `src/hymind/tools/`
- API keys are read from environment variables only — never hardcoded
- All results are normalized to the shared 9-field schema before leaving the module
- External calls must include: retry logic, timeout handling, validation, logging, and graceful failure
- Failed requests must log clearly without exposing secrets
- Workflow nodes check for key presence before calling tools and degrade gracefully on missing keys

---

## Collector Abstraction (Phase 2)

`src/hymind/tools/collector.py` provides `CollectorProtocol` — a structural type interface that any callable with signature `(query: str, **kwargs) -> list[dict]` satisfies. All current `search()` functions satisfy it without modification.

See `docs/architecture/phase_2_research_foundation.md` for the full Phase 2 integration design.
