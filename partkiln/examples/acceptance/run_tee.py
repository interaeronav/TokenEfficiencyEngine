"""The recorded acceptance session: drive the whole partkiln lane through TEE.

A65 Law 19 - *use it, don't just test it*. Every other file in `partkiln/tests`
and `server/tests` calls the kernel or the adapter from inside; this one is a
session, in the order a model would actually work: build a bracket in ONE
batch, edit a parameter and read the blast radius, checkpoint and roll back,
draw a dimensioned sheet, export it, weigh the export with a SECOND kernel,
hand it to Blender, assemble it, check it against a spec that passes and one
that fails, and sum what the whole thing cost in tokens and seconds.

Two rules shape the code:

* **Public surface only.** `TeeApp.run_batch`, `app.registry.call`, the scene
  cache (`app.cache(...)`), the checkpoint machinery (`app.checkpoints` /
  `app.rollback`) and the asset lane. `partkiln` itself is never imported to
  shortcut a step - the only reason `partkiln/src` reaches `sys.path` at all is
  that partkiln is deliberately NOT pip-installed into `server/.venv` (the dev
  route is `uv pip install -e partkiln`, and this repo IS that checkout), so
  the path entry stands in for the editable install the adapter would find.
  The subprocess replay of step 3 goes through `SidecarKernel`, TEE's own
  worker transport, rather than a hand-rolled `python -c`.
* **Every number is printed.** A session whose evidence lives only in an
  assertion is a test, not a use. `--json` writes the same report as a file so
  a benchmark row can be built from it without re-running the session.

Run it:

    cd partkiln && PYTHONPATH=src uv run --project ../server \\
        python examples/acceptance/run_tee.py --out /tmp/pk-acceptance

`--probe` is the kernel-only session (no Blender): the same ten steps minus
the headless DCC handoff, which is what the default pytest suite runs.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import shutil
import socket
import subprocess
import sys
import tempfile
import textwrap
import time
from contextlib import suppress
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[3]


def _ensure_paths() -> None:
    """Make `partkiln` and `tee` importable however this file was started.

    `tee` is an editable install in `server/.venv`; `partkiln` is not (it is
    reached by PYTHONPATH or by the sidecar venv in production). Running the
    file from the repo root also puts the `partkiln/` DIRECTORY on the path,
    which imports as an empty namespace package - so the check is for a real
    submodule, not for the name.
    """
    for candidate in (REPO / "partkiln" / "src", REPO / "server" / "src"):
        if str(candidate) not in sys.path:
            sys.path.insert(0, str(candidate))
    if importlib.util.find_spec("partkiln.document") is None:  # a stale namespace shadow
        sys.modules.pop("partkiln", None)
        importlib.invalidate_caches()


_ensure_paths()

from tee.adapters.partkiln import PartkilnAdapter  # noqa: E402
from tee.adapters.partkiln.wire import SidecarKernel  # noqa: E402
from tee.app import TeeApp  # noqa: E402
from tee.kernel.budget import estimate_tokens  # noqa: E402
from tee.kernel.errors import TeeError  # noqa: E402

# --------------------------------------------------------------------------- the model

# W1 from CLAUDE_A66_SCRIPT.md with explicit hole and slot coordinates: a
# hole's `at` is in the face's own frame, whose origin is the world origin
# projected onto that face, and the rect preset puts its corner at the origin.
# (`server/tests/test_partkiln_live.py` carries the same list for the unit
# tier; this copy is what makes the example runnable on its own.)
W1: list[dict[str, Any]] = [
    {"op": "param_set", "props": {"W": "120mm", "H": "80mm", "T": "10mm"}},
    {"op": "create", "kind": "part", "name": "bracket", "props": {"material": "steel_s275"}},
    {
        "op": "create",
        "kind": "sketch",
        "name": "base",
        "props": {"plane": "XY", "profile": [{"rect": ["W", "H"], "tag": "outer"}]},
    },
    {
        "op": "create",
        "kind": "extrude",
        "name": "plate",
        "props": {"sketch": "base", "distance": "T"},
    },
    {
        "op": "create",
        "kind": "fillet",
        "name": "f1",
        "props": {"edges": "plate:edges(dir=Z)", "r": "5mm"},
    },
    {
        "op": "create",
        "kind": "hole",
        "name": "h",
        "props": {
            "on": "plate.end",
            "at": [[10, 15], [110, 15], [10, 65], [110, 65]],
            "std": "M6 clearance normal",
        },
    },
    {
        "op": "create",
        "kind": "sketch",
        "name": "slot_sk",
        "props": {"plane": "on:plate.end", "profile": [{"slot": [40, 8], "at": [40, 36]}]},
    },
    {
        "op": "create",
        "kind": "extrude",
        "name": "slot",
        "props": {"sketch": "slot_sk", "distance": "through", "mode": "cut"},
    },
    {
        "op": "create",
        "kind": "chamfer",
        "name": "c1",
        "props": {"edges": "plate:edges(of=plate.end, loop=outer)", "d": "1mm"},
    },
]

# F6 from the plan's fixture table, as assembly ops: a 40x40x20 block with a
# d10 through bore, a d10 pin, and a deliberately fat d11 pin that overlaps.
F6: list[dict[str, Any]] = [
    {"op": "create", "kind": "part", "name": "block", "props": {"material": "steel_s275"}},
    {
        "op": "create",
        "kind": "sketch",
        "name": "bsk",
        "props": {"plane": "XY", "profile": [{"rect": [40, 40], "tag": "r"}], "part": "block"},
    },
    {
        "op": "create",
        "kind": "extrude",
        "name": "body",
        "props": {"sketch": "bsk", "distance": 20, "part": "block"},
    },
    {
        "op": "create",
        "kind": "hole",
        "name": "bore",
        "props": {"on": "body.end", "at": [[20, 20]], "dia": 10, "part": "block"},
    },
    {"op": "create", "kind": "part", "name": "pin", "props": {"material": "steel_s275"}},
    {
        "op": "create",
        "kind": "sketch",
        "name": "psk",
        "props": {"plane": "XY", "profile": [{"circle": 10, "tag": "c"}], "part": "pin"},
    },
    {
        "op": "create",
        "kind": "extrude",
        "name": "shaft",
        "props": {"sketch": "psk", "distance": 40, "part": "pin"},
    },
    {"op": "create", "kind": "component", "name": "block", "props": {"part": "block"}},
    {
        "op": "create",
        "kind": "component",
        "name": "pin",
        "props": {"part": "pin", "at": [3, -4, 7]},
    },
    {
        "op": "create",
        "kind": "mate",
        "name": "ins",
        "props": {"kind": "insert", "a": "block.bore.1.wall", "b": "pin.shaft.side.c"},
    },
    {
        "op": "create",
        "kind": "joint",
        "name": "j1",
        "props": {"type": "revolute", "a": "block.bore.1.wall", "b": "pin.shaft.side.c"},
    },
]

# The overlap, added afterwards so the DOF above is measured on a clean fit.
FAT_PIN: list[dict[str, Any]] = [
    {"op": "create", "kind": "part", "name": "pin11", "props": {"material": "steel_s275"}},
    {
        "op": "create",
        "kind": "sketch",
        "name": "p11",
        "props": {"plane": "XY", "profile": [{"circle": 11, "tag": "c"}], "part": "pin11"},
    },
    {
        "op": "create",
        "kind": "extrude",
        "name": "s11",
        "props": {"sketch": "p11", "distance": 40, "part": "pin11"},
    },
    {
        "op": "create",
        "kind": "component",
        "name": "fat",
        "props": {"part": "pin11", "at": [20, 20, -10], "grounded": True},
    },
]

BRIDGE_DIR = REPO / "adapters" / "blender" / "tee_bridge"
BLENDER_CANDIDATES = (
    os.environ.get("TEE_BLENDER"),
    shutil.which("blender"),
    "/Applications/Blender.app/Contents/MacOS/Blender",
)
FREECAD_RPC = ("127.0.0.1", 9875)


# --------------------------------------------------------------------------- the recorder


class Session:
    """The ten steps and what each one measured, cost and took.

    Tokens are counted on both sides of every call - what the model would
    send and what it would be charged for reading back - because "tokens per
    completed part task" is the metric this whole project is judged by, and a
    session that only counts the answers under-reports by the size of the
    batch.
    """

    def __init__(self, out: Path, *, probe: bool) -> None:
        self.out = out
        self.probe = probe
        self.started = time.perf_counter()
        self.steps: list[dict[str, Any]] = []
        self.notes: list[str] = []
        self._in = 0
        self._out = 0
        self._t0 = time.perf_counter()

    # -- metering ---------------------------------------------------------

    def charge(self, request: Any, response: Any) -> Any:
        """Bill one round trip to the step in progress and return the response."""
        self._in += estimate_tokens(request)
        self._out += estimate_tokens(response)
        return response

    def batch(self, app: TeeApp, ops: list[dict[str, Any]]) -> dict[str, Any]:
        return self.charge(ops, app.run_batch("partkiln", ops))

    def call(self, app: TeeApp, tool: str, args: dict[str, Any]) -> Any:
        return self.charge({"tool": tool, **args}, app.registry.call(tool, args))

    # -- steps ------------------------------------------------------------

    def open(self) -> None:
        self._in = self._out = 0
        self._t0 = time.perf_counter()

    def close(self, number: int, title: str, facts: dict[str, Any], *, skipped: str = "") -> None:
        row = {
            "step": number,
            "title": title,
            "wall_s": round(time.perf_counter() - self._t0, 3),
            "tokens_in": self._in,
            "tokens_out": self._out,
            "facts": facts,
        }
        if skipped:
            row["skipped"] = skipped
        self.steps.append(row)

    def note(self, text: str) -> None:
        self.notes.append(text)

    # -- the report -------------------------------------------------------

    def report(self) -> dict[str, Any]:
        return {
            "session": "partkiln acceptance (A66 P6)",
            "probe": self.probe,
            "out": str(self.out),
            "steps": self.steps,
            "notes": self.notes,
            "totals": {
                "wall_s": round(time.perf_counter() - self.started, 3),
                "tokens_in": sum(s["tokens_in"] for s in self.steps),
                "tokens_out": sum(s["tokens_out"] for s in self.steps),
                "tokens": sum(s["tokens_in"] + s["tokens_out"] for s in self.steps),
                "steps_run": sum(1 for s in self.steps if not s.get("skipped")),
                "steps_skipped": sum(1 for s in self.steps if s.get("skipped")),
            },
        }

    def show(self) -> None:
        print("\n" + "=" * 78)
        print("partkiln acceptance session - every number this run measured")
        print("=" * 78)
        for row in self.steps:
            head = f"{row['step']:2d}. {row['title']}"
            if row.get("skipped"):
                print(f"{head}\n    SKIPPED: {row['skipped']}")
                continue
            print(
                f"{head}\n    {row['wall_s']:.3f} s | "
                f"{row['tokens_in']} tok in / {row['tokens_out']} tok out"
            )
            for key, value in row["facts"].items():
                print(f"    {key}: {_fmt(value)}")
        if self.notes:
            print("\nnotes")
            for note in self.notes:
                print(f"  - {note}")
        total = self.report()["totals"]
        print("\n" + "-" * 78)
        print(
            f"TOTAL {total['steps_run']} steps run, {total['steps_skipped']} skipped | "
            f"{total['wall_s']:.2f} s wall | {total['tokens']} tok "
            f"({total['tokens_in']} in + {total['tokens_out']} out)"
        )
        print("-" * 78)


def _fmt(value: Any) -> str:
    if isinstance(value, float):
        return f"{value:.12g}"  # 3 dp on a 6-digit volume needs more than %g's default
    if isinstance(value, list | dict):
        return json.dumps(value, default=str)
    return str(value)


# --------------------------------------------------------------------------- the ten steps


def step1_build(app: TeeApp, session: Session) -> dict[str, Any]:
    """ONE batch, ONE diff that names every created id with volume and faces."""
    session.open()
    health = session.call(app, "pk_probe", {"deep": True})
    kernel = health["kernel"]
    out = session.batch(app, W1)
    created = list(out["created"])
    details = out["details"]
    assumed = [eid for eid, row in details.items() if isinstance(row, dict) and row.get("assumed")]
    resolved = {
        eid: row["resolved"]
        for eid, row in details.items()
        if isinstance(row, dict) and row.get("resolved")
    }
    body = _entity(app, "part:bracket")
    facts = {
        "kernel": f"{health['mode']}, OCCT {kernel['occt']}, partkiln {kernel['partkiln']}, "
        f"python {kernel['python']}, pid {kernel['pid']}, rss {kernel['rss_mb']} MB",
        "kernel OCCT": kernel["occt"],
        "created": created,
        "features": {
            eid: [details[eid]["delta_mm3"], details[eid]["faces"]]
            for eid in created
            if eid.startswith("feat:")
        },
        "part volume_mm3": body["volume_mm3"],
        "part mass_g": body["mass_g"],
        "part bbox_mm": body["bbox_mm"],
        "part faces/edges": [body["faces"], body["edges"]],
        "assumed on": assumed,
        "resolved": resolved,
        "batch tokens": estimate_tokens(W1),
        "diff tokens": estimate_tokens(out),
        "checkpoint": out.get("checkpoint"),
    }
    # The diff is the whole answer: nothing here is a mesh, a point list or a
    # scene dump (hard rule 1), and the batch is one round trip (hard rule 3).
    assert "assumed" in json.dumps(details), "no default was declared"
    assert resolved, "no selector reported what it resolved to"
    session.close(1, "build the bracket in one batch", facts)
    return facts


def step2_edit(app: TeeApp, session: Session) -> dict[str, Any]:
    """Law 14: an edit reports its blast radius, not the new world."""
    session.open()
    stamp = app.cache("partkiln").stamp()
    ops = [{"op": "param_set", "props": {"T": "12mm"}}]
    out = session.batch(app, ops)
    report = out["details"]["part:bracket"]
    since = app.cache("partkiln").diff_since(stamp["epoch"], stamp["revision"])
    facts = {
        "changed": [f"{r['feature']} {r['delta_mm3']:+.3f}" for r in report["changed"]],
        "unchanged": report["unchanged_features"],
        "failed": report["failed"],
        "volume_mm3": report["volume_mm3"],
        "param T": out["details"]["param:T"],
        "diff_since modified": sorted(since["modified"]),
        "edit tokens": estimate_tokens(ops),
        "answer tokens": estimate_tokens(out),
    }
    session.close(2, "edit T=12mm and read the blast radius", facts)
    return facts


def step3_checkpoint(app: TeeApp, session: Session, adapter: PartkilnAdapter) -> dict[str, Any]:
    """D3/Law 16: the checkpoint is the script, and it replays in a fresh process."""
    session.open()
    kept = adapter.kernel.fingerprint()
    volume_before = _entity(app, "part:bracket")["volume_mm3"]
    checkpoint = app.checkpoints.create(adapter, "acceptance", app.cache("partkiln").revision)
    path = Path(checkpoint.payload["path"])

    session.batch(app, [{"op": "param_set", "props": {"T": "16mm"}}])
    moved = adapter.kernel.fingerprint()
    app.rollback("partkiln", checkpoint.id)
    back = _entity(app, "part:bracket")["volume_mm3"]

    # The replay proof: copy the JSON ALONE into an empty directory, so the
    # `.brep` fast path cannot be taken, and restore it in a real subprocess
    # over TEE's own worker transport.
    bare = session.out / "replay"
    bare.mkdir(parents=True, exist_ok=True)
    shutil.copy(path, bare / "script.json")
    spawned = time.perf_counter()
    kernel = SidecarKernel(
        python=sys.executable,
        env={"PYTHONPATH": str(REPO / "partkiln" / "src")},
        stderr_path=session.out / "worker.log",
        timeout_s=120.0,
    )
    kernel.start()
    spawn_s = time.perf_counter() - spawned
    child = PartkilnAdapter(session.out / "child", kernel=kernel)
    restored = time.perf_counter()
    child.restore({"path": str(bare / "script.json")})
    restore_s = time.perf_counter() - restored
    replay_fp = kernel.fingerprint()
    child_pid = kernel.info().get("pid")
    kernel.close()

    facts = {
        "checkpoint": checkpoint.id,
        "checkpoint bytes": path.stat().st_size,
        "volume before/after rollback": [volume_before, back],
        "fingerprint moved on edit": moved != kept,
        "fingerprint restored": adapter.kernel.fingerprint() == kept,
        "subprocess pid": child_pid,
        "subprocess spawn_s": round(spawn_s, 3),
        "subprocess replay_s": round(restore_s, 3),
        "replay fingerprint matches": replay_fp == kept,
        "fingerprint": kept[:16],
    }
    assert back == volume_before and replay_fp == kept
    session.close(3, "checkpoint, rollback, and replay in a subprocess", facts)
    return facts


def step4_drawing(app: TeeApp, session: Session) -> dict[str, Any]:
    """Law 15: the sheet's dimensions are READ from the model - so read them back."""
    session.open()
    folder = session.out / "drawing"
    folder.mkdir(parents=True, exist_ok=True)
    args = {
        "of": "part:bracket",
        "out": str(folder),
        "name": "sheet1",
        "sheet": "A3L",
        "formats": ["svg", "dxf", "pdf"],
        "views": [{"name": "top", "dir": "top"}, {"name": "front", "dir": "front"}],
        "dims": [
            {"name": "d1", "view": "top", "kind": "extent", "axis": "X"},
            {"name": "d2", "view": "top", "kind": "extent", "axis": "Y"},
            {"name": "d3", "view": "front", "kind": "extent", "axis": "Y"},
        ],
        "hole_table": True,
        "title": {"part": "BRACKET-001", "rev": "A"},
    }
    sheet = session.call(app, "pk_drawing", args)
    model = _entity(app, "part:bracket")["bbox_mm"]

    import ezdxf  # read the DXF back with a library that never saw the model
    from pypdf import PdfReader

    dxf = ezdxf.readfile(sheet["files"]["dxf"])
    measured = sorted(round(e.get_measurement(), 6) for e in dxf.modelspace() if _is_dim(e))
    reader = PdfReader(sheet["files"]["pdf"])
    box = reader.pages[0].mediabox
    text = reader.pages[0].extract_text() or ""
    m6_rows = [r for r in sheet["hole_table"] if abs(r["dia_mm"] - 6.6) < 1e-9]

    facts = {
        "files": {k: Path(v).name for k, v in sheet["files"].items()},
        "views (visible|hidden edges)": {
            v["name"]: [v["visible_edges"], v["hidden_edges"]] for v in sheet["views"]
        },
        "sheet dims (value_mm)": {d["name"]: d["value_mm"] for d in sheet["dimensions"]},
        "sheet dims agree": all(d["agree"] for d in sheet["dimensions"]),
        "model bbox_mm": model,
        "DXF $INSUNITS": dxf.header.get("$INSUNITS"),
        "DXF DIMENSION measurements": measured,
        "PDF mediabox_pt": [round(float(box.width), 2), round(float(box.height), 2)],
        "PDF pages": len(reader.pages),
        "PDF text has 6.6": "6.6" in text,
        "PDF text has ISO 273": "ISO 273" in text,
        "hole table rows": len(sheet["hole_table"]),
        "hole table M6 rows": [[r["name"], r["dia_mm"], r["depth"]] for r in m6_rows],
        "hole table rows detail": [
            [r["name"], r["dia_mm"], r["depth"]] for r in sheet["hole_table"]
        ],
    }
    # The DXF must carry the MODEL's own numbers, not typed ones - so the
    # expectation is read from the part, not written here. (The part is 12 mm
    # thick by now: step 2 edited T and step 3 rolled back to that edit.)
    assert measured == sorted(round(v, 6) for v in model), (measured, model)
    assert dxf.header.get("$INSUNITS") == 4  # millimetres
    assert facts["PDF mediabox_pt"] == [1190.55, 841.89]  # A3 landscape
    assert len(m6_rows) == 4
    # Five rows: the four M6 holes and the slot, as ONE slot. The four r5 corner
    # fillets are the same surface with the material on the other side and are
    # NOT rows - this session is what found them printing as `4x d10` (fixed
    # 2026-09-04; the guard below is what keeps them out). The slot's two end
    # cylinders were a sixth and seventh row until the slot pairing landed.
    assert len(sheet["hole_table"]) == 5, sheet["hole_table"]
    assert all(r["dia_mm"] != 10.0 for r in sheet["hole_table"]), "a fillet came back"
    slots = [r for r in sheet["hole_table"] if r.get("kind") == "slot"]
    assert len(slots) == 1, sheet["hole_table"]
    assert slots[0]["length_mm"] == 40.0, slots[0]
    session.close(4, "pk_drawing to SVG + DXF + PDF, read back", facts)
    return facts


