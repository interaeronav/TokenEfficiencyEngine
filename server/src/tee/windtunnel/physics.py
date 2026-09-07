"""The arithmetic the lane owns: coefficients, wall spacing, domain rules,
lifting-line checks and the geometry facts of an STL.

Every rule carries its source and a `firmness` the drafting lane taught us to
declare: `textbook` (a formula), `convention` (best-practice guidance a human
may override), never a number invented here. Stdlib only.
"""

from __future__ import annotations

import math
import struct
from dataclasses import dataclass
from pathlib import Path

# ---------------------------------------------------------------------------
# Coefficients (Anderson, Fundamentals of Aerodynamics, §1.5)
# ---------------------------------------------------------------------------


def dynamic_pressure(rho: float, V: float) -> float:
    return 0.5 * rho * V * V


def coefficients(
    *, lift_N: float, drag_N: float, moment_Nm: float, q_Pa: float, Sref_m2: float, cref_m: float
) -> dict[str, float]:
    """Wind-axis forces to CL, CD, Cm. The solver's liftDir/dragDir already
    rotate body forces into wind axes (see `wind_axes`)."""
    if q_Pa <= 0 or Sref_m2 <= 0 or cref_m <= 0:
        raise ValueError("q, Sref and cref must be positive")
    return {
        "cl": lift_N / (q_Pa * Sref_m2),
        "cd": drag_N / (q_Pa * Sref_m2),
        "cm": moment_Nm / (q_Pa * Sref_m2 * cref_m),
    }


def wind_axes(aoa_deg: float, sideslip_deg: float = 0.0) -> dict[str, tuple[float, float, float]]:
    """Unit vectors for a flow along +x rotated by alpha about +z (2-D and 3-D
    with z up): dragDir along the freestream, liftDir normal to it in the x-y
    plane. OpenFOAM's forceCoeffs and SU2's REF frame both take these."""
    a = math.radians(aoa_deg)
    b = math.radians(sideslip_deg)
    drag = (math.cos(a) * math.cos(b), math.sin(a) * math.cos(b), math.sin(b))
    lift = (-math.sin(a), math.cos(a), 0.0)
    return {"drag": drag, "lift": lift, "U": drag}


# ---------------------------------------------------------------------------
# Wall spacing (Schlichting, Boundary-Layer Theory, flat-plate correlation)
# ---------------------------------------------------------------------------


def first_cell_height(
    *, y_plus: float, rho: float, V: float, L: float, mu: float, cell_centred: bool = True
) -> dict[str, float]:
    """Height of the first cell for a target y+ on a flat plate of length L.

    Cf = (2 log10 Re_L - 0.65)^-2.3 (Schlichting, valid Re_L < 1e9);
    tau_w = Cf q; u_tau = sqrt(tau_w / rho); y = y+ mu / (rho u_tau).
    A cell-centred code (OpenFOAM) puts its first centroid at half the cell
    height, so the cell is 2y; a node-centred dual mesh (SU2) wants y itself.
    """
    if min(y_plus, rho, V, L, mu) <= 0:
        raise ValueError("all inputs must be positive")
    Re = rho * V * L / mu
    cf = (2.0 * math.log10(Re) - 0.65) ** -2.3
    tau_w = cf * 0.5 * rho * V * V
    u_tau = math.sqrt(tau_w / rho)
    y = y_plus * mu / (rho * u_tau)
    return {
        "Re": Re,
        "cf": cf,
        "u_tau": u_tau,
        "y_m": y,
        "first_cell_m": 2.0 * y if cell_centred else y,
        "firmness": "textbook",
        "cite": "Schlichting, Boundary-Layer Theory, flat-plate Cf correlation",
    }


# ---------------------------------------------------------------------------
# Domain and blockage (ERCOFTAC Best Practice Guidelines 2000 §4;
# Barlow, Rae & Pope, Low-Speed Wind Tunnel Testing 3rd ed. ch. 10)
# ---------------------------------------------------------------------------

DOMAIN_2D_RADIUS_C = 50.0
DOMAIN_2D_MIN_RADIUS_C = 20.0
DOMAIN_3D = {
    "up": 5.0,
    "down": 15.0,
    "side": 5.0,
    "top": 5.0,
    "min_up": 3.0,
    "min_down": 10.0,
    "min_side": 3.0,
}
BLOCKAGE_WARN = 0.05
BLOCKAGE_REFUSE = 0.10


@dataclass(frozen=True)
class Domain:
    kind: str
    xmin: float
    xmax: float
    ymin: float
    ymax: float
    zmin: float
    zmax: float
    blockage: float
    firmness: str = "convention"
    cite: str = "ERCOFTAC BPG 2000 §4; Barlow, Rae & Pope ch. 10 (blockage 5 % warn / 10 % refuse)"

    def size(self) -> tuple[float, float, float]:
        return (self.xmax - self.xmin, self.ymax - self.ymin, self.zmax - self.zmin)


