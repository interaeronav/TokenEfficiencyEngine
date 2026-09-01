"""Panels -> one 3D cloth mesh, arranged around a body and ready to solve.

The idea that makes this a garment rather than a shrink-wrap: **rest lengths
come from the flat pattern, never from the 3D placement.** The cloth is
placed roughly around the body, but every constraint remembers the shape the
pattern actually is, so the solve pulls it toward the garment the pattern
describes. Arrange it badly and it still drapes to the same garment, just
slower; measure the rest lengths off the arrangement instead and the pattern
stops meaning anything.

Arrangement mirrors what the incumbents call arrangement points: each panel
is mapped onto a cylinder around the body, then rotated and translated into
place. A large radius is a flat plane, so one primitive covers both.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import trimesh

from seamkiln.drape.triangulate import PanelMesh, triangulate_panel
from seamkiln.pattern.geometry import cumulative_length
from seamkiln.pattern.model import EdgeRef, Panel, Pattern, Seam
from seamkiln.solver.problem import colour_edges

MM = 1e-3


def edge_t_ranges(panel: Panel) -> list[tuple[float, float]]:
    """Each edge's span as a fraction of the whole outline's arc length.

    `EdgeRef.t0/t1` are edge-local; boundary vertices are indexed by
    outline-global t. This is the conversion between them, and getting it
    wrong sews the hem to the armhole with no error message.
    """
    lengths = cumulative_length([*panel.outline, panel.outline[0]])
    total = float(lengths[-1])
    corners = panel.corner_indices()
    if len(corners) < 2:
        return [(0.0, 1.0)]
    ranges: list[tuple[float, float]] = []
    for k, start in enumerate(corners):
        end = corners[(k + 1) % len(corners)]
        t0 = lengths[start] / total
        t1 = (lengths[end] if end > start else total) / total
        ranges.append((t0, t1))
    return ranges


@dataclass(slots=True)
class Placement:
    """Where a panel starts, before gravity and the seams have their say."""

    radius_m: float = 0.20
    centre_angle_deg: float = 0.0
    origin_m: np.ndarray = field(default_factory=lambda: np.zeros(3))
    rotation: np.ndarray = field(default_factory=lambda: np.eye(3))
    top_y_m: float | None = None  # align the panel's top edge to this height

    def apply(self, points_mm: np.ndarray) -> np.ndarray:
        centre = points_mm.mean(axis=0)
        top = points_mm[:, 1].max()
        u = (points_mm[:, 0] - centre[0]) * MM
        v = (points_mm[:, 1] - (top if self.top_y_m is not None else centre[1])) * MM
        angle = np.radians(self.centre_angle_deg) + u / max(self.radius_m, 1e-6)
        local = np.stack(
            [
                self.radius_m * np.sin(angle),
                v + (self.top_y_m or 0.0),
                self.radius_m * np.cos(angle),
            ],
            axis=1,
        )
        return local @ self.rotation.T + self.origin_m


@dataclass(slots=True)
class GarmentMesh:
    """The solvable garment: one point cloud, many panels, seams closed."""

    points: np.ndarray  # float64 [n, 3] metres, Y up
    rest_points_mm: np.ndarray  # float64 [n, 2] the flat pattern it came from
    triangles: np.ndarray  # int32 [m, 3]
    panel_slices: dict[str, tuple[int, int]]
    structural: np.ndarray  # int32 [k, 2]
    structural_rest: np.ndarray  # float64 [k] metres, MEASURED IN 2D
    bending: np.ndarray  # int32 [k, 2]
    bending_rest: np.ndarray
    seams: np.ndarray  # int32 [k, 2]
    seam_rest: np.ndarray  # metres; 0 for a plain seam
    particle_distance_mm: float = 0.0
    seam_orientation: dict[str, str] = field(default_factory=dict)

    @property
    def n_points(self) -> int:
        return int(self.points.shape[0])

    def summary(self) -> dict[str, object]:
        return {
            "points": self.n_points,
            "triangles": int(self.triangles.shape[0]),
            "panels": len(self.panel_slices),
            "structural": int(self.structural.shape[0]),
            "bending": int(self.bending.shape[0]),
            "seam_constraints": int(self.seams.shape[0]),
            "particle_distance_mm": self.particle_distance_mm,
            "seams_flipped": sum(1 for v in self.seam_orientation.values() if v == "flipped"),
        }

    def seam_gaps_mm(self, points: np.ndarray | None = None) -> dict[str, float]:
        """How far apart the sewn pairs still are. The drape's other verdict."""
        if self.seams.shape[0] == 0:
            return {"pairs": 0}
        p = self.points if points is None else points
        gaps = np.linalg.norm(p[self.seams[:, 0]] - p[self.seams[:, 1]], axis=1) * 1000.0
        return {
            "pairs": int(self.seams.shape[0]),
            "max_gap_mm": round(float(gaps.max()), 3),
            "mean_gap_mm": round(float(gaps.mean()), 3),
            "open_over_2mm": int((gaps > 2.0).sum()),
        }


