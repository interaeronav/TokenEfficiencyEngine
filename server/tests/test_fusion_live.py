"""The Mac smoke for the Fusion lane (-m dcc): docs/fusion-lane.md steps 1-11
against the real TEE add-in, in one sitting.

    cd server && UV_FROZEN=1 uv run pytest -q -s -m dcc tests/test_fusion_live.py

Skips cleanly when no bridge add-in answers - the TEE add-in on 127.0.0.1:9881
or the FusionMcpBridge on :8766, whichever the machine runs (A71) - when no
design is open, when the design is direct-modeling, and - so it can never
touch your work - when the active design is not EMPTY: open File > New Design
first. Everything it makes stays in that unsaved design; close it without
saving.

A71: with TEE_FUSION_SCRATCH_DESIGN=1 and NO document open, the harness (not
the lane) opens a fresh untitled design over the bridge before the smoke and
closes that one document without saving afterwards - the calls doc 71 row 51
records, verified live. A design the owner has open is never used or closed.

Every fact doc 71 section 9 leaves to the smoke is measured here and
printed (run with -s), then written to fusion-live-facts.json in the test's
temp dir: which image extension the viewport wrote; whether a bare
rectangle carries constraints of its own; whether a face-placed hole bores
into the material by default; which occurrence a joint moves; the unit each
export declares. Paste the printed block back into the session that fills
doc 71 section 3's live column.
"""

from __future__ import annotations

import json
import math
import os
import re
import struct
import zipfile
from pathlib import Path

import pytest

from tee.adapters.fusion.adapter import FusionAdapter
from tee.adapters.fusion.tools import register_fusion_tools
from tee.adapters.fusion.wire import FusionAutoWire, FusionWire
from tee.app import TeeApp
from tee.kernel.errors import TeeError

pytestmark = pytest.mark.dcc

# Doc 71 row 51 (harness only, never emitted by the lane): a fresh untitled
# parametric design, and the close of exactly that document without saving.
OPEN_DESIGN = """\
import adsk.core
_app = adsk.core.Application.get()
_doc = _app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
result = {"document": str(_doc.name), "documents": _app.documents.count}
"""
CLOSE_DESIGN = """\
import adsk.core
_app = adsk.core.Application.get()
_closed = False
for _i in range(_app.documents.count):
    _d = _app.documents.item(_i)
    if str(_d.name) == %r:
        _closed = bool(_d.close(False)); break
result = {"closed": _closed, "documents": _app.documents.count}
"""


def _scratch_wanted() -> bool:
    return os.environ.get("TEE_FUSION_SCRATCH_DESIGN") == "1"


PLATE_MM3 = 120.0 * 80.0 * 10.0
HOLE_R = 3.3
HOLE_MM3 = math.pi * HOLE_R * HOLE_R * 10.0


def _live_wire() -> FusionWire:
    wire = FusionAutoWire(
        port=int(os.environ.get("TEE_FUSION_PORT", "9881")),
        http_port=int(os.environ.get("TEE_FUSION_HTTP_PORT", "8766")),
    )
    if not wire.probe():
        pytest.skip(
            "no Fusion bridge answering - the TEE add-in on 127.0.0.1:9881 (Utilities > "
            "Add-Ins > Scripts and Add-Ins, add adapters/fusion/tee_bridge/TEE and Run it) or "
            "the FusionMcpBridge on :8766 (auto-starts with Fusion once installed)"
        )
    print(f"\n  [wire] {wire.transport} on :{wire.port}")
    return wire


def _open_scratch(wire: FusionWire, app: TeeApp) -> tuple[dict, str | None]:
    """The active design, opening a scratch one only when nothing is open and
    the owner asked for it (TEE_FUSION_SCRATCH_DESIGN=1)."""
    probe = app.registry.call("fu_probe", {})
    if probe.get("design") is None and _scratch_wanted():
        opened = str(wire.execute(OPEN_DESIGN, timeout=30.0)["document"])
        print(f"  [harness] opened scratch design {opened!r}")
        return app.registry.call("fu_probe", {}), opened
    return probe, None


def _close_scratch(wire: FusionWire, opened: str | None) -> None:
    if opened is None:
        return
    try:
        out = wire.execute(CLOSE_DESIGN % opened, timeout=30.0)
    except TeeError as exc:
        print(f"  [harness] could not close {opened!r}: {exc.code} {exc.message}")
        return
    print(f"  [harness] closed scratch design {opened!r} without saving: {out}")


