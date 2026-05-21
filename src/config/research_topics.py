"""Research topic configuration for HYMIND.

Defines the query lists used by Serper and NewsAPI collectors,
and the RSS feeds used by the RSS reader.

Scope: European hydrogen and fuel cell industry — funding, policy, PEM fuel cell
technology, stationary power, micro-grid, off-grid, backup power, and intralogistics.
"""

# ---------------------------------------------------------------------------
# Serper web search queries
# ---------------------------------------------------------------------------
# Grouped by research pillar. Each query runs as a separate Serper call;
# results from all queries are merged and deduplicated by the workflow.

SERPER_QUERIES: list[str] = [
    # --- Funding: EU-wide, national, regional ---
    "hydrogen funding grant EU Europe 2026",
    "EU Hydrogen Bank IPCEI hydrogen project funding",
    "regional hydrogen funding subsidy Germany Austria Switzerland Spain Italy France Netherlands UK 2026",

    # --- Political & corporate strategy ---
    "EU hydrogen strategy 2026",
    "corporate hydrogen strategy announcement Europe",
    "hydrogen strategy Germany Austria Switzerland Spain Italy France Netherlands UK 2026",
    "corporate hydrogen strategy announcement Europe",

    # --- Fuel Cell / PEM technology ---
    "PEM fuel cell technology news Europe 2026",
    "fuel cell systems manufacturer Europe",

    # --- Stationary power ---
    "stationary fuel cell power generation Europe",

    # --- Micro-grid / off-grid / backup power ---
    "microgrid fuel cell hybrid power Europe",
    "backup power fuel cell hydrogen uninterruptible",
    "off-grid power fuel cell remote site energy",

    # --- Intralogistics ---
    "hydrogen fuel cell forklift intralogistics warehouse Europe",

    # --- Green hydrogen supply context ---
    "green hydrogen electrolyzer production Europe 2026",
]

# ---------------------------------------------------------------------------
# NewsAPI queries
# ---------------------------------------------------------------------------
# Kept shorter and simpler than Serper queries for API compatibility.
# NewsAPI free tier: past 30 days, English language.

NEWS_QUERIES: list[str] = [
    "hydrogen funding Europe",
    "EU hydrogen policy strategy",
    "PEM fuel cell Europe",
    "stationary fuel cell power",
    "hydrogen microgrid power",
    "backup power fuel cell",
    "off-grid fuel cell power",
    "hydrogen intralogistics forklift",
    "green hydrogen Europe",
]

# ---------------------------------------------------------------------------
# RSS feeds
# ---------------------------------------------------------------------------

RSS_FEEDS: list[str] = [
    "https://www.hydrogeninsight.com/rss",
    "https://www.h2-view.com/feed/",
    "https://fuelcellsworks.com/feed/",
    "https://cleantechnica.com/feed/",
    "https://hydrogeneurope.eu/feed/",
    "https://www.h2bulletin.com/feed/",
]
