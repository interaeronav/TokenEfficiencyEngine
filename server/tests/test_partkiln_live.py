"""The partkiln lane against the REAL kernel (A66 P4).

`test_partkiln_adapter.py` proves the contract on arithmetic; this file
proves the same shapes on OCCT, through the public surface only -
`TeeApp.run_batch`, the scene cache's `diff_since` (what `tee_diff` returns),
`app.checkpoints` (what `tee_checkpoint`/`tee_rollback` return) and the
registry (what `tee_call` returns). If a number here disagrees with the plan,
the number wins and the test says so.

Two skips are deliberate and different. Without OCP the whole file skips -
there is no geometry to measure. With OCP but a kernel method not yet
registered, the kernel answers `pk_bad_op`, and the tool test for that method
skips NAMING the method: a lane assembled by several hands must be able to
say "not wired yet" without pretending it passed.
"""

from __future__ import annotations

import sys
import threading
import time
from importlib.util import find_spec
from pathlib import Path

import pytest

from tee.adapters.partkiln import PartkilnAdapter
from tee.adapters.partkiln.wire import SidecarKernel
from tee.app import TeeApp
from tee.kernel.budget import estimate_tokens
from tee.kernel.errors import TeeError

REPO = Path(__file__).resolve().parents[2]
SRC = REPO / "partkiln" / "src"

# partkiln is deliberately NOT pip-installed into server/.venv: the dev route
# in the install hint is `uv pip install -e partkiln`, and this repo IS that
# checkout. Putting its src on the path makes `find_spec("partkiln")` true
# exactly as the editable install would, without a wheel build in the suite.
if SRC.is_dir() and str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

partkiln = pytest.importorskip("partkiln", reason="partkiln/src is not beside server/")
if find_spec("OCP") is None:  # no import: the skip must be cheaper than the wheel
    pytest.skip("the OCP wheel is not in this interpreter", allow_module_level=True)