@pytest.fixture()
def served(tmp_path):
    wire = _live_wire()
    adapter = FusionAdapter(wire, workdir=str(tmp_path / "work"))
    app = TeeApp({"fusion": adapter}, project_root=tmp_path)
    register_fusion_tools(app, adapter)
    opened = None
    try:
        probe, opened = _open_scratch(wire, app)
        if probe.get("design") is None:
            pytest.skip(
                "no design is open: File > New Design, then re-run (or set "
                "TEE_FUSION_SCRATCH_DESIGN=1 to let the harness open and close one)"
            )
        if probe.get("design") != "parametric":
            pytest.skip("the design is direct-modeling: Design Settings > Capture Design History")
        if probe.get("bodies") or probe.get("timeline"):
            pytest.skip(
                "the active design is not empty - the smoke only runs in a fresh, unsaved "
                "design so it can never touch your work (File > New Design)"
            )
        yield app, adapter, probe
    finally:
        _close_scratch(wire, opened)
        app.shutdown()


class _Facts:
    def __init__(self, path: Path):
        self.path = path
        self.rows: dict[str, object] = {}

    def note(self, key: str, value) -> None:
        self.rows[key] = value
        print(f"  [fact] {key}: {value}")

    def dump(self) -> None:
        self.path.write_text(json.dumps(self.rows, indent=2))
        print(f"\nfacts written to {self.path}\n" + json.dumps(self.rows, indent=2))


def _near(a: float, b: float, rel: float = 1e-3) -> bool:
    return abs(a - b) <= rel * max(abs(a), abs(b), 1.0)


def _extent_mm(points: list[tuple[float, float, float]]) -> float:
    """The largest extent of a point set, then the unit that makes the
    120 mm plate read as 120: a measurement, not a declaration."""
    if not points:
        return 0.0
    return max(max(p[i] for p in points) - min(p[i] for p in points) for i in range(3))


def _unit_from_extent(extent: float) -> str:
    for unit, scale in (("mm", 1.0), ("cm", 0.1), ("m", 0.001), ("in", 1 / 25.4)):
        if _near(extent, 120.0 * scale, rel=0.02):
            return unit
    return f"unknown (largest extent {extent:g})"


def _obj_points(path: Path) -> list[tuple[float, float, float]]:
    pts = []
    for line in path.read_text(errors="replace").splitlines():
        if line.startswith("v "):
            parts = line.split()
            pts.append((float(parts[1]), float(parts[2]), float(parts[3])))
    return pts


def _stl_points(path: Path) -> list[tuple[float, float, float]]:
    data = path.read_bytes()
    if data[:5] == b"solid" and b"facet" in data[:400]:
        pts = []
        for line in data.decode(errors="replace").splitlines():
            parts = line.split()
            if parts[:1] == ["vertex"]:
                pts.append((float(parts[1]), float(parts[2]), float(parts[3])))
        return pts
    count = struct.unpack("<I", data[80:84])[0]
    pts = []
    for i in range(min(count, 20000)):
        rec = data[84 + i * 50 : 84 + i * 50 + 48]
        vals = struct.unpack("<12f", rec)
        for k in (3, 6, 9):
            pts.append((vals[k], vals[k + 1], vals[k + 2]))
    return pts


def _iges_units(path: Path) -> str:
    text = path.read_text(errors="replace")
    global_section = "".join(
        line[:72] for line in text.splitlines() if len(line) > 72 and line[72] == "G"
    )
    params = [p.strip() for p in re.split(r"[,;]", global_section)]
    # parameters 14 and 15 of the global section: the unit flag and the unit name
    flag = params[13] if len(params) > 13 else "?"
    name = params[14] if len(params) > 14 else "?"
    return f"flag={flag} name={name}"


def _sat_header(path: Path) -> str:
    lines = path.read_text(errors="replace").splitlines()[:4]
    return " | ".join(lines)


def _3mf_unit(path: Path) -> str:
    with zipfile.ZipFile(path) as zf:
        model = next((n for n in zf.namelist() if n.lower().endswith(".model")), None)
        if model is None:
            return "no .model in the archive"
        found = re.search(rb'unit="([a-z]+)"', zf.read(model))
        return (
            found.group(1).decode() if found else "no unit attribute (millimeter by spec default)"
        )


def _usd_unit(path: Path) -> str:
    data = path.read_bytes()
    if data[:2] == b"PK":  # a USDZ package - what Fusion writes (measured, A71)
        with zipfile.ZipFile(path) as zf:
            members = zf.namelist()
            inner = b"".join(zf.read(m) for m in members)
        declares = b"metersPerUnit" in inner
        return f"usdz package {members}: binary usdc " + (
            "declares metersPerUnit (value unread without the USD library)"
            if declares
            else "carries no metersPerUnit token"
        )
    if data.startswith(b"PXR-USDC"):
        return "binary usdc - read metersPerUnit with usdcat/usdview"
    found = re.search(rb"metersPerUnit\s*=\s*([0-9.eE+-]+)", data)
    return found.group(1).decode() if found else "no metersPerUnit in the file"


