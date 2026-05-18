# HYMIND Agent Instructions

## Working Rules

- Review the repository state before changing files.
- Ask clarifying questions before implementation when the scope is unclear or risky.
- Keep changes focused on the requested phase.
- Prefer small, reversible edits.
- Do not overwrite user changes unless the user asks for that explicitly.
- Never commit or expose secrets from `.env` or any other local file.

## Project Conventions

- Use Python with a `src/` layout.
- Keep modules simple and readable.
- Prefer explicit configuration files over hard-coded values.
- Keep generated reports in `reports/` and runtime outputs in `outputs/`.
- Keep docs practical, short, and current with the codebase.

## Phase Guidance

- Phase 0: scaffold only, no full agent implementation.
- Phase 1: add the first external integrations and basic orchestration.
- Phase 2: add synthesis, validation, and report generation.

## Before Editing

- Confirm the target files.
- Preserve existing useful content.
- Add or update docs when behavior changes.

## Verification

- Prefer lightweight checks first.
- If code is added later, run the smallest useful validation command.
- Report any missing tests or unresolved risks clearly.
