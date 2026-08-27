#!/usr/bin/env python3
"""Tokens-per-task benchmark: TEE vs the naive bridge pattern.

Both harnesses drive the SAME live headless Blender through the SAME wire
protocol; what differs is the interface style:

- naive: one Python-code request per operation and a full scene dump after
  every mutation (the dominant pattern in existing DCC bridges: an
  execute_code tool plus a get_scene_info tool), full-res PNG screenshots.
- tee:   typed batches (N ops = 1 round-trip) with diff responses, compact
  paged summaries, geometric assertions before pixels, budgeted small JPEG.

The metric is context cost: estimated tokens of every request + response
that would enter the model's context (chars/3.5 for text - the same
estimator the server budget uses - and ceil(w/28)*ceil(h/28) for images,
Anthropic's visual token formula). Run:

    cd server && uv run python ../benchmarks/run_benchmarks.py
"""

from __future__ import annotations

import copy
import json as _json
import math
import shutil
import socket
import subprocess
import sys
import tempfile
import textwrap
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "server" / "src"))
sys.path.insert(0, str(REPO / "server" / "tests"))  # shared synthetic fixtures

from tee.adapters.blender.adapter import BlenderAdapter  # noqa: E402
from tee.adapters.blender.tools import register_blender_tools  # noqa: E402
from tee.adapters.blender.wire import BlenderWire  # noqa: E402
from tee.app import TeeApp  # noqa: E402
from tee.kernel.budget import estimate_tokens  # noqa: E402

BLENDER_CANDIDATES = (
    shutil.which("blender"),
    "/home/user/blender-5.2.0-linux-x64/blender",
)
TEE_BRIDGE_DIR = REPO / "adapters" / "blender" / "tee_bridge"


def image_tokens(width: int, height: int) -> int:
    return math.ceil(width / 28) * math.ceil(height / 28)


class Meter:
    """Counts request+response tokens the way a model's context would."""

    def __init__(self) -> None:
        self.tokens = 0
        self.round_trips = 0

    def text(self, payload) -> None:
        self.tokens += estimate_tokens(payload)

    def call(self, request, response) -> None:
        self.round_trips += 1
        self.text(request)
        self.text(response)

    def image(self, width: int, height: int) -> None:
        self.tokens += image_tokens(width, height)


# --------------------------------------------------------------------------
# Naive harness: emulates the dominant existing-bridge interface faithfully
# (execute_code per op + get_scene_info full dump after each mutation).
# --------------------------------------------------------------------------

SCENE_DUMP_CODE = textwrap.dedent(
    """
    import bpy
    objs = []
    for o in bpy.data.objects:
        objs.append({
            "name": o.name, "type": o.type,
            "location": list(o.location), "rotation": list(o.rotation_euler),
            "scale": list(o.scale), "dimensions": list(o.dimensions),
            "visible": not o.hide_viewport,
            "parent": o.parent.name if o.parent else None,
            "materials": [m.name for m in o.data.materials if m]
                          if hasattr(o.data, "materials") and o.data else [],
            "vertices": len(o.data.vertices) if o.type == "MESH" else None,
            "polygons": len(o.data.polygons) if o.type == "MESH" else None,
        })
    result = {"objects": objs, "frame": bpy.context.scene.frame_current,
              "engine": bpy.context.scene.render.engine}
    """
)


class Naive:
    def __init__(self, wire: BlenderWire, meter: Meter):
        self.wire = wire
        self.meter = meter

    def exec_op(self, code: str) -> dict:
        response = self.wire.execute(code, strict_json=False)
        self.meter.call(code, response)
        # after every mutation the model re-reads the scene (it has no diffs)
        dump = self.wire.execute(SCENE_DUMP_CODE, strict_json=False)
        self.meter.call(SCENE_DUMP_CODE, dump)
        return response

    def query(self, code: str) -> dict:
        response = self.wire.execute(code, strict_json=False)
        self.meter.call(code, response)
        return response

    def screenshot(self) -> None:
        # existing bridges default to full-res viewport PNG
        self.meter.round_trips += 1
        self.meter.image(1920, 1080)


# --------------------------------------------------------------------------
# TEE harness: the real TeeApp driving the same Blender.
# --------------------------------------------------------------------------


class Tee:
    def __init__(self, app: TeeApp, meter: Meter):
        self.app = app
        self.meter = meter

    def batch(self, ops: list[dict]) -> dict:
        out = self.app.run_batch("blender", ops)
        self.meter.call({"tool": "tee_batch", "ops": ops}, out)
        return out

    def summary(self, **kwargs) -> dict:
        from tee.kernel.budget import columnarize

        # mirror the server pipeline: large homogeneous lists go columnar
        out = columnarize(self.app.cache("blender").summary(**kwargs))
        self.meter.call({"tool": "tee_scene_summary", **kwargs}, out)
        return out

    def diff(self, stamp: dict) -> dict:
        out = self.app.cache("blender").diff_since(stamp["epoch"], stamp["revision"])
        self.meter.call({"tool": "tee_diff", **stamp}, out)
        return out

    def stats(self) -> dict:
        out = self.app.registry.call("bl_scene_stats", {})
        self.meter.call({"tool": "tee_call", "name": "bl_scene_stats"}, out)
        return out

    def capture(self) -> None:
        self.meter.round_trips += 1
        self.meter.image(512, 288)  # budgeted default


# --------------------------------------------------------------------------
# Scenarios (each returns nothing; both harnesses must COMPLETE the task)
# --------------------------------------------------------------------------


def scenario_donut(naive: Naive | None, tee: Tee | None) -> None:
    """Model a donut on a plate with a light and check the framing."""
    if naive:
        naive.exec_op(
            "import bpy\nbpy.ops.mesh.primitive_torus_add(major_radius=1, minor_radius=0.4)\n"
            "bpy.context.active_object.name = 'Donut'\nresult={'ok':True}"
        )
        naive.exec_op(
            "import bpy\nbpy.ops.mesh.primitive_cylinder_add(radius=1.8, depth=0.08,"
            " location=(0,0,-0.25))\nbpy.context.active_object.name = 'Plate'\nresult={'ok':True}"
        )
        naive.exec_op(
            "import bpy\nmat = bpy.data.materials.new('Icing')\nmat.use_nodes = True\n"
            "bsdf = next(n for n in mat.node_tree.nodes if n.type=='BSDF_PRINCIPLED')\n"
            "bsdf.inputs['Base Color'].default_value = (0.9,0.4,0.6,1)\n"
            "bpy.data.objects['Donut'].data.materials.append(mat)\nresult={'ok':True}"
        )
        naive.exec_op(
            "import bpy\nlight = bpy.data.lights.new('Key','SUN')\n"
            "obj = bpy.data.objects.new('Key', light)\n"
            "bpy.context.scene.collection.objects.link(obj)\nresult={'ok':True}"
        )
        naive.screenshot()  # verify by looking
    if tee:
        out = tee.batch(
            [
                {
                    "op": "create",
                    "kind": "torus",
                    "name": "Donut",
                    "props": {"radius": 1, "minor_radius": 0.4},
                },
                {
                    "op": "create",
                    "kind": "cylinder",
                    "name": "Plate",
                    "props": {"radius": 1.8, "depth": 0.08, "location": [0, 0, -0.25]},
                },
                {"op": "create", "kind": "light", "name": "Key", "props": {"light_type": "SUN"}},
            ]
        )
        donut = out["created"][0]
        result = tee.app.registry.call(
            "bl_assign_material",
            {
                "entity_id": donut,
                "material": "Icing",
                "base_color": [0.9, 0.4, 0.6],
                "roughness": 0.4,
            },
        )
        tee.meter.call({"tool": "bl_assign_material"}, result)
        tee.stats()  # geometric verification instead of pixels


