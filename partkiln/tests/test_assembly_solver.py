"""P3 acceptance for partkiln.assembly (model + solver) on the F6 pin-block numbers.

F6 (A66 P0a): block 40x40x20 with a d10 through hole at (20, 20); pin d10 x 40.
The frames below are what the document layer reads off the named sub-shapes
(block.top, the hole wall's axis, pin.start ...), typed here from the
fixture's dimensions so the solver is exercised with NO kernel installed;
`test_frames_read_from_f6_geometry` derives the same frames from the B-rep
(skipped without OCP) and must land on the same pose.
"""

from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path

import numpy as np
import pytest
import scipy.optimize  # noqa: F401  # warm: the first solve otherwise pays scipy's import (~125 ms)

from partkiln.assembly import Assembly, Component, FrameRef, Joint, Mate, Pose, Ref, solve
from partkiln.assembly.solver import CONVERGED_MM, apply_poses, jacobian, numeric_jacobian
from partkiln.document import CommandError

# The block in world coordinates (grounded).
BLOCK = {
    "hole": FrameRef("axis", (20.0, 20.0, 20.0), (0.0, 0.0, 1.0), radius=5.0),
    "top": FrameRef("plane", (20.0, 20.0, 20.0), (0.0, 0.0, 1.0)),
    "side_x": FrameRef("plane", (40.0, 20.0, 10.0), (1.0, 0.0, 0.0)),
    "side_y": FrameRef("plane", (20.0, 40.0, 10.0), (0.0, 1.0, 0.0)),
}
# The pin in its OWN frame: bottom centre at the origin, axis +Z, a flat at +X.
PIN = {
    "axis": FrameRef("axis", (0.0, 0.0, 0.0), (0.0, 0.0, 1.0), radius=5.0),
    "bottom": FrameRef("plane", (0.0, 0.0, 0.0), (0.0, 0.0, -1.0)),
    "top": FrameRef("plane", (0.0, 0.0, 40.0), (0.0, 0.0, 1.0)),
    "flat": FrameRef("plane", (5.0, 0.0, 20.0), (1.0, 0.0, 0.0)),
}
START = Pose((3.0, -4.0, 7.0))


def pin_block(start: Pose = START) -> Assembly:
    return Assembly(
        [
            Component("block", "block", grounded=True),
            Component("pin", "pin", pose=start),
        ]
    )


def b(name: str) -> Ref:
    return Ref("block", BLOCK[name], name)


def p(name: str) -> Ref:
    return Ref("pin", PIN[name], name)


# --------------------------------------------------------------------------- poses


def test_pose_matrix_compose_inverse_roundtrip() -> None:
    a = Pose.from_axis_angle((1, 2, 3), 37.0, (1.0, -2.0, 3.0))
    c = Pose.from_axis_angle((0, 1, 0), -80.0, (5.0, 5.0, 0.0))
    m = a.matrix() @ c.matrix()
    ac = a.compose(c)
    assert np.allclose(ac.matrix(), m, atol=1e-12)
    assert np.allclose(Pose.from_matrix(m).matrix(), m, atol=1e-12)
    ident = ac.compose(ac.inverse())
    assert ident.is_identity(tol=1e-12)
    # point/vector transforms agree with the matrix
    q = (0.3, -1.2, 4.0)
    assert np.allclose(ac.point(q), (m @ np.array([*q, 1.0]))[:3], atol=1e-12)
    assert np.allclose(ac.vector(q), m[:3, :3] @ np.array(q), atol=1e-12)


def test_pose_quaternion_is_canonical_and_serialisable() -> None:
    a = Pose((0, 0, 0), (-0.5, 0.5, 0.5, 0.5))
    assert a.rotation[0] >= 0  # the double cover is fixed
    assert Pose.from_dict(a.as_dict()) == a.rounded(9)
    with pytest.raises(CommandError) as e:
        Pose((0, 0, 0), (0, 0, 0, 0))
    assert e.value.code == "pk_needs"
    with pytest.raises(CommandError) as e:
        Pose.from_matrix(np.diag([2.0, 1.0, 1.0, 1.0]))
    assert e.value.code == "pk_needs" and "scale" in str(e.value)


