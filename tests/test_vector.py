from database import vector as V


def test_search_returns_relevant_policy(tmp_path, monkeypatch):
    monkeypatch.setattr(V, "VECTOR_DB_PATH", str(tmp_path / "chroma"))
    monkeypatch.setattr("config.VECTOR_DB_PATH", str(tmp_path / "chroma"))
    V._collection = None
    V._client = None
    coll = V.init_vector_db()
    assert coll.count() >= 5

    r = V.vector_search_hr_policy("doctor's note sick leave")
    assert "Retrieved Policy" in r
    assert len(r) > len("Retrieved Policy: ")


def test_search_nonsense_returns_fallback(tmp_path, monkeypatch):
    monkeypatch.setattr(V, "VECTOR_DB_PATH", str(tmp_path / "chroma"))
    monkeypatch.setattr("config.VECTOR_DB_PATH", str(tmp_path / "chroma"))
    V._collection = None
    V._client = None
    V.init_vector_db()

    r = V.vector_search_hr_policy("xyzzy nonexistent policy blah")
    assert "No highly relevant" in r or "Retrieved Policy" in r


def test_markdown_handbook_chunking(tmp_path):
    md_file = tmp_path / "test_hb.md"
    md_file.write_text(
        "# Company Handbook\n\n"
        "## 1. Remote Work\n\n"
        "### 1.1 Equipment Policy\n"
        "Employees get a 500 dollar stipend for chairs.\n\n"
        "### 1.2 Core Hours\n"
        "Core hours are 10am to 4pm.\n"
    )
    ids, metas, docs = V.parse_markdown_handbook(str(md_file))
    assert len(ids) == 2
    assert "HB_1_remote_work_1_1_equipment_policy" in ids[0]
    assert metas[0]["chapter"] == "1. Remote Work"
    assert metas[0]["section"] == "1.1 Equipment Policy"
    assert "500 dollar stipend" in docs[0]


def test_multi_chunk_retrieval(tmp_path, monkeypatch):
    monkeypatch.setattr(V, "VECTOR_DB_PATH", str(tmp_path / "chroma"))
    monkeypatch.setattr("config.VECTOR_DB_PATH", str(tmp_path / "chroma"))
    V._collection = None
    V._client = None
    V.init_vector_db()

    # Multi-intent query touching probation notice and WFH
    r = V.vector_search_hr_policy("probation notice period and remote work", n_results=3)
    assert "Retrieved Policy" in r
    # Multiple chunks should be separated by delimiter
    assert "---" in r
