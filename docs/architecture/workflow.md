# Workflow

## Target Workflow

The future agent should move from a trigger to a report using a small number of explicit steps.

## Planned Steps

1. Receive an input topic or alert request.
2. Search for relevant hydrogen engineering and market signals.
3. Pull structured news items from NewsAPI.
4. Clean and deduplicate the results.
5. Rank the most relevant items.
6. Generate an executive summary with supporting bullet points.
7. Save the report output.

## Future Workflow Notes

- Start with a single synchronous workflow before adding scheduling.
- Keep each step small enough to debug independently.
- Separate retrieval from synthesis so source quality is visible.
- Add retry and error handling only after the basic path works.

## Phase 0 Scope

No workflow execution is implemented yet. This document defines the structure that Phase 1 will build against.
