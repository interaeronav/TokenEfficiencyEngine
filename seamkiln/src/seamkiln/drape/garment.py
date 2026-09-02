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
from typing import Any

import numpy as np
import trimesh

from seamkiln.drape.triangulate import PanelMesh, triangulate_panel
from seamkiln.pattern.geometry import cumulative_length
from seamkiln.pattern.model import EdgeRef, Panel, Pattern, Seam
from seamkiln.solver.problem import colour_edges

MM = 1e-3

# A seam sampled more thinly than this cannot close. The floor exists so that
# "never rely on a coarse preview" is structural rather than a habit.
#
# It is deliberately a FLOOR and not a blessing: passing it does not make a
# drape trustworthy, it only stops the most obviously untrustworthy one. What
# says whether a result converged is `DrapeResult.report()["converged"]`,
# measured from the drape itself.
MIN_SEAM_POINTS = 6


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
    flat: bool = False  # lay the panel in a plane instead of round a cylinder

    def apply(self, points_mm: np.ndarray) -> np.ndarray:
        centre = points_mm.mean(axis=0)
        top = points_mm[:, 1].max()
        u = (points_mm[:, 0] - centre[0]) * MM
        v = (points_mm[:, 1] - (top if self.top_y_m is not None else centre[1])) * MM
        if self.flat:
            # A plane, not a cylinder of enormous radius. That was tried: a
            # cylinder's SURFACE sits at z = radius, so `radius = 1e6` laid the
            # specimen a thousand kilometres away, where it fell in vacuum
            # forever and every fabric scored an identical drape coefficient
            # of exactly 1.000.
            local = np.stack([u, v + (self.top_y_m or 0.0), np.zeros_like(u)], axis=1)
            return local @ self.rotation.T + self.origin_m
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
class Attachment:
    """Constraints and weight added to a garment by something that is not cloth.

    A lace, a zipper chain and a button's thread are all the same shape of
    thing: some particle pairs pulled toward a rest length, at a stiffness
    that is NOT the cloth's, plus - for hardware - real grams hanging on real
    particles. The mass matters more than it sounds: a #5 brass chain down a
    front opening is about 33 g/m, which on a 600 mm opening is 20 g of metal
    on an edge that a 130 gsm poplin only weighs 12 g/m. Hardware that does
    not weigh anything drapes like a decal.
    """

    pairs: np.ndarray  # int32 [k, 2]
    rest: np.ndarray  # float64 [k] metres
    compliance: float  # m/N; the cloth's is not used
    added_mass: np.ndarray | None = None  # float64 [n] kg, per particle
    kind: str = ""

    def __len__(self) -> int:
        return int(self.pairs.shape[0])


