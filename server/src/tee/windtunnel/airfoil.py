"""Sections: NACA four-digit generation, Selig `.dat` files, circles, and the
extruded ASCII STL a 3-D mesher takes.

NACA four-digit (Abbott & von Doenhoff, Theory of Wing Sections, §6.4):
thickness yt = 5t (0.2969 sqrt(x) - 0.1260 x - 0.3516 x^2 + 0.2843 x^3
- 0.1015 x^4), with -0.1036 as the last coefficient for a closed trailing
edge; camber yc = m/p^2 (2 p x - x^2) ahead of p and m/(1-p)^2 ((1 - 2p)
+ 2 p x - x^2) behind it; the surfaces are offset along the camber normal.
Cosine spacing clusters points at the leading and trailing edges.

A section is a CLOSED loop of distinct points, counter-clockwise, starting
at the trailing edge and running over the upper surface to the leading edge
and back along the lower surface - one trailing-edge node, one leading-edge
node. That single-node trailing edge is what lets an O-mesh close around it.
"""

from __future__ import annotations

import itertools
import math
from pathlib import Path

Point = tuple[float, float]


def naca4(code: str, n: int = 100, *, closed_te: bool = True) -> list[Point]:
    """`n` intervals per surface. Closed TE: 2n distinct points with one TE
    node; open TE: 2n + 1 points, both TE points kept (a blunt base)."""
    if len(code) != 4 or not code.isdigit():
        raise ValueError(f"'{code}' is not a four-digit NACA code")
    m = int(code[0]) / 100.0
    p = int(code[1]) / 10.0
    t = int(code[2:]) / 100.0
    if n < 8:
        raise ValueError("n must be at least 8 points per surface")
    a4 = -0.1036 if closed_te else -0.1015
    upper: list[Point] = []
    lower: list[Point] = []
    for k in range(n + 1):
        beta = math.pi * k / n
        x = 0.5 * (1.0 - math.cos(beta))
        yt = (
            5.0
            * t
            * (0.2969 * math.sqrt(x) - 0.1260 * x - 0.3516 * x**2 + 0.2843 * x**3 + a4 * x**4)
        )
        if m == 0 or p == 0:
            yc, dyc = 0.0, 0.0
        elif x < p:
            yc = m / p**2 * (2 * p * x - x * x)
            dyc = 2 * m / p**2 * (p - x)
        else:
            yc = m / (1 - p) ** 2 * ((1 - 2 * p) + 2 * p * x - x * x)
            dyc = 2 * m / (1 - p) ** 2 * (p - x)
        th = math.atan(dyc)
        upper.append((x - yt * math.sin(th), yc + yt * math.cos(th)))
        lower.append((x + yt * math.sin(th), yc - yt * math.cos(th)))
    loop = list(reversed(upper))  # TE ... LE (n+1 points)
    loop += lower[1:n]  # LE excluded, TE excluded
    if closed_te:
        loop[0] = (1.0, 0.0)  # yt(1) = 0 and yc(1) = 0: both surfaces meet here
    else:
        loop.append(lower[n])
    return loop


def circle(n: int = 120, radius: float = 0.5, centre: Point = (0.0, 0.0)) -> list[Point]:
    """A cylinder section (diameter 1 by default), CCW from +x."""
    return [
        (
            centre[0] + radius * math.cos(2 * math.pi * k / n),
            centre[1] + radius * math.sin(2 * math.pi * k / n),
        )
        for k in range(n)
    ]