def _torso_section(mesh: trimesh.Trimesh, y: float):
    """The cross-section polygon containing the body's central axis, or None.

    A horizontal slice through an A-pose body returns THREE polygons: the
    torso and two arms. Taking the largest, or the union, or the convex
    hull, all give a "chest" that includes the arms - which is how a garment
    ends up starting half a metre from the body. The torso is the one the
    axis passes through, and that is the only definition that survives a
    different pose or a different body.
    """
    from shapely.geometry import Point

    section = mesh.section(plane_origin=[0.0, y, 0.0], plane_normal=[0.0, 1.0, 0.0])
    if section is None:
        return None
    planar, _ = section.to_2D()
    for polygon in planar.polygons_full:
        if polygon.contains(Point(0.0, 0.0)):
            return polygon
    return None


def _section_count(mesh: trimesh.Trimesh, y: float) -> int:
    """How many separate closed shapes the body has at this height.

    One means neck or head; three means torso plus two arms. The transition
    IS the shoulder, and unlike a girth threshold it does not mistake a head
    for a pair of shoulders.
    """
    section = mesh.section(plane_origin=[0.0, y, 0.0], plane_normal=[0.0, 1.0, 0.0])
    if section is None:
        return 0
    planar, _ = section.to_2D()
    return len(planar.polygons_full)


def body_landmarks(mesh: trimesh.Trimesh, *, samples: int = 40) -> dict[str, float]:
    """Shoulder height and chest girth, measured off the body by cross-section.

    Order matters, and it was learned the hard way. Finding the chest first
    as "the widest slice in the upper half" breaks the moment a body has
    hips wider than its chest - which is normal anatomy - because the hips
    win and every garment is then sized to the wrong number. So the SHOULDER
    is found first, from where the arms stop being separate shapes, and the
    chest is measured in a band just below it. Both are then independent of
    what the lower body happens to be doing.
    """
    low, high = float(mesh.bounds[0][1]), float(mesh.bounds[1][1])
    height = high - low
    heights = np.linspace(low + height * 0.05, high - height * 0.02, samples)

    # 1. the shoulder: the highest slice where the arms are still separate
    #    shapes. A girth threshold was tried first and put the shoulder on
    #    top of the HEAD - a head is easily 70% of a chest's girth.
    counts = np.array([_section_count(mesh, y) for y in heights])
    upper = heights > low + height * 0.55
    separated = np.flatnonzero((counts >= 2) & upper)
    shoulder_y = (
        float(heights[separated.max()])
        if len(separated)
        else float(heights[int(len(heights) * 0.8)])
    )

    # 2. the chest: the widest torso section in a band BELOW the shoulder
    band = (heights <= shoulder_y - height * 0.02) & (heights >= shoulder_y - height * 0.20)
    if not band.any():
        band = heights <= shoulder_y
    girths = np.array(
        [
            (polygon.length if (polygon := _torso_section(mesh, y)) is not None else 0.0)
            if in_band
            else 0.0
            for y, in_band in zip(heights, band, strict=False)
        ]
    )
    if girths.max() <= 0.0:
        raise ValueError("could not measure a torso cross-section on this body mesh")
    chest_index = int(np.argmax(girths))
    chest_girth = float(girths[chest_index])

    return {
        "height_m": round(height, 4),
        "top_y_m": round(high, 4),
        "chest_y_m": round(float(heights[chest_index]), 4),
        "chest_girth_m": round(chest_girth, 4),
        "chest_radius_m": round(chest_girth / (2 * np.pi), 4),
        "shoulder_y_m": round(shoulder_y, 4),
    }