@dataclass(slots=True)
class GarmentMesh:
    """The solvable garment: one point cloud, many panels, seams closed."""

    points: np.ndarray  # float64 [n, 3] metres, Y up
    rest_points_mm: np.ndarray  # float64 [n, 2] the flat pattern it came from
    triangles: np.ndarray  # int32 [m, 3]
    panel_slices: dict[str, tuple[int, int]]
    structural: np.ndarray  # int32 [k, 2]
    structural_rest: np.ndarray  # float64 [k] metres, MEASURED IN 2D
    bending: np.ndarray  # int32 [k, 4] - a dihedral quad, not a distance pair
    bending_rest: np.ndarray  # rest dihedral angle, radians (0 on a flat pattern)
    seams: np.ndarray  # int32 [k, 2]
    seam_rest: np.ndarray  # metres; 0 for a plain seam
    particle_distance_mm: float = 0.0
    seam_orientation: dict[str, str] = field(default_factory=dict)
    seam_spans: dict[str, tuple[int, int]] = field(default_factory=dict)
    seam_points: dict[str, int] = field(default_factory=dict)
    # Seams declared with a `kind` other than "plain" - a zipper opening, a
    # button placket. They are PAIRED like a seam (so the two edges know which
    # point faces which) but NOT sewn: a zipper opening that is sewn shut is
    # not an opening. The hardware module decides which pairs are engaged.
    hardware_pairs: np.ndarray | None = None  # int32 [k, 2]
    hardware_spans: dict[str, tuple[int, int]] = field(default_factory=dict)
    hardware_kind: dict[str, str] = field(default_factory=dict)
    # Everything added AFTER the pattern was meshed: a lace, a zipper, a
    # fastened button. Named, because hardware moves - unzipping has to
    # REPLACE the zipper's constraints, and an append-only list cannot.
    attachments: dict[str, Attachment] = field(default_factory=dict)

    @property
    def n_points(self) -> int:
        return int(self.points.shape[0])

    def attach(
        self,
        name: str,
        pairs: np.ndarray,
        rest: np.ndarray,
        *,
        compliance: float,
        added_mass: np.ndarray | None = None,
        kind: str = "",
    ) -> None:
        """Add or REPLACE a named block of non-cloth constraints."""
        self.attachments[name] = Attachment(
            pairs=np.ascontiguousarray(pairs, dtype=np.int32).reshape(-1, 2),
            rest=np.ascontiguousarray(rest, dtype=np.float64).reshape(-1),
            compliance=float(compliance),
            added_mass=None if added_mass is None else np.asarray(added_mass, dtype=np.float64),
            kind=kind,
        )

    def detach(self, name: str) -> bool:
        return self.attachments.pop(name, None) is not None

    def added_mass_kg(self) -> np.ndarray:
        """Grams of hardware, per particle, summed over every attachment."""
        total = np.zeros(self.n_points, dtype=np.float64)
        for block in self.attachments.values():
            if block.added_mass is not None:
                total += block.added_mass
        return total

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
            "thinnest_seam_points": min(self.seam_points.values()) if self.seam_points else 0,
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


def _body_shell(mesh: trimesh.Trimesh) -> trimesh.Trimesh:
    from seamkiln.drape.body import body_shell

    return body_shell(mesh)


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


def body_landmarks(mesh: trimesh.Trimesh, *, samples: int = 48) -> dict[str, float]:
    """Neck, shoulder, armpit and chest, measured off the body by cross-section.

    Three definitions here were each wrong once, and each failure is worth
    keeping in view:

    * **Chest first, as "the widest slice in the upper half"** picks the HIPS
      on any body whose hips are wider - normal anatomy. So the vertical
      landmarks are found first and the chest is measured relative to them.
    * **"The arms are separate cross-sections" is the ARMPIT, not the
      shoulder.** On a capsule mannequin the arms detach at the shoulder
      joint; on a real body the deltoid merges into the torso and they only
      separate a hand's width lower.
    * The **shoulder** is therefore found from the neck: scanning down, the
      torso girth jumps when the section stops being a neck and starts being
      a pair of shoulders.
    """
    mesh = _body_shell(mesh)
    low, high = float(mesh.bounds[0][1]), float(mesh.bounds[1][1])
    height = high - low
    heights = np.linspace(low + height * 0.05, high - height * 0.02, samples)
    girths = np.array(
        [
            (polygon.length if (polygon := _torso_section(mesh, y)) is not None else 0.0)
            for y in heights
        ]
    )

    # 1. the neck: the narrowest torso section in the upper quarter, which is
    #    below the head and above the shoulders
    upper = heights > low + height * 0.78
    candidates = np.where(upper & (girths > 0.0), girths, np.inf)
    neck_index = int(np.argmin(candidates))
    neck_girth = float(girths[neck_index])
    neck_y = float(heights[neck_index])

    # 2. the shoulder: the highest slice below the neck whose girth has jumped
    below = heights < neck_y
    shoulders = np.flatnonzero(below & (girths > neck_girth * 1.6))
    shoulder_y = float(heights[shoulders.max()]) if len(shoulders) else neck_y - height * 0.03

    # 3. the armpit: the highest slice where the arms are separate shapes
    counts = np.array([_section_count(mesh, y) for y in heights])
    separated = np.flatnonzero((counts >= 2) & (heights < shoulder_y))
    armpit_y = float(heights[separated.max()]) if len(separated) else shoulder_y - height * 0.06

    # 4. the chest: the widest TORSO section from the armpit down a hand's
    #    width - above the armpit the arms are merged in and inflate it
    band = (heights <= armpit_y) & (heights >= armpit_y - height * 0.12)
    banded = np.where(band, girths, 0.0)
    if banded.max() <= 0.0:
        banded = np.where(heights <= armpit_y, girths, 0.0)
    chest_index = int(np.argmax(banded))
    chest_girth = float(banded[chest_index])
    if chest_girth <= 0.0:
        raise ValueError("could not measure a torso cross-section on this body mesh")

    return {
        "height_m": round(height, 4),
        "top_y_m": round(high, 4),
        "neck_y_m": round(neck_y, 4),
        "neck_girth_m": round(neck_girth, 4),
        "shoulder_y_m": round(shoulder_y, 4),
        "armpit_y_m": round(armpit_y, 4),
        "chest_y_m": round(float(heights[chest_index]), 4),
        "chest_girth_m": round(chest_girth, 4),
        "chest_radius_m": round(chest_girth / (2 * np.pi), 4),
    }


