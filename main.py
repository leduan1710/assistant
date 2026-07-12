import os
import sys
import json
from datetime import datetime, timezone

from dotenv import load_dotenv

load_dotenv()

from scraper import scrape_all
from uploader import get_or_create_store, sync_docs

MARKDOWN_OUTPUT_DIR = os.environ.get("MARKDOWN_OUTPUT_DIR", "./articles")
MIN_ARTICLES = int(os.environ.get("MIN_ARTICLES", "30"))
MAX_ARTICLES = int(os.environ.get("MAX_ARTICLES", "40"))


def main() -> None:
    if not os.environ.get("GEMINI_API_KEY"):
        print("ERROR: GEMINI_API_KEY is not set.")
        sys.exit(1)

    started = datetime.now(timezone.utc).isoformat()
    print(f"[{started}] OptiBot sync job starting")

    print("\nStep 1/3 — Scraping articles from support.optisigns.com ...")
    docs = scrape_all(min_articles=MIN_ARTICLES, limit=MAX_ARTICLES)
    print(f"  scraped {len(docs)} articles")

    os.makedirs(MARKDOWN_OUTPUT_DIR, exist_ok=True)
    for doc in docs:
        path = os.path.join(MARKDOWN_OUTPUT_DIR, doc["filename"])
        with open(path, "w", encoding="utf-8") as f:
            f.write(doc["content"])
    print(f"  saved Markdown files to {MARKDOWN_OUTPUT_DIR}/")

    print("\nStep 2/3 — Getting/creating File Search store ...")
    store_name = get_or_create_store()
    print(f"  using File Search store: {store_name}")

    print("\nStep 3/3 — Syncing (delta upload — added / updated / skipped) ...")
    result = sync_docs(store_name, docs)

    print("\n---- SYNC SUMMARY ----")
    print(json.dumps(result, indent=2))
    print(f"file_search_store_name: {store_name}")
    finished = datetime.now(timezone.utc).isoformat()
    print(f"[{finished}] Job completed successfully.")

    sys.exit(0)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"\nFATAL: job failed: {exc}")
        sys.exit(1)
