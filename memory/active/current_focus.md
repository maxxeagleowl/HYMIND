# Current Focus

## Status

**Phase 7 — Complete. Full consistency audit passed.**

## Phase 6 Deliverables

| Component | File(s) | Status |
|---|---|---|
| README finalization | `README.md` | Done |
| Architecture docs | `docs/architecture/system_architecture.md` | Done |
| Workflow docs | `docs/operations/workflow_documentation.md` | Done |
| n8n workflow docs | `docs/operations/n8n_workflow.md` | Done (new) |
| Demo runbook | `docs/operations/demo_runbook.md` | Done (new) |
| Limitations update | `docs/operations/limitations.md` | Done |
| Task board update | `docs/operations/task_board.md` | Done |
| Project state | `docs/project_state.md` | Done |
| Stories/DOD | `docs/planning/stories.md` | Done |
| MVP summary | `MVP_summary.md` | Done |
| Stale file cleanup | 4 files deleted | Done |
| Path fixes | phase_2_research_foundation.md, news_api.py | Done |
| Decision log | `docs/decision_log.md` | Done |
| Progress log | `docs/operations/progress_log.md` | Done |

## Phase 7 Complete

- Cross-run URL deduplication via url_tracker.py
- Centralized search config, upgraded prompts
- Full consistency audit: model names, section counts, word counts, phase status, dependency list all aligned

## Next Step

Commit all open changes.

## How to Run

```powershell
# Full pipeline
python -m main

# Custom topic
python -m main "hydrogen funding Germany 2026"

# Run tests
pytest tests/ -v

# Start API server
uvicorn src.api.server:app --host 0.0.0.0 --port 8000 --reload

# Start API + ngrok
python start_hymind_api.py
```

## Phase Summary

| Phase | Status |
|---|---|
| Phase 0 | Complete |
| Phase 1 | Complete |
| Phase 2 | Complete |
| Phase 3 | Complete |
| Phase 4 | Complete |
| Phase 5 | Complete |
| Phase 6 | In Progress |