def arm_axes(mesh: trimesh.Trimesh, chest_radius: float) -> dict[str, dict[str, object]]:
    """Where each arm starts, which way it points, and how thick it is.

    Measured, for the same reason the chest is measured: a guessed sleeve
    angle put the cuffs above the shoulders. But the first measured version
    was worse - it took every vertex outboard of the torso and read the arm
    from the innermost to the outermost, which on a real body meant **from a
    FOOT to a hand**: it reported the shoulder at y = 0.015 m, the arm
    pointing upward, and a 227 mm arm radius. The stand-in mannequin hid it,
    because its legs are inboard of the chest radius and a real body's are
    not.

    So: outboard AND in the upper half, shoulder end anchored by height
    (an arm hangs DOWN from its shoulder), hand end by reach.
    """
    body = _body_shell(mesh)
    vertices = np.asarray(body.vertices)
    low, high = float(vertices[:, 1].min()), float(vertices[:, 1].max())
    height = high - low
    outboard = (np.abs(vertices[:, 0]) > chest_radius * 1.15) & (
        vertices[:, 1] > low + height * 0.45
    )
    axes: dict[str, dict[str, object]] = {}
    for label, sign in (("L", -1.0), ("R", 1.0)):
        side = vertices[outboard & (np.sign(vertices[:, 0]) == sign)]
        if len(side) < 8:
            continue
        shoulder = side[np.argmax(side[:, 1])]  # the highest point of the arm
        hand = side[np.argmax(np.abs(side[:, 0]))]  # the farthest reach
        direction = hand - shoulder
        length = float(np.linalg.norm(direction))
        if length < 1e-6 or direction[1] > 0.0:
            continue  # an arm that points upward is a measurement failure
        direction = direction / length
        offsets = side - shoulder
        along = offsets @ direction
        perpendicular = offsets - along[:, None] * direction
        axes[label] = {
            "shoulder": shoulder,
            "direction": direction,
            "length_m": round(length, 4),
            "radius_m": round(float(np.percentile(np.linalg.norm(perpendicular, axis=1), 60)), 4),
        }
    return axes


