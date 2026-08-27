"""Phase 16: KB query module - index, drift, search, reads, budgets, flags.

Unit tests run against a small fixture corpus built in tmp_path (never the
live one). The live-mirror tests at the bottom need the repo checkout's
knowledge-base/ and skip cleanly anywhere else.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from tee.app import TeeApp
from tee.kb.index import resolve_root
from tee.kb.tools import register_kb_tools
from tee.kernel.adapter import FakeAdapter
from tee.kernel.budget import estimate_tokens
from tee.kernel.errors import TeeError

# -- fixture corpus ---------------------------------------------------------


def _file(body: str) -> str:
    return body.lstrip("\n")


FIXTURE_FILES = {
    "10_paving/01_block-paving.md": _file(
        """
---
id: paving.blocks
---
# Concrete block paving

Interlock is the mechanism that turns individual blocks into a pavement.

## Key facts

| Item | Value |
|---|---|
| Bedding sand thickness | 25 mm |

## Laying patterns

Herringbone resists braking forces best. Stretcher bond is weaker.

## Sources

- CMA Book 2 (https://example.test/cma2)
"""
    ),
    "10_paving/02_costing.md": _file(
        """
---
id: paving.costing
---
# Costing paving work

Quantities and waste factors decide the price of a paved surface.

## Waste factors

Allow 5 percent for straight work and 10 percent for curves.
"""
    ),
    "20_walls/01_boundary.md": _file(
        """
---
id: walls.boundary
---
# Boundary walls

A wall is a structure before it is a boundary.

## Key facts

Foundations first.
"""
    ),
}

FLAGS = {
    "paving.blocks": {"confidence": "high", "status": "stable", "jurisdiction": "southern-africa"},
    "paving.costing": {"confidence": "medium", "status": "draft", "jurisdiction": "global"},
    "walls.boundary": {
        "confidence": "low",
        "status": "needs-verification",
        "jurisdiction": "NA",
    },
}


def make_corpus(root: Path) -> Path:
    corpus = root / "kb-corpus"
    entries = []
    for rel, body in FIXTURE_FILES.items():
        path = corpus / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(body, encoding="utf-8")
        fid = body.split("id: ")[1].split("\n")[0]
        title = body.split("# ", 1)[1].split("\n")[0]
        entries.append(
            {
                "path": rel,
                "id": fid,
                "title": title,
                "domain": rel.split("/")[0],
                "tags": ["paving"] if "paving" in rel else ["walls"],
                "words": len(body.split()),
                "sha256": hashlib.sha256(body.encode()).hexdigest()[:16],
                "summary": body.split("\n\n")[1].strip(),
                **FLAGS[fid],
            }
        )
    domains = sorted({e["domain"] for e in entries})
    manifest = {
        "name": "Fixture KB",
        "generated": "2026-08-27",
        "totals": {"domains": len(domains), "files": len(entries), "words": 99},
        "domains": [
            {
                "slug": d,
                "title": d,
                "files": sum(1 for e in entries if e["domain"] == d),
                "words": 0,
            }
            for d in domains
        ],
        "files": entries,
    }
    (corpus / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    return corpus


@pytest.fixture()
def kb(tmp_path):
    corpus = make_corpus(tmp_path)
    project = tmp_path / "project"
    project.mkdir()
    app = TeeApp({"fake": FakeAdapter()}, project_root=project)
    register_kb_tools(app, project, root=str(corpus))
    yield app, corpus
    app.shutdown()


# -- index build + cache + drift -------------------------------------------


def test_index_builds_and_caches(kb, tmp_path):
    app, _corpus = kb
    status = app.registry.call("kb_status", {})
    assert status["ok"] and status["totals"]["files"] == 3
    assert not status["drift"]["stale"]
    cache = tmp_path / "project" / ".tee" / "kb" / "index.json"
    assert cache.is_file(), "index cache should be written under the project"


def test_cache_invalidates_on_manifest_change_with_same_date(kb, tmp_path):
    """The corpus's rebuild scripts hard-code the `generated` date, so a
    regenerated manifest can change while the date stays identical. The
    cache must key on manifest content, not the date."""
    app, corpus = kb
    app.registry.call("kb_status", {})  # populate the cache
    manifest_path = corpus / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    manifest["files"][0]["summary"] = "rewritten by a rebuild with the same date"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    # a fresh index (new process) over the same project must not serve stale records
    from tee.kb.index import KbIndex

    fresh = KbIndex(corpus, tmp_path / "project")
    record = next(r for r in fresh.records() if r["path"] == manifest["files"][0]["path"])
    assert record["summary"] == "rewritten by a rebuild with the same date"


def test_drift_marks_stale_but_still_serves(kb):
    app, corpus = kb
    victim = corpus / "10_paving/01_block-paving.md"
    victim.write_text(victim.read_text() + "\nEDITED", encoding="utf-8")
    status = app.registry.call("kb_status", {})
    assert status["drift"]["stale"]
    assert "10_paving/01_block-paving.md" in status["drift"]["changed"]
    assert "rebuild.py" in status["drift"]["fix"]
    result = app.registry.call("kb_search", {"query": "interlock paving"})
    assert result["hits"], "a stale index must still serve queries"
    assert "stale" in result


def test_missing_file_is_drift_not_a_crash(kb):
    app, corpus = kb
    (corpus / "20_walls/01_boundary.md").unlink()
    status = app.registry.call("kb_status", {})
    assert status["drift"]["missing"] == ["20_walls/01_boundary.md"]


# -- error paths ------------------------------------------------------------


def test_missing_root_fails_loud_with_fix(tmp_path):
    app = TeeApp({"fake": FakeAdapter()}, project_root=tmp_path)
    register_kb_tools(app, tmp_path, root=str(tmp_path / "nowhere"))
    with pytest.raises(TeeError) as err:
        app.registry.call("kb_status", {})
    assert err.value.code == "kb_no_manifest"
    assert "[kb] root" in (err.value.fix or "")
    app.shutdown()


def test_malformed_manifest_fails_loud_with_fix(tmp_path):
    corpus = tmp_path / "bad"
    corpus.mkdir()
    (corpus / "manifest.json").write_text("{not json", encoding="utf-8")
    app = TeeApp({"fake": FakeAdapter()}, project_root=tmp_path)
    register_kb_tools(app, tmp_path, root=str(corpus))
    with pytest.raises(TeeError) as err:
        app.registry.call("kb_status", {})
    assert err.value.code == "kb_bad_manifest"
    assert "rebuild.py" in (err.value.fix or "")
    app.shutdown()


def test_root_resolution_order(tmp_path, monkeypatch):
    """Explicit config wins; then the project's own mirror; then the source
    checkout's; with none of the three the module stays inactive."""
    import tee.kb.index as kb_index

    explicit = tmp_path / "explicit"
    assert resolve_root(tmp_path, str(explicit)) == explicit  # even if broken: fail loud later
    project_mirror = tmp_path / "knowledge-base"
    project_mirror.mkdir()
    (project_mirror / "manifest.json").write_text("{}", encoding="utf-8")
    assert resolve_root(tmp_path, None) == project_mirror
    project_mirror_less = tmp_path / "empty-project"
    project_mirror_less.mkdir()
    # sever the source-checkout fallback so "nothing anywhere" is testable
    monkeypatch.setattr(
        kb_index,
        "__file__",
        str(tmp_path / "nowhere" / "server" / "src" / "tee" / "kb" / "index.py"),
    )
    assert resolve_root(project_mirror_less, None) is None
    app = TeeApp({"fake": FakeAdapter()}, project_root=project_mirror_less)
    assert register_kb_tools(app, project_mirror_less) is None
    assert not any(name.startswith("kb_") for name in app.registry.names())
    app.shutdown()


# -- search ----------------------------------------------------------------


def test_search_ranks_title_match_first(kb):
    app, _ = kb
    result = app.registry.call("kb_search", {"query": "block paving"})
    assert result["hits"][0]["id"] == "paving.blocks"


def test_search_filters_are_exact(kb):
    app, _ = kb
    result = app.registry.call("kb_search", {"query": "paving", "confidence": "medium"})
    assert [h["id"] for h in result["hits"]] == ["paving.costing"]
    result = app.registry.call("kb_search", {"query": "wall", "jurisdiction": "NA"})
    assert [h["id"] for h in result["hits"]] == ["walls.boundary"]


def test_search_rows_carry_flags_verbatim(kb):
    app, _ = kb
    hit = app.registry.call("kb_search", {"query": "boundary wall"})["hits"][0]
    assert hit["confidence"] == "low"
    assert hit["jurisdiction"] == "NA"
    assert hit["status"] == "needs-verification"


def test_empty_result_returns_domains_not_silence(kb):
    app, _ = kb
    result = app.registry.call("kb_search", {"query": "zzzqqq nothing"})
    assert result["hits"] == []
    assert {d["slug"] for d in result["domains"]} == {"10_paving", "20_walls"}


# -- reads -----------------------------------------------------------------


def test_read_without_section_lists_sections_and_flags(kb):
    app, _ = kb
    out = app.registry.call("kb_read", {"id": "paving.blocks"})
    assert [s["section"] for s in out["sections"]] == [
        "intro",
        "Key facts",
        "Laying patterns",
        "Sources",
    ]
    assert out["flags"]["confidence"] == "high"
    assert "text" not in out, "no section arg must never dump the file"


def test_read_section_carries_text_flags_and_sources(kb):
    app, _ = kb
    out = app.registry.call("kb_read", {"id": "paving.blocks", "section": "laying"})
    assert "Herringbone" in out["text"]
    assert out["flags"]["jurisdiction"] == "southern-africa"
    assert "cma2" in out["sources"], "the Sources block rides along"


def test_read_budget_truncates_with_notice(kb):
    app, corpus = kb
    big = corpus / "10_paving/01_block-paving.md"
    big.write_text(
        big.read_text().replace(
            "Herringbone resists braking forces best.",
            "Herringbone resists braking forces best.\n" + "filler line\n" * 400,
        ),
        encoding="utf-8",
    )
    out = app.registry.call(
        "kb_read", {"id": "paving.blocks", "section": "laying", "max_tokens": 100}
    )
    assert estimate_tokens(out["text"]) <= 100
    assert "truncated" in out and "max_tokens" in out["truncated"]


def test_unknown_id_and_section_fail_with_fix(kb):
    app, _ = kb
    with pytest.raises(TeeError) as err:
        app.registry.call("kb_read", {"id": "paving.nonsense"})
    assert err.value.code == "kb_unknown_id"
    with pytest.raises(TeeError) as err:
        app.registry.call("kb_read", {"id": "paving.blocks", "section": "no such"})
    assert "Sections:" in (err.value.fix or "")


def test_unverified_content_is_labelled_never_bare(kb):
    app, _ = kb
    out = app.registry.call("kb_read", {"id": "walls.boundary", "section": "Key facts"})
    assert "UNVERIFIED" in out["warning"]
    assert "needs-verification" in out["warning"]
    assert "A30" in out["warning"]


# -- facts -----------------------------------------------------------------


def test_facts_returns_key_facts_blocks_with_flags(kb):
    app, _ = kb
    out = app.registry.call("kb_facts", {"query": "paving blocks"})
    top = out["blocks"][0]
    assert top["id"] == "paving.blocks"
    assert "25 mm" in top["facts"]
    assert top["flags"]["confidence"] == "high"


def test_facts_without_section_says_so_in_one_line(kb):
    app, _ = kb
    out = app.registry.call("kb_facts", {"ids": ["paving.costing"]})
    assert out["blocks"][0]["facts"] == "no '## Key facts' section in this file"


def test_facts_flag_unverified_sources(kb):
    app, _ = kb
    out = app.registry.call("kb_facts", {"ids": ["walls.boundary"]})
    assert "UNVERIFIED" in out["blocks"][0]["warning"]


# -- live mirror (repo checkout only) --------------------------------------

MIRROR = Path(__file__).resolve().parents[2] / "knowledge-base"
needs_mirror = pytest.mark.skipif(
    not (MIRROR / "manifest.json").is_file(), reason="no knowledge-base mirror here"
)


@pytest.fixture()
def live(tmp_path):
    app = TeeApp({"fake": FakeAdapter()}, project_root=tmp_path)
    register_kb_tools(app, tmp_path, root=str(MIRROR))
    yield app
    app.shutdown()


@needs_mirror
def test_live_status_reads_the_real_corpus(live):
    status = live.registry.call("kb_status", {})
    assert status["totals"]["files"] == 401
    assert status["totals"]["domains"] == 38
    # source-register.md is known upstream drift (manifest vs its own file);
    # anything beyond that would be a real mirror problem.
    assert status["drift"]["changed_count"] <= 1
    assert status["drift"]["missing_count"] == 0


@needs_mirror
def test_live_paving_lookup_carries_citation_and_flags(live):
    hits = live.registry.call("kb_search", {"query": "paving specification"})["hits"]
    assert hits and hits[0]["domain"] == "17_paving_and_roads"
    top = hits[0]["id"]
    out = live.registry.call("kb_read", {"id": top, "section": "Key facts"})
    assert out["flags"]["confidence"] in ("high", "medium", "low")
    assert out["flags"]["jurisdiction"]
    assert out.get("sources"), "a live read must carry the Sources block"
    assert estimate_tokens(out["text"]) <= 800


@needs_mirror
def test_live_facts_lane(live):
    out = live.registry.call("kb_facts", {"query": "concrete block paving", "limit": 3})
    assert out["blocks"]
    assert all(b["flags"]["confidence"] for b in out["blocks"])


@needs_mirror
def test_live_dcc_domains_never_pretend_to_ground_apis(live):
    """The bpy/unreal domains serve like everything else, flag-carrying -
    the CLAUDE.md rule (never an API source) rides on those flags."""
    hits = live.registry.call(
        "kb_search", {"query": "geometry nodes", "domain": "14_software_blender"}
    )["hits"]
    assert hits and all(h["confidence"] for h in hits)
