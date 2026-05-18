# Skill - API Integration Standards

# skill_api_integration.md

---

# Purpose

This skill defines the API integration standards for the HYMIND project.

The goal is to ensure that all external integrations remain reliable, maintainable, secure, and production ready.

This skill applies to:

- REST APIs
- Search APIs
- News APIs
- RSS retrieval
- Web crawling
- LLM providers
- Future MCP integrations
- Future enterprise integrations

---

# Core Philosophy

External APIs are unreliable by default.

All integrations must assume:

- Network instability
- Rate limits
- Invalid responses
- Partial failures
- Timeout risks
- Authentication failures
- Temporary outages

Every integration must therefore include defensive engineering practices.

---

# Mandatory API Requirements

Every API integration must include:

- Timeout handling
- Retry logic
- Input validation
- Response validation
- Structured logging
- Graceful failure handling
- Environment variable based credentials

No direct uncontrolled API calls are allowed.

---

# Environment Variable Rules

All secrets must use environment variables.

Hardcoded credentials are strictly forbidden.

---

# Required Credential Structure

```env
OPENAI_API_KEY=
SERPER_API_KEY=
NEWSAPI_KEY=
ALPHAVANTAGE_API_KEY=
```

---

# Credential Management Rules

## Rule 1

Never commit real credentials to Git.

---

## Rule 2

Only `.env.example` may exist inside the repository.

---

## Rule 3

All runtime secrets must load through environment variables.

---

## Rule 4

Missing credentials must generate clear validation errors.

---

# Timeout Standards

All API calls must define explicit timeouts.

Recommended default timeout:

```python
timeout=30
```

Long running operations must remain configurable.

No request should run indefinitely.

---

# Retry Standards

Retry logic is mandatory for unstable integrations.

Recommended retry scenarios:

- Timeout
- Temporary connection failure
- HTTP 429
- HTTP 500
- HTTP 502
- HTTP 503
- HTTP 504

---

# Retry Philosophy

Retries should remain:

- Limited
- Controlled
- Logged
- Exponential when appropriate

Infinite retries are forbidden.

---

# Validation Standards

## Input Validation

All external requests must validate:

- Query values
- Required parameters
- Data types
- Empty values
- Unsupported inputs

---

## Response Validation

All responses must validate:

- Status code
- Expected fields
- Expected structure
- Content existence
- Empty payloads

Invalid responses must never silently continue.

---

# Logging Standards

All integrations must generate structured logs.

Logs should include:

- API name
- Request target
- Success or failure state
- Retry attempts
- Validation failures
- Timeout events

Sensitive information must never appear in logs.

---

# Error Handling Standards

Errors must remain:

- Controlled
- Readable
- Actionable
- Non destructive

The system should fail gracefully whenever possible.

---

# Graceful Failure Philosophy

If one source fails:

- The workflow should continue when possible
- The failure should be documented
- Partial results may still be generated
- The user should receive visibility into missing sources

The system should degrade gracefully instead of crashing entirely.

---

# API Wrapper Standards

Each external service should use its own wrapper module.

Preferred structure:

```text
src/hymind/tools/
├── serper_search.py
├── news_api.py
├── rss_reader.py
├── web_crawler.py
└── openai_client.py
```

---

# Wrapper Responsibilities

Each wrapper should handle:

- Authentication
- Validation
- Timeout management
- Retry logic
- Response normalization
- Error handling
- Logging

Business logic should remain outside wrappers.

---

# Response Normalization Rules

Different APIs should return normalized structures whenever possible.

Preferred normalized fields:

```python
{
    "title": "",
    "source": "",
    "url": "",
    "published_at": "",
    "summary": "",
    "content": ""
}
```

This simplifies downstream processing and report generation.

---

# Rate Limit Philosophy

APIs should be treated as rate limited resources.

The system should:

- Minimize unnecessary calls
- Avoid duplicate requests
- Support future caching
- Handle HTTP 429 responses cleanly

---

# Web Crawling Standards

Web crawling must remain:

- Controlled
- Respectful
- Minimal
- Relevant

The crawler should avoid:

- Excessive scraping
- Infinite crawling
- Irrelevant pages
- Unnecessary bandwidth usage

---

# LLM Integration Standards

LLM integrations must include:

- Prompt isolation
- Input validation
- Output validation
- Retry handling
- Cost awareness
- Structured responses where possible

Large prompts should remain manageable and modular.

---

# Future Enterprise Integration Philosophy

Future integrations may include:

- SharePoint
- Teams
- Microsoft Graph
- Internal databases
- MCP tools
- Enterprise APIs

The same reliability principles must apply to all future integrations.

---

# Reliability Philosophy

API integrations are treated as critical infrastructure.

A fragile integration is considered incomplete.

The project prioritizes:

- Stability
- Observability
- Defensive engineering
- Controlled failures
- Long term maintainability

over implementation speed.

---

# Operational Engineering Principle

All API integrations inside HYMIND must behave like production style engineering systems.

Reliable integrations are mandatory for trustworthy autonomous intelligence generation.