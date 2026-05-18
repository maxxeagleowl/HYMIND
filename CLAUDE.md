# HYMIND - Claude Runtime Instructions

## Project Identity

HYMIND is an autonomous Hydrogen Engineering Intelligence Agent.

The system researches, analyzes, synthesizes, and generates executive level intelligence reports for the hydrogen and fuel cell industry.

The project focuses on autonomous market intelligence, technical trend analysis, competitor monitoring, funding tracking, and policy intelligence.

---

# Primary Objectives

The system must:

- Collect hydrogen industry intelligence from multiple external sources
- Analyze engineering and market developments
- Generate structured executive reports
- Track funding, regulation, and technology developments
- Operate autonomously with minimal human intervention
- Maintain reliable and reproducible workflows

---

# Technology Stack

| Area | Technology |
|---|---|
| Language | Python |
| Agent Framework | LangGraph |
| Workflow Automation | n8n |
| LLM | OpenAI |
| Search | Serper API |
| News | NewsAPI |
| Vector Storage | ChromaDB or Pinecone |
| Crawling | BeautifulSoup / Playwright |
| Notifications | Gmail / Telegram |
| Reports | Markdown / PDF |

---

# Session Bootstrap Procedure

At the beginning of every session always read files in this order:

1. AGENTS.md
2. docs/project_state.md
3. docs/decision_log.md
4. docs/operations/task_board.md
5. memory/active/latest_context.md
6. memory/active/current_focus.md
7. memory/active/active_risks.md

After reading:
- Summarize current state
- Identify active task
- Identify blockers
- Recommend next implementation step

---

# End Of Session Procedure

Before ending any work session always:

1. Update docs/project_state.md
2. Update docs/decision_log.md
3. Update docs/operations/progress_log.md
4. Update memory/active/latest_context.md
5. Update memory/active/current_focus.md
6. Update memory/active/active_risks.md if needed

---

# Required End Of Session Summary

Every session must document:

- What was completed
- What changed
- Current architecture state
- Open issues
- Active blockers
- Next recommended task
- Risks introduced
- Dependencies added or changed

---

# Repository Validation Before Session End

Before ending a session verify:

- No secrets were committed
- .env is ignored
- Documentation is synchronized
- New files are referenced correctly
- Project structure remains clean
- No broken imports exist
- No temporary debug files remain

---

# Commit Rules

If meaningful progress was completed:

- Create a clean focused commit
- Use a descriptive commit message
- Avoid mixing unrelated changes

Example:

feat: implement rss ingestion pipeline

fix: improve api retry handling

docs: update architecture and workflow documentation

---

# Session Continuity Goal

The repository must always contain enough updated context so that a new session can continue development immediately without relying on hidden chat memory.

---

# Engineering Philosophy

The project prioritizes:

- Reliability over complexity
- Modular architecture
- Maintainability
- Clear workflows
- Reproducible outputs
- Production style structure
- Minimal unnecessary dependencies

---

# MVP Scope Rules

The MVP must remain focused.

Allowed:
- Weekly executive reports
- Research automation
- API integrations
- RSS feeds
- Web crawling
- Basic RAG
- Structured report generation
- Telegram or Gmail notifications

Not allowed during MVP:
- Real time dashboards
- Multi industry support
- Complex forecasting
- Advanced predictive analytics
- Full enterprise deployment
- Large scale microservice architecture

---

# Coding Standards

## General

- Write readable production style Python
- Prefer simple solutions over abstract architectures
- Keep functions modular
- Use explicit naming
- Add comments only where useful
- Avoid unnecessary frameworks

---

## Error Handling

All external integrations must include:

- Validation
- Retry logic
- Timeout handling
- Graceful failure handling
- Logging

---

## API Rules

Never:
- Hardcode secrets
- Commit API keys
- Commit .env files

Always:
- Use environment variables
- Maintain .env.example
- Validate API responses

---

# Documentation Rules

Every major implementation change must update:

- docs/project_state.md
- docs/decision_log.md
- docs/operations/progress_log.md

Architecture changes must also update:
- docs/architecture/

---

# Git Rules

Commits should:
- Be small and focused
- Use meaningful commit messages
- Avoid unrelated file modifications

---

# Skills Usage

Reusable logic and workflows belong inside:

skills/

Each skill should contain:
- Purpose
- Inputs
- Outputs
- Workflow rules
- Expected format

---

# Reporting Standards

Reports must:
- Be executive readable
- Use structured sections
- Separate facts from interpretation
- Preserve source traceability
- Focus on relevance and implications

---

# Reliability Requirements

The system must:
- Fail gracefully
- Never crash silently
- Log important workflow events
- Preserve deterministic outputs where possible

---

# Decision Making Priority

When uncertain prioritize:

1. Stability
2. Simplicity
3. Maintainability
4. Clear structure
5. Performance
6. Advanced features

---

# Long Term Vision

HYMIND should evolve into a production capable autonomous industry intelligence platform for hydrogen engineering and market research.