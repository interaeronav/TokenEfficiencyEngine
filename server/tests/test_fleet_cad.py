"""A45 P2e — parametric CAD.

The reference solid is hand-checkable: a 20x10x5 box minus a through
cylinder of radius r has volume 1000 - pi*r^2*5. Asserting that across
several radii proves three things at once - the build ran, the PARAMETER
actually reached the model, and the measurement is real geometry rather
than a triangle count.
"""

from __future__ import annotations

import math
import pathlib
import struct
import tempfile

import pytest

from tee.fleet import cad, probe
from tee.kernel.errors import TeeError

SRC = (
    "hole_r = 4;\n"
    "difference() {\n"
    "  cube([20, 10, 5], center = true);\n"
    "  cylinder(h = 20, r = hole_r, center = true, $fn = 256);\n"
    "}\n"
)

needs_openscad = pytest.mark.skipif(
    cad.openscad_bin() is None, reason="OpenSCAD not on PATH (brew install --cask openscad)"
)


# -- the security decision --------------------------------------------------


def test_d_flag_is_never_in_the_command_line():
    """OpenSCAD's -D prepends STATEMENTS, so a caller-supplied -D is code
    execution dressed as a parameter. It must not appear anywhere."""
    text = pathlib.Path(cad.__file__).read_text()
    assert '"-D"' not in text and "'-D'" not in text
    assert '"-p"' in text, "parameters go through the customizer JSON instead"


def test_parameter_names_that_look_like_code_are_refused(tmp_path):
    for bad in ("x=1; cube(99)", "a b", "1abc", "$fn", "include <evil.scad>"):
        with pytest.raises(TeeError) as e:
            cad._params_file({bad: 1}, tmp_path)
        assert e.value.code == "cad_bad_param", bad


def test_parameter_values_must_be_scalars(tmp_path):
    with pytest.raises(TeeError) as e:
        cad._params_file({"ok_name": {"nested": "object"}}, tmp_path)
    assert "must be a number, string, bool" in e.value.message


def test_a_valid_parameter_set_is_written_as_customizer_json(tmp_path):
    path = cad._params_file({"hole_r": 4, "label": "x", "flag": True}, tmp_path)
    import json

    data = json.loads(path.read_text())
    assert data["parameterSets"]["tee"]["hole_r"] == 4
    assert data["fileFormatVersion"] == "1"


# -- build + measure, against the real binary ------------------------------


@needs_openscad
@pytest.mark.parametrize("radius", [1, 2, 4])
def test_the_parameter_reaches_the_model_and_the_volume_proves_it(radius):
    """The decisive test. Facet count is INSENSITIVE to radius when $fn is
    fixed - an earlier version of this test compared facets, saw 134 twice
    and wrongly concluded the parameter was ignored. Volume is the honest
    measurement."""
    built = cad.scad_build({"source": SRC, "params": {"hole_r": radius}, "format": "binstl"})
    assert built["ok"] is True
    assert built["bytes"] > 0
    m = cad.measure({"path": built["path"]})
    expected = 20 * 10 * 5 - math.pi * radius**2 * 5
    assert m["volume"] == pytest.approx(expected, rel=0.001)
    assert m["bbox"] == pytest.approx([20.0, 10.0, 5.0], abs=1e-6)


@needs_openscad
def test_a_build_answers_with_facts_not_geometry():
    built = cad.scad_build({"source": SRC, "format": "binstl"})
    payload = repr(built)
    assert built["bytes"] > 1000, "a real mesh was written"
    assert len(payload) < 400, "the answer must not carry the mesh"
    assert "path" in built and "facets" in built


@needs_openscad
def test_a_syntax_error_refuses_with_the_offending_line():
    with pytest.raises(TeeError) as e:
        cad.scad_build({"source": "cube([1,2,3]  // never closed\n"})
    assert e.value.code == "cad_build_failed"
    assert e.value.fix


@needs_openscad
def test_an_unknown_format_is_refused_before_running_anything():
    with pytest.raises(TeeError) as e:
        cad.scad_build({"source": SRC, "format": "gltf"})
    assert e.value.code == "cad_bad_format"
    assert "binstl" in e.value.fix


def test_a_build_with_no_input_refuses():
    with pytest.raises(TeeError) as e:
        cad.scad_build({})
    assert "source" in e.value.fix


# -- the dependency-free STL measurement ------------------------------------


