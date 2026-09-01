"""A52 — reclaiming what TEE left behind, and the four things it will not do.

TEE writes and almost never reaps: adapter workdirs from tempfile.mkdtemp
that outlive their process, derived renders, staged copies, caches. On the
owner's machine `~/TEE/.tee` had reached 1.5 GB with orphaned `tee-*`
directories scattered across /tmp and /var/folders.

A delete tool earns trust by what it refuses, so most of this file is
refusals.
"""

from __future__ import annotations

import pytest

from tee.kernel.errors import TeeError
from tee.purge import CATEGORIES, DEFAULT_CATEGORIES, PROTECTED, purge


@pytest.fixture
def state(tmp_path):
    tee = tmp_path / ".tee"
    (tee / "generated").mkdir(parents=True)
    (tee / "generated" / "render.jpg").write_bytes(b"x" * 2048)
    (tee / "shadow").mkdir()
    (tee / "shadow" / "checkpoint.blend").write_bytes(b"y" * 4096)
    (tee / "sidecars").mkdir()
    (tee / "sidecars" / "cad").mkdir()
    (tee / "sidecars" / "cad" / "big").write_bytes(b"z" * 8192)
    (tee / "senses-cache.json").write_text("{}")
    for keeper in ("config.toml", "memory.json", "extras-seen.json", "llm-profile.json"):
        (tee / keeper).write_text("keep me")
    return tmp_path


# -- the default is to do nothing ------------------------------------------


def test_a_purge_is_a_dry_run_until_told_otherwise(state):
    result = purge({}, project_root=state)
    assert result["dry_run"] is True
    assert "Nothing was deleted" in result["note"]
    assert (state / ".tee" / "generated" / "render.jpg").is_file()


def test_the_dry_run_shows_size_and_age_so_the_choice_is_evidenced(state):
    result = purge({}, project_root=state)
    assert result["candidates"] >= 1
    for item in result["items"]:
        assert item["bytes"] >= 0
        assert "age_days" in item
        assert item["losing_it_costs"], "every item must say what losing it costs"


# -- what it will not touch -------------------------------------------------


def test_records_and_decisions_are_never_candidates(state):
    """Project memory, config, the upgrade record and the engine pin are not
    artefacts: a rebuild cannot restore them."""
    names = {
        p.rsplit("/", 1)[-1]
        for p in (
            i["path"] for i in purge({"categories": list(CATEGORIES)}, project_root=state)["items"]
        )
    }
    assert not (names & PROTECTED)


def test_confirmed_purge_still_leaves_the_records(state):
    purge({"categories": list(CATEGORIES), "confirm": True}, project_root=state)
    for keeper in ("config.toml", "memory.json", "extras-seen.json", "llm-profile.json"):
        assert (state / ".tee" / keeper).is_file(), f"{keeper} was removed"


def test_rollback_history_is_not_swept_by_default(state):
    """Losing the ability to undo is not a housekeeping decision."""
    assert "checkpoints" not in DEFAULT_CATEGORIES
    purge({"confirm": True}, project_root=state)
    assert (state / ".tee" / "shadow" / "checkpoint.blend").is_file()


def test_a_working_capability_is_not_garbage(state):
    """The CAD sidecar is 1.4 GB and IS the STEP-measuring capability. It is
    excluded from the default sweep and its entry says what removing it
    costs."""
    assert "sidecars" not in DEFAULT_CATEGORIES
    purge({"confirm": True}, project_root=state)
    assert (state / ".tee" / "sidecars" / "cad" / "big").is_file()
    listed = purge({"categories": ["sidecars"]}, project_root=state)["items"]
    assert any("cad_measure" in i["losing_it_costs"] for i in listed)


def test_it_cannot_be_aimed_somewhere_else():
    """A purge tool that takes a path is a delete tool with a friendly name.
    The scope is TEE's own state and its own temp dirs, and the schema
    offers no way to change that."""
    import inspect

    from tee import purge as mod

    signature = inspect.signature(mod.purge)
    assert set(signature.parameters) == {"spec", "project_root"}
    # The declared schema offers categories, an age filter and confirm -
    # and no way to name a directory.
    source = inspect.getsource(mod.register_purge_tools)
    block = source[source.index('"properties"') : source.index("handler=")]
    assert '"categories"' in block and '"confirm"' in block
    assert '"path"' not in block and '"root"' not in block and '"dir"' not in block


# -- it does what it says ---------------------------------------------------


def test_confirming_actually_reclaims(state):
    before = purge({"categories": ["derived"]}, project_root=state)
    done = purge({"categories": ["derived"], "confirm": True}, project_root=state)
    assert done["dry_run"] is False
    assert done["removed"] >= 1
    assert done["reclaimed_bytes"] == before["would_reclaim_bytes"]
    assert not (state / ".tee" / "generated").exists()


def test_an_age_filter_spares_fresh_work(state):
    """Purging something made a minute ago is rarely what anyone means."""
    result = purge({"categories": ["derived"], "older_than_days": 365}, project_root=state)
    assert result["candidates"] == 0


def test_an_unknown_category_names_the_real_ones(state):
    with pytest.raises(TeeError) as e:
        purge({"categories": ["everything"]}, project_root=state)
    assert e.value.code == "purge_unknown_category"
    assert "checkpoints" in e.value.fix and "excluded from it on purpose" in e.value.fix


def test_it_writes_artifacts_and_is_explicitly_tabled():
    from tee.kernel import trust

    assert trust.capability_for("tee_purge") == "write-artifacts"
    assert "tee_purge" in trust._EXPLICIT


def test_it_is_discoverable_by_the_words_someone_would_use(tmp_path):
    from tee.app import TeeApp
    from tee.purge import register_purge_tools

    app = TeeApp({}, project_root=tmp_path)
    register_purge_tools(app, tmp_path)
    for query in ("reclaim disk space", "clean up temp files", "purge caches"):
        top = [i["name"] for i in app.registry.search(query)["items"]][:3]
        assert "tee_purge" in top, f"{query!r} -> {top}"
