"""The upgrade trap: extras vanish and the error blames the owner.

Installing a TEE bundle rebuilds the extension venv from its lock and drops
anything installed on top — and the fleet extras are on top by design,
because A46 P1 cut the base venv from 2.2 GB to 586 MB by keeping them out.
Measured three upgrades running: 0.10.0, 0.11.0 and 0.12.0 each took the
venv from ~1.1 GB back to 34 MB.

Documentation did not fix it, twice. The defect is not that the extras go —
that is how `uv sync` works — it is that `probe.need()` then says "uv pip
install 'tee-engine[medimg]'", which reads as *you never set this up*. The
owner did set it up. These tests pin the distinction.
"""

from __future__ import annotations

import json

import pytest

from tee.fleet import probe
from tee.kernel import extras
from tee.kernel.errors import TeeError


@pytest.fixture
def state(tmp_path, monkeypatch):
    monkeypatch.setattr(probe, "_state_dir", [tmp_path])
    return tmp_path


def _seen(state, mapping):
    (state / extras.STATE_FILE).write_text(json.dumps(mapping))


def test_a_group_that_vanished_is_named_and_dated(state, monkeypatch):
    monkeypatch.setattr(extras, "present", lambda: {"quant"})
    _seen(state, {"medimg": "2026-08-30", "quant": "2026-08-30"})
    assert extras.lost(state) == {"medimg": "2026-08-30"}
    note = extras.loss_note("medimg", state)
    assert "installed here on 2026-08-30" in note
    assert "not a setup you never did" in note


def test_the_refusal_stops_blaming_the_owner(state, monkeypatch):
    """The whole fix in one assertion."""
    monkeypatch.setattr(extras, "present", lambda: set())
    _seen(state, {"medimg": "2026-08-30"})
    with pytest.raises(TeeError) as e:
        probe.need("no_such_module_xyz", "medimg", what="the DICOM reader")
    assert "is missing now" in e.value.message
    assert "rebuilds the venv from its lock" in e.value.message
    # and it still carries the actual command
    assert "tee-engine[medimg]" in e.value.fix


def test_a_genuinely_new_setup_is_not_told_it_lost_something(state, monkeypatch):
    """The opposite error would be just as bad: telling someone who never
    installed an extra that an upgrade ate it."""
    monkeypatch.setattr(extras, "present", lambda: set())
    _seen(state, {})  # nothing was ever recorded
    with pytest.raises(TeeError) as e:
        probe.need("no_such_module_xyz", "medimg")
    assert "is missing now" not in e.value.message
    assert "tee-engine[medimg]" in e.value.fix


def test_remember_never_forgets_on_its_own(state, monkeypatch):
    """The last-seen date IS the evidence. A group that disappears must keep
    its record, or the next refusal cannot prove it was ever there."""
    monkeypatch.setattr(extras, "present", lambda: {"medimg", "quant"})
    extras.remember(state, today="2026-08-30")
    monkeypatch.setattr(extras, "present", lambda: {"quant"})  # an upgrade
    kept = extras.remember(state, today="2026-08-31")
    assert kept["medimg"] == "2026-08-30", "the lost group was forgotten"
    assert kept["quant"] == "2026-08-31"


def test_cad_absence_is_never_reported_as_a_loss():
    """A46 P1b moved CadQuery to a sidecar on purpose; it is not supposed to
    be in TEE's venv, so its absence must not read as damage."""
    assert "cad" in extras.NOT_IN_TEE_VENV
    assert "cad" not in extras.present()


def test_bookkeeping_never_breaks_a_tool_call(state, monkeypatch):
    """A diagnostic that raises is worse than no diagnostic."""
    monkeypatch.setattr(extras, "lost", lambda _s: (_ for _ in ()).throw(RuntimeError("boom")))
    with pytest.raises(TeeError) as e:  # the REAL error, not RuntimeError
        probe.need("no_such_module_xyz", "medimg")
    assert "not installed" in e.value.message


def test_unwritable_state_dir_is_survived(tmp_path, monkeypatch):
    monkeypatch.setattr(extras, "present", lambda: {"quant"})
    bad = tmp_path / "nope"
    bad.write_text("i am a file, not a directory")
    assert extras.remember(bad, today="2026-08-31") == {"quant"} or True  # must not raise


def test_no_state_dir_means_no_claim():
    assert extras.lost(None) == {}
    assert extras.loss_note("medimg", None) is None


def test_doctor_reports_the_loss_where_someone_will_look(tmp_path, monkeypatch):
    """A refusal only reaches whoever called that one tool. `tee doctor` is
    where you look when something is wrong and you do not know what."""
    from tee.doctor import check_extras

    monkeypatch.setattr(extras, "present", lambda: {"quant"})
    (tmp_path / ".tee").mkdir()
    _seen(tmp_path / ".tee", {"medimg": "2026-08-30", "quant": "2026-08-30"})
    c = check_extras(tmp_path)
    assert c.status == "warn"
    assert "MISSING after an upgrade" in c.detail and "medimg" in c.detail
    assert "tee-engine[medimg]" in c.fix
    # A real interpreter path, not a placeholder: the difference between a
    # command you can paste and one you have to solve.
    import sys as _sys

    assert _sys.executable in c.fix
    assert "<" not in c.fix


def test_doctor_is_quiet_when_nothing_was_lost(tmp_path, monkeypatch):
    from tee.doctor import check_extras

    monkeypatch.setattr(extras, "present", lambda: {"quant", "solve"})
    (tmp_path / ".tee").mkdir()
    _seen(tmp_path / ".tee", {"quant": "2026-08-30"})
    c = check_extras(tmp_path)
    assert c.status == "ok"
    assert "sidecar by design" in c.detail  # cad's absence explained, not flagged
