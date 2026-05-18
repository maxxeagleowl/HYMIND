"""HYMIND entry point — Phase 1 research workflow."""

from dotenv import load_dotenv

load_dotenv()

from hymind.utils.logger import get_logger
from hymind.workflows.research_workflow import run_research

logger = get_logger("hymind.main")


def smoke_test_workflow() -> None:
    """Run the full research pipeline and print a structured result summary."""
    topic = "hydrogen fuel cell market Europe 2026"
    logger.info("Workflow smoke test starting | topic=%r", topic)

    result = run_research(topic)

    meta = result.get("run_metadata", {})
    errors = result.get("errors", [])
    warnings = result.get("warnings", [])

    logger.info(
        "Workflow smoke test complete | merged=%d | errors=%d",
        meta.get("merged_count", 0),
        len(errors),
    )

    print(f"\n{'='*60}")
    print(f"  HYMIND Research Workflow — Complete")
    print(f"{'='*60}")
    print(f"  Topic          : {result.get('topic', '')}")
    print(f"  Serper results : {meta.get('serper_count', 0)}")
    print(f"  News results   : {meta.get('news_count', 0)}")
    print(f"  RSS results    : {meta.get('rss_count', 0)}")
    print(f"  Merged (unique): {meta.get('merged_count', 0)}")
    print(f"  Crawled URLs   : {meta.get('crawled_count', 0)}")
    print(f"  Crawl success  : {meta.get('crawl_success_count', 0)}")
    print(f"  Duration       : {meta.get('duration_seconds', 0):.1f}s")
    print(f"  Errors         : {len(errors)}")
    print(f"  Warnings       : {len(warnings)}")
    print(f"{'='*60}")

    if errors:
        print("\nErrors:")
        for err in errors:
            print(f"  [ERROR] {err}")

    if warnings:
        print("\nWarnings:")
        for w in warnings:
            print(f"  [WARN]  {w}")

    merged = result.get("merged_results", [])
    if merged:
        print(f"\nTop 5 merged results:")
        for r in merged[:5]:
            src = r.get("source_type", "?")
            print(f"  [{src}] {r.get('title', '(no title)')[:70]}")
            print(f"         {r.get('url', '')[:80]}")


def smoke_test_crawler() -> None:
    """Validate web crawler across success, non-HTML, and connection-failure cases."""
    from hymind.tools.web_crawler import crawl_many

    urls = [
        "https://www.prnewswire.com/news-releases/hydrogen-sensor-market-worth-0-16-billion-by-2032---exclusive-report-by-marketsandmarkets-302773274.html",
        "https://hydrogeneurope.eu/wp-content/uploads/2026/03/Quarterly-Magazine_Issue-14_Design_March-2026.pdf",
        "https://does-not-resolve.hymind-test.invalid/article",
    ]
    logger.info("Crawler smoke test starting | urls=%d", len(urls))
    results = crawl_many(urls)
    successful = [r for r in results if r["extraction_success"]]
    failed = [r for r in results if not r["extraction_success"]]
    logger.info("Crawler smoke test complete | successful=%d | failed=%d", len(successful), len(failed))
    print(f"\n[HYMIND] Crawler smoke test | success={len(successful)} | failed={len(failed)}")


def smoke_test_rss() -> None:
    """Validate RSS ingestion across the default hydrogen feed list."""
    from hymind.tools.rss_reader import read_feed, DEFAULT_HYDROGEN_FEEDS

    logger.info("RSS smoke test starting | feeds=%d", len(DEFAULT_HYDROGEN_FEEDS))
    all_results: list[dict] = []
    for url in DEFAULT_HYDROGEN_FEEDS:
        results = read_feed(url, topic="hydrogen")
        all_results.extend(results)
    logger.info("RSS smoke test complete | total=%d", len(all_results))
    print(f"\n[HYMIND] RSS smoke test | total={len(all_results)} results")


def smoke_test_newsapi() -> None:
    """Validate NewsAPI integration."""
    from hymind.tools.news_api import search as news_search

    results = news_search("hydrogen fuel cell Europe", num_results=10)
    print(f"\n[HYMIND] NewsAPI smoke test | results={len(results)}")


def smoke_test_serper() -> None:
    """Validate Serper search integration."""
    from hymind.tools.serper_search import search as serper_search

    results = serper_search("hydrogen fuel cell market Europe 2026", num_results=10)
    print(f"\n[HYMIND] Serper smoke test | results={len(results)}")


def smoke_test_openai() -> None:
    """Validate OpenAI integration."""
    from hymind.tools.openai_client import complete

    response = complete("In one sentence, confirm you are functioning.", max_tokens=60)
    print(f"\n[HYMIND] OpenAI smoke test | response={response}")


def main() -> None:
    logger.info("HYMIND Phase 1 starting...")
    smoke_test_workflow()


if __name__ == "__main__":
    main()
