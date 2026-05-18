# HYMIND

HYMIND is a Hydrogen Engineering Intelligence Agent for collecting external market and technology signals, analyzing them, and producing structured executive reports.

This repository is in Phase 0. The goal of this phase is to establish a clean project skeleton that is easy to extend without building the full agent yet.

## Current Scope

- Python project structure
- LangGraph-ready source layout
- Documentation scaffold
- Skill scaffolding for reusable work patterns
- Safe environment template

## Repository Layout

```text
README.md
requirements.txt
.env.example
AGENTS.md
docs/
skills/
src/
config/
reports/
outputs/
n8n/
```

## Phase 0 Status

- Project skeleton created
- Minimal dependencies defined
- Initial planning and architecture docs added
- Reusable skill stubs added

## Next Phases

- Add the first real integrations
- Implement the LangGraph workflow
- Add report synthesis with OpenAI
- Generate sample reports
- Add automation and distribution paths

## Setup

1. Create a virtual environment.
2. Install dependencies from `requirements.txt`.
3. Copy `.env.example` to `.env`.
4. Fill in real API keys and configuration values locally.

## Notes

- Do not commit secrets.
- Keep generated outputs in `reports/` and `outputs/`.
- Keep changes small and incremental until the workflow is implemented.
