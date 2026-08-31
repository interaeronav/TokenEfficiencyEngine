"""A49 P2 — the Godot adapter, on a fake wire so CI needs no Godot.

The live acceptance ran against real headless Godot 4.7.2 and is recorded
in PROGRESS. These tests pin the contract and the two behaviours that are
easy to get wrong later: the render refusal must stay a refusal, and the
diff must name what changed rather than reporting success.
"""

from __future__ import annotations

import pytest

from tee.adapters.godot import GodotAdapter
from tee.kernel.adapter import Adapter
from tee.kernel.errors import TeeError


class FakeWire:
    """Speaks the bridge's reply shapes without a game engine."""

    port = 9879

    def __init__(self, **replies):
        self.replies = replies
        self.sent = []

    def probe(self):
        return True

    def request(self, payload, timeout=None):
        self.sent.append(payload)
        kind = payload.get("type")
        if kind == "ping":
            return {"godot": "4.7.2-stable (official)", "display": "headless", "can_render": False}
        if kind == "list":
            return self.replies.get("list", {"nodes": []})
        if kind == "commands":
            return self.replies.get("commands", {"ops": [], "changed": [], "nodes": 0})
        raise AssertionError(f"unexpected request {kind}")


def test_it_satisfies_the_adapter_protocol():
    """The whole point: Godot arrives with NO new always-loaded tools,
    because tee_scene_summary and friends already drive this shape."""
    assert isinstance(GodotAdapter(wire=FakeWire()), Adapter)


def test_info_reports_that_it_cannot_render():
    """Discovered up front, not at capture time."""
    info = GodotAdapter(wire=FakeWire()).info().to_payload()
    assert info["product"] == "Godot" and info["connected"] is True
    assert info["can_render"] is False and info["display"] == "headless"


def test_capture_refuses_with_the_measured_reason():
    """A black rectangle would be worse than a refusal: it looks like an
    answer. The message carries the actual finding, not 'unsupported'."""
    with pytest.raises(TeeError) as e:
        GodotAdapter(wire=FakeWire()).capture("camera", 96 * 1024)
    assert e.value.code == "godot_no_render"
    assert "dummy" in e.value.message and "4.7.2" in e.value.message
    assert "tee_scene_summary" in e.value.fix and "run_scene" in e.value.fix


def test_the_diff_names_what_changed():
    wire = FakeWire(
        commands={
            "ops": [{"op": "add_node", "path": "/root/Player"}],
            "changed": [
                {"added": "Player", "type": "MeshInstance3D", "props": ["mesh"]},
                {"removed": "Old"},
            ],
            "nodes": 1,
        }
    )
    diff = GodotAdapter(wire=wire).execute([{"op": "add_node", "type": "MeshInstance3D"}])
    assert diff.created == ["Player"] and diff.deleted == ["Old"]
    assert diff.details["Player"]["type"] == "MeshInstance3D"


def test_a_run_scene_op_becomes_a_readable_note():
    """The game-design evidence channel: no pixels, so the note carries what
    the logic actually did."""
    wire = FakeWire(
        commands={
            "ops": [
                {
                    "op": "run_scene",
                    "res": "res://main.tscn",
                    "frames_run": 60,
                    "nodes_after_ready": 3,
                    "wall_ms": 12,
                }
            ],
            "changed": [],
            "nodes": 1,
        }
    )
    diff = GodotAdapter(wire=wire).execute([{"op": "run_scene", "res": "res://main.tscn"}])
    assert any("60 frames" in n and "3 nodes ready" in n for n in diff.notes)


def test_entities_carry_stable_paths():
    wire = FakeWire(
        list={
            "nodes": [
                {"path": "/World", "name": "World", "type": "Node3D", "children": 1},
                {
                    "path": "/World/Player",
                    "name": "Player",
                    "type": "CharacterBody3D",
                    "children": 0,
                },
            ]
        }
    )
    entities = GodotAdapter(wire=wire).list_entities()
    assert [e.id for e in entities] == ["/World", "/World/Player"]
    assert entities[1].parent == "/World"


def test_an_empty_batch_does_not_touch_the_engine():
    wire = FakeWire()
    assert GodotAdapter(wire=wire).execute([]).is_empty()
    assert wire.sent == []


def test_a_checkpoint_without_a_scene_refuses():
    with pytest.raises(TeeError) as e:
        GodotAdapter(wire=FakeWire()).restore({})
    assert e.value.code == "godot_bad_checkpoint"


def test_checkpoints_are_written_outside_the_owners_project():
    """A rollback must not leave debris in someone's game."""
    wire = FakeWire()
    payload = GodotAdapter(wire=wire).snapshot("before edit")
    assert payload["scene"].startswith("user://")
    op = wire.sent[-1]["ops"][0]
    assert op["op"] == "save_scene" and op["overwrite"] is True


def test_launching_without_a_project_refuses_by_name(tmp_path):
    adapter = GodotAdapter(wire=FakeWire(), project=tmp_path)
    adapter.wire.probe = lambda: False
    with pytest.raises(TeeError) as e:
        adapter.ensure_bridge(repo_root=tmp_path)
    assert e.value.code in ("godot_no_project", "godot_missing")


# -- run_scene: the headless evidence channel -------------------------------


def test_run_scene_needs_a_project(tmp_path):
    a = GodotAdapter(wire=FakeWire())
    with pytest.raises(TeeError) as e:
        a.run_scene(frames=10)
    assert e.value.code in ("godot_no_project", "godot_missing")


def test_run_scene_counts_script_errors_because_the_exit_code_lies(monkeypatch, tmp_path):
    """Measured: a game whose _ready raises still exits 0. Godot does not
    fail the process on a script error, so a lane that trusted the exit code
    would call a broken game a pass."""
    import subprocess as sp

    from tee.adapters.godot import adapter as mod

    (tmp_path / "project.godot").write_text("config_version=5\n")
    monkeypatch.setattr(mod, "find_godot", lambda: "/bin/echo")

    class Done:
        returncode = 0
        stdout = (
            "Godot Engine v4.7.2\nTEE_SAMPLE ready\n"
            "SCRIPT ERROR: Invalid access to property 'x' on a base object of type 'Nil'.\n"
        )
        stderr = ""

    monkeypatch.setattr(sp, "run", lambda *a, **k: Done())
    result = GodotAdapter(wire=FakeWire(), project=tmp_path).run_scene(frames=20)
    assert result["exit_code"] == 0
    assert result["ok"] is False and result["script_errors"] == 1
    assert "TEE_SAMPLE ready" in result["output"]
    assert not any("Godot Engine v" in line for line in result["output"])


def test_the_bridge_no_longer_pretends_to_run_scenes():
    """The bridge script IS the SceneTree main loop, so it cannot hand that
    loop to a game. Its first version counted a for-loop while _process
    never ran - execution-shaped and not execution."""
    from pathlib import Path

    bridge = Path(__file__).resolve().parents[2] / "adapters/godot/tee_bridge/bridge.gd"
    source = bridge.read_text()
    assert "adapter-level operation" in source
    assert "cannot yield its own main loop" in source


def test_capture_windowed_is_opt_in_and_says_it_opens_a_window():
    """Headless cannot render under ANY driver - measured across vulkan,
    opengl3 and dummy. Pixels cost a real window, so this never happens by
    itself and capture() still refuses."""
    import inspect

    source = inspect.getsource(GodotAdapter.capture_windowed)
    assert "opens a window" in source
    assert "never opens itself" in source
    refusal = inspect.getsource(GodotAdapter.capture)
    assert "capture_windowed" in refusal and "opt-in" in refusal