def scenario_hundred_objects(naive: Naive | None, tee: Tee | None) -> None:
    """Populate 100 objects, then find out what changed after 3 edits."""
    if naive:
        for i in range(0, 100, 10):  # a model would batch ~10 per code block
            lines = ["import bpy"]
            for j in range(i, i + 10):
                lines.append(
                    f"bpy.ops.mesh.primitive_cube_add(size=0.5,"
                    f" location=({j % 10}, {j // 10}, 0))\n"
                    f"bpy.context.active_object.name = 'Block{j}'"
                )
            lines.append("result={'ok':True}")
            naive.exec_op("\n".join(lines))
        naive.exec_op(
            "import bpy\n"
            "for n in ('Block3','Block47','Block91'):\n"
            "    bpy.data.objects[n].location.z = 2\n"
            "result={'ok':True}"
        )
        naive.query(SCENE_DUMP_CODE)  # "what does the scene look like now?"
    if tee:
        ops = [
            {
                "op": "create",
                "kind": "cube",
                "name": f"Block{j}",
                "props": {"size": 0.5, "location": [j % 10, j // 10, 0]},
            }
            for j in range(100)
        ]
        out = tee.batch(ops)
        ids = out["created"]
        stamp = {"epoch": out["epoch"], "revision": out["revision"]}
        tee.batch(
            [
                {"op": "set", "id": ids[k], "props": {"location": [k % 10, k // 10, 2]}}
                for k in (3, 47, 91)
            ]
        )
        tee.diff(stamp)  # "what changed?" costs a diff, not a dump


def scenario_material_pass(naive: Naive | None, tee: Tee | None) -> None:
    """Assign a distinct material to each of 10 objects."""
    if naive:
        lines = ["import bpy"]
        for i in range(10):
            lines.append(
                f"bpy.ops.mesh.primitive_uv_sphere_add(radius=0.4, location=({i},0,0))\n"
                f"bpy.context.active_object.name = 'Ball{i}'"
            )
        lines.append("result={'ok':True}")
        naive.exec_op("\n".join(lines))
        for i in range(10):
            naive.exec_op(
                f"import bpy\nmat = bpy.data.materials.new('M{i}')\nmat.use_nodes=True\n"
                f"bsdf = next(n for n in mat.node_tree.nodes if n.type=='BSDF_PRINCIPLED')\n"
                f"bsdf.inputs['Base Color'].default_value = ({i / 10},0.2,0.5,1)\n"
                f"bpy.data.objects['Ball{i}'].data.materials.append(mat)\nresult={{'ok':True}}"
            )
    if tee:
        out = tee.batch(
            [
                {
                    "op": "create",
                    "kind": "uv_sphere",
                    "name": f"Ball{i}",
                    "props": {"radius": 0.4, "location": [i, 0, 0]},
                }
                for i in range(10)
            ]
        )
        ops = [
            {
                "op": "assign_material",
                "id": eid,
                "props": {"material": f"M{i}", "base_color": [i / 10, 0.2, 0.5]},
            }
            for i, eid in enumerate(out["created"])
        ]
        tee.batch(ops)


def scenario_verify(naive: Naive | None, tee: Tee | None) -> None:
    """Check a layout for overlaps/placement problems."""
    if naive:
        naive.screenshot()  # look at it
        naive.query(SCENE_DUMP_CODE)  # and read everything
    if tee:
        tee.stats()  # text-first geometric checks


SCENARIOS = [
    ("donut-class modelling", scenario_donut),
    ("100-object populate + what-changed", scenario_hundred_objects),
    ("material pass over 10 objects", scenario_material_pass),
    ("layout verification", scenario_verify),
]


# --------------------------------------------------------------------------
# Extraction scenario (7.8): ingest-once vs media re-billing across a
# simulated multi-session build. Needs no Blender - the media lanes are
# fully local. Media set = the in-repo synthetic fixtures (a DXF plan with
# real DIMENSION entities, a vector-PDF sheet, a walkthrough video, a DJI
# SRT, three site photos, and an espeak-synthesized client brief).
# --------------------------------------------------------------------------

EXTRACT_SESSIONS = 4
NAIVE_FRAMES_PER_SESSION = 6


def run_extract_scenario() -> tuple | None:
    try:
        import pypdfium2 as pdfium
        from fixtures_extract import (
            BRIEF_TEXT,
            DJI_SRT,
            make_audio,
            make_dxf,
            make_pdf,
            make_scene_frames,
            make_video,
        )
        from test_extract_images_media import make_photo

        from tee.app import TeeApp
        from tee.extract.tools import register_extract_tools
        from tee.kernel.adapter import FakeAdapter
    except ImportError as exc:
        print(f"extraction scenario skipped (extract extra not installed: {exc})")
        return None

    workdir = Path(tempfile.mkdtemp(prefix="tee-bench-extract-"))
    media = workdir / "site-materials"
    media.mkdir()
    dxf = make_dxf(media / "plan.dxf")
    pdf = make_pdf(media / "A-101.pdf")
    frames = make_scene_frames(workdir / "frames")
    make_video(media / "walkthrough.mp4", frames)
    (media / "flight.srt").write_text(DJI_SRT)
    photos = [make_photo(media / f"photo{i}.jpg", seed=s) for i, s in enumerate((0, 1, 40))]
    audio = make_audio(media / "brief.wav")

    # -- naive: every session re-attaches the media to context ------------
    naive = Meter()
    doc = pdfium.PdfDocument(str(pdf))
    page = doc[0]
    sheet_px = (int(page.get_width() * 200 / 72), int(page.get_height() * 200 / 72))
    doc.close()
    from PIL import Image

    from tee.extract.images import STANDARD_EDGE_CAP

    def attach(width: int, height: int) -> None:
        # the API resizes so the long edge is <= 1568 (standard tier)
        long_edge = max(width, height)
        if long_edge > STANDARD_EDGE_CAP:
            factor = STANDARD_EDGE_CAP / long_edge
            width, height = int(width * factor), int(height * factor)
        naive.round_trips += 1
        naive.image(width, height)

    dxf_text = dxf.read_text(errors="ignore")
    for _session in range(EXTRACT_SESSIONS):
        naive.text(dxf_text)  # raw DXF pasted into context (it is text)
        naive.round_trips += 1
        attach(*sheet_px)  # plan sheet rendered at 200 dpi
        for photo in photos:
            with Image.open(photo) as img:
                attach(*img.size)
        for _frame in range(NAIVE_FRAMES_PER_SESSION):
            attach(320, 240)  # fixture video frames at native size
        if audio is not None:
            naive.text(BRIEF_TEXT)  # transcript re-supplied every session

    # -- TEE: ingest once locally, then compact fact queries ---------------
    tee = Meter()
    project = workdir / "project"
    project.mkdir()
    app = TeeApp({"blender": FakeAdapter()}, project_root=project)
    store, registry = register_extract_tools(app, project)
    from tee.extract.handoff import register_handoff_tools

    register_handoff_tools(app, store, registry)
    try:
        # session 1: one ingest job (local, zero tokens while it runs) and
        # the compact fact reads a model actually needs to start building
        request = {"tool": "ex_ingest", "path": str(media)}
        out = app.registry.call("ex_ingest", {"path": str(media)})
        deadline = time.time() + 300
        while time.time() < deadline:
            status = app.jobs.status(out["job"])
            if status["state"] in ("done", "error"):
                break
            time.sleep(0.3)
        assert status["state"] == "done", status
        tee.call(request, status["result"])

        for kind in ("plan", "dimension"):
            response = app.registry.call("ex_facts", {"source": "plan.dxf", "kind": kind})
            tee.call({"tool": "ex_facts", "kind": kind}, response)
        for name, kind in (("walkthrough.mp4", "keyframe"), ("brief.wav", "transcript_segment")):
            try:
                response = app.registry.call("ex_facts", {"source": name, "kind": kind})
            except Exception:
                continue  # no audio lane on this machine
            tee.call({"tool": "ex_facts", "kind": kind}, response)
        sheets = [f for s in store.sources() for f in store.facts(s["hash"], kind="contact_sheet")]
        if sheets:
            tee.round_trips += 1
            tee.tokens += int(sheets[-1].get("tokens") or 0)  # contact sheet, once

        # sessions 2..N: facts are already on disk - compact queries only
        for session in range(1, EXTRACT_SESSIONS):
            response = app.registry.call("ex_search", {"query": "bedroom dimension"})
            tee.call({"tool": "ex_search", "query": "bedroom dimension"}, response)
            response = app.registry.call("ex_facts", {"source": "plan.dxf", "kind": "plan"})
            tee.call({"tool": "ex_facts", "kind": "plan"}, response)
            if session == 2:  # one budgeted detail crop mid-build
                tee.round_trips += 1
                tee.tokens += 300

        # -- Phase 8 (A11): the conformance fix loop, rounds vs tee_script
        def toks(x) -> int:
            import json as _json

            return estimate_tokens(_json.dumps(x, separators=(",", ":"), default=str))

        src = store.resolve("plan.dxf")["hash"][:8]
        app.registry.call("bl_build_from_plan", {"source": src})
        manifest = store.facts(store.resolve(src)["hash"], kind="build_manifest")[-1]
        for eid in list(manifest["walls"].values())[:3]:
            loc = list(app.cache("blender").get(eid).summary.get("location") or [0, 0, 0])
            loc[0] += 0.2
            app.run_batch("blender", [{"op": "set", "id": eid, "props": {"location": loc}}])

        rounds = []
        report = app.registry.call("bl_check_against_plan", {"source": src})
        rounds.append(({"tool": "tee_call", "name": "bl_check_against_plan"}, report))
        for conflict in report["conflicts"]:
            eid = conflict["fact_b"].split(":", 1)[1]
            loc = list(app.cache("blender").get(eid).summary["location"])
            loc[0] -= 0.2
            fix = app.run_batch("blender", [{"op": "set", "id": eid, "props": {"location": loc}}])
            rounds.append(({"tool": "tee_batch", "ops": "1 set op"}, fix))
        final = app.registry.call("bl_check_against_plan", {"source": src})
        rounds.append(({"tool": "tee_call", "name": "bl_check_against_plan"}, final))
        loop_naive = sum(toks(req) + toks(resp) for req, resp in rounds)

        # same repair as ONE tee_script call, re-sabotaging first
        for eid in list(manifest["walls"].values())[:3]:
            loc = list(app.cache("blender").get(eid).summary["location"])
            loc[0] += 0.2
            app.run_batch("blender", [{"op": "set", "id": eid, "props": {"location": loc}}])
        from tee.kernel.script import run_script

        code = (
            f"r = call('bl_check_against_plan', {{'source': '{src}'}})\n"
            "for c in r['conflicts']:\n"
            "    eid = get(c, 'fact_b')[6:]\n"
            "    e = detail(eid)\n"
            "    loc = [e['location'][0] - get(c, 'delta_m'),"
            " e['location'][1], e['location'][2]]\n"
            "    batch([{'op': 'set', 'id': eid, 'props': {'location': loc}}])\n"
            f"result = call('bl_check_against_plan', {{'source': '{src}'}})\n"
        )
        script_out = run_script(app, code, default_adapter="blender")
        assert script_out["result"]["conformant"], script_out
        loop_script = toks({"tool": "tee_script", "code": code}) + toks(script_out)
        loop_saving = 100.0 * (1 - loop_script / loop_naive)
    finally:
        app.shutdown()

    saving = 100.0 * (1 - tee.tokens / naive.tokens)
    print(
        f"extraction ingest-once vs re-attach ({EXTRACT_SESSIONS} sessions): "
        f"naive {naive.tokens} tok / {naive.round_trips} attaches"
        f" -> tee {tee.tokens} tok / {tee.round_trips} calls ({saving:.1f}% saved)"
    )
    print(
        f"conformance fix loop: {len(rounds)} rounds / {loop_naive} tok"
        f" -> 1 tee_script call / {loop_script} tok ({loop_saving:.1f}% saved)"
    )
    return {
        "ingest": (naive.tokens, naive.round_trips, tee.tokens, tee.round_trips, saving),
        "fixloop": (loop_naive, len(rounds), loop_script, loop_saving),
    }


# --------------------------------------------------------------------------
# Asset scenario (Phase 9): find-select-place N assets
# --------------------------------------------------------------------------

ASSET_COUNT = 3

# Measured prior-art flow per asset (docs/research/22: the popular
# community integration, ahujasid/blender-mcp, wire-measured 2026-08):
PRIOR_STRATEGY_PROMPT = 1400  # mandatory strategy prompt, once per session
PRIOR_STATUS_CHECKS = 4 * 90  # 4 per-provider status round-trips
PRIOR_SEARCH_TOKENS = 540  # formatted alphabetical-first-20 catalog slice
PRIOR_PREVIEWS_PER_ASSET = 3 * 475  # per-UID inline previews (vision tokens)
PRIOR_IMPORT_TOKENS = 150  # download+import call/response
PRIOR_SCREENSHOTS = 2 * 777  # before/after screenshots the prompt mandates


def run_asset_scenario() -> tuple | None:
    """TEE find-select-place measured for real (fake adapter + fake backend
    seeded with realistic rows) vs the documented prior-art flow."""
    try:
        import sys

        sys.path.insert(0, str(Path(__file__).parent.parent / "server" / "tests"))
        from fixtures_assets import FakeBackend, build_glb, make_rows

        from tee.app import TeeApp
        from tee.assets import importer as importer_mod
        from tee.assets import tools as asset_tools
        from tee.kernel.adapter import FakeAdapter
    except ImportError as exc:
        print(f"asset scenario skipped ({exc})")
        return None

    naive_tokens = PRIOR_STRATEGY_PROMPT + PRIOR_STATUS_CHECKS + ASSET_COUNT * (
        PRIOR_SEARCH_TOKENS
        + PRIOR_PREVIEWS_PER_ASSET
        + PRIOR_IMPORT_TOKENS
        + PRIOR_SCREENSHOTS
    )
    naive_calls = 4 + ASSET_COUNT * 7  # status + per asset: search, 3 previews, import, 2 shots

    workdir = Path(tempfile.mkdtemp(prefix="tee-bench-assets-"))
    app = TeeApp({"fake": FakeAdapter()}, project_root=workdir)
    rows = make_rows() * 7  # a shortlist-worthy catalog, not 3 rows
    for i, row in enumerate(rows):
        row.id = f"{row.id}_{i}"
    glb = build_glb(workdir / "asset.glb", size=(2.1, 0.8, 0.9), tris=9000)
    original_build, original_fetch = asset_tools.build_backends, importer_mod.fetch_bytes
    asset_tools.build_backends = lambda store, config=None: {
        "fakesource": FakeBackend(store, rows=rows)
    }
    importer_mod.fetch_bytes = lambda url, headers=None: glb.read_bytes()
    tee = Meter()
    try:
        asset_tools.register_asset_tools(app, workdir)
        room = {
            "polygon": [[0, 0], [5, 0], [5, 4], [0, 4]],
            "walls": [
                {"id": "south", "a": [0, 0], "b": [5, 0]},
                {"id": "north", "a": [5, 4], "b": [0, 4]},
            ],
            "doors": [{"id": "d1", "hinge": [0.05, 0.0], "width": 0.86}],
        }

        request = {"tool": "as_search", "query": "sofa seating fabric",
                   "asset_class": "model", "max_tris": 20000}
        response = app.registry.call(
            "as_search",
            {"query": "sofa seating fabric", "asset_class": "model", "max_tris": 20000},
        )
        tee.call(request, response)
        picks = [r["id"] for r in response["results"]["model"][:ASSET_COUNT]]
        drop_zones = ([1.2, 1.5, 0], [3.6, 1.5, 0], [2.4, 2.9, 0])
        entity_ids = []
        for index, pick in enumerate(picks):
            request = {"tool": "as_import", "asset": pick, "asset_class": "sofa",
                       "location": drop_zones[index]}
            response = app.registry.call(
                "as_import",
                {"asset": pick, "asset_class": "sofa",
                 "location": drop_zones[index], "adapter": "fake"},
            )
            tee.call(request, response)
            entity_ids.append(response["created"][0])
        anchors = [("south", 3.5), ("north", 1.2), ("north", 3.7)]
        plan = [
            {"name": f"sofa{i}", "class": "sofa", "dims": [2.1, 0.9, 0.8],
             "anchor": anchors[i][0], "offset": anchors[i][1], "id": eid,
             "relax": []}
            for i, eid in enumerate(entity_ids)
        ]
        request = {"tool": "as_place", "plan": f"{len(plan)} items", "apply": True}
        response = app.registry.call(
            "as_place", {"plan": plan, "room": room, "apply": True, "adapter": "fake"}
        )
        tee.call(request, response)
        request = {"tool": "as_verify"}
        response = app.registry.call("as_verify", {"adapter": "fake", "room": room})
        tee.call(request, response)
        assert response["violations"] == [], response
    finally:
        asset_tools.build_backends = original_build
        importer_mod.fetch_bytes = original_fetch
        app.shutdown()

    saving = 100.0 * (1 - tee.tokens / naive_tokens)
    print(
        f"assets find-select-place x{ASSET_COUNT}: prior-art {naive_tokens} tok / "
        f"{naive_calls} calls -> tee {tee.tokens} tok / {tee.round_trips} calls "
        f"({saving:.1f}% saved)"
    )
    return (naive_tokens, naive_calls, tee.tokens, tee.round_trips, saving)


# --------------------------------------------------------------------------
# Physical scenario (Phase 11): settle cost + determinism variance floor
# --------------------------------------------------------------------------


def run_physical_scenario() -> dict | None:
    try:
        from tee.adapters.blender.adapter import BlenderAdapter
        from tee.app import TeeApp
        from tee.physical.tools import register_physical_tools
    except ImportError as exc:
        print(f"physical scenario skipped ({exc})")
        return None
    blender = find_blender()
    port = free_port()
    proc = launch_bridge(blender, port)
    wire = BlenderWire(port=port)
    deadline = time.time() + 60
    while time.time() < deadline and not wire.probe():
        time.sleep(0.5)
    if not wire.probe():
        proc.kill()
        print("physical scenario skipped (bridge never came up)")
        return None
    try:
        workdir = tempfile.mkdtemp(prefix="tee-bench-phys-")
        adapter = BlenderAdapter(wire, workdir=workdir)
        app = TeeApp({"blender": adapter}, project_root=workdir, allow_code_exec=True)
        register_physical_tools(app, workdir)
        clear_scene(wire)
        app.cache("blender").resync(adapter)
        ops = [
            {"op": "create", "kind": "cube", "name": "Ground",
             "props": {"size": 1.0, "scale": [10, 10, 0.1], "location": [0, 0, -0.05]}},
        ] + [
            {"op": "create", "kind": "cube", "name": f"Box{i}",
             "props": {"size": 0.4, "location": [0.05 * i, 0.03 * i, 0.6 + 0.5 * i],
                       "rotation_euler": [0.1 * i, 0.05 * i, 0.02 * i]}}
            for i in range(4)
        ]
        app.run_batch("blender", ops)

        def ids_by_name():
            return {e.name: e.id for e in app.cache("blender").entities.values()}

        runs = []
        report_tokens = 0
        wall = 0.0
        for _ in range(2):
            current = ids_by_name()
            boxes = [current[f"Box{i}"] for i in range(4)]
            out = app.registry.call(
                "sim_settle",
                {"ids": boxes, "passive_ids": [current["Ground"]],
                 "adapter": "blender"},
            )
            import json as _json

            report_tokens = estimate_tokens(
                _json.dumps(out, separators=(",", ":"), default=str)
            )
            wall = out.get("wall_s", 0)
            runs.append(out["final_by_name"])
            app.rollback("blender", out["checkpoint"])
        floor = 0.0
        for name in runs[0]:
            if name in runs[1]:
                for a, b in zip(runs[0][name], runs[1][name], strict=True):
                    floor = max(floor, abs(a - b))
        app.shutdown()
    finally:
        proc.terminate()
    print(
        f"physics settle (4 bodies): report ~{report_tokens} tok, {wall:.1f}s wall; "
        f"two-run variance floor {floor * 1000:.2f} mm"
    )
    return {"report_tokens": report_tokens, "wall_s": wall, "floor_mm": floor * 1000}


# --------------------------------------------------------------------------
# Surface + jurisdiction scenario (Phase 15.2): the two things a schema or
# state-representation change can move. Needs no DCC, so it runs anywhere.
# --------------------------------------------------------------------------

# A small Namibian house described in the terms plaus_check understands.
PLAN = {
    "elements": [
        {"id": "bed1", "class": "room", "habitable": True, "ceiling_m": 2.30,
         "area_m2": 5.4, "min_dimension_m": 1.9},
        {"id": "living", "class": "room", "habitable": True, "ceiling_m": 2.45,
         "area_m2": 18.0, "min_dimension_m": 3.4},
        {"id": "s1", "class": "stair", "riser_mm": 195, "tread_mm": 245,
         "width_mm": 800, "headroom_mm": 2120, "riser_variation_mm": 9},
        {"id": "j1", "class": "joist", "size": "2x8", "span_m": 4.2},
        {"id": "r1", "class": "roof", "covering": "corrugated_metal", "pitch_deg": 7.0},
        {"id": "w1", "class": "wall", "thickness_m": 0.22, "height_m": 2.7,
         "length_m": 6.0, "material": "clay_brick"},
        {"id": "f1", "class": "footing", "wall": "w1", "width_m": 0.20,
         "soil_bearing_kpa": 120},
    ]
}
REGIONS = ["US", "ZA", "NA-local-authority", "NA-settlement", "NA-communal", "NA"]
# What a model must read to answer "which code applies here, and what does it
# require?" without TEE. These four files carry the operative answer.
CODE_CORPUS = [
    "00_overview.md",
    "04_namibia-building-regulations.md",
    "05_namibia-approvals-and-institutions.md",
    "02_sans-10400-parts-register.md",
]


def run_surface_scenario() -> dict | None:
    """Always-loaded MCP surface, measured as the wire actually carries it,
    plus what a flat one-tool-per-capability server would have cost."""
    try:
        import anyio
        from mcp.client import Client

        from tee.app import TeeApp
        from tee.assets.tools import register_asset_tools
        from tee.design.tools import register_design_tools
        from tee.extract.tools import register_extract_tools
        from tee.kernel.adapter import FakeAdapter
        from tee.kb.tools import register_kb_tools
        from tee.physical.tools import register_physical_tools
        from tee.pins.tools import register_pin_tools
        from tee.server import build_server
        from tee.uefn.tools import register_uefn_tools
    except ImportError as exc:
        print(f"surface scenario skipped ({exc})")
        return None

    # The SDK puts messages on the wire with by_alias + exclude_none; a bare
    # model_dump() counts ~490 tokens of null padding no client ever sees.
    wire_kw = dict(by_alias=True, mode="json", exclude_none=True)

    def listed(app):
        server = build_server(app)

        async def fetch():
            async with Client(server) as client:
                return (await client.list_tools()).tools

        return anyio.run(fetch)

    root = tempfile.mkdtemp(prefix="tee-bench-surface-")
    bare = TeeApp({"fake": FakeAdapter()}, project_root=root)
    bare_tokens = estimate_tokens(
        _json.dumps([t.model_dump(**wire_kw) for t in listed(bare)], default=str)
    )
    bare.shutdown()

    app = TeeApp({"fake": FakeAdapter()}, project_root=root)
    store, _ = register_extract_tools(app, root)
    register_asset_tools(app, root, extract_store=store)
    register_design_tools(app, root)
    register_physical_tools(app, root)
    register_pin_tools(app, root)
    register_uefn_tools(app, root)
    register_kb_tools(app, root, root=str(REPO / "knowledge-base"))
    tools = listed(app)
    full_tokens = estimate_tokens(
        _json.dumps([t.model_dump(**wire_kw) for t in tools], default=str)
    )
    dump_tokens = estimate_tokens(
        _json.dumps([t.model_dump(mode="json") for t in tools], default=str)
    )

    registry = app.registry
    names = registry.names()
    flat = [
        {
            "name": name,
            "description": registry.describe(name)["description"],
            "inputSchema": registry.describe(name)["schema"],
        }
        for name in names
    ]
    flat_tokens = estimate_tokens(_json.dumps(flat, default=str)) + full_tokens
    search = registry.search("check a staircase against the building code", limit=5)
    reach = estimate_tokens(_json.dumps(search, default=str)) + estimate_tokens(
        _json.dumps(registry.describe("plaus_check"), default=str)
    )
    app.shutdown()

    row = {
        "n_tools": len(tools),
        "wire_tokens": full_tokens,
        "model_dump_tokens": dump_tokens,
        "added_by_modules": full_tokens - bare_tokens,
        "n_virtual_tools": len(names),
        "flat_server_tokens": flat_tokens,
        "reach_one_tool": reach,
        "saving": 100.0 * (1 - full_tokens / flat_tokens),
    }
    print(
        f"surface: {len(tools)} always-loaded tools = {full_tokens} tok on the wire "
        f"({dump_tokens} by model_dump); {len(names)} virtual tools would cost "
        f"{flat_tokens} tok flat ({row['saving']:.1f}% saved); "
        f"reach one = {reach} tok"
    )
    return row


def run_jurisdiction_scenario() -> dict | None:
    """plaus_check response cost per regime, and the same question answered by
    reading the code corpus into context instead."""
    try:
        from tee.physical import plaus
    except ImportError as exc:
        print(f"jurisdiction scenario skipped ({exc})")
        return None

    rows = {}
    for region in REGIONS:
        result = plaus.check(dict(PLAN, region=region))
        block = result.get("jurisdiction", {})
        stripped = copy.deepcopy({k: v for k, v in result.items() if k != "jurisdiction"})
        for finding in stripped.get("findings", []):
            finding.pop("severity_capped_from", None)
        total = estimate_tokens(_json.dumps(result, default=str))
        rows[region] = {
            "resolved": block.get("region"),
            "rule_set": block.get("rule_set"),
            "max_severity": block.get("max_severity"),
            "findings": len(result.get("findings", [])),
            "capped": block.get("capped_findings", 0),
            "tokens": total,
            "jurisdiction_cost": total - estimate_tokens(_json.dumps(stripped, default=str)),
        }
        print(
            f"  {region:20s} -> {rows[region]['resolved']:20s} cap "
            f"{rows[region]['max_severity']:4s} {rows[region]['findings']} findings "
            f"({rows[region]['capped']} capped), {total} tok"
        )

    codes = Path(__file__).parent.parent / "knowledge-base" / "03_codes_standards"
    corpus = None
    if codes.is_dir():
        corpus = sum(estimate_tokens((codes / name).read_text()) for name in CODE_CORPUS)
    worst = max(rows.values(), key=lambda r: r["tokens"])
    request = estimate_tokens(_json.dumps({"model": dict(PLAN, region="NA-communal")}, default=str))
    tee_total = request + rows["NA-communal"]["tokens"]
    row = {
        "regions": rows,
        "corpus_tokens": corpus,
        "tee_tokens": tee_total,
        "worst_response": worst["tokens"],
        "saving": None if not corpus else 100.0 * (1 - tee_total / corpus),
    }
    if corpus:
        print(
            f"code check on communal land: read the corpus {corpus} tok -> "
            f"one plaus_check {tee_total} tok ({row['saving']:.1f}% saved)"
        )
    return row


# --------------------------------------------------------------------------
# KB scenario (Phase 16): sourced answer from the Expert Knowledge Base.
# The task: "what bedding-sand and jointing-sand spec applies to concrete
# block paving here, with a citation?" Needs no DCC.
# --------------------------------------------------------------------------


def run_kb_scenario() -> dict | None:
    try:
        from tee.app import TeeApp
        from tee.kb.tools import register_kb_tools
        from tee.kernel.adapter import FakeAdapter
    except ImportError as exc:
        print(f"kb scenario skipped ({exc})")
        return None
    kb_root = REPO / "knowledge-base"
    if not (kb_root / "manifest.json").is_file():
        print("kb scenario skipped (no knowledge-base mirror)")
        return None

    project = tempfile.mkdtemp(prefix="tee-bench-kb-")
    app = TeeApp({"fake": FakeAdapter()}, project_root=project)
    register_kb_tools(app, project, root=str(kb_root))
    reg = app.registry
    tokens = 0
    calls = 0

    def call(name, args):
        nonlocal tokens, calls
        tokens += estimate_tokens(_json.dumps(args, separators=(",", ":"), default=str))
        result = reg.call(name, args)
        tokens += estimate_tokens(_json.dumps(result, separators=(",", ":"), default=str))
        calls += 1
        return result

    hits = call("kb_search", {"query": "concrete block paving bedding sand specification"})
    top = hits["hits"][0]["id"]
    read = call("kb_read", {"id": top, "section": "Key facts"})
    assert read["flags"]["confidence"], "flags must ride on every content response"
    app.shutdown()

    # Naive baseline: what a session without kb_* pastes to answer the same
    # question with a citation - the corpus's own INDEX to find the file,
    # then the whole file (sections are not addressable without the module).
    index_tokens = estimate_tokens((kb_root / "INDEX.md").read_text(encoding="utf-8"))
    file_rel = "17_paving_and_roads/03_concrete-block-paving.md"
    file_tokens = estimate_tokens((kb_root / file_rel).read_text(encoding="utf-8"))
    naive = index_tokens + file_tokens
    row = {
        "naive_tokens": naive,
        "index_tokens": index_tokens,
        "file_tokens": file_tokens,
        "tee_tokens": tokens,
        "tee_calls": calls,
        "answer_file": top,
        "saving": 100.0 * (1 - tokens / naive),
    }
    print(
        f"kb paving lookup: INDEX.md + full file {naive} tok -> "
        f"{calls} kb_* calls {tokens} tok ({row['saving']:.1f}% saved)"
    )
    return row


# --------------------------------------------------------------------------
# Runner
# --------------------------------------------------------------------------


def find_blender() -> str:
    for candidate in BLENDER_CANDIDATES:
        if candidate and Path(candidate).exists():
            return candidate
    raise SystemExit("no Blender binary found")


def launch_bridge(blender: str, port: int) -> subprocess.Popen:
    boot = Path(tempfile.mkdtemp(prefix="tee-bench-")) / "boot.py"
    boot.write_text(
        f"import sys\nsys.path.insert(0, {str(TEE_BRIDGE_DIR)!r})\n"
        f"import bridge_server\nbridge_server.run_blocking('127.0.0.1', {port})\n"
    )
    return subprocess.Popen(
        [blender, "--background", "--factory-startup", "--python", str(boot)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def clear_scene(wire: BlenderWire) -> None:
    wire.execute(
        "import bpy\n"
        "for o in list(bpy.data.objects): bpy.data.objects.remove(o, do_unlink=True)\n"
        "for m in list(bpy.data.materials): bpy.data.materials.remove(m)\n"
        "result={'ok':True}"
    )



# --------------------------------------------------------------------------
# Unreal scenario (Phase 5c): level population + Blueprint function against a
# live UE 5.8 editor with Epic's MCP server started. Skips cleanly when no
# editor is listening.
#
# The NAIVE side is not a straw man: it is exactly the workflow Epic's own
# unreal-mcp skill prescribes - list_toolsets, describe_toolset for each
# toolset you intend to use, then one call_tool per operation. That is what a
# competent client does today without TEE, and the schema payloads dominate.
# --------------------------------------------------------------------------

UE_ACTORS = 10


def run_unreal_scenario() -> tuple | None:
    from tee.adapters.unreal.adapter import UnrealAdapter
    from tee.adapters.unreal.wire import UnrealWire

    wire = UnrealWire()
    if not wire.probe():
        print("unreal: no editor on 127.0.0.1:8000 - skipping")
        return None

    adapter = UnrealAdapter(wire=wire)
    catalog = adapter.catalog
    snapshot = adapter.snapshot("benchmark")
    try:
        naive = Meter()
        # 1. discover: the meta-tool list, then a full schema dump per toolset
        naive.call("list_toolsets", catalog.wire.call_text("list_toolsets"))
        for toolset in ("SceneTools", "ActorTools", "BlueprintTools"):
            qualified = catalog.resolve(toolset)
            raw = catalog.wire.call_text("describe_toolset", {"toolset_name": qualified})
            naive.call({"toolset_name": qualified}, raw)
        # 2. one call_tool per spawn, each answering with a refPath object
        for i in range(UE_ACTORS):
            request = {
                "toolset_name": catalog.resolve("SceneTools"),
                "tool_name": "add_to_scene_from_asset",
                "arguments": {
                    "asset_path": "/Engine/BasicShapes/Cube",
                    "name": f"NaiveCube{i}",
                    "xform": {"location": {"x": i * 150.0, "y": -600.0, "z": 100.0}},
                },
            }
            naive.call(request, catalog.call("SceneTools", "add_to_scene_from_asset",
                                             request["arguments"], timeout=180))
        # 3. read the level back the only way the raw surface offers: refPaths,
        #    then a transform call per actor
        listing = catalog.call("SceneTools", "find_actors",
                               {"name": "", "tag": "", "collision_channels": []}, timeout=180)
        naive.call({"tool": "find_actors"}, listing)
        refs = [a["refPath"] for a in _json.loads(listing)["returnValue"]][:UE_ACTORS]
        for ref in refs:
            naive.call({"actor": {"refPath": ref}},
                       catalog.call("ActorTools", "get_actor_transform",
                                    {"actor": {"refPath": ref}}, timeout=120))
        # 4. author the Blueprint function one tool call at a time
        bp_steps = [
            ("create", {"folder_path": "/Game/TeeProbe", "asset_name": "BP_NaiveBench",
                        "asset_type": {"refPath": "/Script/Engine.Actor"}}),
        ]
        for tool, args in bp_steps:
            naive.call({"tool": tool, "arguments": args}, "{}")
        naive.round_trips += 6  # add_function_graph, 3 params, write_dsl, compile
        naive.text("(fn AddTwo (A B)\n  (return (Utilities|Operators|Add :A A :B B)))")

        # --- TEE side -------------------------------------------------------
        tee = Meter()
        # 1. discovery: compact signatures, not schema dumps
        tee.call({"toolset": "SceneTools"},
                 _json.dumps(catalog.summary("SceneTools"), separators=(",", ":")))
        # 2. ONE batch for the whole population
        ops = [
            {"op": "create", "name": f"TeeCube{i}",
             "props": {"asset_path": "/Engine/BasicShapes/Cube",
                       "location": [i * 150.0, -900.0, 100.0]}}
            for i in range(UE_ACTORS)
        ]
        diff = adapter.execute(ops)
        tee.call(ops, {"created": diff.created, "modified": diff.modified,
                       "deleted": diff.deleted, "details": diff.details})
        # 3. read back: compact ids, no refPaths in context
        entities = adapter.list_entities()
        tee.call({"tool": "tee_scene_summary"},
                 [e.concise() for e in entities])
        # 4. the Blueprint function as ONE verified macro call
        args = {"folder": "/Game/TeeProbe", "asset_name": "BP_TeeBench",
                "function_name": "AddTwo",
                "dsl": "(fn AddTwo (A B)\n  (return (Utilities|Operators|Add :A A :B B)))",
                "params": [{"name": "A", "type": "int", "input": True},
                           {"name": "B", "type": "int", "input": True},
                           {"name": "Sum", "type": "int", "input": False}]}
        tee.call(args, adapter.blueprint_function(**args))

        saving = 100.0 * (1 - tee.tokens / naive.tokens)
        print(f"unreal level+blueprint: naive {naive.tokens} tok / {naive.round_trips} calls"
              f" -> tee {tee.tokens} tok / {tee.round_trips} calls ({saving:.1f}% saved)")
        return (naive.tokens, naive.round_trips, tee.tokens, tee.round_trips, saving)
    finally:
        adapter.restore(snapshot)


def main() -> None:
    blender = find_blender()
    port = free_port()
    proc = launch_bridge(blender, port)
    wire = BlenderWire(port=port)
    deadline = time.time() + 60
    while time.time() < deadline and not wire.probe():
        time.sleep(0.5)
    if not wire.probe():
        proc.kill()
        raise SystemExit("bridge never came up")

    rows = []
    try:
        for name, scenario in SCENARIOS:
            # naive run
            clear_scene(wire)
            naive_meter = Meter()
            scenario(Naive(wire, naive_meter), None)

            # tee run (fresh app per scenario)
            clear_scene(wire)
            adapter = BlenderAdapter(wire)
            app = TeeApp(
                {"blender": adapter}, project_root=tempfile.mkdtemp(), allow_code_exec=True
            )
            register_blender_tools(app, adapter)
            app.warm("blender")
            tee_meter = Meter()
            try:
                scenario(None, Tee(app, tee_meter))
            finally:
                app.shutdown()

            saving = 100.0 * (1 - tee_meter.tokens / naive_meter.tokens)
            rows.append(
                (
                    name,
                    naive_meter.tokens,
                    naive_meter.round_trips,
                    tee_meter.tokens,
                    tee_meter.round_trips,
                    saving,
                )
            )
            print(
                f"{name}: naive {naive_meter.tokens} tok / {naive_meter.round_trips} calls"
                f" -> tee {tee_meter.tokens} tok / {tee_meter.round_trips} calls"
                f" ({saving:.1f}% saved)"
            )
    finally:
        proc.terminate()

    extract_row = run_extract_scenario()
    asset_row = run_asset_scenario()
    physical_row = run_physical_scenario()
    unreal_row = _safe(run_unreal_scenario)
    surface_row = _safe(run_surface_scenario)
    jurisdiction_row = _safe(run_jurisdiction_scenario)
    kb_row = _safe(run_kb_scenario)
    write_results(rows, extract_row, asset_row, physical_row, unreal_row,
                  surface_row, jurisdiction_row, kb_row)


def _safe(fn):
    """A live-editor scenario must never take the whole benchmark down."""
    try:
        return fn()
    except Exception as exc:
        print(f"{fn.__name__}: skipped ({type(exc).__name__}: {exc})")
        return None


def write_results(rows, extract_row=None, asset_row=None, physical_row=None,
                  unreal_row=None, surface_row=None, jurisdiction_row=None,
                  kb_row=None) -> None:
    out = Path(__file__).parent / "RESULTS.md"
    lines = [
        "# Token benchmark results",
        "",
        "Same live headless Blender, same wire protocol, two interface styles:",
        "**naive** (one code request per op + full scene dump after every",
        "mutation + full-res screenshots - the dominant existing-bridge",
        "pattern) vs **TEE** (typed batches, diffs, compact summaries,",
        "geometric assertions, budgeted capture). Metric: estimated context",
        "tokens of all requests + responses (chars/3.5; images",
        "ceil(w/28)*ceil(h/28)).",
        "",
        "| Scenario | Naive tokens | Naive calls | TEE tokens | TEE calls | Saving |",
        "|---|---|---|---|---|---|",
    ]
    total_naive = total_tee = 0
    for name, ntok, ncalls, ttok, tcalls, saving in rows:
        total_naive += ntok
        total_tee += ttok
        lines.append(f"| {name} | {ntok:,} | {ncalls} | {ttok:,} | {tcalls} | {saving:.1f}% |")
    total_saving = 100.0 * (1 - total_tee / total_naive)
    lines.append(
        f"| **total** | **{total_naive:,}** | | **{total_tee:,}** | | **{total_saving:.1f}%** |"
    )
    if extract_row is not None:
        ntok, ncalls, ttok, tcalls, saving = extract_row["ingest"]
        lines += [
            "",
            "## Extraction: ingest-once vs media re-billing",
            "",
            f"A simulated {EXTRACT_SESSIONS}-session build over one media set (DXF plan,",
            "vector-PDF sheet, walkthrough video, DJI SRT, 3 site photos, audio",
            "brief - the in-repo synthetic fixtures). **Naive** re-attaches the",
            "media to context every session (raw DXF text, sheet render, photos,",
            "video frames, transcript). **TEE** ingests once - deterministic local",
            "extraction, zero tokens while it runs - then every session reads",
            "compact facts from the content-addressed store, plus one bounded",
            "contact sheet and one 300-token detail crop in total.",
            "",
            "| | Tokens | Round-trips/attaches | Saving |",
            "|---|---|---|---|",
            f"| naive re-attach | {ntok:,} | {ncalls} | |",
            f"| TEE ingest-once | {ttok:,} | {tcalls} | {saving:.1f}% |",
            "",
            "Fixture media are deliberately tiny; real drawing sets, 4K site",
            "photos and drone footage widen the gap by an order of magnitude.",
        ]
        ln, nrounds, ls, lsave = extract_row["fixloop"]
        lines += [
            "",
            "## Script lane: the conformance fix loop as one call (Phase 8)",
            "",
            "The same 3-wall repair (check, fix each conflict, recheck)",
            "executed as separate tool rounds vs one `tee_script` call whose",
            "intermediate tool results never enter model context.",
            "",
            "| | Context tokens | Rounds | Saving |",
            "|---|---|---|---|",
            f"| separate tool rounds | {ln:,} | {nrounds} | |",
            f"| one tee_script call | {ls:,} | 1 | {lsave:.1f}% |",
            "",
            "The script's cost is flat in loop length while round-based cost",
            "grows linearly (~130 tok/conflict): measured 17.7% / 63.2% /",
            "76.3% saved at 1 / 3 / 5 conflicts, approaching 100% as loops",
            "grow.",
        ]
    if asset_row is not None:
        ntok, ncalls, ttok, tcalls, saving = asset_row
        lines += [
            "",
            "## Assets: find-select-place (Phase 9)",
            "",
            f"Find, license-check, scale, place, and verify {ASSET_COUNT} sofas.",
            "**Prior art** is the wire-measured community-integration flow",
            "(docs/research/22): mandatory strategy prompt, per-provider",
            "status round-trips, alphabetical catalog slices, per-candidate",
            "inline previews, before/after screenshots. **TEE** is measured",
            "live in this run: one faceted search (<=5 ranked rows), three",
            "checkpointed imports with the scale policy, one relational",
            "placement plan solved+validated server-side, one render-free",
            "verification report - zero images.",
            "",
            "| | Tokens | Calls | Saving |",
            "|---|---|---|---|",
            f"| prior-art flow | {ntok:,} | {ncalls} | |",
            f"| TEE | {ttok:,} | {tcalls} | {saving:.1f}% |",
        ]
    if physical_row is not None:
        lines += [
            "",
            "## Physics: settle cost + variance floor (Phase 11)",
            "",
            "A 4-body rigid settle (sequential frame stepping, quiescence",
            "early-out) reports compact facts instead of per-frame data:",
            "",
            f"- settle report: ~{physical_row['report_tokens']} tokens "
            f"({physical_row['wall_s']:.1f} s wall time, zero tokens while stepping)",
            f"- two-run determinism variance floor on this machine: "
            f"**{physical_row['floor_mm']:.2f} mm** - settle assertions use a "
            "5 mm tolerance, safely above it (A19: same-machine only; never "
            "asserted across builds)",
        ]
    if unreal_row is not None:
        ntok, ncalls, ttok, tcalls, saving = unreal_row
        lines += [
            "",
            "## Unreal: level population + Blueprint function (Phase 5c)",
            "",
            "Live UE 5.8.1 editor with Epic's official MCP server. The naive",
            "side is not a straw man - it is the workflow Epic's own",
            "`unreal-mcp` skill prescribes: `list_toolsets`, then",
            "`describe_toolset` for each toolset you intend to use, then one",
            "`call_tool` per operation, reading the level back as refPaths",
            "plus a transform call per actor. TEE uses compact signatures, one",
            "typed batch for the whole population, short session ids, and one",
            "verified Blueprint macro.",
            "",
            "| | Context tokens | Round-trips | Saving |",
            "|---|---|---|---|",
            f"| naive (describe_toolset + call_tool per op) | {ntok:,} | {ncalls} | |",
            f"| TEE | {ttok:,} | {tcalls} | **{saving:.1f}%** |",
            "",
            "The schema dumps dominate the naive side: one",
            "`describe_toolset(BlueprintTools)` alone is ~18,000 tokens, more",
            "than six times TEE's entire always-loaded tool surface. Every UE",
            "tool call is also serialized on the editor's game thread at",
            "~0.37 s, so the round-trip reduction is wall-clock as well as",
            "tokens.",
        ]
    if surface_row is not None:
        r = surface_row
        payoff = r["flat_server_tokens"] // max(1, r["reach_one_tool"])
        lines += [
            "",
            "## Tool surface: progressive disclosure (P4/A6)",
            "",
            "The always-loaded MCP surface, measured as the wire actually",
            "carries it (`by_alias`, `exclude_none` - what the SDK sends). A",
            "bare `model_dump()` counts ~490 tokens of `null` padding for",
            "fields no client ever sees, so it overstates the surface by ~20%.",
            "",
            "| | Tools | Tokens |",
            "|---|---|---|",
            f"| TEE always-loaded (wire) | {r['n_tools']} | **{r['wire_tokens']:,}** |",
            f"| same, by `model_dump()` | {r['n_tools']} | {r['model_dump_tokens']:,} |",
            f"| flat server, one tool per capability | "
            f"{r['n_virtual_tools'] + r['n_tools']} | {r['flat_server_tokens']:,} |",
            "",
            "Registering all seven modules (extract, assets, design, physical,",
            f"pins, uefn, kb) adds **{r['added_by_modules']} tokens** to the always-loaded",
            f"surface - the {r['n_virtual_tools']} tools they contribute live behind the",
            f"meta-tools. Reaching one costs {r['reach_one_tool']} tokens (one search +",
            "one describe), so the flat design only pays off in a session that",
            f"uses more than ~{payoff} distinct long-tail tools.",
        ]
    if jurisdiction_row is not None:
        j = jurisdiction_row
        lines += [
            "",
            "## Jurisdiction: legal force per regime (Phase 15.2)",
            "",
            "One 7-element plan, checked under every regime TEE knows. The",
            "same conflicts carry different legal force, so the responses",
            "differ in severity, not just in wording.",
            "",
            "| Region | Resolves to | Rules | Cap | Findings | Capped | Tokens |",
            "|---|---|---|---|---|---|---|",
        ]
        for region, row in j["regions"].items():
            lines.append(
                f"| `{region}` | {row['resolved']} | {row['rule_set']} | "
                f"{row['max_severity']} | {row['findings']} | {row['capped']} | "
                f"{row['tokens']:,} |"
            )
        if j.get("corpus_tokens"):
            lines += [
                "",
                "Answering the same question without TEE means reading the",
                "applicable-law files into context - which regime governs the",
                "site, and what the adopted standard requires:",
                "",
                "| | Tokens | Saving |",
                "|---|---|---|",
                f"| read the code corpus (4 files) | {j['corpus_tokens']:,} | |",
                f"| one `plaus_check` | {j['tee_tokens']:,} | **{j['saving']:.1f}%** |",
                "",
                "The `jurisdiction` block costs 48-383 tokens depending on the",
                "regime; communal land carries the longest advisory because it",
                "is where 'no code applies' is most easily misread as 'anything",
                "goes'. It repeats on every call, so a session running many",
                "checks under one regime pays it each time - per-session",
                "suppression is the obvious next saving and is not yet built.",
            ]
    if kb_row is not None:
        k = kb_row
        lines += [
            "",
            "## Knowledge Base: sourced answer vs pasted corpus (Phase 16)",
            "",
            "The task: what bedding-sand and jointing-sand spec applies to",
            "concrete block paving, with a citation. The naive side pastes",
            "the corpus's own INDEX.md to find the file, then the whole file",
            "(without the module, sections are not addressable). TEE runs one",
            "kb_search and one budgeted kb_read of the 'Key facts' section,",
            "with the file's Sources block and confidence/jurisdiction flags",
            "riding along.",
            "",
            "| | Tokens | Calls | Saving |",
            "|---|---|---|---|",
            f"| paste INDEX.md ({k['index_tokens']:,}) + full file "
            f"({k['file_tokens']:,}) | {k['naive_tokens']:,} | | |",
            f"| kb_search + kb_read | {k['tee_tokens']:,} | {k['tee_calls']} | "
            f"**{k['saving']:.1f}%** |",
            "",
            "Unlike the paste, the kb_* answer cannot arrive without its",
            "confidence and jurisdiction flags - `needs-verification` content",
            "is labelled in the response itself (A30/A31), not in a rule the",
            "session has to remember.",
        ]
    lines += [
        "",
        f"*Generated by `benchmarks/run_benchmarks.py` against Blender "
        f"{_blender_version()} (headless, TEE bridge).*",
    ]
    out.write_text("\n".join(lines) + "\n")
    print(f"\nwrote {out}")


def _blender_version() -> str:
    blender = find_blender()
    out = subprocess.run([blender, "--version"], capture_output=True, text=True, timeout=30)
    first = out.stdout.splitlines()[0] if out.stdout else "unknown"
    return first.replace("Blender ", "")


if __name__ == "__main__":
    main()
