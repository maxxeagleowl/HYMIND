"""AgentState definition for the HYMIND research workflow.

All workflow nodes read from and write to this state. Fields annotated with
operator.add are accumulative — LangGraph concatenates the lists returned by
each node rather than replacing them. All other fields are replaced on update.
"""

import operator
from typing import Annotated, TypedDict


class AgentState(TypedDict):
    """Full workflow state passed between every research pipeline node."""

    # --- Input ---
    topic: str

    # --- Per-source collections ---
    serper_results: list[dict]
    news_results: list[dict]
    rss_results: list[dict]

    # --- Merged and processed ---
    merged_results: list[dict]
    crawled_results: list[dict]

    # --- Accumulative across nodes (operator.add = list concatenation) ---
    errors: Annotated[list[str], operator.add]
    warnings: Annotated[list[str], operator.add]

    # --- Run tracking ---
    run_metadata: dict

    # --- Report output ---
    report_path: str  # Absolute path to the saved Markdown report, or "" if not yet generated


def initial_state(topic: str) -> AgentState:
    """Return a clean AgentState for the given topic, ready to invoke."""
    return {
        "topic": topic,
        "serper_results": [],
        "news_results": [],
        "rss_results": [],
        "merged_results": [],
        "crawled_results": [],
        "errors": [],
        "warnings": [],
        "run_metadata": {},
        "report_path": "",
    }