def _hole(**props):
    return {"op": "create", "kind": "hole", "props": props}


def test_the_smoke(served, tmp_path):
    app, adapter, probe = served
    facts = _Facts(tmp_path / "fusion-live-facts.json")
    facts.note("bridge", f"{adapter.wire.transport} on :{adapter.wire.port}")
    facts.note("fusion_version", probe.get("version"))
    facts.note("document", probe.get("document"))

    # -- step 7: does a bare rectangle carry constraints of its own? -----------
    diff = app.run_batch(
        "fusion",
        [{"op": "create", "kind": "sketch", "name": "bare", "props": {"rects": [[0, 0, 40, 20]]}}],
    )
    bare = diff["details"]["sk1"]
    facts.note("bare_rectangle_constraints", bare["constraints"])
    facts.note("bare_rectangle_fully_constrained", bare["constrained"])

    # -- steps 3 and 7: a dimensioned plate bound to user parameters ----------
    diff = app.run_batch(
        "fusion",
        [
            {"op": "create", "kind": "param", "name": "width", "props": {"value": "120 mm"}},
            {"op": "create", "kind": "param", "name": "height", "props": {"value": "80 mm"}},
            {
                "op": "create",
                "kind": "sketch",
                "name": "base",
                "props": {
                    "rects": [[0, 0, 100, 50]],
                    "constraints": [
                        {"type": "coincident", "of": ["r0.bl", "origin"]},
                        {"type": "horizontal", "of": ["r0.bottom"]},
                        {"type": "horizontal", "of": ["r0.top"]},
                        {"type": "vertical", "of": ["r0.left"]},
                        {"type": "vertical", "of": ["r0.right"]},
                    ],
                    "dims": [
                        {
                            "name": "w",
                            "type": "distance",
                            "of": ["r0.bl", "r0.br"],
                            "orientation": "horizontal",
                            "expression": "width",
                        },
                        {
                            "name": "h",
                            "type": "distance",
                            "of": ["r0.bl", "r0.tl"],
                            "orientation": "vertical",
                            "expression": "height",
                        },
                    ],
                },
            },
            {
                "op": "create",
                "kind": "extrude",
                "name": "plate",
                "props": {"sketch": "sk2", "distance": 10},
            },
        ],
    )
    plate = diff["details"]["b1"]
    facts.note("dimensioned_sketch_fully_constrained", diff["details"]["sk2"]["constrained"])
    facts.note("plate_bbox_mm", plate["bbox_mm"])
    assert _near(plate["volume_mm3"], PLATE_MM3), (
        "the dimensions did not drive the rectangle to 120x80"
    )
    app.run_batch("fusion", [{"op": "param_set", "name": "width", "expression": "150 mm"}])
    wide = app.registry.call("fu_measure", {"of": "b1"})
    facts.note("param_set_recomputes_the_body", _near(wide["volume_mm3"], 150.0 * 80.0 * 10.0))
    app.run_batch("fusion", [{"op": "param_set", "name": "width", "expression": "120 mm"}])
    assert _near(app.registry.call("fu_measure", {"of": "b1"})["volume_mm3"], PLATE_MM3)

    # -- step 4: checkpoint, a boss, rollback, capture -------------------------
    # The boss sketch lies on the XY plane at z=0, INSIDE the 10 mm plate; a
    # 5 mm join extrude there adds nothing (the first live run measured exactly
    # 96,000 -> 96,000 on Fusion 2704.1.53 - the shim sums volumes and cannot
    # know). 15 mm reaches 5 mm above the plate, so the join adds pi*10^2*5.
    boss = app.run_batch(
        "fusion",
        [
            {
                "op": "create",
                "kind": "sketch",
                "name": "boss",
                "props": {"circles": [[60, 40, 10]]},
            },
            {
                "op": "create",
                "kind": "extrude",
                "props": {"sketch": "sk3", "distance": 15, "operation": "join"},
            },
        ],
    )
    assert app.registry.call("fu_measure", {"of": "b1"})["volume_mm3"] > PLATE_MM3
    app.rollback("fusion", boss["checkpoint"])  # the auto-checkpoint taken before the boss
    after = app.registry.call("fu_measure", {"of": "b1"})
    facts.note("rollback_restored_the_plate", _near(after["volume_mm3"], PLATE_MM3))
    jpeg = adapter.capture("viewport", 64 * 1024)
    assert jpeg.startswith(b"\xff\xd8")
    written = sorted(p.name for p in Path(adapter.workdir).glob("capture-*"))
    facts.note("capture_extension_fusion_wrote", written)

    # -- step 8: a through hole - which way does it go by default? ------------
    app.run_batch("fusion", [_hole(body="b1", face="+z", at=[20, 20], diameter=6.6, through=True)])
    v1 = app.registry.call("fu_measure", {"of": "b1"})["volume_mm3"]
    into_material = _near(PLATE_MM3 - v1, HOLE_MM3, rel=0.02)
    facts.note("face_hole_default_bores_into_material", into_material)
    if not into_material:
        app.run_batch(
            "fusion",
            [_hole(body="b1", face="+z", at=[100, 60], diameter=6.6, through=True, flip=True)],
        )
        v2 = app.registry.call("fu_measure", {"of": "b1"})["volume_mm3"]
        facts.note("face_hole_flip_bores_into_material", _near(v1 - v2, HOLE_MM3, rel=0.02))
    base = app.registry.call("fu_measure", {"of": "b1"})["volume_mm3"]
    app.run_batch(
        "fusion",
        [
            _hole(
                body="b1",
                face="+z",
                at=[60, 40],
                diameter=6.6,
                depth=10,
                type="counterbore",
                cbore_diameter=11,
                cbore_depth=6,
                flip=not into_material,
            )
        ],
    )
    v3 = app.registry.call("fu_measure", {"of": "b1"})["volume_mm3"]
    cbore = HOLE_MM3 + math.pi * (5.5**2 - HOLE_R**2) * 6.0
    facts.note("counterbore_volume_matches", _near(base - v3, cbore, rel=0.02))

    # -- step 9: a chamfer on the top face's edges; a revolve about x ----------
    diff = app.run_batch(
        "fusion",
        [
            {
                "op": "create",
                "kind": "chamfer",
                "name": "break",
                "props": {"body": "b1", "distance": 1, "edges": {"face": "+z"}},
            }
        ],
    )
    chamfer = next(v for k, v in diff["details"].items() if v.get("type") == "ChamferFeature")
    facts.note("top_face_edges_chamfered", chamfer["edges"])
    # A 10 x 20 mm rectangle spanning y 20..40 - its centroid sits 30 mm off the
    # x axis, so Pappus gives 2*pi*200*30 = 37,699 mm^3, the tube r 20..40 of
    # length 10. (The first live run drew y 20..30 - a 10 x 10 profile at
    # centroid 25 - and Fusion answered its true 2*pi*100*25 = 15,708 mm^3; the
    # expectation, and the shim that agreed with it, were the ones in error.)
    diff = app.run_batch(
        "fusion",
        [
            {
                "op": "create",
                "kind": "sketch",
                "name": "pin_profile",
                "props": {"rects": [[0, 20, 10, 40]]},
            },
            {
                "op": "create",
                "kind": "revolve",
                "name": "pin",
                "props": {"sketch": "sk4", "axis": "x"},
            },
        ],
    )
    pin = next(v for k, v in diff["details"].items() if v.get("kind") == "body" and k != "b1")
    facts.note("revolve_volume_mm3", pin["volume_mm3"])
    facts.note("revolve_bbox_mm", pin["bbox_mm"])
    facts.note(
        "revolve_pappus_matches", _near(pin["volume_mm3"], 2 * math.pi * 200.0 * 30.0, rel=0.01)
    )

    # -- step 10: two components and a revolute joint - which one moves? ------
    diff = app.run_batch(
        "fusion",
        [
            {
                "op": "create",
                "kind": "sketch",
                "name": "post_profile",
                "props": {"circles": [[200, 40, 10]]},
            },
            {
                "op": "create",
                "kind": "extrude",
                "name": "post",
                "props": {"sketch": "sk5", "distance": 20, "operation": "new_component"},
            },
            {
                "op": "create",
                "kind": "sketch",
                "name": "cap_profile",
                "props": {"circles": [[260, 40, 5]]},
            },
            {
                "op": "create",
                "kind": "extrude",
                "name": "cap",
                "props": {"sketch": "sk6", "distance": 10, "operation": "new_component"},
            },
        ],
    )
    comps = [k for k, v in diff["details"].items() if v.get("kind") == "component"]
    facts.note("new_component_extrudes_reported", comps)
    assert len(comps) == 2, "a new_component extrude must report the occurrence it made (row 50)"
    before = {c: app.registry.call("fu_measure", {"of": c})["centre_of_mass_mm"] for c in comps}
    diff = app.run_batch(
        "fusion",
        [
            {
                "op": "create",
                "kind": "joint",
                "name": "hinge",
                "props": {
                    "one": {"component": comps[0], "face": "+z"},
                    "two": {"component": comps[1], "face": "-z"},
                    "motion": "revolute",
                    "axis": "z",
                },
            }
        ],
    )
    # The kernel trims detail fields that echo the op (hard rule 2): a lone
    # joint op maps to its one created id, so `kind`, `name` and `motion` are
    # dropped from the row - `created` is the address (measured live: the row
    # arrived as between/angle_deg/offset_mm/rotation_deg only).
    joint_id = next(k for k in diff["created"] if k.startswith("j"))
    facts.note("joint_row_keys", sorted(diff["details"][joint_id]))
    after = {c: app.registry.call("fu_measure", {"of": c})["centre_of_mass_mm"] for c in comps}
    moved = [
        c
        for c in comps
        if not all(_near(a, b, rel=1e-6) for a, b in zip(before[c], after[c], strict=True))
    ]
    facts.note("joint_moved_occurrences", moved)
    diff = app.run_batch("fusion", [{"op": "set", "id": joint_id, "props": {"rotation": 45}}])
    facts.note("joint_rotation_reads_back", diff["details"][joint_id].get("rotation_deg"))

    # -- step 11: the eight exports and the unit each file declares ----------
    out = tmp_path / "exports"
    # STEP, the archive, IGES, SAT and USD take a component or the whole design
    # (rows 17, 48 - the first live run met Fusion's "3 : invlid argument
    # geometry" on a body); 3MF, STL and OBJ take the body.
    for fmt, of in (
        ("step", None),
        ("obj", "b1"),
        ("stl", "b1"),
        ("3mf", "b1"),
        ("f3d", None),
        ("iges", None),
        ("sat", None),
        ("usd", None),
    ):
        args = {"format": fmt, "out": str(out / f"plate.{fmt}")}
        if of:
            args["of"] = of
        try:
            res = app.registry.call("fu_export", args)
        except TeeError as exc:
            facts.note(f"export_{fmt}", f"refused {exc.code}: {exc.message}")
            continue
        path = Path(res["path"])
        if fmt == "stl":
            facts.note("export_stl_units_declared", res["units"])
        if fmt == "usd":
            facts.note("export_usd_path_suffix", "".join(path.suffixes))
        if fmt == "obj":
            facts.note("export_obj_unit_measured", _unit_from_extent(_extent_mm(_obj_points(path))))
        elif fmt == "stl":
            facts.note("export_stl_unit_measured", _unit_from_extent(_extent_mm(_stl_points(path))))
        elif fmt == "iges":
            facts.note("export_iges_global_units", _iges_units(path))
        elif fmt == "sat":
            facts.note("export_sat_header", _sat_header(path))
        elif fmt == "3mf":
            facts.note("export_3mf_unit", _3mf_unit(path))
        elif fmt == "usd":
            facts.note("export_usd_metersPerUnit", _usd_unit(path))
        else:
            facts.note(f"export_{fmt}_bytes", res["bytes"])
    facts.dump()


