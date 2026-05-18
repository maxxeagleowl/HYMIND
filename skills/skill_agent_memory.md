# Skill - Agent Memory Management

# skill_agent_memory.md

---

# Purpose

This skill defines the persistent repository memory system for the HYMIND project.

The goal is to prevent context loss across sessions and maintain continuity during autonomous development workflows.

This skill is mandatory for all future Codex and autonomous agent interactions.

---

# Core Philosophy

Chat history is not considered reliable operational memory.

All important project knowledge must exist inside the repository.

The repository is the single source of truth.

Persistent project memory is required to support:

- Long running development
- Autonomous continuation
- Multi session workflows
- Reliable handovers
- State continuity
- Decision traceability
- Engineering consistency

---

# Repository Memory Structure

The following memory structure must exist:

```text
memory/
├── latest_context.md
├── handover.md
├── session_summary.md
└── changelog.md
```

---

# Project State Structure

The following project state files must exist:

```text
docs/
├── project_state.md
├── decision_log.md
├── open_questions.md
├── progress_log.md
└── next_actions.md
```

---

# Memory File Responsibilities

## latest_context.md

Contains:

- Current project status
- Current implementation phase
- Active architecture decisions
- Current workflow state
- Important constraints
- Most recent priorities

This file acts as the fastest project overview.

---

## handover.md

Contains:

- Completed work
- Modified files
- Current blockers
- Important implementation notes
- Next recommended tasks
- Important warnings or reminders

This file enables smooth session continuation.

---

## session_summary.md

Contains:

- High level summary of the latest session
- Main decisions
- Key implementation progress
- Important outcomes

This file should remain concise.

---

## changelog.md

Contains:

- Major repository changes
- Architectural milestones
- Significant workflow updates
- Important implementation additions

The changelog tracks long term project evolution.

---

# Project State File Responsibilities

## project_state.md

Contains:

- Current project maturity
- Active implementation phase
- Current system capabilities
- Existing integrations
- Current limitations

This file represents the operational state of the system.

---

## decision_log.md

Contains:

- Important technical decisions
- Architectural reasoning
- Framework selection reasoning
- Workflow decisions
- Rejected alternatives

All major engineering decisions must be documented.

---

## open_questions.md

Contains:

- Unresolved design questions
- Pending architecture decisions
- Future research topics
- Technical uncertainties

This file prevents unresolved topics from being forgotten.

---

## progress_log.md

Contains:

- Significant completed tasks
- Workflow progress
- Sprint progression
- Reliability improvements
- Integration progress

This file acts as a development timeline.

---

## next_actions.md

Contains:

- Immediate next implementation steps
- Current priorities
- Recommended next tasks
- Active implementation focus

This file guides future sessions.

---

# Mandatory Session Workflow

## Session Start Procedure

Before implementation begins, Codex must read:

```text
AGENTS.md
docs/project_state.md
docs/task_board.md
docs/decision_log.md
memory/handover.md
```

After reading, Codex must identify:

- Current implementation phase
- Current active task
- Known blockers
- Current repository state
- Recommended next actions
- Files likely to change

Implementation must not begin before context review is completed.

---

# During Session Responsibilities

During implementation, Codex must update:

```text
docs/progress_log.md
docs/decision_log.md
docs/task_board.md
```

when meaningful progress occurs.

Updates should happen continuously during development.

---

# Session End Procedure

Before ending a session, Codex must update:

```text
memory/handover.md
```

The handover must include:

- Completed work
- Modified files
- Important implementation decisions
- Remaining issues
- Current blockers
- Next recommended task
- Important reminders

This step is mandatory.

---

# Context Preservation Rules

## Rule 1

Never rely on chat history as the operational source of truth.

---

## Rule 2

All important project knowledge must exist inside repository documentation.

---

## Rule 3

All major implementation decisions must be documented.

---

## Rule 4

All unfinished work must be reflected in handover or next action files.

---

## Rule 5

Current repository state must always be reconstructable from repository documentation.

---

# Autonomous Development Principles

The repository memory system is designed to support:

- Autonomous continuation
- Persistent engineering context
- Multi session development
- Long running workflows
- AI assisted engineering
- Reliable implementation continuity

The repository should remain understandable even after long interruptions between sessions.

---

# Reliability Expectations

The memory system must remain:

- Simple
- Structured
- Human readable
- Machine readable
- Easy to maintain
- Continuously updated

Overly complex memory structures should be avoided.

---

# Implementation Philosophy

Persistent engineering memory is treated as a critical infrastructure layer of the HYMIND project.

The memory system is not optional documentation.

It is part of the operational architecture of the autonomous engineering workflow.

All future implementation work depends on maintaining reliable repository memory.