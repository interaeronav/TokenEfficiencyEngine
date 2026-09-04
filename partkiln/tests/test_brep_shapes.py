"""P2a acceptance for partkiln.brep.shapes against the A66 P0a measured table."""

from __future__ import annotations

import math
import time

import pytest

pytest.importorskip("OCP", reason="partkiln[brep] not installed")

from partkiln._errors import KernelError
from partkiln.brep import fixtures, query, shapes

pytestmark = pytest.mark.brep


def _rect(w: float, h: float):
    return shapes.make_face_from_points([(0, 0, 0), (w, 0, 0), (w, h, 0), (0, h, 0)])


def _vertical_corners(shape):
    return [
        e
        for e in query.edges(shape)
        if e.direction and abs(e.direction[2]) > 0.999 and not e.is_seam
    ]


# --------------------------------------------------------------------------- F1 and counts


def test_f1_volume_counts_area_com() -> None:
    t = time.perf_counter()
    f1 = fixtures.build_F1()
    dt = time.perf_counter() - t
    assert shapes.volume(f1) == pytest.approx(59214.602, abs=5e-4)
    assert shapes.counts(f1) == {"solids": 1, "faces": 7, "edges": 15, "vertices": 10}
    assert shapes.area(f1) == pytest.approx(15357.080, abs=5e-4)
    assert shapes.centre_of_mass(f1) == pytest.approx((50.0, 30.0, 5.0), abs=1e-9)
    assert dt < 0.5, f"F1 took {dt:.3f} s (warm budget 30 ms + slack)"


def test_counts_are_unique_not_explorer_visits() -> None:
    from OCP.TopAbs import TopAbs_EDGE
    from OCP.TopExp import TopExp_Explorer

    f5 = fixtures.build_F5()
    visits = 0
    ex = TopExp_Explorer(f5, TopAbs_EDGE)
    while ex.More():
        visits += 1
        ex.Next()
    assert visits == 624  # the explorer double-counts shared edges
    assert shapes.counts(f5)["edges"] == 312  # Law 20: the unique map


def test_bbox_is_tight_and_inertia_symmetric() -> None:
    f1 = fixtures.build_F1()
    assert shapes.bbox(f1) == pytest.approx((0, 0, 0, 100, 60, 10), abs=1e-7)
    m = shapes.inertia(f1)
    assert m[0][1] == pytest.approx(0.0, abs=1e-6)
    assert m[0][0] < m[1][1] < m[2][2]
    assert shapes.is_valid(f1)
    assert shapes.counts(shapes.fix(f1)) == shapes.counts(f1)


# --------------------------------------------------------------------------- primitives


def test_primitives_match_arithmetic() -> None:
    assert shapes.volume(shapes.sphere(5)) == pytest.approx(4 / 3 * math.pi * 125, abs=1e-6)
    assert shapes.volume(shapes.cone(5, 0, 10)) == pytest.approx(math.pi * 25 * 10 / 3, abs=1e-6)
    assert shapes.volume(shapes.cylinder(5, 40, (20, 20, -10))) == pytest.approx(3141.593, abs=5e-4)
    assert shapes.counts(shapes.sphere(5))["faces"] == 1
    with pytest.raises(KernelError, match="positive"):
        shapes.box(0, 1, 1)
    with pytest.raises(KernelError, match="zero vector"):
        shapes.cylinder(1, 1, direction=(0, 0, 0))


# --------------------------------------------------------------------------- sweeps


def test_prism_plain_and_tapered_both_semantics() -> None:
    face = _rect(100, 60)
    plain = shapes.prism(face, (0, 0, 10))
    assert shapes.volume(plain.shape) == pytest.approx(60000.0, abs=1e-6)
    assert shapes.counts(plain.shape)["faces"] == 6
    # the raw OCCT numbers (height ALONG the drafted wall)
    plus = shapes.prism(face, (0, 0, 10), taper_deg=3, height="along_wall")
    assert shapes.volume(plus.shape) == pytest.approx(59085.191, abs=5e-4)
    assert shapes.counts(plus.shape)["faces"] == 6
    assert shapes.bbox(plus.shape)[5] == pytest.approx(10 * math.cos(math.radians(3)), abs=1e-6)
    minus = shapes.prism(face, (0, 0, 10), taper_deg=-3, height="along_wall")
    assert shapes.volume(minus.shape) == pytest.approx(60756.864, abs=5e-4)
    assert shapes.counts(minus.shape)["faces"] == 10
    # the default: vertical height reaches |vec|
    vertical = shapes.prism(face, (0, 0, 10), taper_deg=3)
    assert shapes.bbox(vertical.shape)[5] == pytest.approx(10.0, abs=1e-9)
    assert shapes.volume(vertical.shape) == pytest.approx(59165.138, abs=5e-4)
    # anti-parallel: mirrored through the face plane, same volume, still valid
    down = shapes.prism(face, (0, 0, -10), taper_deg=3, height="along_wall")
    assert shapes.bbox(down.shape)[2] == pytest.approx(-10 * math.cos(math.radians(3)), abs=1e-6)
    assert shapes.volume(down.shape) == pytest.approx(59085.191, abs=5e-4)
    assert shapes.is_valid(down.shape)
    with pytest.raises(KernelError, match="normal to its face"):
        shapes.prism(face, (1, 0, 10), taper_deg=3)
    with pytest.raises(KernelError, match="along_wall"):
        shapes.prism(face, (0, 0, 10), taper_deg=3, height="sideways")