def test_drawing_through_partkiln(tmp_path):
    """Step 11's last line: fu_drawing needs a partkiln lane beside Fusion."""
    pytest.importorskip("partkiln")
    from tee.adapters.partkiln.adapter import PartkilnAdapter

    wire = _live_wire()
    adapter = FusionAdapter(wire, workdir=str(tmp_path / "work"))
    kiln = PartkilnAdapter(tmp_path / "pk")
    app = TeeApp({"fusion": adapter, "partkiln": kiln}, project_root=tmp_path)
    register_fusion_tools(app, adapter)
    opened = None
    try:
        probe, opened = _open_scratch(wire, app)
        if probe.get("design") is None:
            pytest.skip("no design is open")
        if not probe.get("bodies"):
            app.run_batch(
                "fusion",
                [
                    {"op": "create", "kind": "sketch", "props": {"rects": [[0, 0, 120, 80]]}},
                    {"op": "create", "kind": "extrude", "props": {"sketch": "sk1", "distance": 10}},
                ],
            )
        out = app.registry.call(
            "fu_drawing",
            {
                "out": str(tmp_path / "sheets"),
                "name": "plate",
                "views": [{"name": "top", "dir": "top"}],
            },
        )
        print(
            f"\n  [fact] fu_drawing: step={out['step']} part={out['part']} drawing={out['drawing']}"
        )
        assert Path(out["step"]).is_file()
    finally:
        _close_scratch(wire, opened)
        app.shutdown()