def arm_axes(mesh: trimesh.Trimesh, chest_radius: float) -> dict[str, dict[str, object]]:
    """Where each arm starts, which way it points, and how thick it is.

    Measured, for the same reason the chest is measured: a guessed sleeve
    angle put the cuffs above the shoulders and the sleeves sticking out
    sideways like a scarecrow. An arm is whatever lies outboard of the torso
    - so take those vertices, split them by side, and read the direction from
    the innermost to the outermost point.
    """
    vertices = np.asarray(mesh.vertices)
    outboard = np.abs(vertices[:, 0]) > chest_radius * 1.15
    axes: dict[str, dict[str, object]] = {}
    for label, sign in (("L", -1.0), ("R", 1.0)):
        side = vertices[outboard & (np.sign(vertices[:, 0]) == sign)]
        if len(side) < 8:
            continue
        near = side[np.argmin(np.abs(side[:, 0]))]
        far = side[np.argmax(np.abs(side[:, 0]))]
        direction = far - near
        length = float(np.linalg.norm(direction))
        if length < 1e-6:
            continue
        direction = direction / length
        # thickness: spread perpendicular to the axis, not a bounding box
        offsets = side - near
        along = offsets @ direction
        perpendicular = offsets - along[:, None] * direction
        axes[label] = {
            "shoulder": near,
            "direction": direction,
            "length_m": round(length, 4),
            "radius_m": round(float(np.percentile(np.linalg.norm(perpendicular, axis=1), 80)), 4),
        }
    return axes


def top_arrangement(
    pattern: Pattern, body: trimesh.Trimesh, *, ease: float = 1.30
) -> dict[str, Placement]:
    """Front in front, back behind, sleeves out at the shoulders.

    `ease` is how much wider than the body the cloth starts. Starting tight
    is the classic own-goal: the first substep pushes half the panel through
    the body and the solver spends the drape recovering from its own
    initial condition.
    """
    marks = body_landmarks(body)
    radius = marks["chest_radius_m"] * ease
    arms = arm_axes(body, marks["chest_radius_m"])

    # Hang the garment from the TOP of the shoulder, not from the shoulder
    # line. A tee placed level with the shoulder joint starts below the
    # widest part of the body, so gravity walks it straight over the hips
    # and onto the floor - measured, twice, before this line existed. The
    # top of the shoulder is the joint plus the arm's own radius, both of
    # which arm_axes already measures off the body.
    if arms:
        shoulder_y = max(float(a["shoulder"][1]) + float(a["radius_m"]) for a in arms.values())
    else:
        shoulder_y = marks["shoulder_y_m"]
    placements: dict[str, Placement] = {}

    for panel in pattern.panels:
        name = panel.id.upper()
        if name.startswith("SLEEVE"):
            side = "L" if name.endswith("L") else "R"
            arm = arms.get(side)
            if arm is None:
                raise ValueError(
                    f"no arm measured on the {side} side of this body, so "
                    f"{panel.id} cannot be arranged; place it explicitly"
                )
            # rotate the sleeve's hanging direction (-Y) onto the real arm
            rotation = trimesh.geometry.align_vectors(
                [0.0, -1.0, 0.0], np.asarray(arm["direction"])
            )[:3, :3]
            placements[panel.id] = Placement(
                radius_m=max(float(arm["radius_m"]) * 1.45, 0.03),
                centre_angle_deg=0.0,
                rotation=rotation,
                origin_m=np.asarray(arm["shoulder"], dtype=np.float64),
                top_y_m=0.0,
            )
        else:
            placements[panel.id] = Placement(
                radius_m=radius,
                centre_angle_deg=0.0 if name.startswith("FRONT") else 180.0,
                origin_m=np.zeros(3),
                top_y_m=shoulder_y,
            )
    return placements


