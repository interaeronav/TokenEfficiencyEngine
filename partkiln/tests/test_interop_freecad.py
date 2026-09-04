"""Gap 10: a SECOND OCCT reads the STEP we wrote, and says the same numbers.

`pk_export`'s own round trip and `cad_measure` both re-read our STEP through the
*same* `cadquery-ocp-novtk` wheel (OCCT 7.9.3). That proves the file parses; it
cannot prove the file is right, because a writer and a reader that share a build
share its bugs. FreeCAD 1.1.3 on this machine embeds **OCCT 7.8.1** (recorded in
`docs/research/68-evidence/W1-licences.md:104`) - a genuinely different kernel
build, with its own STEP translator and its own `BRepGProp` - so its answer is
independent evidence.

Independence has to be *paid for*, not asserted: this file drives FreeCAD's own
bundled interpreter as a **subprocess**, and imports nothing of FreeCAD's into
the test process. That is also the only posture the licence audit allows -
`W1-licences.md:33` files `/Applications/FreeCAD.app` as OUT-OF-PROCESS because
the .app ships GPL binaries (gmsh, CalculiX) beside the LGPL library. partkiln
gains no dependency on FreeCAD from this file; without FreeCAD the tests skip
and say, in words, that gap 10 is unverified on this machine.

Doc 68 records that `freecadcmd` *crashed* on the headless sketch + TechDraw
probe, so FreeCAD is not the kernel. Reading a STEP and integrating its volume
is a far smaller ask than TechDraw, and it is the only ask made here: measured
2026-09-04, the bundled interpreter reads the W1 bracket and reports its mass
properties in 0.15 s, cold, with no crash and no GUI.
"""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path
from typing import Any

import pytest

pytest.importorskip("OCP", reason="partkiln[brep] not installed")

pytestmark = [pytest.mark.brep, pytest.mark.dcc]

# Where a second OCCT lives, and how to point at another one. The .app path is
# the measured location on this machine; the variable is the escape hatch for a
# Linux/conda FreeCAD whose interpreter is somewhere else entirely.
FREECAD_PYTHON_ENV = "PARTKILN_FREECAD_PYTHON"
FREECAD_APP_PYTHON = Path("/Applications/FreeCAD.app/Contents/Resources/bin/python")

# The child's boot is 0.15 s measured; this only has to catch a hang.
CHILD_TIMEOUT_S = 120.0

# -- tolerances, and why they are these numbers --------------------------------
#
# Measured 2026-09-04, kernel OCCT 7.9.3 vs FreeCAD's OCCT 7.8.1, on the four
# fixtures below: volume agreed to a relative 4.6e-15 (bracket), 8.6e-15 (F2),
# 2.0e-14 (F3) and 5.2e-16 (pair); bbox edge lengths to 6.5e-13 mm at worst.
# That is double-precision Gauss quadrature over the same B-rep, and nothing
# more. The gates below sit ~5x10^4 above the worst measured disagreement, so a
# recompiled OCCT that quadratures slightly differently does not cry wolf - and
# they are still five to nine orders of magnitude tighter than any disagreement
# that would *matter*: a dropped fillet on the bracket is 4.3e-3 relative, a
# lost hole 3.7e-3, a millimetre/centimetre unit slip 1e3.
VOLUME_REL_TOL = 1e-9
BBOX_ABS_TOL_MM = 1e-6
# The published `pk_measure` number is rounded to three decimals, so comparing
# it to a raw double needs half of the last printed digit and nothing more.
PUBLISHED_ABS_TOL_MM3 = 5e-4

# Counts get NO tolerance. Faces and solids are unique sub-shapes (Law 20) -
# integers, either equal or a real topological disagreement.

# The child script. Two forms share a prelude, and the prelude carries the one
# piece of FreeCAD lore this file needs: the .app's bundled `python` does not
# put FreeCAD's own extension modules on `sys.path` - they sit in
# `Contents/Resources/lib`, the sibling of the interpreter's `bin/`.
_PRELUDE = """
import json, pathlib, sys
try:
    import FreeCAD, Part
except ModuleNotFoundError:
    sys.path.insert(0, str(pathlib.Path(sys.executable).resolve().parents[1] / "lib"))
    import FreeCAD, Part
"""

_VERSION_SCRIPT = (
    _PRELUDE
    + """
print(json.dumps({"occt": Part.OCC_VERSION, "freecad": ".".join(FreeCAD.Version()[:3])}))
"""
)