def sleeve_wear(
    garment: GarmentMesh, points: np.ndarray, body: trimesh.Trimesh, *, slack: float = 1.8
) -> dict[str, dict[str, float]]:
    """Is each sleeve ON its arm - the question the seam gap cannot answer.

    A garment whose right sleeve has slipped off the arm and hangs inside out
    at the flank closes its seams beautifully: measured, the mannequin tee's
    "converged" baseline had exactly that sleeve, at 0 % on the arm, for the
    whole life of the cylinder arrangement. Per sleeve: the fraction of its
    particles within `slack` arm radii of the arm's axis and between the
    shoulder and a hand's breadth past the sleeve's own length, and where the
    sleeve sits along the arm (its mean position from the shoulder).
    """
    marks = body_landmarks(body)
    arms = arm_axes(body, marks["chest_radius_m"])
    out: dict[str, dict[str, float]] = {}
    for panel_id, (low, high) in garment.panel_slices.items():
        name = panel_id.upper()
        if not name.startswith("SLEEVE"):
            continue
        arm = arms.get("L" if name.endswith("L") else "R")
        if arm is None:
            continue
        shoulder = np.asarray(arm["shoulder"], dtype=np.float64)
        direction = np.asarray(arm["direction"], dtype=np.float64)
        radius = float(arm["radius_m"])
        rest = garment.rest_points_mm[low:high]
        length = float(rest[:, 1].max() - rest[:, 1].min()) * MM
        offsets = points[low:high] - shoulder
        along = offsets @ direction
        perpendicular = np.linalg.norm(offsets - along[:, None] * direction, axis=1)
        on = (perpendicular < slack * radius) & (along > -0.05) & (along < length + 0.08)
        out[panel_id] = {
            "on_arm": round(float(on.mean()), 3),
            "along_mm": round(float(along.mean()) * 1000.0, 1),
            "clearance_mm": round(float(perpendicular.mean() - radius) * 1000.0, 1),
        }
    return out


def _front_edge_side(pattern: Any, sleeve_id: str) -> int | None:
    """+1 if the sleeve edge sewn to a FRONT panel lies on the piece's +x
    side, -1 if on its -x side, None if no such seam is declared."""
    panel = pattern.panel(sleeve_id)
    edges = panel.edges()
    centre_x = (panel.bbox[0] + panel.bbox[2]) / 2.0
    for seam in pattern.seams:
        for mine, other in ((seam.a, seam.b), (seam.b, seam.a)):
            if mine.panel == sleeve_id and other.panel.upper().startswith("FRONT"):
                run = edges[mine.edge % len(edges)]
                x = float(np.mean([v.x for v in run]))
                return 1 if x >= centre_x else -1
    return None