def build_garment(
    pattern: Pattern,
    placements: dict[str, Placement],
    *,
    particle_distance: float = 15.0,
    relax_passes: int = 2,
) -> GarmentMesh:
    """Triangulate, place, and wire every constraint the solver will need."""
    meshes: dict[str, PanelMesh] = {}
    points3d: list[np.ndarray] = []
    points2d: list[np.ndarray] = []
    triangles: list[np.ndarray] = []
    slices: dict[str, tuple[int, int]] = {}
    offset = 0

    for panel in pattern.panels:
        if panel.id not in placements:
            raise KeyError(
                f"panel {panel.id!r} has no placement; got: {sorted(placements)}. "
                "Every panel must be arranged before it can be draped."
            )
        mesh = triangulate_panel(
            panel, particle_distance=particle_distance, relax_passes=relax_passes
        )
        meshes[panel.id] = mesh
        points3d.append(placements[panel.id].apply(mesh.points))
        points2d.append(mesh.points)
        triangles.append(mesh.triangles + offset)
        slices[panel.id] = (offset, offset + mesh.n_points)
        offset += mesh.n_points

    points = np.vstack(points3d)
    rest2d = np.vstack(points2d)
    tris = np.vstack(triangles).astype(np.int32)

    structural = _unique_edges(tris)
    bending = _bending_pairs(tris)
    seams, orientations = _seam_pairs(pattern, meshes, slices, points)

    return GarmentMesh(
        points=points,
        rest_points_mm=rest2d,
        triangles=tris,
        panel_slices=slices,
        structural=structural,
        structural_rest=_rest_from_2d(rest2d, structural),
        bending=bending,
        bending_rest=_rest_from_2d(rest2d, bending),
        seams=seams,
        seam_rest=np.zeros(seams.shape[0], dtype=np.float64),
        particle_distance_mm=particle_distance,
        seam_orientation=orientations,
    )


def _unique_edges(triangles: np.ndarray) -> np.ndarray:
    edges = np.vstack([triangles[:, [0, 1]], triangles[:, [1, 2]], triangles[:, [2, 0]]])
    return np.unique(np.sort(edges, axis=1), axis=0).astype(np.int32)


def _bending_pairs(triangles: np.ndarray) -> np.ndarray:
    """The two opposite corners of each pair of triangles sharing an edge.

    Bending resistance is what separates silk from denim; without it every
    fabric drapes like a sheet of tissue regardless of its card.
    """
    edge_to_opposite: dict[tuple[int, int], list[int]] = {}
    for tri in triangles:
        a, b, c = int(tri[0]), int(tri[1]), int(tri[2])
        for (u, v), w in (((a, b), c), ((b, c), a), ((c, a), b)):
            key = (u, v) if u < v else (v, u)
            edge_to_opposite.setdefault(key, []).append(w)
    pairs = [sorted(opposite[:2]) for opposite in edge_to_opposite.values() if len(opposite) >= 2]
    return np.asarray(pairs, dtype=np.int32) if pairs else np.zeros((0, 2), dtype=np.int32)


def _rest_from_2d(rest2d: np.ndarray, pairs: np.ndarray) -> np.ndarray:
    """Rest lengths in metres, measured on the FLAT PATTERN."""
    if pairs.shape[0] == 0:
        return np.zeros(0, dtype=np.float64)
    return np.linalg.norm(rest2d[pairs[:, 0]] - rest2d[pairs[:, 1]], axis=1) * MM


def _seam_pairs(
    pattern: Pattern,
    meshes: dict[str, PanelMesh],
    slices: dict[str, tuple[int, int]],
    points: np.ndarray,
) -> tuple[np.ndarray, dict[str, str]]:
    """Pair every seam, choosing each one's orientation by measurement.

    Two panels laid out counter-clockwise traverse their shared edge in
    OPPOSITE directions, so most seams need flipping - and a seam sewn the
    wrong way round does not fail, it twists the garment 180 degrees and
    drapes something that looks like a mistake nobody can name. Rather than
    make that the user's problem (it is the classic beginner error in the
    incumbents too), both orientations are built and the one whose pairs are
    closer together IN THE ARRANGEMENT wins. `Seam.flip` stays available as
    an override for the rare seam that is genuinely meant to twist.
    """
    pairs: list[tuple[int, int]] = []
    orientation: dict[str, str] = {}
    for seam in pattern.seams:
        try:
            direct = _pair_one_seam(pattern, meshes, slices, seam, flip=False)
            flipped = _pair_one_seam(pattern, meshes, slices, seam, flip=True)
        except KeyError:  # a seam naming a panel that is not in this garment
            continue
        if seam.flip:  # explicit override wins, and is recorded as such
            chosen, label = flipped, "flipped (declared)"
        else:
            chosen, label = _closer(direct, flipped, points)
        pairs.extend(chosen)
        orientation[seam.id] = label
    array = np.asarray(pairs, dtype=np.int32) if pairs else np.zeros((0, 2), dtype=np.int32)
    return array, orientation