def _write_stl(path, tris):
    with open(path, "wb") as f:
        f.write(b"\0" * 80)
        f.write(struct.pack("<I", len(tris)))
        for a, b, c in tris:
            f.write(struct.pack("<3f", 0.0, 0.0, 0.0))
            for v in (a, b, c):
                f.write(struct.pack("<3f", *v))
            f.write(b"\0\0")


def test_stl_volume_is_exact_for_a_unit_tetrahedron(tmp_path):
    """A tetrahedron on the origin with legs 1 has volume 1/6."""
    p = tmp_path / "tet.stl"
    o, x, y, z = (0, 0, 0), (1, 0, 0), (0, 1, 0), (0, 0, 1)
    _write_stl(p, [(o, y, x), (o, x, z), (o, z, y), (x, y, z)])
    m = cad.measure({"path": str(p)})
    assert m["kind"] == "mesh"
    assert m["triangles"] == 4
    assert m["volume"] == pytest.approx(1 / 6, abs=1e-6)
    assert m["bbox"] == pytest.approx([1.0, 1.0, 1.0], abs=1e-6)


def test_a_truncated_stl_refuses_rather_than_reading_garbage(tmp_path):
    p = tmp_path / "bad.stl"
    p.write_bytes(b"\0" * 80 + struct.pack("<I", 1000) + b"\0" * 10)
    with pytest.raises(TeeError) as e:
        cad.measure({"path": str(p)})
    assert "truncated" in e.value.fix


def test_measure_requires_an_existing_file():
    with pytest.raises(TeeError) as e:
        cad.measure({"path": "/nope/missing.stl"})
    assert "No such file" in e.value.message


# -- probe + registration ---------------------------------------------------


def test_probe_reports_both_tools_and_their_fixes():
    r = cad.probe()
    assert "openscad" in r and "cadquery" in r
    assert isinstance(r["formats"], list)
    assert "-D" in r["note"], "the probe should say why -D is absent"


def test_cad_tools_are_tabled_by_what_they_do():
    """A build writes a file; a measurement does not. A single family
    prefix would have given the writer the open read tier."""
    from tee.kernel import trust

    assert trust.capability_for("cad_scad_build") == "write-artifacts"
    assert trust.capability_for("cad_measure") == "read-compute"
    with pytest.raises(TeeError):
        trust.capability_for("cad_something_untabled")


def test_registration():
    from tee.app import TeeApp

    app = TeeApp({}, project_root=tempfile.mkdtemp())
    for n in ("cad_scad_build", "cad_measure", "cad_probe"):
        assert n in app.registry._tools, n


@pytest.mark.skipif(not probe.have("cadquery"), reason="cadquery not installed")
def test_cadquery_measures_a_step_solid(tmp_path):
    import cadquery as cq

    wp = cq.Workplane("XY").box(20, 10, 5).faces(">Z").workplane().hole(8.0)
    step = tmp_path / "part.step"
    cq.exporters.export(wp, str(step))
    m = cad.measure({"path": str(step)})
    assert m["kind"] == "solid"
    assert m["valid"] is True
    assert m["volume"] == pytest.approx(20 * 10 * 5 - math.pi * 16 * 5, rel=1e-6)


# -- A66 gap 2: the warm kernel already in this process ---------------------


class _FakePartkilnKernel:
    """A kernel that answers `measure` the way the real one does and counts
    the calls, so a test can prove the wire was used and the file was read
    rather than imported into a document."""

    def __init__(self) -> None:
        self.calls: list[tuple[str, dict]] = []

    def alive(self) -> bool:
        return True

    def call(self, method: str, params: dict) -> dict:
        self.calls.append((method, dict(params)))
        assert method == "measure", method
        what = params["what"]
        if what == "mass":
            return {
                "what": "mass",
                "source": "step:AP242",
                "volume_mm3": 91159.605,
                "area_mm2": 23675.133,
                "bbox_mm": [120.0, 80.0, 10.0],
            }
        return {
            "what": "faces",
            "source": "step:AP242",
            "bodies": [{"of": "bracket", "faces": 26, "solids": 1, "valid": True}],
        }


@pytest.fixture
def warm_partkiln(tmp_path):
    """A PartkilnAdapter holding a live kernel, registered the way a served
    one is. Discarded explicitly: the registry is a WeakSet, but a test must
    not leave a warm kernel behind for the next one to route into."""
    from tee.adapters.partkiln import adapter as pk

    fake = _FakePartkilnKernel()
    adapter = pk.PartkilnAdapter(tmp_path, kernel=fake)
    adapter._state = "warm"
    try:
        yield adapter, fake
    finally:
        pk._LIVE.discard(adapter)


