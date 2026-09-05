"""A68 P3: the handoff lands in-server.

`pk_export`, `sk_handoff` and `fc_export` write a file another application
loads; `kernel/handoff_import.land` is what `into=` runs: the one served
lane that imports the file (or the named one), a write-scene the trust
kernel decides as such, one checkpointed batch on that lane, and a verdict
comparing what the lane read back with what the writer declared. An
export with no `into` never touches a scene. The scale rule is the trap
both handoff modules document: a .glb lands at 1.0 whatever the source's
units; a format that declares nothing scales from the writer's units, and
a writer that declared none is refused, never guessed."""

from __future__ import annotations

import dataclasses
import re
from pathlib import Path

import pytest
from fixtures_freecad import FakeFcWire
from fixtures_partkiln import FakeKernel, _write_minimal_glb
from test_lane_routing import Lane

from tee.adapters.freecad.adapter import FreeCADAdapter
from tee.adapters.freecad.tools import register_freecad_tools
from tee.adapters.partkiln.adapter import PartkilnAdapter
from tee.app import TeeApp
from tee.kernel import trustctx
from tee.kernel.adapter import Diff, Entity, LaneVocab, _upsert
from tee.kernel.errors import TeeError
from tee.kernel.handoff_import import land, scale_for, unit_m, verify

BRACKET_M = [0.12, 0.01, 0.08]  # a GLB's extents, Y-up, metres


def _dims(path: Path) -> list[float]:
    """What a file declares: a real GLB is probed; a test OBJ carries a
    `# dims a b c` line in its own units."""
    if path.suffix.lower() in (".glb", ".gltf"):
        from tee.assets import gltf

        return [float(v) for v in gltf.probe(path)["extents_m"]]
    first = path.read_text().splitlines()[0]
    return [float(v) for v in first.split()[2:5]]


class Scene(Lane):
    """A lane that imports files the way Blender does: an `import_file` op
    creates an entity whose dimensions are what the file declares, times
    props.scale - so a wrong scale shows in the read-back, as it would."""

    def __init__(self, name: str = "scene", imports=("glb", "gltf", "obj")) -> None:
        super().__init__(name, ops=("create", "set", "delete", "import_file"), kinds=("cube",))
        self._vocab = LaneVocab(
            ops=self._vocab.ops,
            kinds=self._vocab.kinds,
            kind_optional=True,
            imports=tuple(imports),
            renders=True,
            purpose=f"the {name} scene",
        )
        self.batches: list[list[dict]] = []

    def execute(self, batch):
        self.batches.append(batch)
        plain = [op for op in batch if op.get("op") != "import_file"]
        diff = super().execute(plain) if plain else Diff()
        for op in batch:
            if op.get("op") != "import_file":
                continue
            path = Path(op["path"])
            scale = (op.get("props") or {}).get("scale") or [1.0, 1.0, 1.0]
            eid = f"e{self._next_id}"
            self._next_id += 1
            ent = Entity(
                id=eid,
                name=op.get("name") or path.stem,
                kind="mesh",
                summary={
                    "dimensions": [round(d * s, 6) for d, s in zip(_dims(path), scale, strict=True)]
                },
            )
            self._store[eid] = ent
            diff.created.append(eid)
            diff.details[eid] = ent.detailed()
            _upsert(diff, ent)
        return diff


def _cad(name: str = "partkiln") -> Lane:
    return Lane(
        name,
        ops=("create", "set", "delete", "param_set", "export"),
        kinds=("part", "sketch"),
        kind_optional=False,
    )


@pytest.fixture
def app(tmp_path):
    application = TeeApp({"partkiln": _cad(), "scene": Scene()}, project_root=tmp_path)
    yield application
    application.shutdown()


def _glb(tmp_path: Path, name: str = "bracket") -> str:
    path = tmp_path / "out" / f"{name}.glb"
    path.parent.mkdir(parents=True, exist_ok=True)
    _write_minimal_glb(path, BRACKET_M)
    return str(path)


def _obj(tmp_path: Path, dims_mm=(120.0, 80.0, 10.0)) -> str:
    path = tmp_path / "out" / "bracket.obj"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("# dims " + " ".join(str(v) for v in dims_mm) + "\nv 0 0 0\n")
    return str(path)