def _closer(
    direct: list[tuple[int, int]], flipped: list[tuple[int, int]], points: np.ndarray
) -> tuple[list[tuple[int, int]], str]:
    def cost(pairs: list[tuple[int, int]]) -> float:
        if not pairs:
            return float("inf")
        index = np.asarray(pairs, dtype=np.int64)
        return float(np.linalg.norm(points[index[:, 0]] - points[index[:, 1]], axis=1).mean())

    return (direct, "direct") if cost(direct) <= cost(flipped) else (flipped, "flipped")


def _global_span(pattern: Pattern, ref: EdgeRef) -> tuple[float, float]:
    ranges = edge_t_ranges(pattern.panel(ref.panel))
    t0, t1 = ranges[ref.edge]
    span = t1 - t0
    return t0 + span * ref.t0, t0 + span * ref.t1


def _boundary_in_span(mesh: PanelMesh, span: tuple[float, float]) -> tuple[np.ndarray, np.ndarray]:
    lo, hi = span
    inside = (mesh.boundary_t >= lo - 1e-9) & (mesh.boundary_t <= hi + 1e-9)
    indices = mesh.boundary[inside]
    params = mesh.boundary_t[inside]
    order = np.argsort(params)
    return indices[order], params[order]


def _pair_one_seam(
    pattern: Pattern,
    meshes: dict[str, PanelMesh],
    slices: dict[str, tuple[int, int]],
    seam: Seam,
    *,
    flip: bool,
) -> list[tuple[int, int]]:
    """Pair boundary vertices by matched position along each run.

    Sides rarely have the same number of vertices - a gathered ruffle has
    twice as many - so pairing is by normalised position along the run, and
    the denser side drives. That is what makes `gather` mean something
    physical instead of just annotating a report.
    """
    mesh_a, mesh_b = meshes[seam.a.panel], meshes[seam.b.panel]
    idx_a, t_a = _boundary_in_span(mesh_a, _global_span(pattern, seam.a))
    idx_b, t_b = _boundary_in_span(mesh_b, _global_span(pattern, seam.b))
    if len(idx_a) < 2 or len(idx_b) < 2:
        return []

    def normalise(values: np.ndarray) -> np.ndarray:
        low, high = values[0], values[-1]
        return (values - low) / max(high - low, 1e-12)

    norm_a, norm_b = normalise(t_a), normalise(t_b)
    if flip:
        norm_b = 1.0 - norm_b

    base_a, base_b = slices[seam.a.panel][0], slices[seam.b.panel][0]
    if len(idx_a) >= len(idx_b):
        driver, follower = (idx_a, norm_a, base_a), (idx_b, norm_b, base_b)
    else:
        driver, follower = (idx_b, norm_b, base_b), (idx_a, norm_a, base_a)

    drive_idx, drive_t, drive_base = driver
    follow_idx, follow_t, follow_base = follower
    order = np.argsort(follow_t)
    follow_t, follow_idx = follow_t[order], follow_idx[order]
    nearest = np.searchsorted(follow_t, drive_t).clip(0, len(follow_idx) - 1)
    return [
        (int(drive_base + d), int(follow_base + follow_idx[n]))
        for d, n in zip(drive_idx, nearest, strict=False)
    ]


def colour_pairs(pairs: np.ndarray, n_points: int) -> list[np.ndarray]:
    """Colour any constraint family so the solver can run it wide."""
    if pairs.shape[0] == 0:
        return []
    return colour_edges(pairs, n_points)