def _is_dim(entity: Any) -> bool:
    return entity.dxftype() == "DIMENSION"


def step5_export(app: TeeApp, session: Session) -> dict[str, Any]:
    """Every format says what it declares about itself - and the STEP is re-weighed."""
    session.open()
    folder = session.out / "export"
    folder.mkdir(parents=True, exist_ok=True)
    written: dict[str, dict[str, Any]] = {}
    for fmt in ("step", "glb", "stl"):
        written[fmt] = session.call(
            app,
            "pk_export",
            {
                "format": fmt,
                "out": str(folder / f"bracket.{fmt}"),
                "of": "part:bracket",
                **({"target": "blender"} if fmt == "glb" else {}),
            },
        )
    body = _entity(app, "part:bracket")
    kernel_volume = body["volume_mm3"]
    back = session.call(app, "pk_measure", {"what": "mass", "path": str(folder / "bracket.step")})

    from tee.assets import gltf

    probed = gltf.probe(folder / "bracket.glb")
    expected_m = [round(v / 1000.0, 4) for v in body["bbox_mm"]]

    facts = {
        "bytes": {f: written[f]["bytes"] for f in written},
        "STEP schema": written["step"]["schema"],
        "STEP roundtrip": written["step"]["roundtrip"],
        "STEP volume read back": back["volume_mm3"],
        "STEP vs kernel (rel)": abs(back["volume_mm3"] - kernel_volume) / kernel_volume,
        "GLB units/up": [written["glb"]["units"], written["glb"]["up"]],
        "GLB extents (writer)": written["glb"]["extents"],
        "GLB probe extents_m": probed["extents_m"],
        "GLB probe dims_zup_m": probed["dims_zup_m"],
        "GLB expected dims_zup_m": expected_m,
        "GLB triangles": probed["triangles"],
        "STL watertight/triangles": [written["stl"]["watertight"], written["stl"]["triangles"]],
        "STL declares units": written["stl"]["declares_units"],
    }
    assert back["volume_mm3"] == kernel_volume
    # Z-up and in metres: the thickness stays on Z, so the part arrives upright.
    assert all(abs(a - b) < 1e-4 for a, b in zip(probed["dims_zup_m"], expected_m, strict=True))
    session.close(5, "pk_export step + glb + stl, read back", facts)
    return facts