def _no_subprocess(monkeypatch):
    """Make any spawn a loud failure: the point of the routing is that none
    happens."""

    def boom(*a, **k):
        raise AssertionError(f"a process was spawned: {a[0] if a else a}")

    monkeypatch.setattr(cad.subprocess, "run", boom)


def test_measure_uses_a_warm_partkiln_kernel_instead_of_spawning_a_second_occt(
    tmp_path, monkeypatch, warm_partkiln
):
    """A66 gap 2. With no in-process CadQuery the STEP route spawned a
    one-shot interpreter that paid a fresh OCP import to read one volume
    (1,531.2 ms measured) while a warm partkiln kernel holding the same
    OCCT sat idle in the same process (23.0 ms for the two reads)."""
    _adapter, fake = warm_partkiln
    step = tmp_path / "part.step"
    step.write_text("ISO-10303-21;\n")  # never parsed here: the kernel answers
    monkeypatch.setattr(cad, "have", lambda name: False)
    _no_subprocess(monkeypatch)

    m = cad.measure({"path": str(step)})

    assert m["engine"] == "partkiln", "the answer must name the kernel that replied"
    assert m["volume"] == pytest.approx(91159.605)
    assert m["area"] == pytest.approx(23675.133)
    assert m["bbox"] == [120.0, 80.0, 10.0]
    assert m["valid"] is True
    # Read-only: `measure` with a path reads the shape; `import` would have
    # put the file into the live document, and cad_measure is read-compute.
    assert [c[0] for c in fake.calls] == ["measure", "measure"]
    assert all(c[1]["path"] == str(step) for c in fake.calls)


def test_measure_falls_back_to_the_one_shot_route_when_no_kernel_is_warm(
    tmp_path, monkeypatch, warm_partkiln
):
    """A kernel that is cold, warming or dead is not a route. Nothing is
    started to make one: the old path runs exactly as it did."""
    adapter, fake = warm_partkiln
    adapter._state = "warming"
    step = tmp_path / "part.step"
    step.write_text("ISO-10303-21;\n")
    monkeypatch.setattr(cad, "have", lambda name: False)
    monkeypatch.setattr(cad, "_sidecar_python", lambda spec: None)

    with pytest.raises(TeeError) as err:
        cad.measure({"path": str(step)})
    assert err.value.code == "cad_no_kernel"
    assert fake.calls == []


def test_a_refusing_kernel_does_not_turn_a_measurable_file_into_an_error(
    tmp_path, monkeypatch, warm_partkiln
):
    """The routed read is an optimisation. When it refuses - an open shell,
    a product partkiln's reader will not pick - the call falls through to
    the route it would have taken anyway."""
    _adapter, fake = warm_partkiln

    def refuse(method, params):
        raise RuntimeError("pk_op_failed: holds no product geometry")

    monkeypatch.setattr(fake, "call", refuse)
    step = tmp_path / "part.step"
    step.write_text("ISO-10303-21;\n")
    monkeypatch.setattr(cad, "have", lambda name: False)
    monkeypatch.setattr(cad, "_sidecar_python", lambda spec: None)

    with pytest.raises(TeeError) as err:
        cad.measure({"path": str(step)})
    assert err.value.code == "cad_no_kernel"


def test_live_kernel_never_starts_or_warms_anything(tmp_path):
    """`live_kernel()` is a question, not a constructor: a cold adapter
    answers None rather than paying the 26 s OCP import inside a
    read-compute tool (Law 17)."""
    from tee.adapters.partkiln import adapter as pk

    cold = pk.PartkilnAdapter(tmp_path, kernel=_FakePartkilnKernel())
    try:
        assert cold._state == "cold"
        assert pk.live_kernel() is None
        cold._state = "warm"
        assert pk.live_kernel() is cold._kernel
        cold.close()
        assert pk.live_kernel() is None, "a closed adapter offers no kernel"
    finally:
        pk._LIVE.discard(cold)


@pytest.mark.skipif(not probe.have("cadquery"), reason="cadquery not installed")
def test_an_in_process_cadquery_still_wins(tmp_path, monkeypatch, warm_partkiln):
    """The routing is only ever a substitute for the SPAWN. Where CadQuery
    is importable it answers in 10.0 ms with full precision and its own
    validity check, and the kernel is not consulted at all."""
    import cadquery as cq

    _adapter, fake = warm_partkiln
    step = tmp_path / "part.step"
    cq.exporters.export(cq.Workplane("XY").box(20, 10, 5), str(step))

    m = cad.measure({"path": str(step)})

    assert m["engine"] == "in-process"
    assert fake.calls == []
