"""Dressing: putting a garment ON a body, which is not the same as closing it.

Two lessons, each paid for with a garment on the floor.

**Where the panels start.** `top_arrangement` measures the body by
cross-section and works on the capsule mannequin it was written against. On
any other body it can mis-measure - asked to dress a 1.80 m figure whose
shoulders were at 1.40 m it hung a jacket's top edge at 2.02 m, at half the
girth, and the coat collapsed into a muff around the ears. `wrap_arrangement`
takes nothing from the body it cannot be sure of: the cylinder's RADIUS comes
from the pattern (the panels have a total width and must wrap exactly once,
so radius = width / 2*pi), the sleeves' radii from the sleeves' own widths,
and the only body facts used are a shoulder height and two arm axes - given
explicitly, or measured by the caller's choice of measurer.

**What holds it up.** A cylinder arrangement leaves front and back meeting at
the SIDES, so when the seams pull together the garment closes into a tube
whose shoulders are on the wearer's flanks - and a tube with no shoulders
slides straight off. Measured: seams closed to 4.7 mm and the whole jacket
ended at y = -0.79, on the floor, with `worn` correctly reporting False.
`dress` does what a fitter does, and what every cloth pipeline calls pinning:
hold the shoulder seams on the shoulders, baste every other seam to its own
midpoint, let the garment find the body, and only then let go.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any

import numpy as np

from seamkiln.drape.environment import Environment
from seamkiln.drape.garment import GarmentMesh, Placement, arm_axes, body_landmarks
from seamkiln.pattern.model import Pattern

Vec = np.ndarray


@dataclass(slots=True)
class BodyFrame:
    """The few body facts a wrap arrangement and a dressing need.

    `shoulder_y` is the height of the shoulder JOINT; `arms` maps "l"/"r" to
    (shoulder point, unit direction down the upper arm); `neck` is where the
    shoulder seams meet. Everything is metres, Y up, +Z forward, in the frame
    the garment will be built in.
    """

    shoulder_y: float
    neck: Vec
    arms: dict[str, tuple[Vec, Vec]] = field(default_factory=dict)
    # How far the shoulder CAP stands above the shoulder joint - a deltoid on
    # a figure, the arm's own radius on a measured mesh. The collar has to
    # clear it: start the top edge level with the joint and the caps poke out
    # through the collar, and the coat reads as slipped off when it has not
    # moved at all.
    cap_m: float = 0.0
    source: str = ""

    def clearance(self, pattern_drop_m: float) -> float:
        """How far above the neck point the garment's top edge must start.

        Derived, not chosen: the shoulder seam sits `pattern_drop_m` below the
        garment's own top edge (the pattern's neck corner is that much higher
        than its shoulder point), and it has to land on TOP of the cap. So
        top = shoulder + cap + drop, and the clearance is that minus the neck.
        A fixed fraction of stature was tried first and was right for exactly
        the one body it was tuned on.
        """
        return max(self.shoulder_y + self.cap_m + pattern_drop_m - float(self.neck[1]), 0.0)


def frame_from_figure(pose: Any, *, height: float = 1.80) -> BodyFrame:
    """A BodyFrame from `seamkiln.figure`'s own joints - exact, no measuring."""
    from seamkiln.figure import joints

    j = joints(pose, height=height)
    arms = {}
    for tag in ("l", "r"):
        shoulder, elbow = j[f"shoulder_{tag}"], j[f"elbow_{tag}"]
        direction = elbow - shoulder
        arms[tag] = (
            np.asarray(shoulder, dtype=np.float64),
            direction / max(float(np.linalg.norm(direction)), 1e-9),
        )
    return BodyFrame(
        shoulder_y=float(j["shoulder_l"][1]),
        neck=np.asarray(j["neck"], dtype=np.float64),
        arms=arms,
        cap_m=height * 0.040 + height * 0.006,  # the deltoid ball, plus its stand
        source="figure joints",
    )