def step6_cross_kernel(app: TeeApp, session: Session, *, occt: str) -> dict[str, Any]:
    """A second OCCT reads the STEP. If FreeCAD's bridge is up, a third does too."""
    session.open()
    step_path = session.out / "export" / "bracket.step"
    kernel_volume = _entity(app, "part:bracket")["volume_mm3"]
    fleet = session.call(app, "cad_measure", {"path": str(step_path)})
    relative = abs(fleet["volume"] - kernel_volume) / kernel_volume
    facts = {
        "kernel volume_mm3": kernel_volume,
        "cad_measure volume": fleet["volume"],
        "relative difference": relative,
        "cad_measure engine": fleet.get("engine"),
        "cad_measure bbox": fleet["bbox"],
        "cad_measure valid": fleet["valid"],
    }
    probe = session.call(app, "cad_probe", {})
    facts["cad_measure reader"] = f"cadquery {probe['cadquery'].get('version')}"
    facts["kernel OCCT"] = occt
    session.note(
        f"cad_measure reads the STEP through cadquery {probe['cadquery'].get('version')}, "
        f"which sits on the SAME OCP wheel the kernel uses (OCCT {occt}): a "
        "second READER over one OCCT build, not a second OCCT version. The second OCCT "
        "build is FreeCAD's 7.8.1, and it does NOT need the GUI-bound RPC bridge below: "
        "partkiln/tests/test_interop_freecad.py drives FreeCAD's own bundled interpreter "
        "as a subprocess and compares volume, bbox and counts against this kernel."
    )
    if _port_open(*FREECAD_RPC):
        try:
            from tee.adapters.freecad.adapter import FreeCADAdapter
            from tee.adapters.freecad.wire import FreeCADWire

            adapter = FreeCADAdapter(FreeCADWire())
            facts["freecad"] = adapter.info().to_payload()
            session.note("the FreeCAD bridge was already up; its OCCT read the same STEP")
        except Exception as exc:  # an optional third kernel is never fatal here
            facts["freecad"] = f"bridge answered but the adapter refused: {exc}"
    else:
        facts["freecad"] = (
            f"not up on {FREECAD_RPC[0]}:{FREECAD_RPC[1]} - not started (the A37 bridge is "
            "GUI-bound: FreeCAD -> TEE -> Start RPC Server)"
        )
    assert relative < 1e-6, relative
    session.close(6, "cross-kernel read-back of the STEP", facts)
    return facts


