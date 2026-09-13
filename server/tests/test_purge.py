"""A52 — reclaiming what TEE left behind, and the four things it will not do.

TEE writes and almost never reaps: adapter workdirs from tempfile.mkdtemp
that outlive their process, derived renders, staged copies, caches. On the
owner's machine `~/TEE/.tee` had reached 1.5 GB with orphaned `tee-*`
directories scattered across /tmp and /var/folders.

A delete tool earns trust by what it refuses, so most of this file is
refusals.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from tee import purge as purge_mod
from tee.kernel.errors import TeeError
from tee.purge import CATEGORIES, DEFAULT_CATEGORIES, PROTECTED, purge


@pytest.fixture(autouse=True)
def fixture_owned_workdir_roots(tmp_path, monkeypatch):
    """No test may enumerate - let alone delete - a real system temp directory.

    `workdirs` discovery ignores `project_root`: it globs `tee-*` under
    `tempfile.gettempdir()` AND a hard-coded `/tmp`. `workdirs` is in
    DEFAULT_CATEGORIES and `older_than_days` defaults to 0, so the three
    `confirm=True` tests below used to sweep the real machine. On 2026-09-13
    that deleted a live review export, its pytest log and a build in progress.
    Patching TMPDIR is NOT enough, because `/tmp` is named in the source.

    Autouse on purpose: a new test must not be able to forget it.
    """
    root = tmp_path / "fixture-temp"
    root.mkdir()
    monkeypatch.setattr(purge_mod, "_workdir_roots", lambda: {root})
    return root


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


# -- the boundary itself, after the suite deleted a live export -------------


def test_a_confirmed_sweep_reaches_only_fixture_owned_paths(
    state, tmp_path, fixture_owned_workdir_roots
):
    """The regression for 2026-09-13: a confirmed purge from this very file
    swept the real system temp directories and destroyed a live review export,
    its log and a build in progress. Discovery ignored `project_root`.

    A sentinel OUTSIDE the fixture root must survive, and the only thing a
    confirmed sweep may remove is a directory TEE can prove it owns and whose
    owner is gone.
    """
    from tee.kernel import workdirs

    sentinel = tmp_path / "outside" / "precious"
    sentinel.mkdir(parents=True)
    (sentinel / "evidence.log").write_text("a review artefact nobody may delete")

    # also name it like a workdir: the prefix must not be what decides
    decoy = tmp_path / "outside" / "tee-decoy"
    decoy.mkdir()
    (decoy / "payload").write_text("outside the roots, so out of reach")

    root = fixture_owned_workdir_roots
    dead = root / "tee-dead"
    dead.mkdir()
    (dead / "payload").write_text("x")
    workdirs.claim(dead)
    marker = json.loads((dead / workdirs.MARKER).read_text())
    marker["pid"] = 2**22  # a pid that cannot be running
    (dead / workdirs.MARKER).write_text(json.dumps(marker))

    live = root / "tee-live"
    live.mkdir()
    (live / "payload").write_text("y")
    workdirs.claim(live)  # this process is the owner and is very much alive

    result = purge({"categories": ["workdirs"], "confirm": True}, project_root=state)

    assert result["removed"] == 1, "only the provably abandoned workdir may go"
    assert not dead.exists()
    assert live.exists(), "a workdir whose owner is running must survive"
    assert (sentinel / "evidence.log").is_file(), "purge reached outside its roots"
    assert (decoy / "payload").is_file(), "a tee-* name outside the roots is not a target"


def test_an_unowned_workdir_is_kept_and_called_unverified_not_orphaned(
    state, fixture_owned_workdir_roots
):
    """No marker means TEE cannot prove the directory is its own, so it stays.
    Leaving legacy directories unreclaimed is the correct trade: their
    existence is not permission to delete them."""
    legacy = fixture_owned_workdir_roots / "tee-from-some-older-run"
    legacy.mkdir()
    (legacy / "payload").write_text("z")

    dry = purge({"categories": ["workdirs"]}, project_root=state)
    assert dry["candidates"] == 0
    kept = {Path(k["path"]).name: k for k in dry["kept"]}
    assert kept["tee-from-some-older-run"]["state"] == "unverified"
    assert {k["state"] for k in dry["kept"]} == {"unverified"}
    # the note must say what it is, and say what it is NOT
    assert "not an orphan" in dry["note"] or "not orphans" in dry["note"]

    purge({"categories": ["workdirs"], "confirm": True}, project_root=state)
    assert legacy.is_dir(), "an unverified directory must survive a confirmed sweep"


def test_a_recycled_pid_does_not_make_a_live_workdir_reclaimable(
    state, fixture_owned_workdir_roots
):
    """The marker records the owner's start time as well as its pid. A pid that
    has been reused reads as unverified - we cannot prove the ORIGINAL owner
    exited - rather than as an abandoned directory."""
    from tee.kernel import workdirs

    d = fixture_owned_workdir_roots / "tee-recycled"
    d.mkdir()
    workdirs.claim(d)
    marker = json.loads((d / workdirs.MARKER).read_text())
    marker["started"] = "not the start time we recorded"
    (d / workdirs.MARKER).write_text(json.dumps(marker))

    assert workdirs.state_of(d)["state"] == workdirs.UNVERIFIED
    purge({"categories": ["workdirs"], "confirm": True}, project_root=state)
    assert d.is_dir()


def test_a_symlink_named_like_a_workdir_is_never_followed(
    state, tmp_path, fixture_owned_workdir_roots
):
    """Following one would delete whatever it points at, which is how a purge
    turns into arbitrary path deletion."""
    target = tmp_path / "outside" / "real"
    target.mkdir(parents=True)
    (target / "payload").write_text("not ours to remove")
    (fixture_owned_workdir_roots / "tee-link").symlink_to(target)

    purge({"categories": ["workdirs"], "confirm": True}, project_root=state)
    assert (target / "payload").is_file()
    assert (fixture_owned_workdir_roots / "tee-link").is_symlink()


def test_ownership_is_rechecked_at_deletion_not_trusted_from_the_dry_run(
    state, fixture_owned_workdir_roots
):
    """A dry run is evidence for a decision, never a licence to delete later:
    a workdir can be claimed by a live owner between the listing and the sweep."""
    from tee.kernel import workdirs

    d = fixture_owned_workdir_roots / "tee-claimed-late"
    d.mkdir()
    (d / "payload").write_text("x")
    workdirs.claim(d)
    marker = json.loads((d / workdirs.MARKER).read_text())
    (d / workdirs.MARKER).write_text(json.dumps({**marker, "pid": 2**22}))

    dry = purge({"categories": ["workdirs"]}, project_root=state)
    assert [Path(i["path"]).name for i in dry["items"]] == ["tee-claimed-late"]

    workdirs.claim(d)  # a live process takes it over after the dry run
    done = purge({"categories": ["workdirs"], "confirm": True}, project_root=state)
    assert done["removed"] == 0
    assert d.is_dir(), "the deletion-time recheck must see the new owner"
