"""A structured O-mesh around a closed section, written for SU2 and for
OpenFOAM - one mesher, two solvers, no external tool.

Rays leave every surface node along a direction that blends from the local
(smoothed) surface normal at the wall to the radial direction of a circle
of radius `radius_c` chords about the mid-chord point at the farfield, so
the first cells are orthogonal to the wall (what y+ control needs) and the
outer boundary is a circle (what a freestream condition wants). Radial
spacing is a geometric progression from the first-cell height with the
growth ratio capped at `max_growth` (ERCOFTAC BPG: keep expansion ratios at
or below ~1.2); when the requested first cell and layer count cannot reach
the farfield within that ratio the layer count is raised and reported.
Construction follows the transfinite/algebraic family in Thompson, Warsi &
Mastin, Numerical Grid Generation (1985), ch. 3.

Stdlib only: a 200 x 100 grid is 20,000 nodes, which Python loops write in
well under a second.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from pathlib import Path

Point = tuple[float, float]


@dataclass
class OMesh:
    ni: int  # nodes around (periodic)
    nj: int  # radial cells
    xy: list[list[Point]] = field(default_factory=list)  # xy[j][i], j = 0 at the wall
    growth: float = 1.0
    first_cell: float = 0.0
    radius_c: float = 0.0
    notes: list[str] = field(default_factory=list)

    @property
    def cells(self) -> int:
        return self.ni * self.nj

    @property
    def nodes(self) -> int:
        return self.ni * (self.nj + 1)

    def node(self, i: int, j: int) -> Point:
        return self.xy[j][i % self.ni]

    def quad(self, i: int, j: int) -> tuple[Point, Point, Point, Point]:
        """Cell (i, j) with COUNTER-CLOCKWISE node order. The section runs
        CCW with the body on its left, so "outward" (j + 1) lies to the right
        of travel and the positive traversal is (i,j) -> (i,j+1) ->
        (i+1,j+1) -> (i+1,j)."""
        return (self.node(i, j), self.node(i, j + 1), self.node(i + 1, j + 1), self.node(i + 1, j))

    def min_jacobian(self) -> float:
        """The smallest signed cell area (a positive minimum means no
        inverted cell anywhere)."""
        worst = math.inf
        for j in range(self.nj):
            for i in range(self.ni):
                a, b, c, d = self.quad(i, j)
                area = 0.5 * (
                    (a[0] * b[1] - b[0] * a[1])
                    + (b[0] * c[1] - c[0] * b[1])
                    + (c[0] * d[1] - d[0] * c[1])
                    + (d[0] * a[1] - a[0] * d[1])
                )
                worst = min(worst, area)
        return worst

    def first_layer_heights(self) -> tuple[float, float]:
        hs = [math.dist(self.node(i, 0), self.node(i, 1)) for i in range(self.ni)]
        return min(hs), max(hs)


def geometric_growth(distance: float, first: float, n: int) -> float:
    """The ratio r with first (1 + r + ... + r^(n-1)) = distance, by bisection."""
    if first * n >= distance:
        return 1.0
    lo, hi = 1.0, 3.0
    for _ in range(80):
        mid = 0.5 * (lo + hi)
        total = first * (mid**n - 1.0) / (mid - 1.0)
        if total < distance:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


def omesh(
    loop: list[Point],
    *,
    first_cell: float,
    nj: int = 100,
    radius_c: float = 50.0,
    max_growth: float = 1.2,
    chord: float = 1.0,
) -> OMesh:
    """Build the O-mesh around a CCW loop (chord-normalised coordinates,
    scaled by `chord` on output)."""
    from tee.windtunnel.airfoil import ccw

    pts = ccw(loop)
    ni = len(pts)
    if ni < 12:
        raise ValueError("a section needs at least 12 points")
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    centre = (0.5 * (max(xs) + min(xs)), 0.5 * (max(ys) + min(ys)))
    R = radius_c * (max(xs) - min(xs))

    # outward normals at nodes (CCW loop: outward = right-hand side of travel)
    normals: list[Point] = []
    for i in range(ni):
        (x0, y0), (x1, y1) = pts[i - 1], pts[(i + 1) % ni]
        tx, ty = x1 - x0, y1 - y0
        mag = math.hypot(tx, ty) or 1.0
        normals.append((ty / mag, -tx / mag))
    for _ in range(3):  # smooth so neighbouring rays never cross near a sharp edge
        normals = [
            _unit(
                (
                    0.5 * normals[i][0] + 0.25 * (normals[i - 1][0] + normals[(i + 1) % ni][0]),
                    0.5 * normals[i][1] + 0.25 * (normals[i - 1][1] + normals[(i + 1) % ni][1]),
                )
            )
            for i in range(ni)
        ]

    # Farfield points: spread around the circle in proportion to arc length
    # along the section (measured 2026-09-06: mapping by the angle from the
    # mid-chord point instead put the trailing-edge rays almost parallel and
    # left eight faces with skewness 15). Angle 0 is the first node (the TE).
    arcs = [0.0]
    for i in range(1, ni):
        arcs.append(arcs[-1] + math.dist(pts[i - 1], pts[i]))
    total = arcs[-1] + math.dist(pts[-1], pts[0])
    theta0 = math.atan2(pts[0][1] - centre[1], pts[0][0] - centre[0])
    dists = []
    outer: list[Point] = []
    for i in range(ni):
        theta = theta0 + 2.0 * math.pi * arcs[i] / total
        far = (centre[0] + R * math.cos(theta), centre[1] + R * math.sin(theta))
        outer.append(far)
        dists.append(math.dist(pts[i], far))
    dmin = min(dists)
    notes: list[str] = []
    h1 = first_cell / chord
    growth = geometric_growth(dmin, h1, nj)
    while growth > max_growth:
        nj += 10
        growth = geometric_growth(dmin, h1, nj)
    t_of_j = [0.0]
    acc = 0.0
    for j in range(nj):
        acc += h1 * growth**j
        t_of_j.append(
            acc / (h1 * (growth**nj - 1.0) / (growth - 1.0)) if growth > 1.0 else (j + 1) / nj
        )
    t_of_j[-1] = 1.0
    if growth == 1.0:
        notes.append("first cell too large for a geometric progression; uniform spacing used")

    rows: list[list[Point]] = []
    for j in range(nj + 1):
        t = t_of_j[j]
        row: list[Point] = []
        for i in range(ni):
            d = dists[i] * t
            e = _unit((outer[i][0] - pts[i][0], outer[i][1] - pts[i][1]))
            w = t * t * (3.0 - 2.0 * t)  # smoothstep: normal at the wall, radial far away
            direction = _unit(
                ((1.0 - w) * normals[i][0] + w * e[0], (1.0 - w) * normals[i][1] + w * e[1])
            )
            row.append((pts[i][0] + d * direction[0], pts[i][1] + d * direction[1]))
        rows.append(row)
    rows[nj] = outer  # the farfield is exactly the circle
    scaled = [[(x * chord, y * chord) for x, y in row] for row in rows]
    return OMesh(
        ni=ni,
        nj=nj,
        xy=scaled,
        growth=growth,
        first_cell=first_cell,
        radius_c=radius_c,
        notes=notes,
    )


def _unit(v: Point) -> Point:
    mag = math.hypot(v[0], v[1]) or 1.0
    return (v[0] / mag, v[1] / mag)


# ---------------------------------------------------------------------------
# SU2 native format (SU2 user guide, "Mesh File"): VTK element ids, quads = 9,
# lines = 3; markers list boundary elements.
# ---------------------------------------------------------------------------


def write_su2(
    path: str | Path, mesh: OMesh, *, wall: str = "airfoil", far: str = "farfield"
) -> int:
    ni, nj = mesh.ni, mesh.nj

    def nid(i: int, j: int) -> int:
        return j * ni + (i % ni)

    lines = ["NDIME= 2", f"NELEM= {mesh.cells}"]
    k = 0
    for j in range(nj):
        for i in range(ni):
            lines.append(f"9 {nid(i, j)} {nid(i, j + 1)} {nid(i + 1, j + 1)} {nid(i + 1, j)} {k}")
            k += 1
    lines.append(f"NPOIN= {mesh.nodes}")
    k = 0
    for j in range(nj + 1):
        for i in range(ni):
            x, y = mesh.xy[j][i]
            lines.append(f"{x:.12g} {y:.12g} {k}")
            k += 1
    lines.append("NMARK= 2")
    lines.append(f"MARKER_TAG= {wall}")
    lines.append(f"MARKER_ELEMS= {ni}")
    for i in range(ni):
        lines.append(f"3 {nid(i, 0)} {nid(i + 1, 0)}")
    lines.append(f"MARKER_TAG= {far}")
    lines.append(f"MARKER_ELEMS= {ni}")
    for i in range(ni):
        lines.append(f"3 {nid(i, nj)} {nid(i + 1, nj)}")
    text = "\n".join(lines) + "\n"
    Path(path).write_text(text)
    return len(text)


def read_su2_counts(path: str | Path) -> dict[str, int]:
    counts: dict[str, int] = {}
    with open(path) as fh:
        for line in fh:
            if line.startswith(("NDIME=", "NELEM=", "NPOIN=", "NMARK=")):
                key, val = line.split("=")
                counts[key.strip()] = int(val.split()[0])
    return counts


# ---------------------------------------------------------------------------
# OpenFOAM polyMesh (OpenFOAM user guide §4.3 "Mesh description"): one cell
# thick in z, faces in upper-triangular order, empty front/back patches.
# ---------------------------------------------------------------------------

_FOAM_HEADER = """/*--------------------------------*- C++ -*----------------------------------*\\
| generated-by: tee.windtunnel.mesh2d                                          |
\\*---------------------------------------------------------------------------*/
FoamFile
{{
    version     2.0;
    format      ascii;
    class       {cls};
    location    "constant/polyMesh";
    object      {obj};
}}
"""


def write_polymesh(
    case_dir: str | Path,
    mesh: OMesh,
    *,
    wall: str = "airfoil",
    far: str = "farfield",
    empty: str = "frontAndBack",
    thickness: float | None = None,
) -> dict[str, int]:
    """Writes constant/polyMesh/{points,faces,owner,neighbour,boundary}.
    Returns the counts checkMesh will report."""
    ni, nj = mesh.ni, mesh.nj
    dz = thickness if thickness is not None else _default_thickness(mesh)
    npl = ni * (nj + 1)  # points per layer

    def pid(i: int, j: int, k: int) -> int:
        return k * npl + j * ni + (i % ni)

    def cid(i: int, j: int) -> int:
        return j * ni + (i % ni)

    points: list[tuple[float, float, float]] = []
    for _k, z in enumerate((0.0, dz)):
        for j in range(nj + 1):
            for i in range(ni):
                x, y = mesh.xy[j][i]
                points.append((x, y, z))

    def centre(c: int) -> tuple[float, float, float]:
        j, i = divmod(c, ni)
        ps = [mesh.node(i, j), mesh.node(i + 1, j), mesh.node(i + 1, j + 1), mesh.node(i, j + 1)]
        return (sum(p[0] for p in ps) / 4.0, sum(p[1] for p in ps) / 4.0, 0.5 * dz)

    def oriented(face: list[int], owner: int, neighbour: int | None) -> list[int]:
        # the face normal must point away from the owner (into the neighbour)
        p0, p1, p2 = points[face[0]], points[face[1]], points[face[2]]
        ux, uy, uz = p1[0] - p0[0], p1[1] - p0[1], p1[2] - p0[2]
        vx, vy, vz = p2[0] - p0[0], p2[1] - p0[1], p2[2] - p0[2]
        nx, ny, nz = uy * vz - uz * vy, uz * vx - ux * vz, ux * vy - uy * vx
        fc = (
            sum(points[q][0] for q in face) / 4.0,
            sum(points[q][1] for q in face) / 4.0,
            sum(points[q][2] for q in face) / 4.0,
        )
        oc = centre(owner)
        d = (fc[0] - oc[0], fc[1] - oc[1], fc[2] - oc[2])
        if nx * d[0] + ny * d[1] + nz * d[2] < 0:
            face = list(reversed(face))
        return face

    internal: list[tuple[int, int, list[int]]] = []  # (owner, neighbour, face)
    wall_faces: list[tuple[int, list[int]]] = []
    far_faces: list[tuple[int, list[int]]] = []
    empty_faces: list[tuple[int, list[int]]] = []
    for j in range(nj):
        for i in range(ni):
            c = cid(i, j)
            # east face (between i and i+1) - internal, periodic at i = ni-1
            east = [pid(i + 1, j, 0), pid(i + 1, j + 1, 0), pid(i + 1, j + 1, 1), pid(i + 1, j, 1)]
            nb = cid(i + 1, j)
            if nb > c:
                internal.append((c, nb, east))
            else:  # wrap: the face is owned by the lower cell id
                internal.append((nb, c, east))
            # north face (between j and j+1)
            north = [pid(i, j + 1, 0), pid(i + 1, j + 1, 0), pid(i + 1, j + 1, 1), pid(i, j + 1, 1)]
            if j + 1 < nj:
                internal.append((c, cid(i, j + 1), north))
            else:
                far_faces.append((c, north))
            if j == 0:
                south = [pid(i, 0, 0), pid(i + 1, 0, 0), pid(i + 1, 0, 1), pid(i, 0, 1)]
                wall_faces.append((c, south))
            empty_faces.append(
                (c, [pid(i, j, 0), pid(i + 1, j, 0), pid(i + 1, j + 1, 0), pid(i, j + 1, 0)])
            )
            empty_faces.append(
                (c, [pid(i, j, 1), pid(i + 1, j, 1), pid(i + 1, j + 1, 1), pid(i, j + 1, 1)])
            )
    internal.sort(key=lambda t: (t[0], t[1]))
    faces: list[list[int]] = []
    owner: list[int] = []
    neighbour: list[int] = []
    for o, n, f in internal:
        faces.append(oriented(f, o, n))
        owner.append(o)
        neighbour.append(n)
    n_internal = len(faces)
    patches = []
    for name, ptype, group in (
        (wall, "wall", wall_faces),
        (far, "patch", far_faces),
        (empty, "empty", empty_faces),
    ):
        start = len(faces)
        for o, f in group:
            faces.append(oriented(f, o, None))
            owner.append(o)
        patches.append((name, ptype, start, len(faces) - start))

    pm = Path(case_dir) / "constant" / "polyMesh"
    pm.mkdir(parents=True, exist_ok=True)
    (pm / "points").write_text(
        _FOAM_HEADER.format(cls="vectorField", obj="points")
        + f"\n{len(points)}\n(\n"
        + "\n".join(f"({x:.12g} {y:.12g} {z:.12g})" for x, y, z in points)
        + "\n)\n"
    )
    (pm / "faces").write_text(
        _FOAM_HEADER.format(cls="faceList", obj="faces")
        + f"\n{len(faces)}\n(\n"
        + "\n".join(f"4({f[0]} {f[1]} {f[2]} {f[3]})" for f in faces)
        + "\n)\n"
    )
    note = (
        f'    note        "nPoints:{len(points)} nCells:{mesh.cells} '
        f'nFaces:{len(faces)} nInternalFaces:{n_internal}";\n'
    )
    (pm / "owner").write_text(
        _FOAM_HEADER.format(cls="labelList", obj="owner").replace(
            "    object      owner;\n", note + "    object      owner;\n"
        )
        + f"\n{len(owner)}\n(\n"
        + "\n".join(str(o) for o in owner)
        + "\n)\n"
    )
    (pm / "neighbour").write_text(
        _FOAM_HEADER.format(cls="labelList", obj="neighbour").replace(
            "    object      neighbour;\n", note + "    object      neighbour;\n"
        )
        + f"\n{len(neighbour)}\n(\n"
        + "\n".join(str(n) for n in neighbour)
        + "\n)\n"
    )
    body = [f"\n{len(patches)}\n("]
    for name, ptype, start, count in patches:
        body.append(f"    {name}\n    {{\n        type            {ptype};")
        if ptype == "wall":
            body.append("        inGroups        List<word> 1(wall);")
        body.append(f"        nFaces          {count};\n        startFace       {start};\n    }}")
    body.append(")\n")
    (pm / "boundary").write_text(
        _FOAM_HEADER.format(cls="polyBoundaryMesh", obj="boundary") + "\n".join(body)
    )
    return {
        "points": len(points),
        "cells": mesh.cells,
        "faces": len(faces),
        "internal_faces": n_internal,
        "wall_faces": len(wall_faces),
        "far_faces": len(far_faces),
        "thickness": dz,  # a 2-D slab: Aref for forceCoeffs is chord x thickness
    }


def _default_thickness(mesh: OMesh) -> float:
    """One cell thick in z: a tenth of a chord, i.e. of the order of the
    mid-field cell size, keeps checkMesh's aspect-ratio report sane."""
    xs = [p[0] for row in mesh.xy for p in row]
    chord = (max(xs) - min(xs)) / (2.0 * max(mesh.radius_c, 1.0))
    return 0.1 * chord
