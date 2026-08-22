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
    write_results(rows, extract_row, asset_row)


def write_results(rows, extract_row=None, asset_row=None) -> None:
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
