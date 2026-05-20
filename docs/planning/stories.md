# HYMIND User Stories

## Product Goal

Build an autonomous hydrogen market intelligence and data platform that gathers information from multiple sources, analyzes it, and produces structured executive intelligence reports.

## Phase 0 Stories

| ID | User Story | Estimate | Dependencies | Definition of Done |
| --- | --- | --- | --- | --- |
| US-01 | As a developer, I want a clean repository structure so that future agent work is easy to organize. | 1 | None | Required folders and baseline files exist and are documented. |
| US-02 | As a developer, I want a minimal dependency list so that setup is fast and understandable. | 1 | None | `requirements.txt` contains only the packages needed for the next phase. |
| US-03 | As a developer, I want a safe `.env.example` so that local configuration is easy without exposing secrets. | 1 | None | All required config keys are listed with empty placeholders or safe defaults. |
| US-04 | As a developer, I want reusable skill files so that future Codex work follows the same project conventions. | 1 | None | `skills/governance/` and `skills/operational/` contain short, practical guidance files. |
| US-05 | As a developer, I want initial docs for architecture, workflow, integrations, limitations, and implementation phases so that the next phase starts from a shared baseline. | 2 | US-01 | The docs exist and describe the intended system at a high level. |

## Initial Sprint Tasks

1. Confirm the Phase 0 repository layout.
2. Create the Python package skeleton under `src/`.
3. Add the safe environment template.
4. Add the AGENTS guidance file for future work.
5. Fill the initial planning and architecture docs.
6. Add reusable skill stubs for research, validation, and report generation.
7. Add placeholder files only where they help preserve empty directories.

## Early Backlog

- Add Serper API integration for search-based research.
- Add NewsAPI integration for structured news collection.
- Add report synthesis with OpenAI.
- Add source validation and deduplication.
- Add one or more sample executive reports.
- Add a basic CLI or workflow trigger.

## Phase 4 Stories

| ID | User Story | Estimate | Dependencies | Definition of Done |
| --- | --- | --- | --- | --- |
| US-06 | As a developer, I want schema validation on workflow outputs so that malformed findings are rejected before production use. | 2 | US-05 | Validation rules are documented, automated tests cover invalid and valid output paths, and the workflow continues gracefully on validation failure. |
| US-07 | As a developer, I want retry, timeout, logging, and error handling hardening so that the research pipeline survives transient failures. | 2 | US-05 | External integrations retry correctly, time out safely, log errors clearly, and preserve partial results without crashing. |
| US-08 | As a developer, I want end-to-end reliability tests and a production hardening checklist so that release readiness is explicit. | 2 | US-06, US-07 | End-to-end success and failure paths are verified, the checklist is documented, and known risks are captured. |

## Phase 5 Stories

| ID | User Story | Estimate | Dependencies | Status | Definition of Done |
| --- | --- | --- | --- | --- | --- |
| US-09 | As an operator, I want an n8n workflow to trigger a report run on a weekly schedule so that delivery happens automatically without manual intervention. | 2 | US-08 | Done | n8n workflow JSON exported to `n8n/HYMIND.json`. Schedule Trigger fires Monday 08:00. HTTP Request calls FastAPI `/run-hymind`. IF node checks success. |
| US-10 | As an operator, I want Gmail delivery of each completed report so that stakeholders receive it immediately after generation. | 3 | US-09 | Done | Gmail node sends HTML-converted report. Markdown→HTML conversion handled in-workflow by n8n Markdown node. PDF descoped. |
| US-11 | As an operator, I want delivery outcomes logged so that I can trace what was sent and when. | 2 | US-10 | Done | Google Sheets node appends timestamp, report title, status, and delivery channel on each successful send. Error alert Gmail fires on failure. Telegram descoped from MVP. |

## Phase 6 Stories

| ID | User Story | Estimate | Dependencies | Status | Definition of Done |
| --- | --- | --- | --- | --- | --- |
| US-12 | As a developer, I want a finalized README and complete architecture documentation so that any reviewer or instructor can understand and reproduce the system. | 2 | US-11 | Done | README covers setup, configuration, run instructions, test commands, n8n usage, output locations, and known limitations. Architecture docs match current `src/` layout. |
| US-13 | As a developer, I want all AGENTS.md files, skills/, and planning artifacts finalized so that the agent-facing specification and Agile artifacts meet submission requirements. | 1 | US-12 | Done | AGENTS.md reflects final system state. skills/ is complete. stories.md has estimates and definitions of done for every phase. |
| US-14 | As a developer, I want a working end-to-end demo runbook and submission-ready repository so that the project can be demonstrated clearly and submitted. | 2 | US-12, US-13 | In Progress | Demo runbook in `docs/operations/demo_runbook.md`. Repository clean — no stale files, no broken paths, no secrets committed. All docs reflect current implementation. |

## Definition Of Done For The Project

- Repository is clean and well-structured.
- README explains setup, run, test, n8n usage, and limitations.
- Architecture documentation matches actual `src/` layout.
- Planning artifacts (stories, task board) reflect final state.
- Sample reports demonstrate actual output quality.
- n8n workflow JSON is exported and documented.
- No secrets committed.
- 243 automated tests pass.
- Demo runbook exists and is accurate.
