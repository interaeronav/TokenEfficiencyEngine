"""The command model (A53 P5): one implementation, every client.

The property these tests protect is the one that makes seamkiln different
from the incumbents: the script is not an export feature, it is the history
the session was keeping anyway, and replaying it rebuilds the garment
exactly. If that ever stops being true, the GUI has grown a code path a
script cannot take - which is the moment the tool becomes a GUI with an API
bolted on, like the ones it is trying to improve upon.
"""

from __future__ import annotations

import json

import pytest

from seamkiln.session import VERBS, Command, CommandError, Session

TINY = {"particle_distance_mm": 25.0}


def built() -> Session:
    session = Session()
    session.apply(Command("block", {"block": "tee"}))
    session.apply(Command("allowance", {"mm": 10.0}))
    session.apply(Command("body", {"kind": "mannequin"}))
    session.apply(Command("arrange", TINY))
    session.apply(Command("drape", {"fabric": "cotton_poplin", "frames": 40}))
    return session


def test_a_command_is_recorded_only_when_it_succeeds() -> None:
    session = Session()
    with pytest.raises(CommandError):
        session.apply(Command("arrange", {}))
    assert session.history == [], "a failed command entered the script"

    session.apply(Command("block", {"block": "tee"}))
    assert [c.op for c in session.history] == ["block"]


def test_replay_reproduces_the_garment_exactly() -> None:
    session = built()
    replayed = Session.replay(session.script())
    assert replayed.fingerprint() == session.fingerprint()
    assert [c.op for c in replayed.history] == [c.op for c in session.history]


def test_a_script_round_trips_through_json(tmp_path) -> None:
    session = built()
    path = session.save_script(tmp_path / "s.json")
    assert json.loads(path.read_text())["seamkiln_script"] == 1
    assert Session.replay(path).fingerprint() == session.fingerprint()


def test_a_script_from_the_future_refuses_rather_than_guessing() -> None:
    with pytest.raises(CommandError, match="script version"):
        Session.replay({"seamkiln_script": 99, "commands": []})


def test_the_adapters_wire_shape_is_understood() -> None:
    """The TEE adapter spells arguments `props`; a script spells them `args`.
    Both are commands, and neither client needs to know about the other."""
    assert Command.from_dict({"op": "block", "props": {"block": "tee"}}).args == {"block": "tee"}
    assert Command.from_dict({"op": "block", "args": {"block": "tee"}}).args == {"block": "tee"}
    with pytest.raises(CommandError, match="names a verb"):
        Command.from_dict({"kind": "block"})


def test_unknown_verbs_list_the_known_ones() -> None:
    with pytest.raises(CommandError, match="seamkiln accepts"):
        Session().apply(Command("knit"))
    assert set(VERBS) == {
        "block",
        "panel",
        "seam",
        "allowance",
        "body",
        "arrange",
        "drape",
        "export",
        "fit",
        "delete",
    }


def test_drape_arranges_and_arrange_makes_a_body() -> None:
    """Each step supplies what the one before it would have. A refusal a
    caller can only answer by typing the obvious next line is friction."""
    session = Session()
    session.apply(Command("block", {"block": "tee"}))
    report = session.apply(Command("drape", {"frames": 10}))
    assert session.body is not None and session.garment is not None
    assert "seam_gaps" in report


def test_editing_the_pattern_invalidates_the_drape() -> None:
    """Stale geometry that looks current is worse than no geometry."""
    session = built()
    assert session.drape is not None
    session.apply(Command("panel", {"id": "EXTRA", "outline": [[0, 0], [50, 0], [50, 50]]}))
    assert session.drape is None and session.garment is None


def test_deleting_a_panel_takes_its_seams_with_it() -> None:
    session = Session()
    session.apply(Command("block", {"block": "tee"}))
    before = len(session.pattern.seams)
    session.apply(Command("delete", {"id": "SLEEVE_L"}))
    assert len(session.pattern.panels) == 3
    assert len(session.pattern.seams) < before
    assert all("SLEEVE_L" not in (s.a.panel, s.b.panel) for s in session.pattern.seams)


def test_a_missing_panel_lists_the_ones_that_exist() -> None:
    session = Session()
    session.apply(Command("block", {"block": "tee"}))
    with pytest.raises(CommandError, match="FRONT"):
        session.apply(Command("delete", {"id": "HOOD"}))


def test_the_summary_is_compact(tmp_path) -> None:
    summary = built().summary()
    assert set(summary) >= {"name", "commands", "pattern", "garment", "drape"}
    assert "Vertex" not in repr(summary) and "points" not in summary
    assert len(repr(summary)) < 2500


def test_export_needs_a_destination_and_a_known_format(tmp_path) -> None:
    session = Session()
    session.apply(Command("block", {"block": "tee"}))
    with pytest.raises(CommandError, match="where the file"):
        session.apply(Command("export", {"format": "dxf"}))
    with pytest.raises(CommandError, match="Formats"):
        session.apply(Command("export", {"format": "gerber", "out": str(tmp_path / "x")}))
    with pytest.raises(CommandError, match="3D export needs a garment"):
        session.apply(Command("export", {"format": "obj", "out": str(tmp_path / "x.obj")}))
    result = session.apply(Command("export", {"format": "svg", "out": str(tmp_path / "p.svg")}))
    assert result["scale"] == "1:1"