# `Part.Shape.read` is FreeCAD's plain STEP/IGES/BREP reader: no document, no
# GUI, no TechDraw. `Volume`, `BoundBox`, `Solids` and `Faces` are FreeCAD's
# own OCCT talking, not ours.
_READ_SCRIPT = (
    _PRELUDE
    + """
shape = Part.Shape()
shape.read(sys.argv[1])
box = shape.BoundBox
print(json.dumps({
    "occt": Part.OCC_VERSION,
    "volume_mm3": shape.Volume,
    "bbox_mm": [box.XLength, box.YLength, box.ZLength],
    "solids": len(shape.Solids),
    "faces": len(shape.Faces),
    "valid": shape.isValid(),
}))
"""
)


def _candidates() -> list[tuple[str, Path]]:
    """Every route to a second OCCT, in order, each with the name of its route.

    The route name is carried so a skip can say which one it looked down: "the
    variable you set points nowhere" and "you have no FreeCAD" are different
    problems with different fixes.
    """
    override = os.environ.get(FREECAD_PYTHON_ENV)
    if override:
        return [(f"${FREECAD_PYTHON_ENV}", Path(override))]
    return [("the macOS app bundle", FREECAD_APP_PYTHON)]


def _absent_reason(tried: list[tuple[str, Path]]) -> str:
    """The words a machine with no FreeCAD prints. Named so a test can read it."""
    where = "; ".join(f"{route} -> {path}" for route, path in tried)
    return (
        f"gap 10 UNVERIFIED here: no second OCCT to read our STEP. No interpreter found "
        f"({where}), so nothing but the kernel's own OCCT {_kernel_occt()} has ever read "
        f"this file - a second reader, not a second kernel. Install FreeCAD 1.1+, or set "
        f"${FREECAD_PYTHON_ENV} to a python that can `import FreeCAD, Part`."
    )


def _run(python: Path, script: str, *args: str) -> subprocess.CompletedProcess[str]:
    # A local interpreter, a local path, no shell, and cwd=/ so a stray relative
    # path in FreeCAD's own start-up cannot pick anything out of the repo.
    return subprocess.run(
        [str(python), "-c", script, *args],
        capture_output=True,
        text=True,
        timeout=CHILD_TIMEOUT_S,
        cwd="/",
    )


def _payload(done: subprocess.CompletedProcess[str]) -> dict[str, Any]:
    """The last JSON line of stdout; FreeCAD is free to chatter around it."""
    for line in reversed(done.stdout.splitlines()):
        if line.startswith("{"):
            return json.loads(line)
    raise AssertionError(f"no JSON on stdout.\nstdout:\n{done.stdout}\nstderr:\n{done.stderr}")


@pytest.fixture(scope="module")
def freecad() -> dict[str, Any]:
    """A second OCCT, or a skip that says exactly what is missing and why.

    A missing FreeCAD skips; a FreeCAD that is present but cannot `import
    FreeCAD, Part` also skips, carrying the child's stderr **verbatim** - the
    outcome doc 68 warns about is a real possibility, and a paraphrased crash
    is not evidence of anything.
    """
    tried = _candidates()
    found = [path for _route, path in tried if path.exists()]
    if not found:
        pytest.skip(_absent_reason(tried))
    python = found[0]
    try:
        done = _run(python, _VERSION_SCRIPT)
    except (OSError, subprocess.TimeoutExpired) as exc:  # not executable, or hung
        pytest.skip(f"gap 10 UNVERIFIED here: {python} would not run: {exc!r}")
    if done.returncode != 0:
        pytest.skip(
            f"gap 10 UNVERIFIED here: {python} cannot import FreeCAD headlessly "
            f"(exit {done.returncode}). Its error, verbatim:\n{done.stderr.strip()}"
        )
    return {"python": python, **_payload(done)}


def _kernel_occt() -> str:
    from partkiln.client import occt_version

    return occt_version() or "unknown"


# -- the fixtures we ask it to read --------------------------------------------
#
# Built here, from partkiln's own verbs, into pytest's tmp dir - never from
# another agent's output directory. W1 is the bracket the campaign pins
# (91,159.605 mm3, bbox [120, 80, 10]); F2 and F3 are the document-level
# fixtures with a concave fillet and a revolve + cosmetic thread; `pair` is two
# parts in one file, so `solids` is not the constant 1 in every row.


def _pair_ops() -> list[dict[str, Any]]:
    """Two independent parts in one document -> a two-product STEP."""
    ops: list[dict[str, Any]] = []
    for name, (w, h, t) in (("plate_a", (40, 30, 10)), ("plate_b", (20, 20, 20))):
        ops += [
            {"op": "create", "kind": "part", "name": name},
            {
                "op": "create",
                "kind": "sketch",
                "name": f"sk_{name}",
                "props": {
                    "plane": "XY",
                    "profile": [{"rect": [w, h], "tag": "r"}],
                    "part": name,
                },
            },
            {
                "op": "create",
                "kind": "extrude",
                "name": f"ex_{name}",
                "props": {"sketch": f"sk_{name}", "distance": t, "part": name},
            },
            {
                "op": "create",
                "kind": "hole",
                "name": f"h_{name}",
                "props": {"on": f"ex_{name}.end", "at": [[w / 2, h / 2]], "dia": 6, "part": name},
            },
        ]
    return ops


