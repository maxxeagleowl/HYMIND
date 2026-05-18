# Project State

## Documentation Structure

The repository documentation is organized into the following operational groups:

```text
docs/
├── architecture/
│   ├── architecture.md
│   ├── api_integrations.md
│   └── workflow.md
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
| Phase 3 | Planned | Advanced orchestration, monitoring, alerting, RAG, trend analysis |

## Operational Notes

- `project_state.md` and `decision_log.md` remain in the docs root.
- Memory behavior remains in `memory/` and is unchanged.
- Internal references should use the new subfolder paths above.
- Reporting standards now live at `docs/operations/reporting_standards.md`.
- Phase 2 adds: `src/hymind/tools/collector.py`, `tests/test_news_api_collector.py`, `docs/architecture/phase_2_research_foundation.md`.

## Skills Structure

```text
skills/
├── governance/
└── operational/
```

- Governance skills define system behavior, reliability, memory, documentation, and workflow standards.
- Operational skills define research, validation, reporting, and domain execution behavior.
