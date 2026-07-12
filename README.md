# OptiBot Mini-Clone

A small RAG support bot cloning OptiSigns' OptiBot: scrapes
`support.optisigns.com`, converts articles to Markdown, and loads them into
a Gemini File Search store (Gemini's managed vector store + retrieval).

## Setup

```powershell
git clone <this-repo>
cd <this-repo>
python -m venv venv
venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.sample .env
```

Get a free API key (no credit card needed) at https://aistudio.google.com/apikey
and paste it into `.env` as `GEMINI_API_KEY`.

## Run locally

```powershell
python main.py
```

Scrapes ~40 articles into `articles/`, creates a File Search store on first
run (copy the printed store name into `.env` as `FILE_SEARCH_STORE_NAME` to
reuse it next time), then uploads only what's new or changed.

Test the bot:

```powershell
python scripts\query_bot.py "<file_search_store_name>" "How do I add a YouTube video?"
```

## Run via Docker

```powershell
docker build -t optibot-sync .
docker run -e GEMINI_API_KEY=AIza... -e FILE_SEARCH_STORE_NAME=fileSearchStores/... optibot-sync
```

Runs once, exits 0 on success.

## Chunking

Handled automatically by Gemini File Search (`gemini-embedding-001`) — no
manual tuning needed for prose-heavy support articles.

## Delta detection

No database — each document is named `<slug>--<hash>.md`. Every run lists
what's already in the store, compares hashes against the fresh scrape, and
only uploads what's new or changed. State lives in the store itself, so
this is safe to run in a fresh container every day.

## Daily job

Runs on a schedule via [Railway/Render/Fly.io — fill in yours] cron.
Logs: 

## Sample answer



## Structure

```
main.py               scrape -> save -> sync, exits 0/1
scraper.py             Zendesk API -> Markdown
uploader.py             Gemini File Search + delta sync
scripts/query_bot.py    test query with the required system prompt
```
