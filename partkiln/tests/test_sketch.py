"""P1 acceptance for the sketch model and its solver (A66 script, P1)."""

from __future__ import annotations

import math
import time

import numpy as np
import pytest

from partkiln.document import CommandError
from partkiln.sketch import Arc, Circle, Line, Point, Sketch, expand
from partkiln.sketch.solver import jacobian, numeric_jacobian


def rectangle(*, w: float = 100.0, h: float = 60.0, dims: int = 2) -> Sketch:
    """The acceptance rectangle: four lines, H/V, `dims` length dimensions, unanchored."""
    sk = Sketch("r", "XY")
    for k, (x, y) in enumerate([(0, 0), (w, 0), (w, h), (0, h)]):
        sk.add(Point(f"p{k}", x, y))
    for k in range(4):
        sk.add(Line(f"l{k}", f"p{k}", f"p{(k + 1) % 4}"))
    sk.constrain("horizontal", "l0", tag="h0")
    sk.constrain("vertical", "l1", tag="v1")
    sk.constrain("horizontal", "l2", tag="h2")
    sk.constrain("vertical", "l3", tag="v3")
    if dims >= 1:
        sk.dimension("len", "l0", value=w, tag="dw")
    if dims >= 2:
        sk.dimension("len", "l1", value=h, tag="dh")
    return sk


def test_unanchored_rectangle_has_two_dof() -> None:
    sk = rectangle()
    report = sk.solve()
    assert report.dof == 2
    assert report.status == "under"
    assert report.residual_max_mm < 1e-6


def test_fixing_a_corner_solves_to_the_closed_form() -> None:
    sk = rectangle()
    # start away from the answer so the solver has to move
    sk.point("p1").x, sk.point("p1").y = 80.0, 7.0
    sk.point("p2").x, sk.point("p2").y = 90.0, 50.0
    sk.point("p3").x, sk.point("p3").y = -3.0, 70.0
    sk.constrain("fix", "p0")
    report = sk.solve()
    assert report.dof == 0
    assert report.status == "ok"
    expected = {"p0": (0, 0), "p1": (100, 0), "p2": (100, 60), "p3": (0, 60)}
    for tag, (x, y) in expected.items():
        assert abs(sk.point(tag).x - x) < 1e-6, tag
        assert abs(sk.point(tag).y - y) < 1e-6, tag
    assert sk.closed()
    assert sk.area_mm2() == pytest.approx(6000.0, abs=1e-6)
    assert report.iterations > 0


def test_minus_one_distance_is_under() -> None:
    sk = rectangle(dims=1)
    sk.constrain("fix", "p0")
    report = sk.solve()
    assert report.dof == 1
    assert report.status == "under"


def test_conflicting_dimension_names_both() -> None:
    sk = rectangle()
    sk.constrain("fix", "p0")
    sk.dimension("len", "l3", value=61.0, tag="d61")
    report = sk.solve()
    assert report.status == "conflict"
    assert report.residual_max_mm >= 1e-6
    assert any(c.startswith("dh ") for c in report.conflicts), report.conflicts
    assert any(c.startswith("d61 ") for c in report.conflicts), report.conflicts
    assert not any(c.startswith("dw ") for c in report.conflicts)
    assert "=61" in " ".join(report.conflicts)  # the geometry, not just a tag