# -- the scale rule -----------------------------------------------------------


def test_a_self_describing_file_never_gets_a_scale():
    assert scale_for("glb", "mm") == 1.0
    assert scale_for("gltf", None) == 1.0
    assert scale_for("obj", "mm") == 0.001
    assert scale_for("obj", "cm") == 0.01
    assert scale_for("fbx", 0.0254) == 0.0254  # metres per unit, as a number
    assert unit_m("1 unit = 0.01 m") == 0.01  # seamkiln's manifest line


def test_a_writer_that_declared_no_units_is_refused_not_guessed():
    with pytest.raises(TeeError) as err:
        scale_for("obj", None)
    assert err.value.code == "handoff_units_unknown"
    assert "glb" in err.value.fix


# -- landing ------------------------------------------------------------------


def test_a_glb_lands_at_scale_one_as_one_checkpointed_batch_with_a_verdict(app, tmp_path):
    scene = app.adapters["scene"]
    out = land(app, files={"bracket": _glb(tmp_path)}, into="scene", units="m", caller="t")
    assert out["lane"] == "scene" and out["scale"] == 1.0
    assert out["checkpoint"].startswith("cp") and len(out["created"]) == 1
    assert "note" not in out
    assert len(scene.batches) == 1 and scene.batches[0][0]["op"] == "import_file"
    assert scene.batches[0][0]["props"] == {}, "a glb declares its own units: no scale"
    # the verdict compares what the lane read back with what the file declares
    assert out["verify"]["ok"] is True
    assert sorted(out["verify"]["read_back"]) == pytest.approx(sorted(BRACKET_M))
    # the checkpoint is the lane's own: rollback finds it there
    assert app.checkpoints.find(out["checkpoint"])[0] == "scene"


def test_a_format_that_declares_nothing_scales_from_the_writers_units(app, tmp_path):
    scene = app.adapters["scene"]
    out = land(
        app,
        files={"bracket": _obj(tmp_path)},
        into="scene",
        units="mm",
        expected_dims_m=[0.12, 0.08, 0.01],
        caller="t",
    )
    assert out["scale"] == 0.001 and "metre" in out["note"]
    assert scene.batches[0][0]["props"]["scale"] == [0.001, 0.001, 0.001]
    assert out["verify"]["ok"] is True
    # the same file with the wrong units reads back a thousand times off
    wrong = land(
        app,
        files={"b2": _obj(tmp_path)},
        into="scene",
        units="m",
        expected_dims_m=[0.12, 0.08, 0.01],
        caller="t",
    )
    assert wrong["verify"]["ok"] is False and "deviates" in wrong["verify"]["note"]


def test_two_files_land_in_one_batch_and_the_primary_gets_the_verdict(app, tmp_path):
    scene = app.adapters["scene"]
    files = {"jacket": _glb(tmp_path, "jacket"), "jacket-hardware": _glb(tmp_path, "jacket-hw")}
    out = land(app, files=files, into="scene", caller="t")
    assert len(scene.batches) == 1 and len(scene.batches[0]) == 2
    assert len(out["created"]) == 2 and out["verify"]["ok"] is True


def test_into_auto_is_the_one_served_lane_that_imports_the_suffix(tmp_path):
    three = TeeApp(
        {"partkiln": _cad(), "scene": Scene(), "seamkiln": _cad("seamkiln")},
        project_root=tmp_path,
    )
    try:
        out = land(three, files={"b": _glb(tmp_path)}, into="auto", caller="t")
        assert out["lane"] == "scene"
        assert land(three, files={"b": _glb(tmp_path)}, into=None, caller="t")["lane"] == "scene"
    finally:
        three.shutdown()


def test_auto_refuses_when_no_lane_or_two_lanes_import_the_suffix(tmp_path):
    none = TeeApp({"partkiln": _cad(), "seamkiln": _cad("seamkiln")}, project_root=tmp_path)
    try:
        with pytest.raises(TeeError) as err:
            land(none, files={"b": _glb(tmp_path)}, into="auto", caller="t")
        assert err.value.code == "handoff_no_importer"
    finally:
        none.shutdown()
    two = TeeApp({"a": Scene("a"), "b": Scene("b"), "partkiln": _cad()}, project_root=tmp_path)
    try:
        with pytest.raises(TeeError) as err:
            land(two, files={"b": _glb(tmp_path)}, into="auto", caller="t")
        assert err.value.code == "handoff_importer_ambiguous"
        assert "a, b" in err.value.message
    finally:
        two.shutdown()