def test_revolve_sweep_loft() -> None:
    from OCP.BRepBuilderAPI import (
        BRepBuilderAPI_MakeEdge,
        BRepBuilderAPI_MakePolygon,
        BRepBuilderAPI_MakeWire,
    )
    from OCP.gp import gp_Ax2, gp_Circ, gp_Dir, gp_Pnt

    rev = shapes.revolve(_rect(10, 20), (0, 0, 0), (0, 1, 0), 360)
    assert shapes.volume(rev.shape) == pytest.approx(math.pi * 100 * 20, abs=1e-6)
    half = shapes.revolve(_rect(10, 20), (0, 0, 0), (0, 1, 0), 180)
    assert shapes.volume(half.shape) == pytest.approx(math.pi * 100 * 10, abs=1e-6)

    path = BRepBuilderAPI_MakeWire(
        BRepBuilderAPI_MakeEdge(gp_Pnt(0, 0, 0), gp_Pnt(0, 0, 50)).Edge()
    ).Wire()
    circle = BRepBuilderAPI_MakeEdge(gp_Circ(gp_Ax2(gp_Pnt(0, 0, 0), gp_Dir(0, 0, 1)), 3)).Edge()
    profile = BRepBuilderAPI_MakeWire(circle).Wire()
    sw = shapes.sweep(profile, path)
    assert shapes.volume(sw.shape) == pytest.approx(math.pi * 9 * 50, abs=1e-3)
    assert shapes.counts(sw.shape)["solids"] == 1

    def ring(pts, z):
        pg = BRepBuilderAPI_MakePolygon()
        for x, y in pts:
            pg.Add(gp_Pnt(x, y, z))
        pg.Close()
        return pg.Wire()

    w1 = ring([(0, 0), (40, 0), (40, 40), (0, 40)], 0)
    w2 = ring([(10, 10), (30, 10), (30, 30), (10, 30)], 30)
    lf = shapes.loft([w1, w2], ruled=True)
    assert shapes.volume(lf.shape) == pytest.approx(28000.0, abs=1e-6)
    with pytest.raises(KernelError, match="at least 2"):
        shapes.loft([w1])


# --------------------------------------------------------------------------- booleans


def test_f5_one_nary_cut() -> None:
    t = time.perf_counter()
    f5 = fixtures.build_F5()
    dt = time.perf_counter() - t
    assert shapes.volume(f5) == pytest.approx(520481.421, abs=5e-4)
    c = shapes.counts(f5)
    assert (c["faces"], c["edges"]) == (106, 312)
    assert dt <= 0.3, f"n-ary cut took {dt:.3f} s (measured 0.09-0.10 s)"


def test_boolean_result_reports_no_effect_and_empty() -> None:
    hit = shapes.cut(shapes.box(100, 60, 10), [shapes.cylinder(5, 12, (50, 30, -1))])
    assert hit.is_done and not hit.no_effect and not hit.empty
    assert hit.counts_before["faces"] == 6 and hit.counts_after["faces"] == 7
    miss = shapes.cut(shapes.box(10, 10, 10), [shapes.box(5, 5, 5, (50, 50, 50))])
    assert miss.is_done and miss.no_effect and not miss.empty  # Law 11
    assert miss.volume_after == pytest.approx(miss.volume_before, rel=1e-12)
    apart = shapes.common(shapes.box(10, 10, 10), shapes.box(5, 5, 5, (50, 50, 50)))
    assert apart.empty and not apart.no_effect
    with pytest.raises(KernelError, match="at least one tool"):
        shapes.cut(shapes.box(1, 1, 1), [])


