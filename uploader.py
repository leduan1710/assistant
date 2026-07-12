import os
import re
import time
import tempfile

from google import genai

client = genai.Client()

FILENAME_RE = re.compile(r"^(?P<slug>.+)--(?P<hash>[0-9a-f]{10})\.md$")
DEFAULT_STORE_DISPLAY_NAME = "optisigns-support-docs"


def get_or_create_store(display_name: str = DEFAULT_STORE_DISPLAY_NAME) -> str:
    env_name = os.environ.get("FILE_SEARCH_STORE_NAME")
    if env_name:
        return env_name

    for store in client.file_search_stores.list():
        if store.display_name == display_name:
            return store.name

    store = client.file_search_stores.create(config={"display_name": display_name})
    print(
        f"  created new File Search store '{display_name}' ({store.name}) — "
        f"set FILE_SEARCH_STORE_NAME={store.name} as an env var to reuse it "
        f"on future runs"
    )
    return store.name


def list_existing_state(store_name: str) -> dict:
    state = {}
    for doc in client.file_search_stores.documents.list(parent=store_name):
        match = FILENAME_RE.match(doc.display_name or "")
        if not match:
            continue  # skip docs that don't follow our naming convention
        state[match.group("slug")] = {
            "hash": match.group("hash"),
            "doc_name": doc.name,
        }
    return state


def _upload_and_wait(store_name: str, display_name: str, content: str) -> None:
    tmp_path = os.path.join(tempfile.gettempdir(), display_name)
    with open(tmp_path, "w", encoding="utf-8") as f:
        f.write(content)

    try:
        operation = client.file_search_stores.upload_to_file_search_store(
            file=tmp_path,
            file_search_store_name=store_name,
            config={"display_name": display_name, "mime_type": "text/markdown"},
        )
        while not operation.done:
            time.sleep(2)
            operation = client.operations.get(operation)
    finally:
        os.remove(tmp_path)


def _delete_doc(doc_name: str) -> None:
    try:
        client.file_search_stores.documents.delete(name=doc_name, config={"force": True})
    except Exception as e:
        print(f"    warn: could not delete {doc_name}: {e}")


def sync_docs(store_name: str, docs: list) -> dict:
    existing = list_existing_state(store_name)
    added = updated = skipped = 0

    for doc in docs:
        slug, content_hash = doc["slug"], doc["hash"]
        prev = existing.get(slug)

        if prev is None:
            _upload_and_wait(store_name, doc["filename"], doc["content"])
            added += 1
            print(f"  + added:     {doc['filename']}")
        elif prev["hash"] != content_hash:
            _delete_doc(prev["doc_name"])
            _upload_and_wait(store_name, doc["filename"], doc["content"])
            updated += 1
            print(f"  ~ updated:   {doc['filename']}")
        else:
            skipped += 1

    return {
        "added": added,
        "updated": updated,
        "skipped": skipped,
        "total_scraped": len(docs),
    }
