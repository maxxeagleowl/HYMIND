# API Integrations

## Initial Integrations

| Integration | Purpose | Status | Notes |
| --- | --- | --- | --- |
| Serper API | Google Search-based research for hydrogen topics | Planned | Useful for market, competitor, and policy discovery. |
| NewsAPI | Structured news collection from news publishers | Planned | Useful for recent headlines and topic-based filtering. |

## Later Integrations

| Integration | Purpose | Status | Notes |
| --- | --- | --- | --- |
| RSS feeds | Monitor recurring industry sources | Optional | Good for stable sources that publish frequently. |
| Requests + BeautifulSoup | Crawl specific websites | Optional | Use only where allowed and necessary. |
| Telegram or Gmail | Send report alerts | Optional | Useful for operational distribution. |
| ChromaDB or FAISS | Local memory and retrieval | Optional | Useful if the system needs long-term context. |
| n8n | Orchestration and scheduling | Optional | Useful for automation and delivery. |

## Integration Rules

- Keep each integration in its own module.
- Store API keys only in local environment variables.
- Normalize all source items into a common internal structure.
- Log failures clearly without exposing secrets.

## Phase 0 Note

The APIs are documented here so the next phase can implement them without redesigning the repository.