def _sleeve_frame(
    direction: np.ndarray, front_at_plus_x: int | None = None, outward: np.ndarray | None = None
) -> np.ndarray:
    """The rotation that hangs a sleeve down an arm WITH ITS ROLL SET.

    Aligning the tube to the arm with a minimal rotation leaves the roll about
    the arm unspecified, and it landed the cap apex (the panel's centre, angle
    0) at the FRONT of the arm with the underarm seam at the back. Sewn to an
    armhole whose corner is on top of the shoulder and whose bottom is in the
    armpit, the sleeve then has to twist a quarter turn round the arm, and
    the twist piles up at the corner: 95-150 mm open at the shoulder point on
    both front armholes, whatever the basting did.

    So the frame is built in full: local -Y down the arm, local +Z (the cap
    apex) toward the top of the shoulder - the direction perpendicular to the
    arm with the most up in it - and local +X their cross product.

    Then the HANDEDNESS. A block drafts one sleeve piece and uses it for both
    arms, as a cutter does, and a proper rotation can only put that one piece
    the right way round on ONE arm: measured, the left sleeve's front edge
    landed in front and the right sleeve's landed behind, so the right sleeve
    dragged the shoulder seam 128 mm backwards while it closed. The cutter
    lays the second piece face-down, and so does this: `front_at_plus_x`
    says which side of the piece is sewn to the front, and when the frame
    would put that side behind the arm, local +X is reversed - a reflection,
    which is what a flipped piece is.
    """
    down = np.asarray(direction, dtype=np.float64)
    down = down / max(float(np.linalg.norm(down)), 1e-9)
    up = np.asarray([0.0, 1.0, 0.0])
    apex = up - float(up @ down) * down
    if float(np.linalg.norm(apex)) < 0.05:
        # An arm hanging straight down has no "most up" across it. The cap
        # then faces OUTWARD - away from the body - which the caller says
        # with `outward` (the shoulder's side); a fixed +x put the left
        # sleeve's cap against the body on the mannequin and twisted it.
        hint = np.asarray(outward if outward is not None else [1.0, 0.0, 0.0], dtype=np.float64)
        apex = hint - float(hint @ down) * down
        if float(np.linalg.norm(apex)) < 1e-9:
            apex = np.asarray([1.0, 0.0, 0.0])
    apex = apex / float(np.linalg.norm(apex))
    local_y = -down
    local_x = np.cross(local_y, apex)
    if front_at_plus_x is not None and float(local_x[2]) * float(front_at_plus_x) < 0.0:
        local_x = -local_x  # the piece laid face-down
    return np.stack([local_x, local_y, apex], axis=1)


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
            #
            # A note worth keeping, because the first diagnosis was wrong. The
            # right sleeve was turning inside out during the solve, and the
            # obvious suspect was this line: `align_vectors` returns the
            # MINIMAL rotation, so two mirrored arms get different twists about
            # their own axes. Building the frame explicitly was tried and made
            # things WORSE - the worst seam gap went 48 mm to 205 mm.
            #
            # The actual cause was a restitution bug added the same hour, in
            # the collision pass: it pushed the particle out a SECOND time
            # instead of reflecting its velocity, and at a restitution of 0.02
            # - barely a bounce - that was enough to evert a sleeve and take
            # the worst seam gap from 33 mm to 248 mm. Fixing it there fixed
            # this, and `collision.alignment` now reports every panel facing
            # outward. The lesson is the ordinary one: the line you changed
            # last is a better suspect than the line that looks suspicious.
            # The full frame, with the roll set and the handedness read from
            # the seams, the same as the wrap path: the minimal rotation left
            # the cap apex at the front of the arm and one sleeve twisted a
            # quarter turn, which the collision normal's old sideways bias
            # half-everted (agreement 0.19, 42 % of it facing the body) and
            # the corrected normal everted outright.
            #
            # What the true normal and the full frame then exposed was worse
            # than a roll. With both sleeves genuinely on the arms the tee's
            # right side seam opened 82 mm at the armpit corner, and a sweep
            # of every roll from 0 to 180 degrees, both handednesses, two cap
            # raises, three tube radii, a zero-gravity baste, dressing, lower
            # arms and a mirrored arrangement moved it between 54 and 82 - or
            # "closed" it by sliding a sleeve off the arm, which is what the
            # 25.8 mm baseline had been all along (right sleeve 0 % on the
            # arm, inside out at the flank). The cause was the seam pairing:
            # a one-vertex register error on the right side seam only, from
            # a first-at-or-after match on rounding-equal parameters (see
            # `_pair_one_seam`, and the loop-closing vertex `_boundary_in_span`
            # left out of every last edge). Matched to the nearest vertex,
            # the tee's worst seam is 19 mm with both sleeves 100 % on the
            # arms and facing out, the zipped jacket's 6.
            #
            # The tube's radius comes from the sleeve's OWN width, as the
            # wrap path's does, not 1.45 x the arm: measured with the
            # pairing right, that takes the tee's side seams from 13 mm to
            # 2-6 with the sleeves' facing 0.63-0.73 instead of 0.52, and
            # the zipped jacket's worst seam from 13 mm to 6 (0.41-0.43
            # facing instead of 0.31). The cap is still hung at the joint:
            # raising it changed the worst seam by under a millimetre.
            shoulder = np.asarray(arm["shoulder"], dtype=np.float64)
            rotation = _sleeve_frame(
                np.asarray(arm["direction"]),
                _front_edge_side(pattern, panel.id),
                outward=np.asarray([np.sign(shoulder[0]) or 1.0, 0.0, 0.0]),
            )
            width_m = (panel.bbox[2] - panel.bbox[0]) * MM
            placements[panel.id] = Placement(
                radius_m=max(width_m / (2.0 * np.pi), 0.03),
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
        # A piece placed by a REFLECTION (laid face-down: one sleeve piece
        # serving both arms) has its winding mirrored, so its normals would
        # face the body - the render-direction check called it inside out,
        # and fur grown along those normals grows inward. Reverse the winding
        # for that piece; the flat pattern, seams and rest lengths are
        # unchanged by it.
        if np.linalg.det(np.asarray(placements[panel.id].rotation, dtype=np.float64)) < 0.0:
            mesh.triangles = np.ascontiguousarray(mesh.triangles[:, ::-1])
        points2d.append(mesh.points)
        triangles.append(mesh.triangles + offset)
        slices[panel.id] = (offset, offset + mesh.n_points)
        offset += mesh.n_points

    points = np.vstack(points3d)
    rest2d = np.vstack(points2d)
    tris = np.vstack(triangles).astype(np.int32)

    structural = _unique_edges(tris)
    bending = bending_quads(tris)
    seams, orientations, spans, counts, hw, hw_spans, hw_kind = _seam_pairs(
        pattern, meshes, slices, points
    )

    thin = {name: n for name, n in counts.items() if 0 < n < MIN_SEAM_POINTS}
    if thin:
        worst = ", ".join(f"{k} ({v} points)" for k, v in sorted(thin.items())[:4])
        finer = particle_distance * min(thin.values()) / MIN_SEAM_POINTS
        raise ValueError(
            f"particle_distance {particle_distance:g} mm is too coarse for this "
            f"garment's seams: {worst}. A seam sampled this thinly cannot close - "
            f"measured on the tee block, mean seam gap falls from 2.2 mm at 26 mm "
            f"to 0.7 mm at 9 mm. Use {finer:.0f} mm or finer."
        )

    return GarmentMesh(
        points=points,
        rest_points_mm=rest2d,
        triangles=tris,
        panel_slices=slices,
        structural=structural,
        structural_rest=_rest_from_2d(rest2d, structural),
        bending=bending,
        # The rest dihedral of a FLAT pattern is PI, not zero. Both triangles
        # are listed off the same shared edge (p1, p2, ·), so their computed
        # normals point in opposite directions when the sheet is flat and
        # n1 . n2 = -1. Setting the rest to zero told every element in a flat
        # sheet to fold itself in half, and the specimen contracted from a
        # 150 mm radius to 8 mm in twenty frames - a very convincing bug,
        # because the mesh stayed finite and the seams stayed closed the
        # whole way down.
        bending_rest=np.full(bending.shape[0], np.pi, dtype=np.float64),
        seams=seams,
        seam_rest=np.zeros(seams.shape[0], dtype=np.float64),
        particle_distance_mm=particle_distance,
        seam_orientation=orientations,
        seam_spans=spans,
        seam_points=counts,
        hardware_pairs=hw,
        hardware_spans=hw_spans,
        hardware_kind=hw_kind,
    )


def _unique_edges(triangles: np.ndarray) -> np.ndarray:
    edges = np.vstack([triangles[:, [0, 1]], triangles[:, [1, 2]], triangles[:, [2, 0]]])
    return np.unique(np.sort(edges, axis=1), axis=0).astype(np.int32)


def bending_quads(triangles: np.ndarray) -> np.ndarray:
    """Interior edges as (a, b, c, d): the shared edge, then the two opposite
    corners. What a DIHEDRAL bending constraint needs.

    The first version used a distance constraint between c and d, and it was
    quietly useless. A distance between opposite corners changes only
    QUADRATICALLY with the fold angle, so it resists a sharp crease and
    barely notices gentle curvature - and drape is gentle curvature,
    accumulated over hundreds of elements. Measured: a cloth with every
    compliance set to 1e-6, which is rigid by any reading, still collapsed
    from a 300 mm disc to a drape coefficient of 0.17 and fell 69 mm.
    """
    edge_faces: dict[tuple[int, int], list[tuple[int, int]]] = {}
    for tri in triangles:
        a, b, c = int(tri[0]), int(tri[1]), int(tri[2])
        for (u, v), w in (((a, b), c), ((b, c), a), ((c, a), b)):
            key = (u, v) if u < v else (v, u)
            edge_faces.setdefault(key, []).append((w, 0))
    quads = [
        (edge[0], edge[1], opposite[0][0], opposite[1][0])
        for edge, opposite in edge_faces.items()
        if len(opposite) >= 2
    ]
    return np.asarray(quads, dtype=np.int32) if quads else np.zeros((0, 4), dtype=np.int32)


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
) -> tuple[
    np.ndarray,
    dict[str, str],
    dict[str, tuple[int, int]],
    dict[str, int],
    np.ndarray,
    dict[str, tuple[int, int]],
    dict[str, str],
]:
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
    spans: dict[str, tuple[int, int]] = {}
    counts: dict[str, int] = {}
    hw_pairs: list[tuple[int, int]] = []
    hw_spans: dict[str, tuple[int, int]] = {}
    hw_kind: dict[str, str] = {}
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
        orientation[seam.id] = label
        if seam.kind != "plain":
            start = len(hw_pairs)
            hw_pairs.extend(chosen)
            hw_spans[seam.id] = (start, len(hw_pairs))
            hw_kind[seam.id] = seam.kind
            counts[seam.id] = len(chosen)
            continue
        start = len(pairs)
        pairs.extend(chosen)
        spans[seam.id] = (start, len(pairs))
        counts[seam.id] = len(chosen)
    array = np.asarray(pairs, dtype=np.int32) if pairs else np.zeros((0, 2), dtype=np.int32)
    hardware = (
        np.asarray(hw_pairs, dtype=np.int32) if hw_pairs else np.zeros((0, 2), dtype=np.int32)
    )
    return array, orientation, spans, counts, hardware, hw_spans, hw_kind


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
    if not 0 <= ref.edge < len(ranges):
        raise ValueError(
            f"seam refers to {ref}, but panel {ref.panel!r} has {len(ranges)} edges "
            f"(0..{len(ranges) - 1}). An edit that changed the panel's CORNER COUNT "
            "invalidates seams that named the edges after it - re-sew, or edit the "
            "panel without changing its corners."
        )
    t0, t1 = ranges[ref.edge]
    span = t1 - t0
    return t0 + span * ref.t0, t0 + span * ref.t1


