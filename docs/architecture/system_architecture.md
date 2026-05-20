# HYMIND System Architecture

# Overview

HYMIND is an autonomous hydrogen market intelligence and data platform built around a modular multi-layer architecture.

The system combines:

- LangGraph based autonomous research orchestration
- Multi source intelligence collection
- OpenAI powered analysis and synthesis
- RAG based historical context retrieval
- Reliability and validation layers
- Optional n8n based distribution automation

The architecture separates:

- Core research intelligence
- Knowledge and retrieval systems
- Reliability and validation
- External report distribution

This separation keeps the system maintainable, scalable, and production oriented.

---

# High Level Architecture

```text
Research Trigger
        ↓
LangGraph Research Workflow
        ↓
Multi Source Intelligence Collection
        ↓
Content Cleaning & Deduplication
        ↓
Classification & Validation
        ↓
RAG Context Retrieval
        ↓
OpenAI Analysis & Synthesis
        ↓
Markdown Executive Report
        ↓
Phase 5 Distribution Layer [Optional]
        ↓
PDF Generation
        ↓
Gmail / Telegram Delivery
        ↓
Delivery Logging & Archiving
```

---

# Core System Layers

# 1. Trigger Layer

The system can start through multiple trigger types.

## Supported Triggers

- Manual execution
- Scheduled execution
- Future webhook execution
- Future event based triggers

## Current MVP

The MVP currently supports:

- Manual Python execution
- Scheduled workflow support prepared for n8n integration

---

# 2. Research Collection Layer

The research layer gathers intelligence from multiple external sources.

## APIs

### Serper API

Used for:

- Google search based intelligence gathering
- Competitor research
- Market developments
- Technical announcements

### NewsAPI

Used for:

- Structured news aggregation
- Industry news monitoring
- Political developments
- Funding announcements

---

## RSS Feed Collection

RSS feeds are used because many hydrogen industry platforms do not expose APIs.

### Example Sources

- Hydrogen Insight
- Fuel Cells Works
- H2 View
- Government hydrogen programs
- Energy research institutions

---

## Website Crawling

Controlled crawling is used for:

- Press releases
- Strategy documents
- Technical publications
- Research announcements
- Funding information

### Technologies

- BeautifulSoup
- Requests
- Playwright [future option]

---

# 3. Processing & Validation Layer

Collected content is normalized and validated before analysis.

## Responsibilities

- Content cleaning
- HTML removal
- Deduplication
- Schema normalization
- Validation
- Relevance filtering
- Metadata extraction

---

# 4. RAG & Knowledge Layer

The RAG layer stores and retrieves historical intelligence.

## Purpose

The retrieval system improves:

- Historical awareness
- Trend analysis
- Context retention
- Long term intelligence quality
- Report consistency

---

## Current Implementation

### Vector Database

- Pinecone

### Embeddings

- OpenAI embeddings

### Stored Data

- Research findings
- Summaries
- Metadata
- Source references
- Historical context

---

# 5. LangGraph Orchestration Layer

LangGraph coordinates the autonomous workflow.

## Responsibilities

- State management
- Workflow routing
- Tool orchestration
- Validation handling
- Retry handling
- Context propagation
- Multi step execution

---

## Current Workflow

```text
Research Input
    ↓
Source Collection
    ↓
Normalization
    ↓
Deduplication
    ↓
Validation
    ↓
RAG Retrieval
    ↓
OpenAI Synthesis
    ↓
Report Generation
```

---

# 6. OpenAI Analysis Layer

OpenAI performs the reasoning and synthesis tasks.

## Responsibilities

- Summarization
- Strategic analysis
- Trend interpretation
- Executive synthesis
- Report generation
- Context aware reasoning

---

# 7. Report Generation Layer

The system generates structured Markdown reports.

## Current Output

- Markdown executive reports
- Structured report sections
- Source linked findings
- Strategic summaries

---

## Planned Report Types

