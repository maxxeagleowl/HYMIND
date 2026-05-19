# HYMIND User Stories

## Product Goal

Build an autonomous hydrogen engineering and market intelligence agent that gathers information from multiple sources, analyzes it, and produces structured executive reports.

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

| ID | User Story | Estimate | Dependencies | Definition of Done |
| --- | --- | --- | --- | --- |
| US-09 | As an operator, I want an n8n workflow to trigger distribution from a completed Markdown report so that delivery starts only after the core research pipeline finishes. | 2 | US-08, completed Markdown report generation | The workflow reads an existing Markdown report path, triggers reliably, and logs each run. |
| US-10 | As an operator, I want Markdown-to-PDF conversion and Gmail delivery so that executive reports can be distributed in a polished format. | 3 | US-09 | A PDF is generated into `outputs/`, Gmail delivery succeeds or retries cleanly, and delivery outcomes are logged. |
| US-11 | As an operator, I want optional Telegram alerts, delivery logging, and archived workflow artifacts so that stakeholders and operators have lightweight notification and traceability. | 2 | US-09, US-10 | Telegram can be enabled or skipped safely, delivery logs are preserved, and reusable workflow JSON plus screenshots are documented. |

## Phase 6 Stories

| ID | User Story | Estimate | Dependencies | Definition of Done |
| --- | --- | --- | --- | --- |
| US-12 | As a developer, I want a finalized README and complete architecture documentation so that any reviewer or instructor can understand and reproduce the system. | 2 | US-11 | README covers setup, configuration, architecture, and run instructions. Architecture diagrams are accurate and current. |
| US-13 | As a developer, I want all AGENTS.md files, skills/, and planning artifacts finalized so that the agent-facing specification and Agile artifacts meet submission requirements. | 1 | US-12 | AGENTS.md reflects final system state, skills/ is complete, stories.md has estimates and definitions of done for every phase. |
| US-14 | As a developer, I want a working end-to-end demo and presentation material so that the project can be demonstrated professionally in 5–7 minutes. | 2 | US-12, US-13 | Demo runs without error from trigger to report, presentation covers architecture decisions and reliability features, repository is submission-ready. |

## Definition Of Done For The Phase

- Repository is scaffolded cleanly.
- Documentation is present and understandable.
- No secrets are committed.
- The repo is ready for Phase 1 implementation work.