def test_frame_ref_normalises_and_derives_xdir() -> None:
    f = FrameRef("axis", (1, 2, 3), (0, 0, 2))
    assert f.axis == (0.0, 0.0, 1.0)
    assert f.xdir == (1.0, 0.0, 0.0)  # the canonical perpendicular of +Z
    g = FrameRef("plane", (0, 0, 0), (0, 0, 1), xdir=(1, 1, 5))
    assert g.xdir == pytest.approx((2**-0.5, 2**-0.5, 0.0))
    with pytest.raises(CommandError) as e:
        FrameRef("axis", (0, 0, 0), (0, 0, 0))
    assert e.value.code == "pk_needs" and "zero length" in str(e.value)
    with pytest.raises(CommandError) as e:
        FrameRef("line", (0, 0, 0), (0, 0, 1))
    assert e.value.code == "pk_bad_op"


# --------------------------------------------------------------------------- gradients


def test_analytic_jacobian_matches_finite_differences() -> None:
    """Every row kind, from a generic start, against central differences."""
    a = pin_block(Pose.from_axis_angle((1, 2, 3), 20.0, (3.0, -4.0, 7.0)))
    a.add_mate(Mate("m1", "mate", b("top"), p("bottom"), offset_mm=2.0))
    a.add_mate(Mate("i1", "insert", b("hole"), p("axis"), offset_mm=1.0))
    a.add_mate(Mate("ang", "angle", b("side_y"), p("flat"), angle_deg=60.0))
    a.add_mate(Mate("t1", "tangent", b("side_x"), p("axis"), offset_mm=1.0))
    a.add_mate(Mate("t2", "tangent", b("hole"), p("axis")))
    a.add_joint(Joint("sl", "slider", b("hole"), p("axis"), angle_deg=15.0))
    a.add_joint(Joint("rg", "rigid", b("top"), p("top"), offset_mm=3.0, angle_deg=-40.0))
    a.add_joint(Joint("cy", "cylindrical", b("hole"), p("axis")))
    a.add_joint(Joint("pl", "planar", b("top"), p("bottom")))
    a.add_joint(Joint("ba", "ball", b("top"), p("top")))
    _f, J, owners = jacobian(a)
    assert J.shape == (len(owners), 6)
    assert np.max(np.abs(J - numeric_jacobian(a))) < 1e-6 * max(1.0, np.max(np.abs(J)))


# --------------------------------------------------------------------------- joints -> DOF


@pytest.mark.parametrize(
    ("kind", "dof"),
    [("rigid", 0), ("revolute", 1), ("slider", 1), ("cylindrical", 2), ("planar", 3), ("ball", 3)],
)
def test_joint_kinds_between_pin_and_hole_axis(kind: str, dof: int) -> None:
    a = pin_block()
    a.add_joint(Joint("j1", kind, b("hole"), p("axis")))
    r = solve(a)
    assert r.dof == dof
    assert r.dof_by_component == {"pin": dof}
    assert r.residual_mm < 1e-9
    assert r.status == ("ok" if dof == 0 else "under")
    assert r.conflicts == [] and r.redundant == []
    # the pin's axis is on the hole axis whatever the joint left free
    t = r.poses["pin"].translation
    if kind != "ball" and kind != "planar":
        assert t[:2] == pytest.approx((20.0, 20.0), abs=1e-9)


# --------------------------------------------------------------------------- insert + mate


def test_insert_and_mate_place_the_pin_within_budget() -> None:
    a = pin_block()
    a.add_mate(Mate("insert1", "insert", b("hole"), p("axis")))
    a.add_mate(Mate("mate1", "mate", b("top"), p("bottom")))
    t0 = time.perf_counter()
    r = solve(a)
    wall_ms = (time.perf_counter() - t0) * 1000
    assert r.poses["pin"].translation == pytest.approx((20.0, 20.0, 20.0), abs=1e-6)
    assert r.residual_mm < 1e-9
    assert r.status == "under" and r.dof == 1 and r.dof_by_component == {"pin": 1}
    assert wall_ms <= 200.0, f"solve took {wall_ms:.1f} ms"
    assert r.poses["block"] == Pose()  # grounded, untouched
    # nothing was mutated until the caller commits
    assert a.component("pin").pose == START
    apply_poses(a, r.poses)
    assert a.component("pin").pose.translation == pytest.approx((20.0, 20.0, 20.0), abs=1e-9)