def test_a_lane_that_does_not_import_the_suffix_refuses_naming_one_that_can(app, tmp_path):
    with pytest.raises(TeeError) as err:
        land(app, files={"b": _glb(tmp_path)}, into="partkiln", caller="t")
    assert err.value.code == "handoff_import_unsupported"
    assert "into=scene" in err.value.fix
    assert app.adapters["scene"].batches == [], "nothing landed anywhere"


def test_a_step_file_is_refused_with_the_glb_advice(app, tmp_path):
    step = tmp_path / "bracket.step"
    step.write_text("ISO-10303-21;\n")
    with pytest.raises(TeeError) as err:
        land(app, files={"b": str(step)}, into="scene", caller="t")
    assert err.value.code == "handoff_import_unsupported"
    assert "Export glb" in err.value.fix


def test_an_unknown_lane_and_a_missing_file_are_refused(app, tmp_path):
    with pytest.raises(TeeError) as err:
        land(app, files={"b": _glb(tmp_path)}, into="unreal", caller="t")
    assert err.value.code == "unknown_adapter"
    with pytest.raises(TeeError) as err:
        land(app, files={"b": str(tmp_path / "never.glb")}, into="scene", caller="t")
    assert err.value.code == "handoff_file_missing"


def test_landing_is_a_write_scene_the_trust_kernel_decides(app, tmp_path):
    """The calling tool is write-artifacts; the landing is a write-scene and
    is decided as one: a task carrying untrusted content may not do it. With
    the owner's flip signed the denial enforces; before it, the shadow band
    records it under the caller's name."""
    scene = app.adapters["scene"]
    before = trustctx.snapshot()
    try:
        app.registry.grants = dataclasses.replace(app.registry.grants, enforce_quality_band=True)
        trustctx.install("job", ("fetch-web:evil.example/page",))
        with pytest.raises(TeeError) as err:
            land(app, files={"b": _glb(tmp_path)}, into="scene", caller="pk_export")
        assert err.value.code == "trust_denied"
        assert "pk_export into=scene" in err.value.message
        assert scene.batches == [], "denied means nothing landed"
        app.registry.grants = dataclasses.replace(app.registry.grants, enforce_quality_band=False)
        out = land(app, files={"b": _glb(tmp_path)}, into="scene", caller="pk_export")
        assert out["lane"] == "scene"
        shadow = [d for d in app.registry.trust_denials if d["tool"] == "pk_export into=scene"]
        assert shadow and shadow[0]["capability"] == "write-scene" and shadow[0]["shadow"]
    finally:
        trustctx.install(*before)
        trustctx.clear_for_tests()


def test_the_verdict_matches_the_named_entity_first():
    batch = {
        "details": {
            "e1": {"name": "other", "dimensions": [9.0, 9.0, 9.0]},
            "e2": {"name": "bracket", "dimensions": [0.08, 0.12, 0.01]},
        }
    }
    assert verify(batch, [0.12, 0.01, 0.08], name="bracket")["ok"] is True
    assert verify(batch, None) is None
    assert verify({"details": {}}, [1.0]) is None


# -- the three tools ------------------------------------------------------------


def test_pk_export_into_lands_through_the_fake_kernel(tmp_path):
    kiln = PartkilnAdapter(tmp_path / "pk", kernel=FakeKernel())
    scene = Scene()
    app = TeeApp({"partkiln": kiln, "scene": scene}, project_root=tmp_path)
    try:
        out = str(tmp_path / "export" / "bracket.glb")
        plain = app.registry.call("pk_export", {"format": "glb", "out": out})
        assert "landed" not in plain and scene.batches == [], "no into: no scene touched"
        landed = app.registry.call("pk_export", {"format": "glb", "out": out, "into": "scene"})
        assert landed["path"] == out and landed["landed"]["lane"] == "scene"
        assert landed["landed"]["scale"] == 1.0 and len(landed["landed"]["created"]) == 1
        assert landed["landed"]["verify"]["ok"] is True
        assert len(scene.batches) == 1
        # the kernel never saw `into`, and the reply still says what was written
        assert landed["units"] == "mm" and landed["declares_units"] is True
        with pytest.raises(TeeError) as err:
            app.registry.call("pk_export", {"format": "glb", "out": out, "into": "partkiln"})
        assert err.value.code == "handoff_import_unsupported" and "into=scene" in err.value.fix
    finally:
        app.shutdown()