def _fixture_scripts() -> dict[str, tuple[list[dict[str, Any]], str]]:
    """name -> (ops, the `of` the export and the measures take)."""
    import sys

    root = Path(__file__).resolve().parents[1]
    if str(root) not in sys.path:  # `examples/` sits beside `src/`, per test_examples.py
        sys.path.insert(0, str(root))
    from test_document_parts import F2, F3

    from examples.bracket.model import OPS as BRACKET_OPS

    return {
        "bracket": (list(BRACKET_OPS), "bracket"),
        "F2": (F2(), "bracket"),
        "F3": (F3(), "shaft"),
        "pair": (_pair_ops(), "all"),
    }


@pytest.fixture(scope="module")
def exported(tmp_path_factory: pytest.TempPathFactory) -> dict[str, dict[str, Any]]:
    """Build, export, and record what OUR kernel says - raw and as published."""
    from partkiln.brep import shapes
    from partkiln.client import LocalKernel

    out_dir = tmp_path_factory.mktemp("gap10_step")
    built: dict[str, dict[str, Any]] = {}
    for name, (ops, of) in _fixture_scripts().items():
        kernel = LocalKernel()
        kernel.apply(ops)
        path = out_dir / f"{name}.step"
        export = kernel.call(
            "export", {"format": "step", "of": of, "out": str(path), "schema": "AP242"}
        )
        mass = kernel.call("measure", {"of": of, "what": "mass"})
        bodies = kernel.call("measure", {"of": of, "what": "faces"})["bodies"]
        # Raw doubles beside the published 3-decimal numbers: the tolerance on
        # a rounded number is a rounding tolerance, not a kernel tolerance.
        parts = kernel.document.parts
        raw = [shapes.volume(parts[row["of"]].shape) for row in bodies]
        box = shapes.bbox(
            parts[bodies[0]["of"]].shape
            if len(bodies) == 1
            else _compound([parts[row["of"]].shape for row in bodies])
        )
        built[name] = {
            "path": path,
            "products": export["products"],
            "unit": export["unit"],
            "published_volume_mm3": mass["volume_mm3"],
            "published_bbox_mm": mass["bbox_mm"],
            "volume_mm3": sum(raw),
            "bbox_mm": [box[3] - box[0], box[4] - box[1], box[5] - box[2]],
            "faces": sum(row["faces"] for row in bodies),
            "solids": sum(row["solids"] for row in bodies),
        }
    return built


def _compound(shapes_in: list[Any]) -> Any:
    from OCP.BRep import BRep_Builder
    from OCP.TopoDS import TopoDS_Compound

    compound = TopoDS_Compound()
    builder = BRep_Builder()
    builder.MakeCompound(compound)
    for shape in shapes_in:
        builder.Add(compound, shape)
    return compound


@pytest.fixture(scope="module")
def second_kernel(
    freecad: dict[str, Any], exported: dict[str, dict[str, Any]]
) -> dict[str, dict[str, Any]]:
    """One subprocess per file: what FreeCAD's OCCT makes of what we wrote."""
    read: dict[str, dict[str, Any]] = {}
    for name, ours in exported.items():
        done = _run(freecad["python"], _READ_SCRIPT, str(ours["path"]))
        assert done.returncode == 0, (
            f"FreeCAD's OCCT {freecad['occt']} could not read our {name}.step "
            f"(exit {done.returncode}). Its error, verbatim:\n{done.stderr.strip()}"
        )
        read[name] = _payload(done)
    return read


FIXTURES = ("bracket", "F2", "F3", "pair")


def test_a_machine_without_freecad_is_told_what_is_missing_and_how_to_fix_it() -> None:
    """The skip wording, checked on a machine that HAS FreeCAD.

    A skip message nobody reads until the one day it appears is a message
    nobody has read. This exercises `_absent_reason` directly - it takes no
    subprocess and no FreeCAD - so the words are pinned everywhere.
    """
    reason = _absent_reason([("the macOS app bundle", FREECAD_APP_PYTHON)])
    assert "gap 10 UNVERIFIED here" in reason
    assert str(FREECAD_APP_PYTHON) in reason
    assert FREECAD_PYTHON_ENV in reason
    assert "a second reader, not a second kernel" in reason
    assert _kernel_occt() in reason  # names the ONE kernel that has read it