def test_remove_one_mate_names_the_dof_per_component() -> None:
    a = pin_block()
    a.add_mate(Mate("insert1", "insert", b("hole"), p("axis")))
    a.add_mate(Mate("mate1", "mate", b("top"), p("bottom")))
    a.add_mate(Mate("clock", "angle", b("side_y"), p("flat"), angle_deg=90.0))
    full = solve(a)
    assert full.status == "ok" and full.dof == 0 and full.dof_by_component == {"pin": 0}
    a.remove_constraint("clock")
    r = solve(a)
    assert r.status == "under" and r.dof == 1
    assert r.dof_by_component == {"pin": 1}
    with pytest.raises(CommandError) as e:
        a.remove_constraint("clock")
    assert e.value.code == "pk_ref_unknown" and "insert1, mate1" in str(e.value)


def test_rigid_plus_contradictory_offset_names_the_later_mate() -> None:
    """The rigid joint stands the pin on the hole's top origin (bottom at z = 20);
    mate2 wants the same faces 5 mm apart: the LATER constraint is the conflict,
    and its residual is the full 5.000, not the least-squares split."""
    a = pin_block()
    a.add_joint(Joint("rigid1", "rigid", b("hole"), p("axis")))
    a.add_mate(Mate("mate2", "mate", b("top"), p("bottom"), offset_mm=5.0))
    r = solve(a)
    assert r.status == "conflict"
    assert r.over_constrained == ["mate2"]
    assert r.conflicts == [{"constraint": "mate2", "residual_mm": 5.0}]
    assert r.residual_mm == pytest.approx(5.0, abs=1e-9)
    # the poses satisfy the consistent subset (the rigid joint alone)
    assert r.poses["pin"] == Pose((20.0, 20.0, 20.0))
    assert r.dof == 0
    # the same two in the other order charge the joint instead
    other = pin_block()
    other.add_mate(Mate("mate2", "mate", b("top"), p("bottom"), offset_mm=5.0))
    other.add_joint(Joint("rigid1", "rigid", b("hole"), p("axis")))
    assert solve(other).over_constrained == ["rigid1"]


def test_redundant_constraint_is_named_not_conflicting() -> None:
    a = pin_block()
    a.add_mate(Mate("insert1", "insert", b("hole"), p("axis")))
    a.add_joint(Joint("cyl", "cylindrical", b("hole"), p("axis")))
    r = solve(a)
    assert r.status == "over"
    assert r.redundant == ["insert1", "cyl"]  # either alone would do the same work
    assert r.conflicts == [] and r.dof == 2


def test_no_grounded_component_counts_the_rigid_body_freedom() -> None:
    a = Assembly([Component("block", "block"), Component("pin", "pin")])
    a.add_mate(Mate("insert1", "insert", b("hole"), p("axis")))
    r = solve(a)
    assert r.status == "under" and r.dof == 12 - 4
    # a shared motion counts for every component it moves
    assert r.dof_by_component == {"block": 6, "pin": 6}


def test_opposed_faces_under_a_rigid_joint_flip_instead_of_stalling() -> None:
    """The exact antipode is a stationary point; the nudge retry turns it into a flip."""
    a = pin_block()
    a.add_joint(Joint("rigid1", "rigid", b("top"), p("bottom")))
    r = solve(a)
    assert r.status == "ok" and r.dof == 0 and r.residual_mm < 1e-9
    assert r.poses["pin"].vector((0, 0, 1)) == pytest.approx((0.0, 0.0, -1.0), abs=1e-9)


def test_rigid_and_slider_carry_the_angle_offset() -> None:
    a = pin_block()
    a.add_joint(Joint("rg", "rigid", b("hole"), p("axis"), offset_mm=-20.0, angle_deg=90.0))
    r = solve(a)
    assert r.status == "ok"
    assert r.poses["pin"].translation == pytest.approx((20.0, 20.0, 0.0), abs=1e-9)
    assert r.poses["pin"].vector((1, 0, 0)) == pytest.approx((0.0, 1.0, 0.0), abs=1e-9)
    s = pin_block()
    s.add_joint(Joint("sl", "slider", b("hole"), p("axis"), angle_deg=30.0, limits=(-5.0, 5.0)))
    r = solve(s)
    assert r.dof == 1
    assert r.poses["pin"].vector((1, 0, 0)) == pytest.approx(
        (np.cos(np.pi / 6), 0.5, 0.0), abs=1e-9
    )
    assert r.joint_values["sl"] == {"travel_mm": -13.0}  # started at z = 7, hole origin z = 20
    assert r.warnings == ["sl: -13 is outside limits [-5, 5]"]