def frame_from_mesh(body: Any) -> BodyFrame:
    """A BodyFrame measured off an arbitrary body mesh.

    Uses only the two landmark measurements that survive an unfamiliar body:
    the shoulder height from the neck-to-shoulders girth jump, and the arm
    axes. The chest radius is deliberately NOT used - it is the measurement
    that cascaded on the figure (0.082 m read for a 0.19 m chest) and took the
    whole arrangement with it.
    """
    marks = body_landmarks(body)
    axes = arm_axes(body, marks["chest_radius_m"])
    arms = {}
    caps = []
    for label, tag in (("L", "l"), ("R", "r")):
        if label in axes:
            arms[tag] = (
                np.asarray(axes[label]["shoulder"], dtype=np.float64),
                np.asarray(axes[label]["direction"], dtype=np.float64),
            )
            caps.append(float(axes[label]["radius_m"]))
    shoulder_y = float(marks["shoulder_y_m"])
    # The neck is placed from the SHOULDER, not from the neck landmark. On the
    # figure the landmark scan read the neck 140 mm high (it found the
    # head-cowl junction, the narrowest slice in the top fifth) while the
    # shoulder girth-jump landed within 13 mm - so the reliable one anchors
    # the unreliable one. The neck point only serves as the inner end of the
    # shoulder seams, and a shoulder's width in is a fine place for that.
    return BodyFrame(
        shoulder_y=shoulder_y,
        neck=np.asarray([0.0, shoulder_y + 0.02, 0.0]),
        arms=arms,
        cap_m=max(caps) if caps else 0.0,
        source="body_landmarks + arm_axes",
    )


def _is_sleeve(panel_id: str) -> str | None:
    """ "l" / "r" for a sleeve panel, None otherwise. The convention every
    bundled block uses is SLEEVE_L / SLEEVE_R; anything else is body."""
    upper = panel_id.upper()
    if not upper.startswith("SLEEVE"):
        return None
    return "l" if upper.endswith("L") else "r"


def shoulder_drop_mm(pattern: Pattern) -> float:
    """How far the shoulder seam sits below the top of its panel, in mm.

    Read off the pattern's own shoulder seams: the top of the panel is its
    max y, the shoulder point is the lower end of the seam's edge. A block
    with no shoulder seam gets a tee's typical 40 mm.
    """
    drops = []
    for seam in pattern.seams:
        if not seam.id.startswith("shoulder"):
            continue
        for ref in (seam.a, seam.b):
            try:
                panel = pattern.panel(ref.panel)
                ends = (panel.point_on_edge(ref.edge, 0.0), panel.point_on_edge(ref.edge, 1.0))
            except (KeyError, IndexError):
                continue
            drops.append(panel.bbox[3] - min(e[1] for e in ends))
    return max(drops) if drops else 40.0


def wrap_arrangement(
    pattern: Pattern,
    frame: BodyFrame,
    *,
    height: float = 1.80,
    clearance_m: float | None = None,
) -> dict[str, Placement]:
    """Place panels round a cylinder whose radius the PATTERN dictates.

    Body panels wrap the torso exactly once: total width over 2*pi is the
    radius, and each panel's centre angle is the arc position of its own
    centre - so two front halves land side by side instead of on top of each
    other. Sleeves wrap a cylinder of their own width, hung down the arm.
    """
    if clearance_m is None:
        clearance_m = frame.clearance(shoulder_drop_mm(pattern) / 1000.0)
    top_y = float(frame.neck[1]) + clearance_m
    _ = height
    body_panels = [p for p in pattern.panels if _is_sleeve(p.id) is None]
    if not body_panels:
        raise ValueError("a wrap arrangement needs at least one body panel")
    total_mm = sum(p.bbox[2] - p.bbox[0] for p in body_panels)
    radius = total_mm / 1000.0 / (2.0 * math.pi)

    placements: dict[str, Placement] = {}
    for panel in pattern.panels:
        tag = _is_sleeve(panel.id)
        if tag is not None:
            if tag not in frame.arms:
                raise ValueError(
                    f"panel {panel.id!r} is a sleeve but the body frame has no "
                    f"{tag!r} arm axis (have: {sorted(frame.arms)}). Measure the arms, "
                    "or hand the frame explicit arm axes."
                )
            shoulder, direction = frame.arms[tag]
            import trimesh

            rotation = trimesh.geometry.align_vectors([0.0, -1.0, 0.0], direction)[:3, :3]
            width_mm = panel.bbox[2] - panel.bbox[0]
            placements[panel.id] = Placement(
                radius_m=width_mm / 1000.0 / (2.0 * math.pi),
                rotation=rotation,
                origin_m=np.asarray(shoulder, dtype=np.float64),
                top_y_m=0.0,
            )
            continue
        minx, _, maxx, _ = panel.bbox
        centre_x = (minx + maxx) / 2000.0
        base = 180.0 if panel.id.upper().startswith("BACK") else 0.0
        placements[panel.id] = Placement(
            radius_m=radius,
            centre_angle_deg=base + math.degrees(centre_x / radius),
            top_y_m=top_y,
        )
    return placements