def _boundary_in_span(mesh: PanelMesh, span: tuple[float, float]) -> tuple[np.ndarray, np.ndarray]:
    lo, hi = span
    t = mesh.boundary_t
    inside = (t >= lo - 1e-9) & (t <= hi + 1e-9)
    indices = mesh.boundary[inside]
    params = t[inside]
    if hi >= 1.0 - 1e-9 and lo > 1e-9:
        # The outline is a loop, so the vertex at t = 0 is also the END of
        # the last edge, at t = 1. Left out, the last edge's run is one
        # vertex short of its partner's and the pairing stretches it to fit:
        # a register error of up to half a particle along the whole seam,
        # on the tee's hem-to-armpit side seams and nowhere else.
        closing = t <= 1e-9
        if closing.any():
            indices = np.concatenate([indices, mesh.boundary[closing]])
            params = np.concatenate([params, np.full(int(closing.sum()), 1.0)])
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
    # The NEAREST follower, not the first one at or after the driver's t.
    # `searchsorted` alone gave the first-at-or-after, and two runs of the
    # same length sampled the same way differ in t by rounding only - so
    # whether the match landed on the right vertex or the next one was a
    # coin toss of 1e-17 per seam. On the tee it came up one way for the
    # left side seam and the other for the right: the right was sewn one
    # vertex (12 mm) out of register along its whole length, with the
    # doubled pair at the armpit corner where three seams meet. That
    # register error was the 82 mm open corner on the mannequin, and the
    # jacket's 0.7 mm convergence margin; matched by distance, the tee's
    # worst seam is 17 mm and the jacket's 13.
    after = np.searchsorted(follow_t, drive_t).clip(0, len(follow_idx) - 1)
    before = (after - 1).clip(0, len(follow_idx) - 1)
    closer = np.abs(follow_t[before] - drive_t) < np.abs(follow_t[after] - drive_t)
    nearest = np.where(closer, before, after)
    return [
        (int(drive_base + d), int(follow_base + follow_idx[n]))
        for d, n in zip(drive_idx, nearest, strict=False)
    ]


def colour_pairs(pairs: np.ndarray, n_points: int) -> list[np.ndarray]:
    """Colour any constraint family so the solver can run it wide."""
    if pairs.shape[0] == 0:
        return []
    return colour_edges(pairs, n_points)
