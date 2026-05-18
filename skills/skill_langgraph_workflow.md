# Skill - LangGraph Workflow Standards

# skill_langgraph_workflow.md

---

# Purpose

This skill defines the LangGraph workflow architecture standards for the HYMIND project.

The goal is to ensure that all autonomous workflows remain modular, maintainable, reliable, and easy to extend.

This skill applies to:

- LangGraph state management
- Workflow node architecture
- Routing logic
- Agent orchestration
- Retry behavior
- Validation flows
- Autonomous execution design

---

# Core Philosophy

The workflow is treated as a production style autonomous system.

The architecture must remain:

- Modular
- Observable
- Reliable
- Deterministic where possible
- Easy to debug
- Easy to extend

The workflow should prioritize reliability and clarity over unnecessary complexity.

---

# Workflow Design Philosophy

The HYMIND workflow follows a staged execution model.

Preferred high level structure:

```text
Trigger
    ↓
Research Collection
    ↓
Content Processing
    ↓
Validation
    ↓
Analysis
    ↓
Report Generation
    ↓
Distribution
```

Each stage should remain independently testable.

---

# LangGraph Architecture Principles

The LangGraph implementation should use:

- Explicit workflow state
- Modular nodes
- Controlled transitions
- Validation checkpoints
- Retry aware routing
- Structured outputs

Implicit state handling should be avoided.

---

# State Management Standards

Workflow state must remain centralized and explicit.

Preferred structure:

```python
class AgentState(TypedDict):
    topic: str
    raw_sources: list
    processed_sources: list
    validated_sources: list
    analysis_summary: str
    report_markdown: str
    errors: list
```

---

# State Rules

## Rule 1

All important workflow information must exist in state.

---

## Rule 2

Nodes should not rely on hidden global variables.

---

## Rule 3

State updates should remain predictable and traceable.

---

## Rule 4

State structures should remain simple and readable.

---

# Node Design Standards

Each node should perform one primary responsibility only.

Preferred node examples:

```text
collect_research
process_content
validate_sources
analyze_findings
generate_report
distribute_report
```

---

# Node Naming Rules

Node names should:

- Use snake_case
- Describe actions clearly
- Remain implementation focused
- Avoid vague naming

Good examples:

```text
collect_news
validate_articles
generate_executive_summary
```

Bad examples:

```text
doStuff
mainNode
handler
```

---

# Node Responsibility Rules

Each node should:

- Accept workflow state
- Perform a focused task
- Return updated workflow state
- Handle local validation
- Avoid unrelated side effects

Nodes should remain modular and reusable.

---

# Routing Standards

Routing logic should remain explicit and easy to understand.

Preferred routing examples:

```text
Success
→ continue workflow

Validation Failure
→ retry or fallback

Critical Failure
→ terminate gracefully
```

Hidden routing behavior should be avoided.

---

# Retry Routing Standards

Retry handling should be built into workflow logic.

Recommended retry scenarios:

- Temporary API failures
- Validation inconsistencies
- Parsing failures
- Timeout related issues

Retries should remain controlled and logged.

---

# Fallback Behavior Standards

Fallback behavior is mandatory for unstable operations.

Examples:

- Missing source data
- Failed API responses
- Partial report generation
- Invalid content extraction

The workflow should degrade gracefully whenever possible.

---

# Validation Node Philosophy

Validation should exist as explicit workflow stages.

Validation may include:

- Source quality checks
- Duplicate detection
- Empty result filtering
- Content relevance checks
- Report completeness checks

Validation should never remain implicit.

---

# Structured Output Standards

Nodes should return structured data whenever possible.

Preferred formats:

- TypedDict
- Pydantic models
- Structured dictionaries

Unstructured outputs should be minimized.

---

# Workflow Logging Standards

Important workflow events should be logged.

Logs should include:

- Node execution
- Retry attempts
- Validation failures
- Workflow transitions
- Critical errors

The workflow must remain observable.

---

# Error Handling Philosophy

Workflow failures must remain:

- Controlled
- Traceable
- Recoverable where possible

The workflow should avoid catastrophic termination whenever partial continuation is possible.

---

# Workflow Modularity Principles

The architecture should support future expansion.

Future workflow stages may include:

- RAG retrieval
- Enterprise integrations
- SharePoint access
- Teams notifications
- LinkedIn monitoring
- Multi company analysis
- Real time alerts

The workflow must remain extensible without major redesign.

---

# Human In The Loop Philosophy

The system should support optional human review stages.

Possible future checkpoints:

- Report approval
- Strategic validation
- Alert confirmation
- Source verification

Human oversight should remain possible without redesigning the workflow.

---

# Preferred Repository Structure

```text
src/hymind/
├── agents/
├── workflows/
├── tools/
├── reporting/
├── memory/
└── utils/
```

---

# Workflow File Organization

Preferred workflow structure:

```text
src/hymind/workflows/
├── research_workflow.py
├── report_workflow.py
├── routing.py
└── state.py
```

---

# Reliability Philosophy

Workflow reliability is mandatory.

The system prioritizes:

- Predictable execution
- Clear routing
- Controlled failures
- Observability
- State traceability
- Maintainability

over unnecessary autonomy complexity.

---

# Operational Engineering Principle

The LangGraph workflow is treated as the operational backbone of the HYMIND autonomous intelligence platform.

The workflow architecture must remain understandable, testable, and maintainable throughout the entire project lifecycle.