def shoulder_anchors(frame: BodyFrame, offset: Vec | None = None) -> dict[str, tuple[Vec, Vec]]:
    """Where each shoulder seam belongs: from the neck to the shoulder tip."""
    shift = np.zeros(3) if offset is None else np.asarray(offset, dtype=np.float64)
    out = {}
    for seam_id, tag in (("shoulder-right", "r"), ("shoulder-left", "l")):
        if tag in frame.arms:
            out[seam_id] = (frame.neck + shift, frame.arms[tag][0] + shift)
    return out


def dress(
    garment: GarmentMesh,
    sdf: Any,
    *,
    fabric: str,
    anchors: dict[str, tuple[Vec, Vec]],
    baste: bool = True,
    hold_frames: int = 180,
    settle_frames: int = 220,
    substeps: int = 22,
    environment: Environment | None = None,
) -> Any:
    """Pin the named seams to the body, baste the rest, settle, release.

    `anchors` maps a seam id to the (start, end) the seam should lie along -
    for a jacket, the two shoulder seams from neck to shoulder tip. Which end
    of a seam's index order is the neck end is not knowable, so both are tried
    and the one that moves the cloth less wins: the same measured-not-declared
    choice `_seam_pairs` makes about orientation, for the same reason.

    Returns the DrapeResult of the free settle; the garment's points are left
    at that state.
    """
    from seamkiln.drape.solve import DrapeSettings, drape, prepare

    calm = environment or Environment(name="dressing")
    pins = np.zeros(garment.n_points)
    targets = garment.points.copy()
    missing = [s for s in anchors if s not in garment.seam_spans]
    if missing:
        raise ValueError(
            f"no seam(s) {missing} on this garment to pin (have: "
            f"{', '.join(sorted(garment.seam_spans))})."
        )

    for seam_id, (start, end) in anchors.items():
        lo, hi = garment.seam_spans[seam_id]
        pairs = garment.seams[lo:hi]
        if not len(pairs):
            continue
        start = np.asarray(start, dtype=np.float64)
        end = np.asarray(end, dtype=np.float64)
        index = pairs.reshape(-1)
        u = np.repeat(np.linspace(0.0, 1.0, len(pairs)), 2)[:, None]
        forward = start + (end - start) * u
        backward = end + (start - end) * u
        here = garment.points[index]
        chosen = (
            forward
            if np.linalg.norm(forward - here) <= np.linalg.norm(backward - here)
            else backward
        )
        pins[index] = 1.0
        targets[index] = chosen

    if baste:
        # Every other seam pair is pulled to its own midpoint at the same time.
        # The anchors say where the garment goes; this says its seams are
        # sewn, without needing to know where on the body each belongs. It is
        # what closes an armhole that starts 283 mm open: a stiff shell will
        # not walk that together on its own.
        held = pins > 0.0
        for seam_id, (lo, hi) in garment.seam_spans.items():
            if seam_id in anchors or hi <= lo:
                continue
            pairs = garment.seams[lo:hi]
            mid = 0.5 * (garment.points[pairs[:, 0]] + garment.points[pairs[:, 1]])
            for side in (0, 1):
                free = ~held[pairs[:, side]]
                pins[pairs[free, side]] = 1.0
                targets[pairs[free, side]] = mid[free]

    hold = DrapeSettings(frames=hold_frames, substeps=substeps, environment=calm)
    pinned = drape(
        garment,
        sdf,
        fabric=fabric,
        settings=hold,
        pins=pins,
        pin_target=targets,
        prepared=prepare(garment, fabric=fabric, settings=hold),
    )
    garment.points = pinned.points
    free = DrapeSettings(frames=settle_frames, substeps=substeps, environment=calm)
    result = drape(
        garment,
        sdf,
        fabric=fabric,
        settings=free,
        prepared=prepare(garment, fabric=fabric, settings=free),
    )
    garment.points = result.points
    return result


__all__ = [
    "BodyFrame",
    "dress",
    "frame_from_figure",
    "frame_from_mesh",
    "shoulder_anchors",
    "shoulder_drop_mm",
    "wrap_arrangement",
]