def test_conflict_search_on_sixty_rows_under_200ms() -> None:
    """The leave-one-out search is capped (CONFLICT_SEARCH_CAP) so naming a
    conflict on a 60-row sketch stays under the 200 ms budget the solver
    docstring promises; this pins the number instead of trusting the prose."""
    from partkiln.sketch.solver import CONFLICT_SEARCH_CAP

    def build() -> Sketch:
        sk = Sketch("grid", "XY")
        for n in range(10):
            ox, oy = (n % 5) * 150.0, (n // 5) * 100.0
            for k, (x, y) in enumerate(
                [(ox, oy), (ox + 100, oy), (ox + 100, oy + 60), (ox, oy + 60)]
            ):
                sk.add(Point(f"r{n}.p{k}", x, y))
            for k in range(4):
                sk.add(Line(f"r{n}.{k}", f"r{n}.p{k}", f"r{n}.p{(k + 1) % 4}"))
            sk.constrain("horizontal", f"r{n}.0")
            sk.constrain("vertical", f"r{n}.1")
            sk.constrain("horizontal", f"r{n}.2")
            sk.constrain("vertical", f"r{n}.3")
            sk.dimension("len", f"r{n}.0", value=100.0, tag=f"r{n}.w")
            sk.dimension("len", f"r{n}.1", value=60.0, tag=f"r{n}.h")
            sk.constrain("fix", f"r{n}.p0")
        sk.dimension("len", "r9.3", value=61.0, tag="bad")  # the one bad dimension
        return sk

    build().solve()  # warm
    best = math.inf
    for _ in range(3):
        sk = build()
        t0 = time.perf_counter()
        report = sk.solve()
        best = min(best, time.perf_counter() - t0)
    assert report.status == "conflict"
    assert any(c.startswith("bad ") for c in report.conflicts), report.conflicts
    assert any(c.startswith("r9.h ") for c in report.conflicts), report.conflicts
    assert len(report.conflicts) <= CONFLICT_SEARCH_CAP
    assert best < 0.200, f"conflict search took {best * 1000:.1f} ms (budget 200 ms)"
    print(f"\n60-row conflict search named the bad dim in {best * 1000:.2f} ms")


def test_duplicated_horizontal_is_redundant() -> None:
    sk = rectangle()
    sk.constrain("fix", "p0")
    sk.constrain("horizontal", "l0", tag="again")
    report = sk.solve()
    assert report.status == "over"
    assert report.dof == 0
    assert any(r.startswith("again ") for r in report.redundant), report.redundant
    # its twin is equally droppable, and the report says so
    assert any(r.startswith("h0 ") for r in report.redundant)


def test_equal_on_an_hv_rectangle_is_redundant() -> None:
    """Opposite sides of an H/V rectangle are already equal; `equal` adds no rank."""
    sk = rectangle()
    sk.constrain("fix", "p0")
    sk.constrain("equal", "l0", "l2", tag="eq")
    report = sk.solve()
    assert report.dof == 0
    assert any(r.startswith("eq ") for r in report.redundant)


def test_forty_entities_sixty_constraints_under_50ms() -> None:
    """Ten rectangles, each from a deliberately wrong initial guess."""

    def build() -> Sketch:
        sk = Sketch("grid", "XY")
        for n in range(10):
            ox = (n % 5) * 150.0
            oy = (n // 5) * 100.0
            guess = [(ox, oy), (ox + 10, oy + 3), (ox + 12, oy + 9), (ox - 2, oy + 8)]
            for k, (x, y) in enumerate(guess):
                sk.add(Point(f"r{n}.p{k}", x, y))
            for k in range(4):
                sk.add(Line(f"r{n}.{k}", f"r{n}.p{k}", f"r{n}.p{(k + 1) % 4}"))
            sk.constrain("horizontal", f"r{n}.0")
            sk.constrain("vertical", f"r{n}.1")
            sk.constrain("horizontal", f"r{n}.2")
            sk.constrain("vertical", f"r{n}.3")
            sk.dimension("len", f"r{n}.0", value=100.0 + n)
            sk.dimension("len", f"r{n}.1", value=60.0 + n)
            sk.constrain("fix", f"r{n}.p0")
        return sk

    assert len(build().curves()) == 40
    assert len(build().constraints) + len(build().dims) == 70  # 60 + the ten anchors
    build().solve()  # warm: scipy imported, code paths compiled
    best = math.inf
    for _ in range(3):
        sk = build()
        t0 = time.perf_counter()
        report = sk.solve()
        best = min(best, time.perf_counter() - t0)
    assert report.status == "ok"
    assert report.dof == 0
    assert sk.point("r9.p2").x == pytest.approx(600.0 + 109.0, abs=1e-6)
    assert best < 0.050, f"solve took {best * 1000:.1f} ms (budget 50 ms)"
    print(f"\n40-entity / 60-constraint sketch solved in {best * 1000:.2f} ms")


def test_analytic_jacobian_matches_finite_differences() -> None:
    """Every term kind at once, at a generic (unsolved) configuration."""
    sk = Sketch("mix", "XY")
    pts = {
        "a": (0, 0), "b": (10, 1), "c": (3, 8), "d": (11, 9), "e": (5, 4), "f": (20, 2),
        "g": (25, 5), "h": (22, 9), "cc": (30, 30), "s": (36, 31), "t": (31, 37), "u": (40, 40),
        "v": (45, 41), "w": (41, 47),
    }  # fmt: skip
    for tag, (x, y) in pts.items():
        sk.add(Point(tag, float(x), float(y)))
    sk.add(Line("l1", "a", "b"))
    sk.add(Line("l2", "c", "d"))
    sk.add(Line("l3", "f", "g"))
    sk.add(Arc("arc", "cc", "s", "t"))
    sk.add(Arc("arc2", "u", "t", "w"))
    sk.add(Circle("circ", "e", 3.0))
    sk.constrain("parallel", "l1", "l2")
    sk.constrain("perpendicular", "l1", "l3")
    sk.constrain("collinear", "l1", "l2")
    sk.constrain("tangent", "l3", "circ")
    sk.constrain("tangent", "l2", "arc")
    sk.constrain("symmetric", "c", "h", "l1")
    sk.constrain("coincident", "e", "l3")
    sk.constrain("coincident", "h", "circ")
    sk.constrain("concentric", "arc", "circ")
    sk.constrain("equal", "arc", "circ")
    sk.constrain("equal", "l1", "l2")
    sk.constrain("smooth", "arc", "arc2")
    sk.constrain("horizontal", "l3")
    sk.constrain("vertical", "a", "c")
    sk.dimension("len", "l1", value=12)
    sk.dimension("dist", "a", "d", value=5)
    sk.dimension("dist", "a", "d", value=5, axis="X")
    sk.dimension("dist", "a", "d", value=5, axis="Y")
    sk.dimension("dist", "e", "l2", value=2)
    sk.dimension("angle", "l1", "l2", value=30)
    sk.dimension("dia", "circ", value=6)
    sk.dimension("rad", "arc", value=6)
    _f, J, owners = jacobian(sk)
    Jn = numeric_jacobian(sk)
    worst = np.max(np.abs(J - Jn))
    assert worst < 1e-5, (
        f"max |analytic - numeric| = {worst:.2e} at row "
        f"{owners[int(np.argmax(np.max(np.abs(J - Jn), axis=1)))]}"
    )


def test_presets_rect_circle_slot_polygon_poly() -> None:
    def mm(v):
        return float(v)

    sk = Sketch("all", "XY")
    for spec in (
        {"rect": [100, 60], "tag": "r"},
        {"circle": 20, "at": [50, 30], "tag": "c"},
        {"slot": [40, 10], "at": [200, 0], "tag": "s"},
        {"polygon": 6, "d": 30, "at": [300, 0], "tag": "g"},
        {"poly": [[0, 200], [50, 200], [25, 240]], "tag": "t"},
    ):
        exp = expand(spec, length=mm, angle=mm, existing=sk.tags())
        for e in exp.entities:
            sk.add(e)
        for kind, refs, tag in exp.constraints:
            sk.constrain(kind, *refs, tag=tag)
        for kind, refs, value, tag, axis, expr in exp.dims:
            sk.dimension(kind, *refs, value=value, tag=tag, axis=axis, expr=expr)
    report = sk.solve()
    assert report.status == "ok", (report.status, report.conflicts, report.redundant)
    assert report.dof == 0
    assert sk.closed()
    assert len(sk.loops()) == 5
    areas = sorted(abs(sk.loop_area(lp)) for lp in sk.loops())
    slot = 30 * 10 + math.pi * 25
    hexagon = 6 / 2 * 15**2 * math.sin(math.radians(60))
    assert areas == pytest.approx(sorted([6000.0, math.pi * 100, slot, hexagon, 1000.0]), abs=1e-6)
    assert sk.area_mm2() == pytest.approx(6000.0)


def test_slot_at_an_angle_and_set_dim() -> None:
    def mm(v):
        return float(v)

    sk = Sketch("s", "XY")
    exp = expand({"slot": [40, 10], "angle": 30, "tag": "s"}, length=mm, angle=mm)
    for e in exp.entities:
        sk.add(e)
    for kind, refs, tag in exp.constraints:
        sk.constrain(kind, *refs, tag=tag)
    for kind, refs, value, tag, axis, expr in exp.dims:
        sk.dimension(kind, *refs, value=value, tag=tag, axis=axis, expr=expr)
    report = sk.solve()
    assert (report.status, report.dof) == ("ok", 0)
    assert sk.area_mm2() == pytest.approx(300 + math.pi * 25, abs=1e-6)
    sk.set_dim("s.w", 20.0)
    report = sk.solve()
    assert report.status == "ok"
    assert sk.radius("s.a0") == pytest.approx(10.0, abs=1e-6)


def test_driven_dimension_measures_and_never_constrains() -> None:
    sk = rectangle()
    sk.constrain("fix", "p0")
    sk.dimension("dist", "p0", "p2", value=1.0, driven=True, tag="diag")
    report = sk.solve()
    assert report.status == "ok"
    assert sk.report()["driven"]["diag"] == pytest.approx(math.hypot(100, 60), abs=1e-6)
    assert sk.report()["dims"] == 2


def test_report_is_compact_and_has_no_coordinates() -> None:
    sk = rectangle()
    sk.constrain("fix", "p0")
    report = sk.report()
    assert set(report) >= {
        "entities", "constraints", "dof", "status", "conflicts", "redundant",
        "closed", "area_mm2", "frame",
    }  # fmt: skip
    assert report["frame"] == "XY"
    assert report["entities"] == 8
    assert not any(
        isinstance(v, list) and v and isinstance(v[0], int | float) for v in report.values()
    )


def test_refusals_name_the_fix() -> None:
    sk = rectangle()
    with pytest.raises(CommandError, match="Constraints:"):
        sk.constrain("wobbly", "l0")
    with pytest.raises(CommandError, match="needs two lines"):
        sk.constrain("parallel", "l0", "p0")
    with pytest.raises(CommandError, match="Entities:"):
        sk.constrain("horizontal", "nope")
    with pytest.raises(CommandError, match="already used"):
        sk.add(Point("p0", 1, 1))
    with pytest.raises(CommandError, match="Dimensions:"):
        sk.dimension("area", "l0", value=1)
    with pytest.raises(CommandError, match="share no endpoint"):
        sk.add(Point("q", 5, 5))
        sk.add(Point("q2", 6, 6))
        sk.add(Point("q3", 7, 7))
        sk.add(Arc("a1", "q", "p0", "p1"))
        sk.add(Arc("a2", "q2", "q3", "p2"))
        sk.constrain("smooth", "a1", "a2")
    with pytest.raises(CommandError, match="plane"):
        Sketch("bad", "ZZ")


def test_coincident_corners_close_a_loop_and_a_circle_is_its_own_loop() -> None:
    sk = Sketch("tri", "XY")
    sk.add(Point("a", 0, 0, fixed=True))
    sk.add(Point("b", 10, 0, fixed=True))
    sk.add(Point("c", 0, 10, fixed=True))
    sk.add(Point("c2", 0, 10))
    sk.add(Line("l0", "a", "b"))
    sk.add(Line("l1", "b", "c"))
    sk.add(Line("l2", "c2", "a"))
    sk.constrain("coincident", "c", "c2")
    sk.add(Point("o", 50, 50, fixed=True))
    sk.add(Circle("ring", "o", 5))
    sk.dimension("rad", "ring", value=5)
    sk.solve()
    assert sk.closed()
    assert len(sk.loops()) == 2
    assert sk.area_mm2() == pytest.approx(math.pi * 25)
