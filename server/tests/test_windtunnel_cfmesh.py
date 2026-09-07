"""A74 P1 — the cfMesh writer, with no cfMesh.

The campaign exists because snappyHexMesh's own log admitted 1.32 of 2
requested boundary layers at 41.6 % of the requested thickness on the lane's
prism, and because the mesher that covers its layers by construction is
already inside the OpenFOAM this lane drives (doc 74 §2.2).

These tests are hermetic: a fake `cartesianMesh` that checks the things a real
one checks - the dictionary exists, the surface it names exists, and the
patches come from the STL's `solid` names.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
from fixtures_windtunnel import make_app, wait_job

from tee.kernel.errors import TeeError
from tee.windtunnel import airfoil, foam, physics, runs


@pytest.fixture
def app(tmp_path):
    return make_app(tmp_path)


@pytest.fixture
def body_case(app, tmp_path):
    """A 3-D case over a prism, the geometry A74 P0 measured both meshers on."""
    stl = tmp_path / "prism.stl"
    airfoil.extrude_stl(stl, airfoil.naca4("0012", 24), span=0.4, chord=0.3, name="section")
    out = app.registry.call("wt_case", {"action": "create", "stl": str(stl), "V_mps": 20})
    return out["case_id"]


# -- the dictionary ----------------------------------------------------------


def _tunnel(**kw):
    return foam.Tunnel3D(
        xmin=-1.5,
        xmax=4.8,
        ymin=-2.0,
        ymax=2.0,
        zmin=-2.2,
        zmax=2.2,
        base_cell=0.15,
        body_name="body",
        body_bbox=((0.0, -0.018, -0.2), (0.3, 0.018, 0.2)),
        **kw,
    )


def test_the_dict_carries_the_keys_that_were_read_off_a_real_file():
    text = foam.cfmesh_dict(
        _tunnel(), surface_file="constant/triSurface/domain.stl", body_cell=0.0375, layers=2
    )
    assert 'surfaceFile     "constant/triSurface/domain.stl";' in text
    assert "maxCellSize" in text and "0.15" in text
    assert '"body.*"' in text and "cellSize" in text
    assert "nLayers" in text and "thicknessRatio" in text
    assert text.startswith("/*----") and "meshDict" in text


def test_the_dict_never_emits_the_key_that_cost_630980_cells():
    """`boundaryCellSize` refines at EVERY boundary, farfield walls included.

    Doc 74 §2.3: the first cfMesh run of this campaign used it and produced
    630,980 cells in 17.1 s against 37,960 in 1.6 s with `localRefinement` on
    the body. Both meshes are valid, so nothing downstream would have caught
    it - the only place it can be caught is here.
    """
    text = foam.cfmesh_dict(_tunnel(), surface_file="s.stl", body_cell=0.01, layers=2)
    assert "boundaryCellSize" not in text
    assert "localRefinement" in text


def test_the_dict_is_byte_stable_and_drops_the_layer_block_when_none_are_asked():
    a = foam.cfmesh_dict(_tunnel(), surface_file="s.stl", body_cell=0.01, layers=3)
    b = foam.cfmesh_dict(_tunnel(), surface_file="s.stl", body_cell=0.01, layers=3)
    assert a == b
    none = foam.cfmesh_dict(_tunnel(), surface_file="s.stl", body_cell=0.01, layers=0)
    assert "boundaryLayers" not in none and "nLayers" not in none


# -- the surface -------------------------------------------------------------


def test_the_domain_surface_is_one_file_with_the_box_and_the_body_named(app, body_case, tmp_path):
    """cfMesh meshes the volume BOUNDED by its surface, and each solid becomes
    a patch - so the body is rewritten under a known name rather than copied,
    because the name inside a user's STL is whatever their exporter wrote (and
    a binary STL has none at all)."""
    rec = _record(app, body_case)
    edir = Path(rec["engine_dir"])
    surface = runs.domain_surface(rec, edir)
    text = surface.read_text()
    solids = [ln.split()[1] for ln in text.splitlines() if ln.startswith("solid ")]
    # blockMesh's own patch names, because a solid IS a patch and one set of
    # boundary conditions has to serve both meshers (A74 P2)
    assert solids == ["inlet", "outlet", "sides", "top", "ground", "body"], solids
    assert text.count("endsolid") == 6
    # the body's own STL called its solid "section": the name did not survive,
    # which is the point
    assert "section" not in text
    whole = physics.read_stl(surface)
    body = physics.read_stl(Path(rec["geometry"]["stl"]))
    assert len(whole.tris) == len(body.tris) + 12  # the box is still twelve triangles
    assert len(physics.read_stl(edir / "constant" / "triSurface" / "sides.stl").tris) == 4


def test_the_domain_surface_encloses_the_body(app, body_case):
    rec = _record(app, body_case)
    surface = runs.domain_surface(rec, Path(rec["engine_dir"]))
    (bx0, by0, bz0), (bx1, by1, bz1) = physics.read_stl(surface).bbox
    dom = rec["domain"]
    assert (bx0, by0, bz0) == pytest.approx((dom["xmin"], dom["ymin"], dom["zmin"]))
    assert (bx1, by1, bz1) == pytest.approx((dom["xmax"], dom["ymax"], dom["zmax"]))


def test_the_box_faces_carry_blockmeshs_names_and_point_outward():
    """The defect P2 found, pinned. A single `farfield` solid meshes perfectly
    and then stops the solver at `Cannot find patchField entry for farfield`,
    because `0/p` names inlet, outlet, sides, top and ground."""
    faces = physics.box_faces(-1.0, 4.0, -2.0, 2.0, -3.0, 3.0)
    assert list(faces) == ["inlet", "outlet", "sides", "top", "ground"]
    assert sum(len(v) for v in faces.values()) == 12
    assert len(faces["sides"]) == 4  # one patch, two walls of the box
    centre = (1.5, 0.0, 0.0)
    for name, tris in faces.items():
        for p0, q, r in tris:
            u = [q[i] - p0[i] for i in range(3)]
            v = [r[i] - p0[i] for i in range(3)]
            n = [
                u[1] * v[2] - u[2] * v[1],
                u[2] * v[0] - u[0] * v[2],
                u[0] * v[1] - u[1] * v[0],
            ]
            mid = [sum(pt[i] for pt in (p0, q, r)) / 3 - centre[i] for i in range(3)]
            assert sum(n[i] * mid[i] for i in range(3)) > 0, f"{name} points inward"


# -- through the tool --------------------------------------------------------


def test_wt_mesh_with_cfmesh_runs_cartesian_mesh_and_says_which_mesher(app, body_case):
    started = app.registry.call(
        "wt_mesh", {"case_id": body_case, "mesher": "cfmesh", "base_cell_m": 0.15, "layers": 2}
    )
    status = wait_job(app, started["job"], timeout_s=120)
    assert status["state"] == "done", status
    mesh = status["result"]
    assert mesh["kind"] == "cfmesh" and mesh["ok"] is True
    assert mesh["cells"] > 0 and mesh["layers"] == 2
    assert mesh["body_cell_m"] == pytest.approx(0.15 / 16)  # levels default (3, 4)
    assert mesh["threads"] == 1 and mesh["reproducible"] is True
    edir = Path(_record(app, body_case)["engine_dir"])
    assert (edir / "system" / "meshDict").is_file()
    assert not (edir / "system" / "snappyHexMeshDict").is_file(), "the snappy path did not run"
    log = (edir / "log.cartesianMesh").read_text()
    assert "(cfmesh)" in log and "6 patches" in log
    boundary = (edir / "constant" / "polyMesh" / "boundary").read_text()
    for patch in ("inlet", "outlet", "sides", "top", "ground", "body"):
        assert patch in boundary, f"{patch} is not a patch of the mesh"


def test_reproducible_is_the_default_and_cores_is_how_speed_is_bought(app, body_case):
    """cfMesh threads itself and threaded it is NOT reproducible: measured
    2026-09-07, the same case gave mesh hashes 7c260615fd23772e and
    cc2a2a95b348336a at an identical 38,352 cells, where OMP_NUM_THREADS=1
    gave c5fa100c6f08f733 twice for 25 % more wall time.

    The lane's own laws decide the default: the mesh hash travels with every
    coefficient, and same-mesh deltas are first-class. Neither survives a
    mesher that answers differently each time it is asked.
    """
    default = wait_job(
        app, app.registry.call("wt_mesh", {"case_id": body_case, "mesher": "cfmesh"})["job"], 120
    )["result"]
    assert default["threads"] == 1 and default["reproducible"] is True
    assert "same hash" in default["cores_note"]

    threaded = wait_job(
        app,
        app.registry.call("wt_mesh", {"case_id": body_case, "mesher": "cfmesh", "cores": 4})["job"],
        120,
    )["result"]
    assert threaded["threads"] == 4 and threaded["reproducible"] is False
    assert "NOT reproducible" in threaded["cores_note"]


def test_the_snappy_path_is_untouched_and_is_still_the_default(app, body_case):
    started = app.registry.call(
        "wt_mesh", {"case_id": body_case, "base_cell_m": 0.15, "levels": [1, 2], "layers": 2}
    )
    status = wait_job(app, started["job"], timeout_s=120)
    assert status["state"] == "done", status
    assert status["result"]["kind"] == "snappy"
    edir = Path(_record(app, body_case)["engine_dir"])
    assert (edir / "system" / "snappyHexMeshDict").is_file()
    assert not (edir / "system" / "meshDict").is_file()


def test_an_unknown_mesher_refuses_and_auto_says_which_phase_owns_it(app, body_case):
    for name in ("nonsense", "auto"):
        with pytest.raises(TeeError) as exc:
            app.registry.call("wt_mesh", {"case_id": body_case, "mesher": name})
        assert exc.value.code == "wt_bad_mesher"
        assert "snappy" in exc.value.fix and "cfmesh" in exc.value.fix
    assert "P4" in exc.value.fix, "auto's refusal names the phase that will measure it"


def test_mesher_on_a_two_d_case_refuses_rather_than_being_ignored(app):
    created = app.registry.call(
        "wt_case", {"action": "create", "naca": "0012", "V_mps": 30, "aoa_deg": 4}
    )
    with pytest.raises(TeeError) as exc:
        app.registry.call("wt_mesh", {"case_id": created["case_id"], "mesher": "cfmesh"})
    assert exc.value.code == "wt_bad_mesher" and "airfoil2d" in exc.value.message


def _record(app, case_id):
    return app._wt_store.load(case_id)  # make_app attaches the store it registered


# -- P3: the feature edges ---------------------------------------------------


class _FakeInstall:
    def argv(self, *a):
        return ["/usr/bin/openfoam2606", *a]


def test_the_sequence_extracts_feature_edges_before_meshing():
    """`surfaceFeatureEdges` is the first step, not an afterthought: the FMS
    it writes is the surface `cartesianMesh` is then pointed at."""
    seq = runs.mesh_sequence_3d_cfmesh(_FakeInstall(), Path("/case"), 1)
    assert [name for name, _ in seq] == ["surfaceFeatureEdges", "cartesianMesh", "checkMesh"]
    argv = seq[0][1]
    assert argv[-2:] == [
        "/case/constant/triSurface/domain.stl",
        "/case/constant/triSurface/domain.fms",
    ], argv
    # measured 2026-09-07: the real binary takes `-case` from any cwd and
    # accepts the float form of the angle (`surfaceFeatureEdges -help` says
    # `-angle <scalar>`); both forms were run before this argv was written
    assert argv[argv.index("-angle") + 1] == "30.0"
    assert argv[argv.index("-case") + 1] == "/case"


def test_the_plain_surface_route_survives_as_the_thing_the_measurement_compared():
    """`feature_angle=0` is what P3 measured against, and it is what a machine
    with no `surfaceFeatureEdges` would fall back to. It is NOT reachable from
    the tool - see the law-5 test below - and it is what FAILS `checkMesh`."""
    seq = runs.mesh_sequence_3d_cfmesh(_FakeInstall(), Path("/case"), 1, feature_angle=0)
    assert [name for name, _ in seq] == ["cartesianMesh", "checkMesh"]


def test_the_dict_names_the_fms_the_feature_step_has_yet_to_write(app, body_case):
    """The dictionary names a file that does not exist yet, exactly as the
    snappy route names an `.eMesh` `surfaceFeatureExtract` has yet to write."""
    rec = _record(app, body_case)
    edir = Path(rec["engine_dir"])
    prep = runs.write_tunnel_3d_cfmesh(rec, edir, base_cell_m=0.15, body_cell_m=0.0375, layers=2)
    text = (edir / "system" / "meshDict").read_text()
    assert 'surfaceFile     "constant/triSurface/domain.fms";' in text
    assert not (edir / "constant" / "triSurface" / "domain.fms").exists()
    assert (edir / "constant" / "triSurface" / "domain.stl").is_file(), "the STL feeds the FMS"
    assert prep["feature_angle"] == 30.0 and prep["surface"].endswith("domain.fms")
    assert prep["stl"].endswith("domain.stl")

    plain = runs.write_tunnel_3d_cfmesh(
        rec, edir, base_cell_m=0.15, body_cell_m=0.0375, layers=2, feature_angle=0
    )
    assert (
        'surfaceFile     "constant/triSurface/domain.stl";'
        in (edir / "system" / "meshDict").read_text()
    )
    assert plain["surface"] == plain["stl"]


def test_the_feature_route_carries_every_patch_name_through_the_conversion(app, body_case):
    """The FMS is a different file format, and a format that lost the patch
    names would mesh perfectly and then stop `simpleFoam` dead at `Cannot find
    patchField entry` - which is A74 P2's defect 1, in a new place."""
    started = app.registry.call(
        "wt_mesh", {"case_id": body_case, "mesher": "cfmesh", "base_cell_m": 0.15, "layers": 2}
    )
    mesh = wait_job(app, started["job"], timeout_s=120)["result"]
    assert mesh["feature_angle"] == 30.0
    edir = Path(_record(app, body_case)["engine_dir"])
    assert (edir / "log.surfaceFeatureEdges").is_file(), "the feature step did not run"
    fms = edir / "constant" / "triSurface" / "domain.fms"
    assert fms.is_file() and fms.stat().st_size > 0
    named = [ln.split()[0] for ln in fms.read_text().split(")", 1)[0].splitlines() if " " in ln]
    assert named == ["inlet", "outlet", "sides", "top", "ground", "body"], named
    boundary = (edir / "constant" / "polyMesh" / "boundary").read_text()
    for patch in named:
        assert patch in boundary, f"{patch} survived the FMS but not the mesh"


def test_the_feature_angle_is_not_a_caller_argument(app):
    """A74 law 5: the caller's arguments do not change between meshers, which
    is what makes `auto` honest. snappy's own `includedAngle 150` is the same
    criterion from the other end (180 - 150 = 30) and is not an argument
    either - so this one is a constant the reply reports, not a knob."""
    schema = app.registry.describe("wt_mesh")["schema"]["properties"]
    assert "feature_angle" not in schema
    assert "mesher" in schema, "the one argument the meshers do differ on"
    snappy_angle = re.search(
        r"includedAngle\s+([0-9.]+);", foam.surface_feature_extract_dict("body")
    )
    assert snappy_angle, "the snappy route's own feature angle moved"
    assert 180.0 - float(snappy_angle.group(1)) == runs.FEATURE_ANGLE_DEG