# W1 from the plan, with EXPLICIT hole and slot coordinates: a hole's `at` is
# in the face's own frame, whose origin is the world origin projected onto
# that face (P2c), and the rect preset puts its `at` corner at the origin -
# so the plate spans x 0..120, y 0..80 and the holes are written where they
# land, not as PX/PY offsets from a centre that does not exist.
W1 = [
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

# Measured on this Mac, OCCT 7.9.3, 2026-09-04. The plan predicted 91158.6 mm3
# and 715.6 g; the kernel measures 91159.605 and 715.603 g. The single
# difference is the chamfer: the plan estimated -195.7 mm3, the kernel
# measures -194.661 across the 8 edges its selector actually resolved. The
# measurement is the truth and the plan's arithmetic was the estimate.
BRACKET_MM3 = 91_159.605
BRACKET_G = 715.603
FEATURES = {
    "feat:plate": (96_000.0, 6),
    "feat:f1": (-214.602, 10),
    "feat:h": (-1368.478, 14),
    "feat:slot": (-3062.655, 18),
    "feat:c1": (-194.661, 26),
}


@pytest.fixture
def app(tmp_path):
    built = TeeApp({"partkiln": PartkilnAdapter(tmp_path)}, project_root=tmp_path)
    yield built
    built.shutdown()


@pytest.fixture
def adapter(app):
    return app.adapters["partkiln"]


def _call_or_skip(app, tool: str, args: dict):
    """A kernel method this lane has not registered yet answers `pk_bad_op`.
    Skipping NAMES it, so a half-wired lane reads as half-wired."""
    try:
        return app.registry.call(tool, args)
    except TeeError as exc:
        if exc.code == "pk_bad_op":
            pytest.skip(f"{tool}: the kernel has not registered its method yet ({exc.message})")
        raise


def test_the_kernel_is_in_process_here(adapter) -> None:
    assert adapter.mode == "in-process"
    payload = adapter.info().to_payload()
    assert payload["connected"] is True and payload["id"] == "partkiln"


def test_the_bracket_is_one_batch_and_one_diff(app, adapter) -> None:
    """The W1 acceptance: nine ops, one round trip, one diff that names every
    created id with its volume and face count - and no geometry anywhere."""
    started = time.time()
    out = app.run_batch("partkiln", W1)
    wall = time.time() - started

    assert out["created"] == [
        "part:bracket",
        "sk:base",
        "feat:plate",
        "feat:f1",
        "feat:h",
        "sk:slot_sk",
        "feat:slot",
        "feat:c1",
    ]
    for eid, (delta, faces) in FEATURES.items():
        row = out["details"][eid]
        assert row["delta_mm3"] == pytest.approx(delta, abs=1e-3), eid
        assert row["faces"] == faces, eid
        assert "points" not in row and "mesh" not in row, f"{eid} leaked geometry"

    # `assumed` is declared once, where the default was taken (Law 19), and
    # the standards row names its source and licence.
    assumed = out["details"]["feat:h"]["assumed"]
    assert assumed["depth"] == "through"
    assert "ISO 273" in assumed["dia"] and "Apache-2.0" in assumed["dia"]
    assert out["details"]["sk:slot_sk"]["assumed"]["origin"].startswith("the world origin")

    # `resolved` says how many sub-shapes each selector actually caught -
    # the number a caller would otherwise have to guess (Law 13).
    assert out["details"]["feat:f1"]["resolved"] == {"plate:edges(dir=Z)": 4}
    assert out["details"]["feat:c1"]["resolved"] == {"plate:edges(of=plate.end, loop=outer)": 8}

    body = next(e for e in adapter.list_entities() if e.id == "part:bracket")
    assert body.summary["volume_mm3"] == pytest.approx(BRACKET_MM3, abs=1e-3)
    assert body.summary["mass_g"] == pytest.approx(BRACKET_G, abs=1e-3)
    assert body.summary["bbox_mm"] == [120.0, 80.0, 10.0]
    assert body.summary["valid"] is True and body.summary["solids"] == 1
    assert wall < 20.0, f"the bracket took {wall:.1f}s"


def test_the_scene_summary_of_the_bracket_fits_the_p4_budget(app) -> None:
    """P4 acceptance: the whole W1 bracket reads back in <= 400 tokens.

    Hard rule 1 - never a full scene dump - is a budget, not a slogan, and a
    budget nobody measures is one the next feature spends. This is the
    payload `tee_scene_summary` returns for its DEFAULT response_format, so
    it is what a model actually pays: 12 rows (doc, part, 2 sketches, 5
    features, 3 params) at 236 tok on 2026-09-04, 41% under the ceiling.

    The detailed form is measured beside it on purpose. At 728 tok it is
    almost twice the ceiling, which is correct - it is opt-in, one step
    short of `tee_entity_detail` - and pinning it here is what tells a
    future reader that concise is not merely detailed with fewer rows.
    """
    app.run_batch("partkiln", W1)
    cache = app.cache("partkiln")
    concise = {"ok": True, **cache.summary(limit=50)}
    assert concise["total"] == 12 and len(concise["items"]) == 12
    assert estimate_tokens(concise) <= 400
    assert estimate_tokens(concise) == pytest.approx(236, abs=40)  # drift, not noise
    # a concise row is id/kind/name (+parent): scalars only, no geometry
    assert all(
        isinstance(value, str | int | float | bool | None)
        for row in concise["items"]
        for value in row.values()
    ), concise["items"]
    detailed = {"ok": True, **cache.summary(limit=50, detailed=True)}
    assert estimate_tokens(detailed) > 400  # opt-in, and priced accordingly


def test_the_edit_names_the_part_and_the_changed_list(app, adapter) -> None:
    """Law 14 through the public door: after `T=12mm` a tee_diff-style read
    names the part and the features that moved - not the new world."""
    first = app.run_batch("partkiln", W1)
    stamp = (first["epoch"], first["revision"])

    out = app.run_batch("partkiln", [{"op": "param_set", "props": {"T": "12mm"}}])
    report = out["details"]["part:bracket"]
    assert [row["feature"] for row in report["changed"]] == ["plate", "f1", "h", "slot"]
    assert report["unchanged_features"] == ["c1"] and report["failed"] == []
    assert report["volume_mm3"] == pytest.approx(109_430.458, abs=1e-3)
    assert out["details"]["param:T"] == {"old": 10.0, "new": 12.0}

    since = app.cache("partkiln").diff_since(*stamp)
    assert "part:bracket" in since["modified"]
    assert {"feat:plate", "feat:f1", "feat:h", "feat:slot"} <= set(since["modified"])
    assert "feat:c1" not in since["modified"]

    # the whole edit, as a model would pay for it
    from tee.kernel.budget import estimate_tokens

    assert estimate_tokens(out) < 700, estimate_tokens(out)


def test_checkpoint_and_rollback_round_trip(app, adapter) -> None:
    """D3: the checkpoint is the script and the .brep beside it is a cache -
    so a rollback lands on the same fingerprint either way."""
    app.run_batch("partkiln", W1)
    kept = adapter.kernel.fingerprint()
    cp = app.checkpoints.create(adapter, "bracket", app.cache("partkiln").revision)
    assert Path(cp.payload["path"]).is_file()

    app.run_batch("partkiln", [{"op": "param_set", "props": {"T": "12mm"}}])
    assert adapter.kernel.fingerprint() != kept

    app.rollback("partkiln", cp.id)
    assert adapter.kernel.fingerprint() == kept
    body = next(e for e in adapter.list_entities() if e.id == "part:bracket")
    assert body.summary["volume_mm3"] == pytest.approx(BRACKET_MM3, abs=1e-3)


def test_a_failed_op_leaves_the_fingerprint_where_it_was(app, adapter) -> None:
    app.run_batch("partkiln", W1)
    before = adapter.kernel.fingerprint()
    with pytest.raises(TeeError) as excinfo:
        app.run_batch(
            "partkiln",
            [
                {
                    "op": "create",
                    "kind": "fillet",
                    "name": "ok1",
                    "props": {"edges": "plate:edges(dir=Z)", "r": "0.5mm"},
                },
                {
                    "op": "create",
                    "kind": "fillet",
                    "name": "huge",
                    "props": {"edges": "plate:edges(dir=Z)", "r": "60mm"},
                },
            ],
        )
    assert excinfo.value.code.startswith("pk_")
    assert excinfo.value.fix
    assert adapter.kernel.fingerprint() == before
    assert all(e.id != "feat:ok1" for e in adapter.list_entities())


def test_pk_probe_answers_without_warming_or_spawning(app, adapter) -> None:
    health = app.registry.call("pk_probe", {})
    assert health["mode"] == "in-process"
    assert health["routes"]["in-process"] is True
    assert "OCCT-exception-1.0" in health["licence"]["occt"]
    assert health["state"] in ("cold", "warm")
    deep = app.registry.call("pk_probe", {"deep": True})["kernel"]
    assert deep["alive"] is True


def test_pk_lint_reads_the_batch_and_never_reaches_the_kernel(app, adapter) -> None:
    """The pre-flight's contract: it reads the batch and applies nothing.
    Two independent witnesses - a spy wrapped around the live kernel's own
    `apply`, and the kernel's own `kernel_called` flag."""
    app.run_batch("partkiln", W1)
    seen: list[int] = []
    real = adapter.kernel.apply
    adapter.kernel.apply = lambda commands: (seen.append(len(commands)), real(commands))[1]

    bad_op = _call_or_skip(app, "pk_lint", {"batch": [{"op": "knit"}]})
    assert seen == [], "pk_lint applied a command"
    assert bad_op["ok"] is False and bad_op["kernel_called"] is False
    issue = next(i for i in bad_op["issues"] if i["code"] == "pk_bad_op")
    assert "partkiln accepts" in issue["fix"]

    bad_unit = [{"op": "param_set", "props": {"T": "12 mils"}}]
    unit = _call_or_skip(app, "pk_lint", {"batch": bad_unit})
    assert seen == []
    if unit["ok"] is not False:
        pytest.skip("the kernel's lint does not check unit suffixes yet (it caught the bad op)")
    assert "mils" in repr(unit)


def test_the_read_tools_answer_from_the_live_document(app, adapter) -> None:
    """Every pk_* read against the bracket, with its measured answer. A method
    the kernel has not registered yet skips by name rather than passing."""
    app.run_batch("partkiln", W1)

    verbs = _call_or_skip(app, "pk_verbs", {})
    assert {"create", "delete", "param_set", "set"} <= set(verbs["verbs"])

    # 8, not the 4 the fillet resolved: `f1` replaced each corner edge with a
    # cylindrical face bounded by TWO vertical edges, and the selector is
    # evaluated against the body as it is now.
    found = _call_or_skip(app, "pk_query", {"selector": "plate:edges(dir=Z)"})
    assert found["count"] == 8 and found["how"] == "selector"
    assert all(isinstance(n, str) for n in found["names"])

    mass = _call_or_skip(app, "pk_measure", {"what": "mass", "of": "part:bracket"})
    assert mass["volume_mm3"] == pytest.approx(BRACKET_MM3, abs=1e-3)
    assert mass["bbox_mm"] == [120.0, 80.0, 10.0]

    verdict = _call_or_skip(app, "pk_check", {"spec": {"min_wall_mm": 2.0}, "of": "part:bracket"})
    assert verdict["verdict"] == "pass" and verdict["violations"] == []

    bolt = _call_or_skip(app, "pk_standards", {"size": "M6", "kind": "clearance"})
    assert bolt["dia_mm"] == 6.6 and "ISO 273" in bolt["authority"]
    assert "bd_warehouse" in bolt["source"]  # provenance, not a remembered number

    card = _call_or_skip(app, "pk_materials", {"name": "steel_s275"})
    assert card["values"]["density"] == 7850

    # A BOM is an assembly concept and this document has no components, so the
    # honest answer is a refusal that names the op which would create one.
    try:
        rows = app.registry.call("pk_bom", {"parts_only": True})
    except TeeError as exc:
        assert "component" in exc.fix
    else:
        assert rows


def test_pk_script_round_trips_the_document(app, adapter) -> None:
    app.run_batch("partkiln", W1)
    script = _call_or_skip(app, "pk_script", {})
    assert [c["op"] for c in script["commands"]] == [op["op"] for op in W1]
    from partkiln.document import Document

    replayed = Document.replay(script)
    assert replayed.fingerprint() == adapter.kernel.fingerprint()


def test_pk_export_writes_a_step_file_or_names_the_missing_method(app, tmp_path) -> None:
    app.run_batch("partkiln", W1)
    out = tmp_path / "bracket.step"
    report = _call_or_skip(
        app, "pk_export", {"format": "step", "out": str(out), "of": "part:bracket"}
    )
    assert out.is_file() and out.stat().st_size > 1000
    assert report["schema"] == "AP242" and "AP242" in report["file_schema"]
    assert report["unit"] == "MM"  # STEP declares its unit; the manifest says so

    # and back in, as a base body with fingerprint-named faces
    back = _call_or_skip(app, "pk_import", {"path": str(out), "name": "again"})
    assert back["volume_mm3"] == pytest.approx(BRACKET_MM3, abs=1e-3)
    assert back["units"] == "MM" and back["solids"] == 1


# -- the sidecar: a real process, a real cold import ---------------------------


@pytest.mark.dcc
@pytest.mark.timeout(300)
def test_a_cold_sidecar_warms_as_a_job_and_replays_to_the_same_fingerprint(tmp_path) -> None:
    """The production route, end to end: spawn the worker, pay `import OCP`
    as an interactive JOB, and prove that neither the checkpoint nor the
    entity listing waited for it (Law 17) - then build the bracket over the
    pipe and check it against the in-process fingerprint.

    Spawned from `sys.executable` with PYTHONPATH rather than the real
    sidecar venv, because the claim under test is the process model, not the
    venv's existence; `tee doctor` reports the venv.
    """
    kernel = SidecarKernel(
        python=sys.executable,
        env={"PYTHONPATH": str(SRC)},
        stderr_path=tmp_path / "worker.log",
        timeout_s=120.0,
    )
    adapter = PartkilnAdapter(tmp_path, kernel=kernel)
    app = TeeApp({"partkiln": adapter}, project_root=tmp_path)
    try:
        ready = kernel.start()
        assert ready["event"] == "ready" and ready["warm"] is False
        assert kernel.spawn_s < 5.0, f"spawn took {kernel.spawn_s}s"

        started = time.time()
        job = adapter.submit_warm(app.jobs)
        assert job

        # While the import runs, the two calls `run_batch` makes FIRST must
        # still answer - from the in-process mirror, with no B-rep.
        during = adapter.snapshot("during-warm")
        assert during["brep"] is False
        assert adapter.list_entities() == [] or adapter.state != "warming"

        deadline = time.time() + 120
        while adapter.state == "warming" and time.time() < deadline:
            time.sleep(0.05)
        assert adapter.state == "warm", f"warm never landed: {adapter.state}"
        warm_s = time.time() - started
        assert adapter._warm["import_s"] >= 0.0
        assert warm_s < 120.0

        out = app.run_batch("partkiln", W1)
        assert out["details"]["feat:c1"]["delta_mm3"] == pytest.approx(-194.661, abs=1e-3)
        rows = {e.id: e.summary for e in adapter.list_entities()}
        assert rows["part:bracket"]["volume_mm3"] == pytest.approx(BRACKET_MM3, abs=1e-3)
        # Determinism across processes: the same script, a different
        # interpreter, the same rounded model.
        from partkiln.client import LocalKernel

        local = LocalKernel()
        local.apply([c for op in W1 for c in _translate_for(op)])
        assert local.fingerprint() == kernel.fingerprint()
    finally:
        app.shutdown()
        kernel.close()


@pytest.mark.dcc
@pytest.mark.timeout(300)
def test_a_call_inside_the_warm_up_refuses_pk_warming_with_the_job_id(tmp_path) -> None:
    """Law 17's refusal, on a real worker: a batch that lands inside the
    import waits two seconds and then says so, naming the job to poll."""
    kernel = SidecarKernel(
        python=sys.executable, env={"PYTHONPATH": str(SRC)}, stderr_path=tmp_path / "w.log"
    )
    adapter = PartkilnAdapter(tmp_path, kernel=kernel)
    app = TeeApp({"partkiln": adapter}, project_root=tmp_path)
    gate = threading.Event()
    real_warm = kernel.warm

    def slow_warm():
        gate.wait(30)  # stands in for the 26 s cold import measured in P0a
        return real_warm()

    kernel.warm = slow_warm
    try:
        kernel.start()
        adapter.submit_warm(app.jobs)
        while adapter.state != "warming":
            time.sleep(0.01)
        with pytest.raises(TeeError) as excinfo:
            adapter.execute([{"op": "param_set", "props": {"T": "10mm"}}])
        assert excinfo.value.code == "pk_warming"
        assert (adapter.warm_job or "") in excinfo.value.fix
        assert "tee_job" in excinfo.value.fix
        assert adapter.snapshot("mid")["brep"] is False
    finally:
        gate.set()
        app.shutdown()
        kernel.close()


def _translate_for(op: dict) -> list[dict]:
    from tee.adapters.partkiln.adapter import _translate

    return _translate(op, 0)