def step7_blender(
    session: Session, glb: Path, *, target_dims: list[float], blender: str | None
) -> dict[str, Any]:
    """The handoff: ingest the GLB into the asset library, import it headless."""
    session.open()
    binary = blender or _find_blender()
    if binary is None or not Path(binary).exists():
        session.close(
            7,
            "hand the GLB to headless Blender",
            {},
            skipped=f"no Blender binary at {binary!r} (set TEE_BLENDER or pass --blender)",
        )
        return {}
    from tee.adapters.blender.adapter import BlenderAdapter
    from tee.adapters.blender.wire import BlenderWire
    from tee.assets import tools as asset_tools

    port = _free_port()
    boot = session.out / "blender_boot.py"
    boot.write_text(
        textwrap.dedent(
            f"""
            import sys
            sys.path.insert(0, {str(BRIDGE_DIR)!r})
            import bridge_server
            bridge_server.run_blocking("127.0.0.1", {port})
            """
        ),
        encoding="utf-8",
    )
    started = time.perf_counter()
    proc = subprocess.Popen(  # our own bridge script, our own binary
        [binary, "--background", "--factory-startup", "--python", str(boot)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    wire = BlenderWire(port=port)
    # A bridge that never comes up is an environment fact, so it is RECORDED
    # and the session goes on. Anything that fails AFTER Blender is answering
    # is a defect in the handoff and is left to raise.
    down = ""
    deadline = time.time() + 90
    while time.time() < deadline:
        if proc.poll() is not None:
            down = f"Blender exited early, rc={proc.returncode} (boot script: {boot})"
            break
        if wire.probe():
            break
        time.sleep(0.25)
    else:
        down = f"the bridge on 127.0.0.1:{port} never answered within 90 s"
    if down:
        proc.terminate()
        with suppress(subprocess.TimeoutExpired):
            proc.wait(timeout=10)
        session.close(7, "hand the GLB to headless Blender", {"blender": binary}, skipped=down)
        return {}
    boot_s = time.perf_counter() - started

    try:
        app = TeeApp(
            {"blender": BlenderAdapter(wire, workdir=str(session.out))},
            project_root=session.out,
        )
        asset_tools.register_asset_tools(app, session.out)
        # The library keys a local asset by file STEM, so `bracket.glb` and
        # `bracket.stl` from step 5 would be one entry and the last one wins.
        # Ingest a folder holding only the file being handed over.
        handoff = session.out / "handoff"
        handoff.mkdir(parents=True, exist_ok=True)
        shutil.copy(glb, handoff / glb.name)
        try:
            ingest = session.call(app, "as_ingest", {"directory": str(handoff)})
            placed = session.call(
                app,
                "as_import",
                {
                    "asset": f"local:{glb.stem}",
                    "adapter": "blender",
                    "asset_class": "model",
                    "target_dims": list(target_dims),
                    "name": "bracket",
                },
            )
            entity = placed["created"][0]
            row = app.cache("blender").entities[entity]
            summary = dict(row.summary)
        finally:
            app.shutdown()
    finally:
        proc.terminate()
        with suppress(subprocess.TimeoutExpired):
            proc.wait(timeout=10)

    dims = summary.get("dimensions") or summary.get("dims_m")
    facts = {
        "blender": binary,
        "bridge boot_s": round(boot_s, 3),
        "as_ingest": ingest,
        "ingested from": str(handoff),
        "scale band": placed["scale_band"],
        "verify.ok": placed["verify"]["ok"],
        "target dims_m": list(target_dims),
        "expected dims_m": placed["verify"]["expected_dims"],
        "read back dims_m": placed["verify"]["read_back"],
        "entity": entity,
        "entity dimensions_m": dims,
        "entity summary": summary,
    }
    assert placed["verify"]["ok"] is True
    # Upright: the plate's thinnest axis must land on Z, not on Y - a glTF
    # handed over without the Z-up correction arrives lying on its side.
    read_back = placed["verify"]["read_back"]
    assert read_back[2] == min(read_back), read_back
    session.close(7, "hand the GLB to headless Blender", facts)
    return facts


def step8_assembly(app: TeeApp, session: Session) -> dict[str, Any]:
    """Components, an insert mate, a revolute joint - then DOF, interference, BOM."""
    session.open()
    out = session.batch(app, F6)
    asm = out["details"]["asm"]
    measured = session.call(app, "pk_measure", {"what": "asm"})
    fat = session.batch(app, FAT_PIN)
    overlap = fat["details"]["asm"]["interference"]
    block_fat = next(r for r in overlap if {r["a"], r["b"]} == {"block", "fat"})
    bom = session.call(app, "pk_bom", {"parts_only": True})
    facts = {
        "components": measured["components"],
        "dof": measured["dof"],
        "status": measured["status"],
        "grounded": measured["grounded"],
        "residual": measured["residual"],
        "redundant": measured.get("redundant"),
        "dof_by_component": measured["dof_by_component"],
        "joint_values": measured["joint_values"],
        "interference (clean fit)": measured["interference"],
        "clearance_mm (clean fit)": measured["clearance_mm"],
        "interference (d11 pin)": overlap,
        "interference block/fat mm3": block_fat["mm3"],
        "BOM rows": [
            f"{r['item']}. {r['part']} x{r['qty']} {r['material']} {r['total_g']} g"
            for r in bom["rows"]
        ],
        "BOM total_g": bom["total_g"],
        "BOM partial": bom["partial"],
    }
    assert measured["dof"] == 1 and asm["dof"] == 1
    assert block_fat["mm3"] == 329.867, block_fat
    session.note(
        "the insert mate and the revolute joint constrain the SAME axis pair, so the "
        f"assembly reads dof {measured['dof']} with status {measured['status']!r} and "
        f"redundant {measured.get('redundant')} - reported, not refused (A66 D7)"
    )
    session.close(8, "assemble: mate, joint, DOF, interference, BOM", facts)
    return facts


def step9_check(app: TeeApp, session: Session) -> dict[str, Any]:
    """One spec that passes and one that fails - the failure names got/limit/fix."""
    session.open()
    body = _entity(app, "part:bracket")
    width, height, thickness = body["bbox_mm"]
    # The passing spec is the drawing's own intent; the failing one asks for a
    # thinner plate and a lighter part than the model actually is.
    thin = [width, height, thickness - 2.0]
    band = [round(body["mass_g"] - 120, 1), round(body["mass_g"] - 20, 1)]
    good = session.call(
        app,
        "pk_check",
        {
            "spec": {
                "bbox": body["bbox_mm"],
                "holes": [{"dia": 6.6, "count": 4}],
                "min_wall_mm": 1.0,
                "valid": True,
            },
            "of": "part:bracket",
        },
    )
    bad = session.call(
        app, "pk_check", {"spec": {"bbox": thin, "mass_g": band}, "of": "part:bracket"}
    )
    refusal: dict[str, str] = {}
    try:
        session.call(
            app, "pk_check", {"spec": {"bbox": thin}, "of": "part:bracket", "strict": True}
        )
    except TeeError as exc:
        refusal = {"code": exc.code, "message": exc.message, "fix": exc.fix or ""}
    facts = {
        "part bbox_mm / mass_g": [body["bbox_mm"], body["mass_g"]],
        "pass spec": {"bbox": body["bbox_mm"], "holes": "4x d6.6", "min_wall_mm": 1.0},
        "fail spec": {"bbox": thin, "mass_g": band},
        "pass verdict": good["verdict"],
        "pass checked": good["checked"],
        "pass unproven": good.get("unproven", []),
        "fail verdict": bad["verdict"],
        "fail violations": bad["violations"],
        "strict refusal": refusal,
    }
    assert good["verdict"] == "pass" and good["violations"] == []
    assert bad["verdict"] == "fail" and len(bad["violations"]) == 2
    for violation in bad["violations"]:
        assert {"rule", "got", "limit", "fix"} <= set(violation), violation
    assert refusal.get("code") == "pk_spec_conflict" and refusal.get("fix")
    session.close(9, "pk_check: one spec that passes, one that fails", facts)
    return facts


# --------------------------------------------------------------------------- the session


def run(out: Path, *, probe: bool = False, blender: str | None = None) -> dict[str, Any]:
    """The whole session. Returns the report; also prints it."""
    out.mkdir(parents=True, exist_ok=True)
    adapter = PartkilnAdapter(out)
    app = TeeApp({"partkiln": adapter}, project_root=out)
    session = Session(out, probe=probe)
    try:
        built = step1_build(app, session)
        step2_edit(app, session)
        step3_checkpoint(app, session, adapter)
        step4_drawing(app, session)
        exported = step5_export(app, session)
        step6_cross_kernel(app, session, occt=built["kernel OCCT"])
        if probe:
            session.close(7, "hand the GLB to headless Blender", {}, skipped="--probe")
        else:
            step7_blender(
                session,
                out / "export" / "bracket.glb",
                target_dims=exported["GLB probe dims_zup_m"],
                blender=blender,
            )
        step8_assembly(app, session)
        step9_check(app, session)
    finally:
        app.shutdown()
    session.open()
    session.close(10, "sum the session", {})
    total = session.report()["totals"]
    session.steps[-1]["facts"] = {
        "steps run": total["steps_run"],
        "steps skipped": total["steps_skipped"],
        "tokens in": total["tokens_in"],
        "tokens out": total["tokens_out"],
        "tokens total": total["tokens"],
        "wall_s": total["wall_s"],
    }
    session.show()
    return session.report()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="run_tee.py", description=__doc__)
    parser.add_argument(
        "--out",
        default=None,
        help="working directory for the session's files (default: a temp dir)",
    )
    parser.add_argument(
        "--probe",
        action="store_true",
        help="the kernel-only session: every step but the headless Blender handoff",
    )
    parser.add_argument("--blender", default=None, help="Blender executable (else $TEE_BLENDER)")
    parser.add_argument("--json", default=None, help="write the report to this path as JSON")
    args = parser.parse_args(argv)

    out = Path(args.out) if args.out else Path(tempfile.mkdtemp(prefix="pk-acceptance-"))
    report = run(out, probe=args.probe, blender=args.blender)
    if args.json:
        Path(args.json).write_text(json.dumps(report, indent=1, default=str), encoding="utf-8")
        print(f"report written to {args.json}")
    return 0


# --------------------------------------------------------------------------- helpers


def _entity(app: TeeApp, entity_id: str) -> dict[str, Any]:
    """One entity's scalar summary, straight off the scene cache."""
    row = app.cache("partkiln").entities.get(entity_id)
    if row is None:
        raise KeyError(f"{entity_id} is not in the scene cache")
    return dict(row.summary)


def _find_blender() -> str | None:
    for candidate in BLENDER_CANDIDATES:
        if candidate and Path(candidate).exists():
            return candidate
    return None


def _free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def _port_open(host: str, port: int, timeout: float = 0.4) -> bool:
    """Is something listening? A probe, never a start (the bridge is GUI-bound)."""
    sock = socket.socket()
    sock.settimeout(timeout)
    try:
        sock.connect((host, port))
        return True
    except OSError:
        return False
    finally:
        sock.close()


if __name__ == "__main__":
    raise SystemExit(main())