def test_pk_export_into_defaults_the_target_to_a_lane_named_for_its_application(tmp_path):
    kernel = FakeKernel()
    kiln = PartkilnAdapter(tmp_path / "pk", kernel=kernel)
    app = TeeApp({"partkiln": kiln, "blender": Scene("blender")}, project_root=tmp_path)
    try:
        out = str(tmp_path / "export" / "bracket.glb")
        app.registry.call("pk_export", {"format": "glb", "out": out, "into": "blender"})
        seen = [c for c in kernel.calls if c[0] == "export"][-1][1]
        assert seen.get("target") == "blender" and "into" not in seen
    finally:
        app.shutdown()


class _ExportingWire(FakeFcWire):
    """The hermetic shim has no exporters: the export script is answered
    here, writing the file the way FreeCAD would."""

    def py_json(self, code: str):
        found = re.search(r"export\(objs, '([^']+)'\)", code)
        if found and "import FreeCAD, json" in code:
            target = Path(found.group(1))
            target.parent.mkdir(parents=True, exist_ok=True)
            if target.suffix == ".glb":
                _write_minimal_glb(target, [0.6, 0.018, 0.4])
            else:
                target.write_text("ISO-10303-21;\n")
            return {"path": str(target), "bytes": target.stat().st_size}
        return super().py_json(code)


def test_fc_export_into_lands_a_glb_and_refuses_a_step(tmp_path):
    freecad = FreeCADAdapter(_ExportingWire())
    scene = Scene()
    app = TeeApp({"freecad": freecad, "scene": scene}, project_root=tmp_path)
    register_freecad_tools(app, freecad)
    try:
        glb = str(tmp_path / "fab" / "panel.glb")
        out = app.registry.call(
            "fc_export", {"objects": ["panel"], "format": "glb", "path": glb, "into": "auto"}
        )
        assert out["ok"] and out["landed"]["lane"] == "scene"
        assert out["landed"]["scale"] == 1.0 and out["landed"]["verify"]["ok"] is True
        with pytest.raises(TeeError) as err:
            app.registry.call(
                "fc_export",
                {
                    "objects": ["panel"],
                    "format": "step",
                    "path": glb[:-4] + ".step",
                    "into": "auto",
                },
            )
        assert err.value.code == "handoff_no_importer"
        assert len(scene.batches) == 1
    finally:
        app.shutdown()


def test_sk_handoff_out_and_into_land_the_bundle(tmp_path):
    pytest.importorskip("seamkiln")
    from seamkiln.session import Command

    from tee.adapters.seamkiln.adapter import SeamkilnAdapter

    garment = SeamkilnAdapter(str(tmp_path))
    scene = Scene()
    app = TeeApp(
        {"seamkiln": garment, "scene": scene}, project_root=tmp_path
    )  # sk_* register at boot
    try:
        listing = app.registry.call("sk_handoff", {})
        assert "targets" in listing and "blender" in listing["targets"]
        try:
            for command in (
                Command("block", {"block": "jacket-zip"}),
                Command("body", {"kind": "mannequin"}),
                Command("arrange", {"particle_distance_mm": 12.0}),
            ):
                garment.session.apply(command)
        except ModuleNotFoundError as exc:  # the drape solver's extra is not here
            pytest.skip(f"seamkiln needs {exc.name} to arrange a garment on this machine")
        out = app.registry.call(
            "sk_handoff", {"out": str(tmp_path / "shot"), "target": "blender", "into": "scene"}
        )
        assert out["target"] == "blender" and Path(out["files"]["garment"]).suffix == ".glb"
        assert "ops" not in out, "the ops were run, not handed back"
        assert out["landed"]["lane"] == "scene" and out["landed"]["scale"] == 1.0
        assert out["landed"]["verify"]["ok"] is True
        assert len(scene.batches) == 1
    finally:
        app.shutdown()
