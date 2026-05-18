# Runtime Notice

Read CLAUDE.md before starting any session work.

# HYMIND Agent Instructions

## Project Identity

HYMIND is an autonomous hydrogen engineering intelligence and executive reporting system.

The project focuses on reliable multi source research, structured intelligence synthesis, executive level reporting, and persistent operational memory.

The system is designed as a production style autonomous research platform rather than a simple AI demo.

---

# Core Operational Philosophy

## Persistent Engineering Memory

Chat history is never considered the operational source of truth.

All important information must exist inside the repository.

Operational continuity must survive across sessions, environments, and operators.

---

## Reliability First

Reliability is always more important than feature expansion.

Fragile implementations are not accepted.

The system must fail gracefully and preserve operational stability whenever possible.

---

## Executive Readability

All outputs must remain executive readable.

Reports should:

- Lead with business impact
- Remain concise and structured
- Separate facts from interpretation
- Preserve source traceability
- Avoid unnecessary technical overload

---

# Documentation Hierarchy

Priority order for operational truth:

1. AGENTS.md
2. docs/project_state.md
3. docs/decision_log.md
4. memory/active/latest_context.md
5. docs/operations/task_board.md
6. Relevant governance and operational skills inside skills/governance/ and skills/operational/
7. Remaining repository documentation

When conflicts appear, higher priority documents override lower priority documents.

---

# Repository Structure

## Documentation

```text
docs/
├── architecture/
├── roadmap/
├── operations/
├── planning/
├── project_state.md
└── decision_log.md
```

## Memory

```text
memory/
├── active/
├── archive/
├── compressed/
├── failure_patterns.md
└── changelog.md
```

## Skills

```text
skills/
├── governance/
└── operational/
```

Governance skills define engineering behavior and operational standards.

Operational skills define execution behavior for hydrogen intelligence, research workflows, reporting, and validation.

All skills are mandatory operational constraints.

---

# Session Workflow

## Session Start

Before implementation begins:

1. Read AGENTS.md
2. Read docs/project_state.md
3. Read docs/operations/task_board.md
4. Read docs/decision_log.md
5. Read memory/active/latest_context.md
6. Read memory/active/current_focus.md
7. Read memory/active/active_risks.md
8. Read memory/failure_patterns.md
9. Read all relevant skills from skills/governance/ and skills/operational/
10. Identify governance skills and operational skills relevant to the active task
11. Summarize:
   - Current project state
   - Current active task
   - Blocked items
   - Current risks
   - Next recommended action
   - Files likely to change

No implementation may begin before operational memory has been reviewed.

---

## During Session

During implementation:

1. Update docs/operations/progress_log.md whenever meaningful progress occurs
2. Update docs/decision_log.md whenever an important decision is made
3. Update docs/operations/task_board.md when task status changes
4. Update memory/active/current_focus.md when active work changes
5. Update memory/active/active_risks.md when new risks appear
6. Document recurring operational failures inside memory/failure_patterns.md
7. Preserve repository consistency and documentation integrity
8. Keep edits focused and reversible whenever possible

---

## Session End

Before ending a session:

1. Update memory/handover.md or memory/archive/handovers/
2. Document:
   - Completed work
   - Changed files
   - Important decisions
   - Remaining problems
   - Current risks
   - Next recommended task
   - Important reminders
3. Update memory/active/latest_context.md
4. Update memory/active/current_focus.md
5. Update memory/active/active_risks.md
6. Update docs/operations/progress_log.md
7. Compress obsolete context into memory/compressed/strategic_summary.md when useful
8. Ensure documentation and operational memory remain aligned

---

# Working Rules

- Review repository state before changing files
- Preserve existing useful content
- Prefer small, reversible changes
- Keep implementations operationally stable
- Ask clarifying questions when scope or risk is unclear
- Never overwrite user changes without explicit instruction
- Never expose or commit secrets from `.env` or local files
- Prefer explicit configuration over hardcoded values
- Critical tasks always take precedence over experimental work
- Reliability always takes priority over feature expansion
- Avoid introducing regressions while implementing new functionality
- Existing operational functionality must remain stable after changes

---

# Engineering Standards

All APIs and external integrations must include:

- Validation
- Retry logic
- Timeout handling
- Logging
- Graceful failure behavior

Whenever possible, integrations should also include:

- Fallback behavior
- Duplicate detection
- Structured outputs
- Source traceability

---

# Definition Of Done

A task is only considered complete if:

- Functionality implemented
- Validation added
- Error handling added
- Retry logic added
- Timeout handling added
- Logging implemented
- Manual testing completed
- Documentation updated
- Memory updated
- No hardcoded secrets
- Graceful failure behavior verified
- Existing functionality remains operational
- Outputs follow project formatting standards
- Relevant decisions documented
- Definition of done reviewed before closure

---

# Project Conventions

- Use Python with a `src/` layout
- Keep modules readable and maintainable
- Prefer explicit configuration files
- Keep reports inside `reports/`
- Keep runtime outputs inside `outputs/`
- Keep documentation concise and operationally useful
- Maintain source traceability whenever possible

---

# Phase Guidance

## Phase 0

- Repository scaffolding
- Architecture planning
- Documentation structure
- Memory system setup
- No full agent implementation

## Phase 1

- External integrations
- Initial orchestration
- API connectivity
- RSS and crawling setup
- Basic reliability mechanisms

## Phase 2

- Research synthesis
- Validation workflows
- Report generation
- RAG integration
- Executive formatting improvements

## Phase 3

- Advanced orchestration
- Monitoring
- Alerting
- Trend analysis
- Operational hardening

---

# Verification Rules

Before considering work complete:

- Prefer lightweight validation first
- Run the smallest meaningful verification step
- Confirm previous functionality still works
- Identify unresolved risks clearly
- Document limitations and edge cases
- Ensure operational memory reflects current state

---

# Failure Handling Philosophy

Operational failures are expected and must be managed systematically.

Recurring failures must be documented inside:

```text
memory/failure_patterns.md
```

Failure documentation should include:

- Problem description
- Root cause
- Detection method
- Mitigation strategy
- Prevention guidance

The system should continuously improve operational resilience over time.

---

# Report Standards

All reports must:

- Lead with strategic relevance
- Prioritize clarity over verbosity
- Highlight why developments matter
- Separate confirmed facts from interpretation
- Include source traceability
- Maintain professional executive tone
- Remain concise and structured

---

# Skill System

## Governance Skills

Govern:

- Architecture
- Reliability
- Workflow behavior
- Memory management
- Engineering standards
- Documentation behavior

## Operational Skills

Govern:

- Hydrogen research behavior
- Source validation
- Market intelligence collection
- Technical analysis
- Executive reporting
- Alert generation

All skills inside the `skills/governance/` and `skills/operational/` directories are mandatory operational constraints for the agent.

---

# Final Operational Rule

Never rely on temporary conversational context as the source of truth.

The repository is the operational memory system.