def properties(loop: list[Point]) -> dict[str, float]:
    """Chord, max thickness (and where), max camber (and where): the checks a
    generated section must pass before it is meshed. The loop is split at
    the leading edge (min x) into an upper and a lower surface."""
    xs = [p[0] for p in loop]
    x_le, x_te = min(xs), max(xs)
    chord = x_te - x_le
    n = len(loop)
    le = min(range(n), key=lambda i: loop[i][0])
    upper = sorted(loop[: le + 1], key=lambda p: p[0])
    lower = sorted([loop[0], *loop[le:]], key=lambda p: p[0])

    def interp(pts: list[Point], x: float) -> float:
        for (x0, y0), (x1, y1) in itertools.pairwise(pts):
            if x0 <= x <= x1:
                return y0 if x1 == x0 else y0 + (y1 - y0) * (x - x0) / (x1 - x0)
        return pts[-1][1]

    best_t, best_tx, best_c, best_cx = 0.0, 0.0, 0.0, 0.0
    for k in range(1, 200):
        x = x_le + chord * k / 200
        yu, yl = interp(upper, x), interp(lower, x)
        thick = yu - yl
        camb = 0.5 * (yu + yl)
        if thick > best_t:
            best_t, best_tx = thick, x
        if abs(camb) > abs(best_c):
            best_c, best_cx = camb, x
    return {
        "chord": chord,
        "max_thickness": best_t / chord,
        "max_thickness_x": (best_tx - x_le) / chord,
        "max_camber": best_c / chord,
        "max_camber_x": (best_cx - x_le) / chord,
        "points": float(n),
    }


def write_selig(path: str | Path, loop: list[Point], name: str) -> None:
    """Selig format: a name line, then x y from the TE over the upper surface
    to the LE and back along the lower surface, closing at the TE."""
    lines = [name] + [f"{x:.7f} {y:.7f}" for x, y in loop] + [f"{loop[0][0]:.7f} {loop[0][1]:.7f}"]
    Path(path).write_text("\n".join(lines) + "\n")


def read_selig(path: str | Path) -> tuple[str, list[Point]]:
    """Reads Selig (TE-upper-LE-lower-TE) coordinates; the closing duplicate
    of the TE is dropped so the result is the loop this module uses."""
    text = Path(path).read_text().splitlines()
    name = text[0].strip() if text and not _is_pair(text[0]) else Path(path).stem
    pts: list[Point] = []
    for line in text:
        if _is_pair(line):
            a, b = line.split()[:2]
            pts.append((float(a), float(b)))
    if len(pts) < 8:
        raise ValueError(f"{Path(path).name}: {len(pts)} coordinate pairs is not a section")
    if math.dist(pts[0], pts[-1]) < 1e-9:
        pts = pts[:-1]
    return name, pts


def _is_pair(line: str) -> bool:
    parts = line.split()
    if len(parts) < 2:
        return False
    try:
        float(parts[0]), float(parts[1])
    except ValueError:
        return False
    return True


def signed_area(loop: list[Point]) -> float:
    a = 0.0
    n = len(loop)
    for i in range(n):
        x0, y0 = loop[i]
        x1, y1 = loop[(i + 1) % n]
        a += x0 * y1 - x1 * y0
    return 0.5 * a


def ccw(loop: list[Point]) -> list[Point]:
    """The loop with counter-clockwise orientation, first point kept first."""
    return loop if signed_area(loop) > 0 else [loop[0], *loop[1:][::-1]]


def extrude_stl(
    path: str | Path,
    loop: list[Point],
    *,
    span: float,
    chord: float = 1.0,
    z0: float | None = None,
    name: str = "section",
) -> int:
    """A watertight prism: the section scaled to `chord`, extruded along z
    over `span` and capped with fans from the mid-chord point (a thin section
    is star-shaped from there). Returns the triangle count."""
    from tee.windtunnel.physics import write_stl_ascii

    pts = [(x * chord, y * chord) for x, y in ccw(loop)]
    zlo = -0.5 * span if z0 is None else z0
    zhi = zlo + span
    n = len(pts)
    tris = []
    for i in range(n):
        (xa, ya), (xb, yb) = pts[i], pts[(i + 1) % n]
        # outward-facing side quads for a CCW loop viewed from +z
        tris.append(((xa, ya, zlo), (xb, yb, zlo), (xb, yb, zhi)))
        tris.append(((xa, ya, zlo), (xb, yb, zhi), (xa, ya, zhi)))
    cx = 0.5 * chord
    cy = 0.5 * (max(y for _, y in pts) + min(y for _, y in pts))
    for i in range(n):
        (xa, ya), (xb, yb) = pts[i], pts[(i + 1) % n]
        tris.append(((cx, cy, zhi), (xa, ya, zhi), (xb, yb, zhi)))  # top cap, normal +z
        tris.append(((cx, cy, zlo), (xb, yb, zlo), (xa, ya, zlo)))  # bottom cap, normal -z
    write_stl_ascii(path, tris, name)
    return len(tris)
