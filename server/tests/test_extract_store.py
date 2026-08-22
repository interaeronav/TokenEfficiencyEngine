import re
from pathlib import Path

import pytest

from tee.extract.store import ExtractStore
from tee.kernel.errors import TeeError


@pytest.fixture()
def store(tmp_path):
    return ExtractStore(tmp_path)


def make_file(tmp_path, name="a.dxf", content=b"hello dxf"):
    path = tmp_path / name
    path.write_bytes(content)
    return path


def test_register_dedupes_by_content(store, tmp_path):
    p1 = make_file(tmp_path, "a.dxf")
    p2 = make_file(tmp_path, "copy.dxf")  # same bytes, different name
    m1 = store.register_source(p1)
    m2 = store.register_source(p2)
    assert m1["hash"] == m2["hash"]
    assert m2["already_known"] is True
    assert len(store.sources()) == 1


def test_facts_roundtrip_and_idempotence(store, tmp_path):
    meta = store.register_source(make_file(tmp_path))
    facts = [{"kind": "dimension", "value_m": 4.2, "tier": "dimension_text"}]
    assert store.store_facts(meta["hash"], "dxf", "1", facts) == 1
    assert store.has_facts(meta["hash"], "dxf", "1")
    read = store.facts(meta["hash"], kind="dimension")
    assert read[0]["value_m"] == 4.2
    assert read[0]["extractor"] == "dxf"


def test_fact_validation(store, tmp_path):
    meta = store.register_source(make_file(tmp_path))
    with pytest.raises(TeeError):
        store.store_facts(meta["hash"], "x", "1", [{"no_kind": True}])
    with pytest.raises(TeeError):
        store.store_facts(meta["hash"], "x", "1", [{"kind": "d", "tier": "bogus"}])


def test_search_finds_by_words(store, tmp_path):
    meta = store.register_source(make_file(tmp_path))
    store.store_facts(
        meta["hash"],
        "dxf",
        "1",
        [{"kind": "room", "name": "Bedroom 1"}, {"kind": "room", "name": "Kitchen"}],
    )
    hits = store.search("bedroom")
    assert len(hits) == 1
    assert hits[0]["fact"]["name"] == "Bedroom 1"


def test_resolve_by_prefix_name_and_ambiguity(store, tmp_path):
    m1 = store.register_source(make_file(tmp_path, "plan.dxf", b"one"))
    store.register_source(make_file(tmp_path, "site.jpg", b"two"))
    assert store.resolve(m1["hash"][:8])["name"] == "plan.dxf"
    assert store.resolve("site.jpg")["media_type"] == "image"
    with pytest.raises(TeeError) as err:
        store.resolve("zzz-nothing")
    assert err.value.code == "unknown_source"


def test_license_lint_no_banned_imports():
    """A8: AGPL/NC dependencies must never enter the server source."""
    banned = re.compile(
        r"^\s*(?:import|from)\s+(fitz|pymupdf|marker|ultralytics)\b", re.MULTILINE | re.IGNORECASE
    )
    src = Path(__file__).resolve().parents[1] / "src"
    offenders = [
        str(path) for path in src.rglob("*.py") if banned.search(path.read_text(errors="ignore"))
    ]
    assert offenders == []
