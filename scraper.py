import re
import time
import hashlib

import requests
from markdownify import markdownify as html_to_md

ZENDESK_ARTICLES_URL = "https://support.optisigns.com/api/v2/help_center/en-us/articles.json"
PAGE_SIZE = 100
REQUEST_TIMEOUT = 30
REQUEST_DELAY_SEC = 0.2  # be polite to the API


def _slugify(title: str, article_id: int) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
    slug = slug[:60].strip("-")  # keep filenames reasonable
    return f"{slug}-{article_id}"


def fetch_raw_articles(limit: int | None = None) -> list[dict]:
    articles = []
    url = f"{ZENDESK_ARTICLES_URL}?per_page={PAGE_SIZE}"

    while url:
        resp = requests.get(url, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        data = resp.json()

        articles.extend(data.get("articles", []))
        url = data.get("next_page")

        if limit and len(articles) >= limit:
            break

        time.sleep(REQUEST_DELAY_SEC)

    return articles[:limit] if limit else articles


def _clean_markdown(raw_html: str) -> str:
    markdown = html_to_md(
        raw_html or "",
        heading_style="ATX",
        bullets="-",
        strip=["script", "style"],
    )
    markdown = re.sub(r"\n{3,}", "\n\n", markdown).strip()
    return markdown


def build_markdown_doc(article: dict) -> dict:
    title = article["title"]
    url = article["html_url"]
    body_md = _clean_markdown(article.get("body", ""))

    content = f"# {title}\n\nArticle URL: {url}\n\n{body_md}\n"

    content_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()[:10]
    slug = _slugify(title, article["id"])
    filename = f"{slug}--{content_hash}.md"

    return {
        "filename": filename,
        "slug": slug,
        "hash": content_hash,
        "content": content,
        "title": title,
        "url": url,
        "updated_at": article.get("updated_at"),
    }


def scrape_all(min_articles: int = 30, limit: int | None = None) -> list[dict]:
    raw_articles = fetch_raw_articles(limit=limit)
    docs = [build_markdown_doc(a) for a in raw_articles if a.get("body")]

    if len(docs) < min_articles:
        print(
            f"WARNING: only found {len(docs)} articles with usable body content "
            f"(requested minimum {min_articles})"
        )

    return docs
