"""HYMIND entry point — full research and report pipeline."""

from dotenv import load_dotenv

load_dotenv()

from hymind.utils.logger import get_logger
from hymind.workflows.research_workflow import run_research
from hymind.reporting.report_generator import generate_report

logger = get_logger("hymind.main")


def smoke_test_full_pipeline() -> None:
    """Run the complete pipeline: research workflow → report generation."""
    topic = "hydrogen fuel cell market Europe 2026"
    logger.info("Full pipeline starting | topic=%r", topic)

    # --- Step 1: Research workflow ---
    state = run_research(topic)
    meta = state.get("run_metadata", {})
    crawled = state.get("crawled_results", [])
    crawl_success = sum(1 for r in crawled if r.get("extraction_success"))

    # --- Step 2: Report generation ---
    try:
        report_path, char_count = generate_report(state)
    except RuntimeError as exc:
        logger.error("Report generation skipped | reason=%s", exc)
        print(f"\n[HYMIND] Report generation failed: {exc}")
        return

    logger.info("Full pipeline complete | report=%s | chars=%d", report_path, char_count)

    print(f"\n{'='*60}")
    print(f"  HYMIND — Full Pipeline Complete")
    print(f"{'='*60}")
    print(f"  Topic           : {topic}")
    print(f"  Serper results  : {meta.get('serper_count', 0)}")
    print(f"  News results    : {meta.get('news_count', 0)}")
    print(f"  RSS results     : {meta.get('rss_count', 0)}")
    print(f"  Merged (unique) : {meta.get('merged_count', 0)}")
    print(f"  Crawl success   : {crawl_success}")
    print(f"  Report path     : {report_path}")
    print(f"  Report size     : {char_count:,} characters")
    print(f"  Duration        : {meta.get('duration_seconds', 0):.1f}s")
    print(f"{'='*60}")


def smoke_test_workflow() -> None:
    """Run only the research workflow, no report generation."""
    topic = "hydrogen fuel cell market Europe 2026"
    logger.info("Workflow smoke test starting | topic=%r", topic)
    state = run_research(topic)
    meta = state.get("run_metadata", {})
    errors = state.get("errors", [])
    print(f"\n[HYMIND] Workflow only | merged={meta.get('merged_count', 0)} | errors={len(errors)}")


def smoke_test_crawler() -> None:
    """Validate web crawler."""
    from hymind.tools.web_crawler import crawl_many

    urls = [
        "https://www.prnewswire.com/news-releases/hydrogen-sensor-market-worth-0-16-billion-by-2032---exclusive-report-by-marketsandmarkets-302773274.html",
        "https://hydrogeneurope.eu/wp-content/uploads/2026/03/Quarterly-Magazine_Issue-14_Design_March-2026.pdf",
        "https://does-not-resolve.hymind-test.invalid/article",
    ]
    results = crawl_many(urls)
    successful = sum(1 for r in results if r["extraction_success"])
    print(f"\n[HYMIND] Crawler smoke test | success={successful}/{len(results)}")


def smoke_test_rss() -> None:
    """Validate RSS ingestion."""
    from hymind.tools.rss_reader import read_feed, DEFAULT_HYDROGEN_FEEDS

    total = sum(len(read_feed(url, topic="hydrogen")) for url in DEFAULT_HYDROGEN_FEEDS)
    print(f"\n[HYMIND] RSS smoke test | total={total} results")


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
    logger.info("HYMIND starting...")
    smoke_test_full_pipeline()


if __name__ == "__main__":
    main()
