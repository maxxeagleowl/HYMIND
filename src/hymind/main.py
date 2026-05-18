"""HYMIND entry point — Phase 1 smoke tests."""

from dotenv import load_dotenv

load_dotenv()

from hymind.utils.logger import get_logger
from hymind.tools.rss_reader import read_feed, DEFAULT_HYDROGEN_FEEDS

logger = get_logger("hymind.main")


def smoke_test_rss() -> None:
    """Validate RSS ingestion across the default hydrogen feed list."""
    logger.info("RSS smoke test starting | feeds=%d", len(DEFAULT_HYDROGEN_FEEDS))

    all_results: list[dict] = []
    feed_summary: list[tuple[str, int]] = []

    for url in DEFAULT_HYDROGEN_FEEDS:
        results = read_feed(url, topic="hydrogen")
        source = results[0]["source"] if results else url
        feed_summary.append((source, len(results)))
        all_results.extend(results)

    logger.info("RSS smoke test complete | total_results=%d", len(all_results))

    print(f"\n[HYMIND] RSS smoke test")
    print(f"Feeds   : {len(DEFAULT_HYDROGEN_FEEDS)}")
    print(f"Total   : {len(all_results)} results\n")
    print("Per feed:")
    for source, count in feed_summary:
        print(f"  {source:<40} {count} results")

    if all_results:
        print("\nFirst 3 entries:")
        for r in all_results[:3]:
            print(f"\n  [{r['rank']}] {r['title']}")
            print(f"       Source : {r['source']}")
            print(f"       URL    : {r['url']}")


def smoke_test_newsapi() -> None:
    """Validate NewsAPI integration with one live query."""
    from hymind.tools.news_api import search as news_search

    query = "hydrogen fuel cell Europe"
    logger.info("NewsAPI smoke test | query=%r", query)
    results = news_search(query, num_results=10)
    logger.info("NewsAPI smoke test complete | results=%d", len(results))
    print(f"\n[HYMIND] NewsAPI smoke test")
    print(f"Query   : {query}")
    print(f"Results : {len(results)}\n")
    for r in results[:3]:
        print(f"  [{r['rank']}] {r['title']}")
        print(f"       Source : {r['source']}")
        print(f"       URL    : {r['url']}\n")


def smoke_test_serper() -> None:
    """Validate Serper search integration with one live query."""
    from hymind.tools.serper_search import search as serper_search

    query = "hydrogen fuel cell market Europe 2026"
    logger.info("Serper smoke test | query=%r", query)
    results = serper_search(query, num_results=10)
    logger.info("Serper smoke test complete | results=%d", len(results))
    print(f"\n[HYMIND] Serper smoke test")
    print(f"Query   : {query}")
    print(f"Results : {len(results)}\n")
    for r in results[:3]:
        print(f"  [{r['rank']}] {r['title']}")
        print(f"       {r['url']}\n")


def smoke_test_openai() -> None:
    """Validate OpenAI integration with a one-sentence completion call."""
    from hymind.tools.openai_client import complete

    logger.info("OpenAI smoke test starting...")
    response = complete(
        prompt="In one sentence, confirm that you are functioning correctly.",
        max_tokens=60,
        temperature=0.0,
    )
    logger.info("OpenAI smoke test passed | response=%s", response)
    print(f"\n[HYMIND] OpenAI smoke test passed.\nModel response: {response}\n")


def main() -> None:
    logger.info("HYMIND Phase 1 starting...")
    smoke_test_rss()


if __name__ == "__main__":
    main()