def test_common_cubes_and_f6_interference() -> None:
    c = shapes.common(shapes.box(20, 20, 20), shapes.box(20, 20, 20, (19, 0, 0)))
    assert c.volume_after == pytest.approx(400.000, abs=5e-4)
    assert shapes.centre_of_mass(c.shape) == pytest.approx((19.5, 10.0, 10.0), abs=1e-9)
    block, pin = fixtures.build_F6()
    assert shapes.volume(block) == pytest.approx(30429.204, abs=5e-4)
    assert shapes.volume(pin) == pytest.approx(3141.593, abs=5e-4)
    assert shapes.common(block, pin).volume_after == pytest.approx(
        0.0, abs=1e-6
    )  # a d10 pin in a d10 hole
    fat = shapes.cylinder(5.5, 40, (20, 20, -10))
    assert shapes.common(block, fat).volume_after == pytest.approx(329.867, abs=5e-4)


def test_f2_fuse_unify_fillet_holes() -> None:
    f2 = fixtures.build_F2()
    assert shapes.volume(f2) == pytest.approx(44916.967, abs=5e-4)
    c = shapes.counts(f2)
    assert (c["faces"], c["edges"]) == (13, 33)
    fused = shapes.fuse([shapes.box(80, 60, 6), shapes.box(80, 6, 34, (0, 0, 6))])
    assert shapes.counts(fused.shape)["faces"] == 11  # the shared face is split, not merged
    unified, hist = shapes.unify(fused.shape)
    assert (
        shapes.counts(unified)["faces"] == 8
    )  # an L prism: 6 sides + 2 caps; +1 fillet +4 holes = 13
    assert hist is not None


def test_fuse_touching_glue_only_for_pattern_copies() -> None:
    a, b = shapes.box(10, 10, 10), shapes.box(10, 10, 10, (10, 0, 0))
    glued = shapes.fuse([a, b], touching=True)
    assert glued.is_done and shapes.volume(glued.shape) == pytest.approx(2000.0, abs=1e-9)
    with pytest.raises(KernelError, match="at least 2"):
        shapes.fuse([a])


# --------------------------------------------------------------------------- fillet / chamfer


def test_fillet_r2_on_f1_corners_reports_the_seam() -> None:
    f1 = fixtures.build_F1()
    all_z = [e for e in query.edges(f1) if e.direction and abs(e.direction[2]) > 0.999]
    assert len(all_z) == 5 and sum(e.is_seam for e in all_z) == 1
    res = shapes.fillet(f1, [e.shape for e in all_z], 2.0)
    assert res.is_done and res.faulty_contours == 0
    seam_index = next(i for i, e in enumerate(all_z) if e.is_seam)
    assert res.ignored_edges == (seam_index,)  # never silently accepted (Law 11)
    assert shapes.volume(res.shape) == pytest.approx(59180.266, abs=5e-4)
    assert shapes.volume(res.shape) - shapes.volume(f1) == pytest.approx(-34.336, abs=5e-4)
    assert shapes.counts(res.shape)["faces"] == 11
    clean = shapes.fillet(f1, [e.shape for e in _vertical_corners(f1)], 2.0)
    assert clean.ignored_edges == ()


def test_fillet_r12_on_top_front_edge_refuses_naming_faulty_contours() -> None:
    f1 = fixtures.build_F1()
    edge = fixtures.edge_at(f1, (50.0, 0.0, 10.0))
    with pytest.raises(KernelError, match=r"NbFaultyContours=1"):
        shapes.fillet(f1, [edge], 12.0)
    with pytest.raises(KernelError, match="> 0"):
        shapes.fillet(f1, [edge], 0.0)


def test_variable_fillet_and_chamfers() -> None:
    f1 = fixtures.build_F1()
    edge = fixtures.edge_at(f1, (50.0, 0.0, 10.0))
    var = shapes.fillet(f1, [edge], (1.0, 3.0))
    assert var.is_done and var.ignored_edges == ()
    # "less than F1" passed for ANY radius, including a constant r that quietly
    # ignored the (start, end) pair; the 1->3 taper removes 94.763 mm3, which no
    # constant radius does (r=1 -21.460, r=2 -85.841, r=3 -193.142; measured
    # 2026-09-04 on OCP 7.9.3).
    assert shapes.volume(var.shape) - shapes.volume(f1) == pytest.approx(-94.763, abs=5e-4)
    sym = shapes.chamfer(f1, [edge], 2.0)
    assert shapes.volume(sym.shape) - shapes.volume(f1) == pytest.approx(-200.0, abs=5e-4)
    asym = shapes.chamfer(f1, [edge], (2.0, 4.0))
    assert shapes.volume(asym.shape) - shapes.volume(f1) == pytest.approx(-400.0, abs=5e-4)
    assert asym.ignored_edges == ()
    with pytest.raises(KernelError, match="at least one edge"):
        shapes.chamfer(f1, [], 1.0)


