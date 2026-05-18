# Skill - Agile Execution Management

# skill_agile_execution.md

---

# Purpose

This skill defines the Agile execution framework for the HYMIND project.

The goal is to ensure that development remains structured, traceable, and implementation driven throughout the autonomous engineering workflow.

This skill applies to all project planning, implementation tracking, and task execution activities.

---

# Core Philosophy

Agile planning is treated as an operational engineering capability.

Project planning is not separate from implementation.

Planning, execution, validation, and documentation must remain continuously synchronized.

The Agile system must support:

- Incremental delivery
- Clear implementation priorities
- Dependency awareness
- Traceable progress
- Reliable handovers
- Autonomous continuation
- Definition of done validation

---

# Agile Repository Structure

The following Agile planning files must exist:

```text
docs/
├── planning/stories.md
├── roadmap/sprint_plan.md
├── operations/task_board.md
├── operations/definition_of_done.md
├── operations/progress_log.md
└── roadmap/next_actions.md
```

---

# Planning Responsibilities

## planning/stories.md

Contains:

- Product goals
- User stories
- Story estimates
- Dependencies
- Definitions of done
- Sprint organization

This file acts as the primary project planning document.

---

## roadmap/sprint_plan.md

Contains:

- Current sprint goals
- Sprint priorities
- Planned implementation phases
- Sprint scope boundaries
- Active sprint deliverables

Sprint planning must remain realistic and implementation focused.

---

## operations/task_board.md

Contains:

- Todo tasks
- In progress tasks
- Blocked tasks
- Completed tasks
- Task ownership
- Current implementation focus

The task board represents the operational execution state.

---

## operations/definition_of_done.md

Contains:

- Global completion standards
- Validation expectations
- Reliability expectations
- Documentation requirements
- Testing expectations

A task is not complete until its definition of done is satisfied.

---

## operations/progress_log.md

Contains:

- Important implementation progress
- Completed milestones
- Architecture improvements
- Reliability updates
- Integration progress

This file acts as the historical execution timeline.

---

## roadmap/next_actions.md

Contains:

- Immediate next priorities
- Recommended implementation order
- Pending architecture decisions
- Short term execution focus

This file guides future sessions.

---

# User Story Standards

All user stories should contain:

- Unique identifier
- Clear user perspective
- Functional goal
- Business or engineering value
- Estimate
- Dependencies
- Definition of done

---

# Preferred User Story Format

```text
As a [role]
I want [capability]
So that [value]
```

---

# Story Estimation Rules

Story points represent:

- Relative complexity
- Engineering uncertainty
- Integration difficulty
- Validation effort
- Risk level

Story points do not represent hours or days.

---

# Recommended Estimation Scale

| Story Points | Meaning |
|---|---|
| 1 | Very small |
| 2 | Small |
| 3 | Moderate |
| 5 | Complex |
| 8 | Very complex |
| 13 | Too large and should be divided |

---

# Dependency Management Rules

Dependencies must be documented whenever:

- A task requires another task to finish first
- An integration depends on infrastructure
- Validation depends on implementation
- Workflow sequencing matters

Dependencies should remain explicit and easy to understand.

---

# Definition Of Done Standards

Every implementation task must satisfy:

- Functional completion
- Validation completed
- Documentation updated
- No known critical issues
- Repository consistency maintained
- Relevant project memory updated

A feature is not considered complete if documentation is missing.

---

# Autonomous Agile Principles

Agile management is treated as part of the autonomous engineering workflow.

Codex may assist with:

- Story generation
- Task decomposition
- Dependency tracking
- Progress tracking
- Missing implementation detection
- Definition of done validation
- Sprint organization
- Documentation consistency checks

---

# Sprint Execution Philosophy

Sprints should remain:

- Realistic
- Focused
- Incremental
- Testable
- Deliverable oriented

The project should prioritize stable progress over excessive scope expansion.

---

# MVP Protection Rules

The MVP scope must remain protected.

Implementation should prioritize:

1. Stable core functionality
2. End to end workflow completion
3. Reliability
4. Documentation
5. Optional enhancements last

Overengineering should be avoided during early phases.

---

# Progress Tracking Rules

Important implementation progress must be documented continuously.

Progress tracking should include:

- Completed integrations
- Reliability improvements
- Architecture changes
- Workflow milestones
- Testing outcomes

Progress documentation should remain concise but informative.

---

# Blocker Management Rules

Blocked tasks must be documented immediately.

Blocked tasks should include:

- Description of blocker
- Impacted functionality
- Potential workaround
- Recommended next step

Untracked blockers are not acceptable.

---

# Reliability Philosophy

Agile execution is not complete unless the system remains reliable.

The project prioritizes:

- Stability
- Maintainability
- Traceability
- Reproducibility
- Clear implementation structure

Fragile implementations are not considered complete.

---

# Operational Engineering Principle

Agile management is treated as part of the operational architecture of the HYMIND project.

Planning, implementation, validation, and documentation are continuous engineering activities and must remain synchronized throughout development.