def domain_3d(
    bbox: tuple[tuple[float, float, float], tuple[float, float, float]],
    frontal_area_m2: float,
    *,
    up_c: float = DOMAIN_3D["up"],
    down_c: float = DOMAIN_3D["down"],
    side_c: float = DOMAIN_3D["side"],
    top_c: float = DOMAIN_3D["top"],
    ground: bool = False,
) -> Domain:
    """A box around a body: multiples of the body length upstream/downstream
    and of the body height/width sideways. `ground=True` puts the floor at
    the body's lowest point (a car, a building)."""
    (x0, y0, z0), (x1, y1, z1) = bbox
    L = max(x1 - x0, 1e-9)
    W = max(y1 - y0, 1e-9)
    H = max(z1 - z0, 1e-9)
    xmin, xmax = x0 - up_c * L, x1 + down_c * L
    ymin, ymax = y0 - side_c * max(W, H), y1 + side_c * max(W, H)
    zmin = z0 if ground else z0 - top_c * max(W, H)
    zmax = z1 + top_c * max(W, H)
    cross = (ymax - ymin) * (zmax - zmin)
    return Domain("box", xmin, xmax, ymin, ymax, zmin, zmax, frontal_area_m2 / cross)


def blockage_verdict(blockage: float) -> str:
    if blockage > BLOCKAGE_REFUSE:
        return "refuse"
    if blockage > BLOCKAGE_WARN:
        return "warn"
    return "ok"


# ---------------------------------------------------------------------------
# Lifting-line sanity (Anderson §4.8, §5.3-5.4; Helmbold for low AR)
# ---------------------------------------------------------------------------


def cl_alpha_2d() -> float:
    """Thin-airfoil lift slope, per radian."""
    return 2.0 * math.pi


def cl_alpha_3d(AR: float, e: float = 0.9, a0: float | None = None) -> float:
    """Prandtl lifting-line slope a = a0 / (1 + a0 / (pi e AR)), per radian.
    Below AR 4 Helmbold's a0 / sqrt(1 + (a0/(pi AR))^2) + a0/(pi AR) is used."""
    a0 = cl_alpha_2d() if a0 is None else a0
    if AR <= 0:
        raise ValueError("AR must be positive")
    if AR < 4.0:
        k = a0 / (math.pi * AR)
        return a0 / (math.sqrt(1.0 + k * k) + k)
    return a0 / (1.0 + a0 / (math.pi * e * AR))


def induced_drag(CL: float, AR: float, e: float = 0.9) -> float:
    """CDi = CL^2 / (pi e AR)."""
    return CL * CL / (math.pi * e * AR)


# ---------------------------------------------------------------------------
# STL facts (binary and ASCII; no library)
# ---------------------------------------------------------------------------

Vec = tuple[float, float, float]


@dataclass
class Surface:
    tris: list[tuple[Vec, Vec, Vec]]
    name: str = ""

    @property
    def bbox(self) -> tuple[Vec, Vec]:
        xs = [p[0] for t in self.tris for p in t]
        ys = [p[1] for t in self.tris for p in t]
        zs = [p[2] for t in self.tris for p in t]
        return (min(xs), min(ys), min(zs)), (max(xs), max(ys), max(zs))

    @property
    def area(self) -> float:
        return sum(_tri_area(*t) for t in self.tris)

    def projected_area(self, axis: int = 0, cells: int = 256) -> float:
        """Frontal area seen along `axis` (0 = x, the flow direction): the
        triangles rasterised onto a grid so overlapping faces count once.
        Resolution error is ~2/cells of the bbox side, i.e. < 1 % at 256."""
        a, b = [i for i in range(3) if i != axis]
        (lo0, lo1, lo2), (hi0, hi1, hi2) = self.bbox
        lo = (lo0, lo1, lo2)
        hi = (hi0, hi1, hi2)
        w, h = hi[a] - lo[a], hi[b] - lo[b]
        if w <= 0 or h <= 0:
            return 0.0
        grid = [bytearray(cells) for _ in range(cells)]
        sx, sy = cells / w, cells / h
        for tri in self.tris:
            pts = [((p[a] - lo[a]) * sx, (p[b] - lo[b]) * sy) for p in tri]
            _raster(grid, pts, cells)
        covered = sum(sum(row) for row in grid)
        return covered * (w / cells) * (h / cells)

    def watertight(self) -> tuple[bool, int]:
        """Every edge shared by exactly two triangles (the open-edge count is
        what a snappyHexMesh user needs to hear)."""
        edges: dict[tuple[Vec, Vec], int] = {}
        for t in self.tris:
            for i in range(3):
                p, q = t[i], t[(i + 1) % 3]
                key = (p, q) if p <= q else (q, p)
                edges[key] = edges.get(key, 0) + 1
        open_edges = sum(1 for n in edges.values() if n != 2)
        return open_edges == 0, open_edges


def _tri_area(p: Vec, q: Vec, r: Vec) -> float:
    ux, uy, uz = q[0] - p[0], q[1] - p[1], q[2] - p[2]
    vx, vy, vz = r[0] - p[0], r[1] - p[1], r[2] - p[2]
    cx, cy, cz = uy * vz - uz * vy, uz * vx - ux * vz, ux * vy - uy * vx
    return 0.5 * math.sqrt(cx * cx + cy * cy + cz * cz)