- Weekly executive reports
- Competitor intelligence reports
- Technology trend reports
- Funding and policy reports
- Strategic alerts

---

# 8. Reliability & Hardening Layer

This layer improves operational stability and production readiness.

## Responsibilities

- Retry logic
- Error handling
- API validation
- Schema validation
- Fallback handling
- Logging
- Failure isolation
- Rate limit handling

---

## Goal

Ensure the autonomous workflow operates reliably without manual intervention.

---

# 9. Phase 5 Distribution Layer

The distribution layer is intentionally separated from the core intelligence pipeline.

This layer is optional for the MVP core workflow and focuses on external delivery automation.

---

## Responsibilities

- n8n orchestration
- Markdown report loading
- PDF generation
- Gmail delivery
- Telegram notifications
- Delivery logging
- Report archiving

---

## Implemented Workflow (Phase 5)

```text
Markdown Report
    ↓
FastAPI /run-hymind endpoint
    ↓
n8n Schedule Trigger (Monday 08:00)
    ↓
HTTP Request → FastAPI server (via ngrok)
    ↓
IF status == success
    ↓
Markdown → HTML (n8n built-in conversion)
    ↓
Gmail Delivery
    ↓
Google Sheets Delivery Logging
```

**Note on PDF:** PDF generation was evaluated and descoped from the MVP. The n8n workflow converts Markdown to HTML inline using n8n's built-in Markdown node, producing an email-readable format without an additional dependency.

---

# Repository Structure

```text
HYMIND/
│
├── src/
│   ├── api/                  # FastAPI HTTP wrapper (Phase 5)
│   ├── rag/                  # Pinecone RAG layer (Phase 3)
│   ├── reporting/            # Report generator + output validator (Phase 4)
│   ├── workflows/            # LangGraph pipeline + AgentState
│   ├── tools/                # Serper, NewsAPI, RSS, crawler, collector
│   ├── utils/                # Shared logger
│   └── main.py               # CLI entry point
│
├── n8n/                      # Exported n8n workflow JSON files (Phase 5)
│
├── docs/
│   ├── architecture/
│   ├── operations/
│   ├── roadmap/
│   └── planning/
│       └── stories.md
│
├── memory/
│   └── active/
│
├── skills/
│
├── tests/                    # 243-test automated suite
│
├── outputs/
│   ├── reports/              # Generated reports
│   └── sample_reports/       # 3 example reports
│
├── AGENTS.md
├── README.md
├── requirements.txt
└── .env.example
```

---

# Architectural Design Decisions

# Why LangGraph

LangGraph was selected because:

- Multi step workflows are required
- State handling is important
- Tool orchestration is easier
- Validation and retries are easier to control
- Future autonomous routing is supported

---

# Why RAG

RAG was selected because:

- Historical context matters
- Trend analysis requires memory
- Long term intelligence improves report quality
- Repeated information can be reused efficiently

---

# Why n8n

n8n was selected because:

- Excellent workflow orchestration
- Reliable scheduling
- Easy external integrations
- Strong automation ecosystem
- Good fit for report distribution workflows

---

# Current MVP Scope

The MVP currently includes:

- Hydrogen industry intelligence
- Multi source research
- LangGraph orchestration
- OpenAI analysis
- Pinecone RAG
- Markdown report generation
- Reliability features
- Structured testing

---

# Future Extensions

Possible future improvements:

- Microsoft Teams integration
- SharePoint integration
- LinkedIn monitoring
- Real time dashboards
- Human approval workflows
- Multi company comparison
- Predictive intelligence
- Internal enterprise knowledge integration
- Automated briefing generation
- Multi language support

---

# Architectural Philosophy

HYMIND follows a layered architecture philosophy.

The system intentionally separates:

- Intelligence gathering
- Knowledge retrieval
- Analysis and reasoning
- Reliability handling
- Distribution automation

This separation improves:

- Maintainability
- Scalability
- Reliability
- Testability
- Future extensibility