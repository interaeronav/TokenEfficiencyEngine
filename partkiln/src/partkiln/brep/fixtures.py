"""The measured fixtures of A66 (P0a, 2026-09-02) as builders, so every test
and benchmark pins the same numbers.

  F1  100x60x10 plate minus a d10 through hole at (50, 30):
      V 59 214.602 mm3, 7 faces, 15 edges, area 15 357.080, COM (50, 30, 5).
  F2  L bracket: 80x60x6 base fused with an 80x6x34 upright at z=6, unified
      (13 faces only after UnifySameDomain), inner fillet r6 on the edge at
      y=6, z=6, then 4 x d6.6 through holes: V 44 916.967, 13 faces, 33 edges.
  F5  220x220x12 plate with 10x10 d8 holes at pitch 20 from (20, 20) as ONE
      n-ary cut: V 520 481.421, 106 faces, 312 unique edges, ~0.1 s.
  F6  40x40x20 block with a d10 through hole at its centre (30 429.204) and a
      d10 x 40 pin (3 141.593); a d11 pin interferes by 329.867.
  W3  120x80x10 plate, 12 x d6 at (15+30i, 20+20j), EVERY edge filleted r1:
      the HLR trap fixture (62 faces).
"""

from __future__ import annotations

from partkiln._errors import KernelError
from partkiln.brep import require_ocp

require_ocp()

from OCP.TopoDS import TopoDS_Edge, TopoDS_Shape  # noqa: E402

from partkiln.brep import query, shapes  # noqa: E402


def edge_at(
    shape: TopoDS_Shape, midpoint: tuple[float, float, float], tol: float = 1e-6
) -> TopoDS_Edge:
    """The one edge whose mid-parameter point is `midpoint` (a test helper)."""
    hits = [
        e
        for e in query.edges(shape)
        if all(abs(a - b) <= tol for a, b in zip(e.midpoint, midpoint, strict=True))
    ]
    if len(hits) != 1:
        raise KernelError(
            f"expected one edge at {midpoint}, found {len(hits)}.", fix="check the point"
        )
    return hits[0].shape


def build_F1() -> TopoDS_Shape:
    plate = shapes.box(100, 60, 10)
    hole = shapes.cylinder(5, 12, (50, 30, -1))
    return shapes.cut(plate, [hole]).shape


def build_F2() -> TopoDS_Shape:
    base = shapes.box(80, 60, 6)
    upright = shapes.box(80, 6, 34, (0, 0, 6))
    fused, _ = shapes.unify(shapes.fuse([base, upright]).shape)
    inner = edge_at(fused, (40.0, 6.0, 6.0))
    filleted = shapes.fillet(fused, [inner], 6.0).shape
    holes = [
        shapes.cylinder(3.3, 8, (x, y, -1)) for x, y in ((20, 30), (60, 30), (20, 50), (60, 50))
    ]
    return shapes.cut(filleted, holes).shape


def f5_tools() -> list[TopoDS_Shape]:
    return [
        shapes.cylinder(4, 14, (20 + 20 * i, 20 + 20 * j, -1)) for i in range(10) for j in range(10)
    ]


def build_F5() -> TopoDS_Shape:
    return shapes.cut(shapes.box(220, 220, 12), f5_tools()).shape


def build_F6() -> tuple[TopoDS_Shape, TopoDS_Shape]:
    block = shapes.cut(shapes.box(40, 40, 20), [shapes.cylinder(5, 22, (20, 20, -1))]).shape
    pin = shapes.cylinder(5, 40, (20, 20, -10))
    return block, pin


def build_W3() -> TopoDS_Shape:
    holes = [
        shapes.cylinder(3, 12, (15 + 30 * i, 20 + 20 * j, -1)) for i in range(4) for j in range(3)
    ]
    plate = shapes.cut(shapes.box(120, 80, 10), holes).shape
    edges = [e.shape for e in query.edges(plate) if not e.is_seam]
    return shapes.fillet(plate, edges, 1.0).shape


__all__ = ["build_F1", "build_F2", "build_F5", "build_F6", "build_W3", "edge_at", "f5_tools"]