# ------------------------------------------------------------------- shell / draft / transform


def test_shell_in_and_out() -> None:
    b = shapes.box(40, 40, 20)
    top = next(f for f in query.faces(b) if f.normal[2] > 0.99)
    inner = shapes.shell(b, [top.shape], 2.0, "in")
    assert shapes.volume(inner.shape) == pytest.approx(32000 - 36 * 36 * 18, abs=1e-6)
    assert shapes.counts(inner.shape)["faces"] == 11
    outer = shapes.shell(b, [top.shape], 2.0, "out")
    # pinned, not just "> inner": the outward shell is 10370.737 mm3, LESS than
    # the 10592 of 44x44x22 - 40x40x20 because the added corners are rounded
    # (measured 2026-09-04); "> inner" passed for an operation that returned the
    # solid box untouched.
    assert shapes.volume(outer.shape) == pytest.approx(10370.737, abs=5e-4)
    assert shapes.volume(outer.shape) > shapes.volume(inner.shape)
    assert shapes.bbox(outer.shape)[0] == pytest.approx(-2.0, abs=1e-6)
    with pytest.raises(KernelError, match="'in' or 'out'"):
        shapes.shell(b, [top.shape], 2.0, "sideways")


def test_draft_side_walls_and_refuse_sphere() -> None:
    b = shapes.box(40, 40, 20)
    sides = [f for f in query.faces(b) if abs(f.normal[2]) < 0.01]
    res = shapes.draft(b, [f.shape for f in sides], 5.0, ((0, 0, 0), (0, 0, 1)), (0, 0, 1))
    assert res.status == "NoError"
    top = 40 - 2 * 20 * math.tan(math.radians(5))
    frustum = 20 / 3 * (1600 + top * top + math.sqrt(1600 * top * top))
    assert shapes.volume(res.shape) == pytest.approx(frustum, abs=1e-6)
    sphere = shapes.sphere(5)
    with pytest.raises(KernelError, match="it is a sphere"):
        shapes.draft(sphere, [query.faces(sphere)[0].shape], 5.0, ((0, 0, 0), (0, 0, 1)), (0, 0, 1))


def test_transform_copies_rotates_then_translates() -> None:
    f1 = fixtures.build_F1()
    moved = shapes.transform(f1, translation=(10, 0, 0))
    assert shapes.centre_of_mass(moved.shape) == pytest.approx((60, 30, 5), abs=1e-9)
    assert shapes.centre_of_mass(f1) == pytest.approx((50, 30, 5), abs=1e-9)  # the source is intact
    turned = shapes.transform(f1, rotation=((0, 0, 0), (0, 0, 1), 90))
    assert shapes.bbox(turned.shape) == pytest.approx((-60, 0, 0, 0, 100, 10), abs=1e-7)
    both = shapes.transform(f1, translation=(60, 0, 0), rotation=((0, 0, 0), (0, 0, 1), 90))
    assert shapes.bbox(both.shape) == pytest.approx((0, 0, 0, 60, 100, 10), abs=1e-7)


def test_make_face_refuses_bad_polygons() -> None:
    with pytest.raises(KernelError, match="at least 3"):
        shapes.make_face_from_points([(0, 0, 0), (1, 0, 0)])
    with pytest.raises(KernelError, match="planar"):
        shapes.make_face_from_points([(0, 0, 0), (1, 0, 0), (1, 1, 0), (0, 1, 5)])


def test_require_ocp_refuses_with_the_kernel_absent_code(monkeypatch) -> None:
    """The kernel-absent refusal must carry `pk_kernel_absent`, not the default.

    `KernelError`'s default code is `pk_op_failed` (`_errors.py`), so a
    `require_ocp()` that passed no code refused with "the operation failed"
    and an adapter branching on `pk_kernel_absent` (D8) never saw it - the
    one refusal a caller is meant to handle by installing the extra.
    """
    import partkiln.brep as brep

    monkeypatch.setattr(brep, "_ocp_present", False)
    assert brep.ocp_available() is False
    with pytest.raises(KernelError) as e:
        brep.require_ocp()
    assert e.value.code == "pk_kernel_absent"
    assert brep.INSTALL_LINE in str(e.value)
    assert e.value.fix == brep.INSTALL_LINE
