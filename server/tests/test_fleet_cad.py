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