def test_tangent_and_flush_rows() -> None:
    a = pin_block()
    a.add_mate(Mate("t", "tangent", b("side_x"), p("axis")))
    r = solve(a)
    assert r.poses["pin"].translation[0] == pytest.approx(45.0, abs=1e-9)  # r5 outside x = 40
    a = pin_block()
    a.add_mate(Mate("t", "tangent", b("hole"), p("axis")))
    t = solve(a).poses["pin"].translation
    assert ((t[0] - 20) ** 2 + (t[1] - 20) ** 2) ** 0.5 == pytest.approx(10.0, abs=1e-9)
    a = pin_block()
    a.add_mate(Mate("f", "flush", b("top"), p("top")))
    assert solve(a).poses["pin"].translation[2] == pytest.approx(-20.0, abs=1e-9)


def test_solving_twice_is_bit_identical() -> None:
    def build() -> Assembly:
        a = pin_block(Pose.from_axis_angle((1, 1, 0), 33.0, (3.0, -4.0, 7.0)))
        a.add_mate(Mate("insert1", "insert", b("hole"), p("axis")))
        a.add_mate(Mate("mate1", "mate", b("top"), p("bottom")))
        return a

    r1, r2 = solve(build()), solve(build())
    assert r1.poses == r2.poses
    assert r1.as_dict() == r2.as_dict()
    assert r1.poses["pin"].translation == pytest.approx((20.0, 20.0, 20.0), abs=1e-6)


def test_three_components_solve_within_200_ms() -> None:
    a = Assembly(
        [
            Component("block", "block", grounded=True),
            Component("pin1", "pin", pose=Pose((3.0, -4.0, 7.0))),
            Component("pin2", "pin", pose=Pose((30.0, 1.0, 2.0))),
        ]
    )
    hole2 = FrameRef("axis", (30.0, 10.0, 20.0), (0.0, 0.0, 1.0), radius=5.0)
    for name, hole in (("pin1", BLOCK["hole"]), ("pin2", hole2)):
        a.add_mate(Mate(f"i_{name}", "insert", Ref("block", hole), Ref(name, PIN["axis"])))
        a.add_mate(Mate(f"m_{name}", "mate", b("top"), Ref(name, PIN["bottom"])))
    t0 = time.perf_counter()
    r = solve(a)
    wall_ms = (time.perf_counter() - t0) * 1000
    assert wall_ms <= 200.0, f"{wall_ms:.1f} ms"
    assert r.dof == 2 and r.dof_by_component == {"pin1": 1, "pin2": 1}
    assert r.poses["pin2"].translation == pytest.approx((30.0, 10.0, 20.0), abs=1e-6)


# --------------------------------------------------------------------------- refusals


def test_refusals_name_reason_and_fix() -> None:
    a = pin_block()
    with pytest.raises(CommandError) as e:
        a.add_mate(Mate("x", "mate", Ref("bolt", BLOCK["top"]), p("bottom")))
    assert e.value.code == "pk_ref_unknown" and "block, pin" in str(e.value)
    with pytest.raises(CommandError) as e:
        Mate("x", "weld", b("top"), p("bottom"))
    assert e.value.code == "pk_bad_op" and "mate, flush, angle, tangent, insert" in str(e.value)
    with pytest.raises(CommandError) as e:
        Joint("x", "hinge", b("top"), p("bottom"))
    assert e.value.code == "pk_bad_op" and "revolute" in str(e.value)
    with pytest.raises(CommandError) as e:
        Mate("x", "mate", b("hole"), p("bottom"))
    assert e.value.code == "pk_spec_conflict" and "use insert" in str(e.value)
    with pytest.raises(CommandError) as e:
        Mate("x", "angle", b("top"), p("bottom"), angle_deg=180.0)
    assert e.value.code == "pk_needs" and "flush" in str(e.value)
    with pytest.raises(CommandError) as e:
        Mate("x", "tangent", b("top"), Ref("pin", FrameRef("axis", (0, 0, 0), (0, 0, 1))))
    assert e.value.code == "pk_needs" and "radius" in str(e.value)
    with pytest.raises(CommandError) as e:
        Mate("x", "mate", b("top"), Ref("block", BLOCK["side_x"]))
    assert e.value.code == "pk_spec_conflict" and "itself" in str(e.value)
    a.add_mate(Mate("m", "mate", b("top"), p("bottom")))
    with pytest.raises(CommandError) as e:
        a.add_joint(Joint("m", "ball", b("top"), p("bottom")))
    assert e.value.code == "pk_ref_ambiguous"
    with pytest.raises(CommandError) as e:
        a.add_component(Component("pin", "pin"))
    assert e.value.code == "pk_ref_ambiguous"
    with pytest.raises(CommandError) as e:
        Joint("x", "slider", b("hole"), p("axis"), limits=(5.0, -5.0))
    assert e.value.code == "pk_needs" and "reversed" in str(e.value)


