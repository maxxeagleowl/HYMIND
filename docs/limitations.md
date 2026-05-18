# Limitations

## Current Phase Limits

- The autonomous agent is not implemented yet.
- No external API calls are wired up yet.
- No report generation pipeline exists yet.
- No persistence or memory layer exists yet.

## Expected Operational Limits

- External APIs will have rate limits and quotas.
- Search and news results will vary by region, topic, and time.
- Source quality will differ across providers.
- Automated summaries can miss nuance without validation.

## Engineering Risks To Watch

- Duplicate or low-quality sources
- Missing or stale API keys
- API schema changes
- Overly broad searches that return noisy results
- Unclear ownership between retrieval and synthesis logic

## Mitigation Strategy

- Keep validation explicit.
- Add small integration tests when APIs are introduced.
- Store raw source data separately from synthesized outputs.
- Review and refine the prompt and workflow after the first sample reports.