def test_the_second_reader_is_a_second_kernel(freecad: dict[str, Any]) -> None:
    """The whole point: a DIFFERENT OCCT build, not another copy of ours.

    If this ever fails, the cross-read below is still a second *reader* and
    still worth running - but it stops being the independent evidence gap 10
    asks for, and PROGRESS must stop claiming it is.
    """
    ours = _kernel_occt()
    theirs = freecad["occt"]
    assert theirs != ours, (
        f"FreeCAD {freecad['freecad']} now embeds OCCT {theirs}, the same build the kernel "
        f"uses ({ours}). A second reader on the same kernel is not independent evidence: "
        f"point ${FREECAD_PYTHON_ENV} at a FreeCAD with a different OCCT, or reopen gap 10."
    )


@pytest.mark.parametrize("name", FIXTURES)
def test_second_occt_agrees_on_volume_and_bbox(
    name: str, exported: dict[str, dict[str, Any]], second_kernel: dict[str, dict[str, Any]]
) -> None:
    """Volume and bbox, our OCCT 7.9.3 against FreeCAD's 7.8.1, at 1e-9 relative."""
    ours, theirs = exported[name], second_kernel[name]
    delta = abs(theirs["volume_mm3"] - ours["volume_mm3"])
    assert delta <= VOLUME_REL_TOL * ours["volume_mm3"], (
        f"{name}: volume disagrees across OCCT builds - ours {ours['volume_mm3']!r} mm3, "
        f"FreeCAD's {theirs['volume_mm3']!r} mm3, rel {delta / ours['volume_mm3']:.3e} "
        f"> {VOLUME_REL_TOL:.0e}. Do not widen this: at this size a disagreement is a "
        f"feature the STEP lost, not arithmetic."
    )
    for axis, mine, other in zip("XYZ", ours["bbox_mm"], theirs["bbox_mm"], strict=True):
        assert abs(mine - other) <= BBOX_ABS_TOL_MM, (
            f"{name}: bbox {axis} disagrees - ours {mine!r} mm, FreeCAD's {other!r} mm."
        )


@pytest.mark.parametrize("name", FIXTURES)
def test_second_occt_agrees_on_solid_and_face_counts(
    name: str, exported: dict[str, dict[str, Any]], second_kernel: dict[str, dict[str, Any]]
) -> None:
    """Counts are integers (Law 20): equal, or the topology really differs."""
    ours, theirs = exported[name], second_kernel[name]
    assert theirs["solids"] == ours["solids"], (
        f"{name}: solid count differs - ours {ours['solids']}, FreeCAD's {theirs['solids']} "
        f"(the STEP declares {ours['products']} product(s))."
    )
    assert theirs["faces"] == ours["faces"], (
        f"{name}: face count differs - ours {ours['faces']}, FreeCAD's {theirs['faces']}. "
        f"A second kernel splitting or merging a face is a real B-rep difference."
    )
    assert theirs["valid"], f"{name}: FreeCAD's OCCT calls our own STEP invalid."


@pytest.mark.parametrize("name", FIXTURES)
def test_published_numbers_are_what_the_second_kernel_rounds_to(
    name: str, exported: dict[str, dict[str, Any]], second_kernel: dict[str, dict[str, Any]]
) -> None:
    """The numbers PROGRESS prints are the numbers a second kernel reads back.

    Separate from the test above on purpose: that one compares raw doubles,
    this one compares what `pk_measure` actually *publishes* - three decimals -
    so nothing in the reporting path can drift without a failure here.
    """
    ours, theirs = exported[name], second_kernel[name]
    assert abs(theirs["volume_mm3"] - ours["published_volume_mm3"]) <= PUBLISHED_ABS_TOL_MM3, (
        f"{name}: pk_measure publishes {ours['published_volume_mm3']!r} mm3 but a second "
        f"OCCT reads {theirs['volume_mm3']!r} mm3."
    )
    for axis, mine, other in zip("XYZ", ours["published_bbox_mm"], theirs["bbox_mm"], strict=True):
        assert abs(mine - other) <= PUBLISHED_ABS_TOL_MM3, (
            f"{name}: pk_measure publishes bbox {axis} {mine!r} mm, second OCCT {other!r} mm."
        )


def test_the_pinned_bracket_numbers_survive_a_second_kernel(
    exported: dict[str, dict[str, Any]], second_kernel: dict[str, dict[str, Any]]
) -> None:
    """W1 by its campaign numbers, read by an OCCT that never wrote them."""
    theirs = second_kernel["bracket"]
    assert exported["bracket"]["published_volume_mm3"] == 91159.605
    assert exported["bracket"]["published_bbox_mm"] == [120.0, 80.0, 10.0]
    assert abs(theirs["volume_mm3"] - 91159.605) <= PUBLISHED_ABS_TOL_MM3
    assert [round(v, 3) for v in theirs["bbox_mm"]] == [120.0, 80.0, 10.0]
    assert (theirs["solids"], theirs["faces"]) == (1, 26)
