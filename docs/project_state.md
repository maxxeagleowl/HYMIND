# Project State

## Documentation Structure

The repository documentation is organized into the following operational groups:

```text
docs/
├── architecture/
│   ├── system_architecture.md
│   ├── api_integrations.md
│   ├── research_pipeline.md
│   └── phase_2_research_foundation.md
├── roadmap/
│   ├── project_phases.md
│   ├── sprint_plan.md
│   └── next_actions.md
├── operations/
│   ├── definition_of_done.md
│   ├── limitations.md
│   ├── open_questions.md
│   ├── reporting_standards.md
│   ├── task_board.md
│   └── progress_log.md
├── planning/
│   └── stories.md
├── project_state.md
└── decision_log.md
```

## Phase Status

| Phase | Status | Summary |
|---|---|---|
| Phase 0 | Complete | Repository scaffolding, documentation structure, memory system |
| Phase 1 | Complete | All integrations (OpenAI, Serper, NewsAPI, RSS, crawler), LangGraph workflow, report generator, 72 tests |
| Phase 2 | Complete | Collector abstraction, validation layer, Phase 2 NewsAPI test suite, API integration docs |
| Phase 3 | Complete | Pinecone RAG storage and retrieval, 46 new tests, backward-compatible workflow nodes |
| Phase 4 | Complete | End-to-end reliability hardening, output validation layer, 73 new tests (243 total), sample reports, logging improvements |
| Phase 5 | Complete | FastAPI HTTP wrapper, n8n scheduled workflow, Gmail delivery, Google Sheets delivery logging, ngrok integration. PDF and Telegram descoped from MVP. |
| Phase 6 | Complete | README finalization, architecture documentation, deliverable validation, demo runbook, submission review |
| Phase 7 | Complete | Centralized search query config (`src/config/research_topics.py`), pillar-organized Serper (15) + NewsAPI (9) queries, crawl blocklist (18 domains), upgraded report prompts (European H2 + fuel cell focus), cross-run URL deduplication (`src/utils/url_tracker.py`) |

## Operational Notes

- `project_state.md` and `decision_log.md` remain in the docs root.
- Memory behavior remains in `memory/` and is unchanged.
- Internal references should use the new subfolder paths above.
- Reporting standards now live at `docs/operations/reporting_standards.md`.
- Phase 2 adds: `src/tools/collector.py`, `tests/test_news_api_collector.py`, `docs/architecture/phase_2_research_foundation.md`.
- Phase 3 adds: `src/rag/` (schemas, embeddings, pinecone_store, retriever), `tests/test_rag.py`, two new LangGraph nodes (`store_findings_in_pinecone`, `retrieve_context_from_pinecone`), `rag_context` field in AgentState, RAG context injection in report_generator.py.
- Phase 4 adds: `src/reporting/validator.py` (validate_findings, check_state_quality), `tests/test_reliability.py` (73 failure scenario tests), `tests/test_validator.py` (34 validator unit tests), 3 sample reports in `outputs/sample_reports/`, validator integration in report_generator.py, node-level START/END logging markers across all 9 workflow nodes.
- Structural refactor (2026-05-20): removed `src/hymind/` nesting — all modules now live directly under `src/`. Import paths flattened: `from X import Y` (was `from hymind.X import Y`). 243 tests pass.
- Phase 5 adds: `src/api/server.py` (FastAPI wrapper), `scripts/run_api.py`, `start_hymind_api.py`, `n8n/HYMIND.json` (Schedule → HTTP → Markdown→HTML → Gmail → Sheets), `n8n/Global Error Handler.json`. PDF generation descoped; Telegram descoped. Delivery logging implemented via Google Sheets.
- Phase 6: Documentation finalization, deliverable validation, demo runbook, submission review.
- Phase 7 adds: `src/config/research_topics.py` (15 Serper queries, 9 NewsAPI queries, 6 RSS feeds, 18-domain crawl blocklist), upgraded report prompts (European H2 + fuel cell focus, McKinsey-style writing rules), `src/utils/url_tracker.py` (cross-run URL deduplication — Pinecone fetch-by-ID primary, SQLite `data/seen_urls.db` fallback), integrated into `merge_and_deduplicate` and `finalize_state`.

## Skills Structure

```text
skills/
├── governance/
└── operational/
```

- Governance skills define system behavior, reliability, memory, documentation, and workflow standards.
- Operational skills define research, validation, reporting, and domain execution behavior.