def _raster(grid: list[bytearray], pts: list[tuple[float, float]], n: int) -> None:
    (x0, y0), (x1, y1), (x2, y2) = pts
    ymin = max(math.floor(min(y0, y1, y2)), 0)
    ymax = min(math.ceil(max(y0, y1, y2)), n - 1)
    for row in range(ymin, ymax + 1):
        yc = row + 0.5
        xs: list[float] = []
        for (ax, ay), (bx, by) in (
            ((x0, y0), (x1, y1)),
            ((x1, y1), (x2, y2)),
            ((x2, y2), (x0, y0)),
        ):
            if (ay <= yc < by) or (by <= yc < ay):
                xs.append(ax + (yc - ay) * (bx - ax) / (by - ay))
        if len(xs) < 2:
            continue
        xa, xb = min(xs), max(xs)
        for col in range(max(math.floor(xa), 0), min(math.ceil(xb), n)):
            if xa <= col + 0.5 <= xb:
                grid[row][col] = 1


def read_stl(path: str | Path) -> Surface:
    """Binary or ASCII STL, decided by content rather than by the 80-byte
    header text (a binary file may start with 'solid')."""
    path = Path(path)
    data = path.read_bytes()
    if len(data) >= 84:
        (n,) = struct.unpack_from("<I", data, 80)
        if 84 + 50 * n == len(data):
            tris = []
            off = 84
            for _ in range(n):
                vals = struct.unpack_from("<12fH", data, off)
                tris.append(
                    (
                        (vals[3], vals[4], vals[5]),
                        (vals[6], vals[7], vals[8]),
                        (vals[9], vals[10], vals[11]),
                    )
                )
                off += 50
            return Surface(tris, path.stem)
    tris = []
    verts: list[Vec] = []
    for line in data.decode("utf-8", "replace").splitlines():
        parts = line.split()
        if len(parts) == 4 and parts[0] == "vertex":
            verts.append((float(parts[1]), float(parts[2]), float(parts[3])))
            if len(verts) == 3:
                tris.append((verts[0], verts[1], verts[2]))
                verts = []
    if not tris:
        raise ValueError(f"{path.name}: no triangles found (neither binary nor ASCII STL)")
    return Surface(tris, path.stem)


def box_tris(
    xmin: float, xmax: float, ymin: float, ymax: float, zmin: float, zmax: float
) -> list[tuple[Vec, Vec, Vec]]:
    """A closed box as twelve triangles, normals outward.

    cfMesh meshes the volume BOUNDED by the surface it is given, so an
    external-aero case hands it the domain box and the body as one surface
    (doc 74 §2.4). snappyHexMesh needs no such thing - it carves the body out
    of a background blockMesh - which is why this arrives with cfMesh.
    """
    v = [
        (xmin, ymin, zmin),
        (xmax, ymin, zmin),
        (xmax, ymax, zmin),
        (xmin, ymax, zmin),
        (xmin, ymin, zmax),
        (xmax, ymin, zmax),
        (xmax, ymax, zmax),
        (xmin, ymax, zmax),
    ]
    faces = [
        (0, 2, 1),
        (0, 3, 2),
        (4, 5, 6),
        (4, 6, 7),
        (0, 1, 5),
        (0, 5, 4),
        (1, 2, 6),
        (1, 6, 5),
        (2, 3, 7),
        (2, 7, 6),
        (3, 0, 4),
        (3, 4, 7),
    ]
    return [(v[a], v[b], v[c]) for a, b, c in faces]


def write_stl_ascii(path: str | Path, tris: list[tuple[Vec, Vec, Vec]], name: str = "tee") -> int:
    """ASCII STL with computed facet normals; returns the byte count."""
    out = [f"solid {name}"]
    for p, q, r in tris:
        ux, uy, uz = q[0] - p[0], q[1] - p[1], q[2] - p[2]
        vx, vy, vz = r[0] - p[0], r[1] - p[1], r[2] - p[2]
        nx, ny, nz = uy * vz - uz * vy, uz * vx - ux * vz, ux * vy - uy * vx
        mag = math.sqrt(nx * nx + ny * ny + nz * nz) or 1.0
        out.append(f"  facet normal {nx / mag:.9g} {ny / mag:.9g} {nz / mag:.9g}")
        out.append("    outer loop")
        for v in (p, q, r):
            out.append(f"      vertex {v[0]:.9g} {v[1]:.9g} {v[2]:.9g}")
        out.append("    endloop")
        out.append("  endfacet")
    out.append(f"endsolid {name}")
    text = "\n".join(out) + "\n"
    Path(path).write_text(text)
    return len(text)


def units_sanity(bbox: tuple[Vec, Vec]) -> str | None:
    """A body under 5 mm or over 200 m across is almost always a unit slip
    (mm read as m, or the reverse). Returns the warning or None."""
    (x0, y0, z0), (x1, y1, z1) = bbox
    span = max(x1 - x0, y1 - y0, z1 - z0)
    if span < 0.005:
        return f"largest extent {span:.4g} m - a millimetre model read as metres? set units="
    if span > 200.0:
        return f"largest extent {span:.4g} m - metres read as millimetres? set units="
    return None