def test_assembly_import_is_ocp_free() -> None:
    code = (
        "import sys\n"
        "import partkiln.assembly, partkiln.assembly.solver, partkiln.assembly.bom\n"
        "import partkiln.assembly.interference\n"
        "from partkiln.assembly import Assembly, Component, FrameRef, Mate, Ref, solve\n"
        "f = FrameRef('axis', (0, 0, 0), (0, 0, 1))\n"
        "a = Assembly([Component('a', 'a', grounded=True), Component('b', 'b')])\n"
        "a.add_mate(Mate('m', 'insert', Ref('a', f), Ref('b', f)))\n"
        "print(solve(a).dof)\n"
        "bad = [m for m in sys.modules\n"
        "       if m.split('.')[0] in ('OCP', 'tee', 'cadquery', 'casadi')]\n"
        "print(sorted(bad))\n"
    )
    root = Path(__file__).resolve().parents[1] / "src"
    out = subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True,
        text=True,
        env={"PYTHONPATH": str(root), "PATH": "/usr/bin:/bin"},
        check=True,
    )
    assert out.stdout.split() == ["2", "[]"], out.stdout


# --------------------------------------------------------------------------- frames from the B-rep


@pytest.mark.brep
def test_frames_read_from_f6_geometry_land_on_the_same_pose() -> None:
    """The hand-typed frames above ARE the fixture's: derive them from F6's faces
    and edges (as naming.py will) and solve to the same (20, 20, 20)."""
    pytest.importorskip("OCP", reason="partkiln[brep] not installed")
    from partkiln.brep import fixtures, query, shapes

    block, _fixture_pin = fixtures.build_F6()
    pin = shapes.cylinder(5.0, 40.0)  # the pin in its own frame

    def plane(shape, normal):
        f = next(
            f
            for f in query.faces(shape)
            if f.surface_type == "plane" and f.normal == pytest.approx(normal, abs=1e-9)
        )
        return FrameRef("plane", f.centroid, f.normal)

    def axis(shape, radius):
        rings = [
            e
            for e in query.edges(shape)
            if e.curve_type == "circle" and abs(e.radius - radius) < 1e-9
        ]
        centres = sorted(
            {
                tuple(round((f.bbox[i] + f.bbox[i + 3]) / 2, 9) for i in range(3))
                for f in query.faces(shape)
                if f.surface_type == "cylinder" and abs(f.radius - radius) < 1e-9
            }
        )
        lo = min(min(e.midpoint[2] for e in rings), centres[0][2])
        hi = max(e.midpoint[2] for e in rings)
        c = centres[0]
        return FrameRef("axis", (c[0], c[1], hi), (0.0, 0.0, hi - lo), radius=radius)

    a = pin_block()
    a.add_mate(
        Mate("insert1", "insert", Ref("block", axis(block, 5.0)), Ref("pin", axis(pin, 5.0)))
    )
    a.add_mate(
        Mate(
            "mate1",
            "mate",
            Ref("block", plane(block, (0, 0, 1))),
            Ref("pin", plane(pin, (0, 0, -1))),
        )
    )
    r = solve(a)
    assert r.status == "under" and r.dof == 1
    assert r.residual_mm < CONVERGED_MM
    assert r.poses["pin"].translation == pytest.approx((20.0, 20.0, 20.0), abs=1e-6)
