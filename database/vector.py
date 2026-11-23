import csv
import os
import re

from config import HANDBOOK_MD_PATH, POLICIES_CSV_PATH, VECTOR_DB_PATH

_client = None
_collection = None


def parse_markdown_handbook(path: str):
    """Parse markdown handbook by ## and ### headers into structured chunks with metadata."""
    if not os.path.exists(path):
        return [], [], []

    try:
        with open(path, "r", encoding="utf-8") as f:
            lines = f.readlines()
    except (OSError, UnicodeDecodeError) as e:
        print(f"Warning: Failed reading {path}: {e}")
        return [], [], []

    current_chapter = None
    current_section = None
    current_text = []
    chunks = []

    def flush(chapter, section, text_lines):
        if not chapter or not section:
            return
        body = "".join(text_lines).strip()
        if body:
            slug = re.sub(r"[^a-zA-Z0-9]+", "_", f"{chapter}_{section}").strip("_").lower()
            doc_text = f"[{chapter} > {section}]\n{body}"
            chunks.append((
                f"HB_{slug}",
                {"source": "handbook", "chapter": chapter, "section": section},
                doc_text,
            ))

    for line in lines:
        if line.startswith("## "):
            flush(current_chapter, current_section, current_text)
            current_chapter = line.strip("# \t\r\n")
            current_section = None
            current_text = []
        elif line.startswith("### "):
            flush(current_chapter, current_section, current_text)
            current_section = line.strip("# \t\r\n")
            current_text = []
        else:
            if current_chapter is not None and current_section is not None:
                current_text.append(line)

    flush(current_chapter, current_section, current_text)

    ids = [c[0] for c in chunks]
    metas = [c[1] for c in chunks]
    docs = [c[2] for c in chunks]
    return ids, metas, docs


def _collection_handle():
    global _client, _collection
    import chromadb

    if _collection is None:
        _client = chromadb.PersistentClient(path=VECTOR_DB_PATH)
        _collection = _client.get_or_create_collection(name="hr_policies")

        all_ids, all_metas, all_docs = [], [], []

        # 1. Ingest legacy CSV policies if available
        if os.path.exists(POLICIES_CSV_PATH):
            try:
                with open(POLICIES_CSV_PATH, newline="", encoding="utf-8") as f:
                    for row in csv.DictReader(f):
                        all_ids.append(row["policy_id"])
                        all_metas.append({"source": "csv", "topic": row["topic"]})
                        all_docs.append(row["policy_text"])
            except (OSError, csv.Error) as e:
                print(f"Warning: Failed reading {POLICIES_CSV_PATH}: {e}")

        # 2. Ingest markdown handbook sections
        hb_ids, hb_metas, hb_docs = parse_markdown_handbook(HANDBOOK_MD_PATH)
        all_ids.extend(hb_ids)
        all_metas.extend(hb_metas)
        all_docs.extend(hb_docs)

        if all_ids:
            _collection.upsert(documents=all_docs, metadatas=all_metas, ids=all_ids)

    return _collection


def init_vector_db():
    return _collection_handle()


def vector_search_hr_policy(query: str, n_results: int = 3) -> str:
    coll = _collection_handle()
    count = coll.count()
    if count == 0:
        return "No highly relevant policy found. Advise user to contact HR."
    k = min(n_results, count)
    res = coll.query(query_texts=[query], n_results=k)
    docs = res.get("documents", [[]])[0]
    if docs:
        snippets = [d.strip() for d in docs if d.strip()]
        return "Retrieved Policy: " + "\n\n---\n\n".join(snippets)
    return "No highly relevant policy found. Advise user to contact HR."
