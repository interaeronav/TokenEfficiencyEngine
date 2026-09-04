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
from seamkiln.drape.garment import (
    GarmentMesh,
    Placement,
    _front_edge_side,
    _sleeve_frame,
    arm_axes,
    body_landmarks,
)
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


def frame_from_figure(
    pose: Any, *, height: float = 1.80, build: Any = "male", facing_deg: float = 0.0
) -> BodyFrame:
    """A BodyFrame from `seamkiln.figure`'s own joints - exact, no measuring.

    `facing_deg` turns the frame the way `figure(facing_deg=)` turns the
    mesh. Without it a figure built facing +x was dressed by a frame facing
    +z: the tee went on sideways, its front level with its back and both
    sleeves 30-43 cm from any arm, and the drape still reported "worn".
    """
    from seamkiln.figure import _yaw, joints
    from seamkiln.figure import build as figure_build

    b = figure_build(build)
    j = joints(pose, height=height, build=b)
    turn = _yaw(float(facing_deg)) if facing_deg else np.eye(3)
    arms = {}
    for tag in ("l", "r"):
        shoulder, elbow = j[f"shoulder_{tag}"], j[f"elbow_{tag}"]
        direction = elbow - shoulder
        arms[tag] = (
            turn @ np.asarray(shoulder, dtype=np.float64),
            turn @ (direction / max(float(np.linalg.norm(direction)), 1e-9)),
        )
    return BodyFrame(
        shoulder_y=float(j["shoulder_l"][1]),
        neck=turn @ np.asarray(j["neck"], dtype=np.float64),
        arms=arms,
        cap_m=height * b.deltoid_r + height * 0.006,  # the deltoid ball, plus its stand
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


def sleeve_cap_height_mm(panel: Any) -> float:
    """How far the cap rises above the sleeve's biceps line, in mm.

    A bundled block drafts its sleeve with the biceps line at y = 0, so the
    cap height was the panel's top - and a sleeve that arrived from CAD, at
    y = 1218..1369 in its marker, was hung 1.37 m above the shoulder joint
    and dragged onto the body inside out (both sleeves facing inward,
    -0.26 and -0.19). The biceps line is the sleeve's own widest line: the
    outline's extreme-x vertices are the underarm corners, and the cap is
    what rises above them.
    """
    outline = panel.outline
    left = min(outline, key=lambda v: v.x)
    right = max(outline, key=lambda v: v.x)
    biceps_y = (left.y + right.y) / 2.0
    return max(float(panel.bbox[3]) - biceps_y, 0.0)


def _panel_is_sleeve(panel_id: str, sleeves: set[str] | None) -> bool:
    return panel_id in sleeves if sleeves is not None else _is_sleeve(panel_id) is not None


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
    roles: dict[str, str] | None = None,
    facing_deg: float = 0.0,
) -> dict[str, Placement]:
    """Place panels round a cylinder whose radius the PATTERN dictates.

    Body panels wrap the torso exactly once: total width over 2*pi is the
    radius, and each panel's centre angle is the arc position of its own
    centre - so two front halves land side by side instead of on top of each
    other. Sleeves wrap a cylinder of their own width, hung down the arm.
    `roles` names the pieces when their ids do not (`piece_roles`);
    `facing_deg` is the way the body faces (a placement angle of 90 puts a
    panel at +x, the same turn `figure(facing_deg=90)` gives its front) -
    the sleeves take theirs from the frame's arms, the body panels need it
    said, and a figure facing +x dressed with it unsaid wore its tee
    sideways.
    """
    from seamkiln.drape.garment import piece_roles

    cast = piece_roles(pattern, roles)
    fronts = {pid for pid, role in cast.items() if role == "front"}
    if clearance_m is None:
        clearance_m = frame.clearance(shoulder_drop_mm(pattern) / 1000.0)
    top_y = float(frame.neck[1]) + clearance_m
    _ = height
    body_panels = [p for p in pattern.panels if not cast[p.id].startswith("sleeve")]
    if not body_panels:
        raise ValueError("a wrap arrangement needs at least one body panel")
    total_mm = sum(p.bbox[2] - p.bbox[0] for p in body_panels)
    radius = total_mm / 1000.0 / (2.0 * math.pi)
    # A panel's arc position is its centre RELATIVE to the panels it shares
    # a side with, not its absolute x: a block lays two front halves either
    # side of x = 0, but a CAD marker puts the back a metre to the right of
    # the front, and read absolutely that started the back 33 degrees off
    # its place before the seams pulled it round.
    group_centre: dict[str, float] = {}
    for base_role in ("front", "back"):
        members = [p for p in body_panels if cast[p.id] == base_role]
        if members:
            group_centre[base_role] = float(
                np.mean([(p.bbox[0] + p.bbox[2]) / 2000.0 for p in members])
            )

    placements: dict[str, Placement] = {}
    for panel in pattern.panels:
        role = cast[panel.id]
        tag = role[-1] if role.startswith("sleeve") else None
        if tag is not None:
            if tag not in frame.arms:
                raise ValueError(
                    f"panel {panel.id!r} is a sleeve but the body frame has no "
                    f"{tag!r} arm axis (have: {sorted(frame.arms)}). Measure the arms, "
                    "or hand the frame explicit arm axes."
                )
            shoulder, direction = frame.arms[tag]
            # "outward" is from the neck to this shoulder, level: the sign
            # of the shoulder's x was outward only for a body facing +z
            lateral = np.asarray(shoulder, dtype=np.float64) - np.asarray(
                frame.neck, dtype=np.float64
            )
            lateral[1] = 0.0
            if float(np.linalg.norm(lateral)) < 1e-9:
                lateral = np.asarray([1.0, 0.0, 0.0])
            rotation = _sleeve_frame(
                direction,
                _front_edge_side(pattern, panel.id, fronts),
                outward=lateral / float(np.linalg.norm(lateral)),
            )
            width_mm = panel.bbox[2] - panel.bbox[0]
            # The cap starts ABOVE the deltoid. A sleeve is drafted with its
            # biceps line at y = 0 and the cap rising above it, so hanging the
            # panel's top edge at the shoulder joint put the cap's apex at the
            # ball's equator and 196 of its 470 particles inside the ball,
            # where collision resolved them downward and the apex ended 75 mm
            # under the joint. Hung a cap height higher, the apex starts over
            # the shoulder and settles on top of the ball (measured +71 mm
            # against a 68 mm ball); the worst armhole pair went from 120 mm
            # to 21.
            cap_rise_m = sleeve_cap_height_mm(panel) / 1000.0
            placements[panel.id] = Placement(
                radius_m=width_mm / 1000.0 / (2.0 * math.pi),
                rotation=rotation,
                origin_m=np.asarray(shoulder, dtype=np.float64),
                top_y_m=cap_rise_m,
            )
            continue
        minx, _, maxx, _ = panel.bbox
        centre_x = (minx + maxx) / 2000.0 - group_centre[role]
        base = (180.0 if role == "back" else 0.0) + float(facing_deg)
        placements[panel.id] = Placement(
            radius_m=radius,
            centre_angle_deg=base + math.degrees(centre_x / radius),
            top_y_m=top_y,
        )
    return placements


def shoulder_anchors(
    frame: BodyFrame, offset: Vec | None = None, *, tip_fraction: float = 0.85
) -> dict[str, tuple[Vec, Vec]]:
    """Where each shoulder seam belongs: from the neck toward the shoulder tip,
    ending `tip_fraction` of the way there - INBOARD of the deltoid's crest.

    Ending the line on the joint put the seam's tip exactly on the crest of
    the ball, a knife-edge where either side is downhill, and the solver's
    arbitrary order picked a side: measured, the two sleeves started as
    mirror images to 2 mm, and after the hold one cap sat 27 mm inboard of
    the crest and the other 6 mm, then 25 mm OUTBOARD after the settle - and
    that one slid 60 mm down the arm in the first second of every walk while
    the other never moved. A set-in sleeve gets its purchase on the inner
    slope of the shoulder and its cap spills over the crest from there.
    """
    shift = np.zeros(3) if offset is None else np.asarray(offset, dtype=np.float64)
    out = {}
    for seam_id, tag in (("shoulder-right", "r"), ("shoulder-left", "l")):
        if tag in frame.arms:
            tip = frame.neck + (frame.arms[tag][0] - frame.neck) * float(tip_fraction)
            out[seam_id] = (frame.neck + shift, tip + shift)
    return out


def outside_the_body(
    sdf: Any,
    targets: Vec,
    *,
    standoff_m: float = 0.010,
    iterations: int = 8,
    direction: str = "gradient",
    max_lift_m: float = 0.12,
) -> tuple[np.ndarray, dict[str, float]]:
    """Move every target that is inside the body (or closer than `standoff_m`)
    out until it stands off the surface - along the field's gradient, or
    straight `up`.

    `up` is for a shoulder line: the neck joint is inside the neck and the
    shoulder joint is the centre of the deltoid, and the nearest surface to
    a point between them is wherever the field says - the deltoid's outer
    side as easily as its top. A shoulder seam belongs on TOP of the shoulder,
    so its anchors are lifted, not pushed out - unless the lift would be more
    than `max_lift_m`, which means the point is inside a COLUMN (the neck,
    with the head on top of it: 350-417 mm of lift measured on the line's
    first six points) and not under a shelf; those go out by the gradient,
    which puts them on the neck's surface where a collar sits.

    A pin target inside the body is an instruction the solver cannot follow:
    collision pushes the particle out on whichever side the field chooses,
    and the two particles of one seam pair can leave on different sides of a
    limb - measured on the jacket's armholes, where 78 of 114 basting
    midpoints sat inside the deltoid and two pairs per armhole ended 100 mm
    apart, split across the ball. Pin to the surface, never to the bone.

    Where the gradient is degenerate (the centre of a ball) the point is
    lifted straight up first, which is where a shoulder seam belongs anyway.
    Returns the moved targets and a small report.
    """
    original = np.asarray(targets, dtype=np.float64)
    out = original.copy()
    before = sdf.sample(out)
    moved = np.zeros(len(out), dtype=bool)
    for _ in range(max(int(iterations), 1)):
        distance = sdf.sample(out)
        need = distance < standoff_m
        if not need.any():
            break
        if direction == "up":
            step = np.tile(np.asarray([0.0, 1.0, 0.0]), (int(need.sum()), 1))
        else:
            step = sdf.gradient(out[need])
            flat = np.linalg.norm(step, axis=1) < 0.5
            step[flat] = np.asarray([0.0, 1.0, 0.0])
        out[need] += (standoff_m - distance[need])[:, None] * step
        moved |= need
    fell_back = 0
    if direction == "up":
        too_far = (np.linalg.norm(out - original, axis=1) > max_lift_m) | (
            sdf.sample(out) < standoff_m
        )
        if too_far.any():
            out[too_far], _ = outside_the_body(
                sdf, original[too_far], standoff_m=standoff_m, iterations=iterations
            )
            fell_back = int(too_far.sum())
    after = sdf.sample(out)
    return out, {
        "moved": int(moved.sum()),
        "fell_back_to_gradient": fell_back,
        "deepest_before_mm": round(float(-before.min()) * 1000.0, 1) if len(before) else 0.0,
        "shallowest_after_mm": round(float(after.min()) * 1000.0, 1) if len(after) else 0.0,
        "mean_shift_mm": round(
            float(np.linalg.norm(out - np.asarray(targets, dtype=np.float64), axis=1).mean())
            * 1000.0,
            1,
        )
        if len(out)
        else 0.0,
    }


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
    standoff_mm: float = 10.0,
    baste_sleeves_to_body: bool = True,
    head_mm: float = 60.0,
    sleeves: set[str] | None = None,
) -> Any:
    """Pin the named seams to the body, baste the rest, settle, release.

    `sleeves` names the sleeve panels; without it the block convention
    (SLEEVE_L / SLEEVE_R) is read off the ids, and a sleeve named by its
    maker is basted like a body panel and its head is never pinned over
    the shoulder - measured on a CAD tee as one sleeve facing 41 % inward.

    `anchors` maps a seam id to the (start, end) the seam should lie along -
    for a jacket, the two shoulder seams from neck to shoulder tip. Which end
    of a seam's index order is the neck end is not knowable, so both are tried
    and the one that moves the cloth less wins: the same measured-not-declared
    choice `_seam_pairs` makes about orientation, for the same reason.

    Every target - the anchored seams and the basted midpoints - is moved OUT
    of the body to `standoff_mm` before the cloth is held there
    (`outside_the_body`): the line from the neck joint to the shoulder joint
    runs through the neck and the deltoid, and a basting midpoint between two
    armhole edges that start 100 mm apart is inside the arm.

    Returns the DrapeResult of the free settle; the garment's points are left
    at that state, and `result.dressing` records what the pins did.
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

    standoff_m = float(standoff_mm) / 1000.0
    lifted_report: dict[str, float] = {}
    for seam_id, (start, end) in anchors.items():
        lo, hi = garment.seam_spans[seam_id]
        pairs = garment.seams[lo:hi]
        if not len(pairs):
            continue
        start = np.asarray(start, dtype=np.float64)
        end = np.asarray(end, dtype=np.float64)
        index = pairs.reshape(-1)
        u = np.repeat(np.linspace(0.0, 1.0, len(pairs)), 2)[:, None]
        # the line from the neck joint to the shoulder joint runs INSIDE the
        # body; the seam goes on TOP of it, so the line is lifted, not pushed
        forward, lifted_report = outside_the_body(
            sdf, start + (end - start) * u, standoff_m=standoff_m, direction="up"
        )
        backward, _ = outside_the_body(
            sdf, start + (end - start) * (1.0 - u), standoff_m=standoff_m, direction="up"
        )
        here = garment.points[index]
        chosen = (
            forward
            if np.linalg.norm(forward - here) <= np.linalg.norm(backward - here)
            else backward
        )
        pins[index] = 1.0
        targets[index] = chosen

    if baste:
        # Every other seam pair is pulled together at the same time. The
        # anchors say where the garment goes; this says its seams are sewn,
        # without needing to know where on the body each belongs. It is what
        # closes an armhole that starts 283 mm open: a stiff shell will not
        # walk that together on its own.
        #
        # A seam between a SLEEVE and the body is basted to the body's side
        # of it, not to the midpoint. The body panels hang from the pinned
        # shoulders and drape over the OUTSIDE of the deltoid; the sleeve cap
        # starts at the ball's equator. A midpoint between them is on the
        # ball's flank, and a pair held there ends up straddling the ball
        # when released - measured at 95-120 mm on both front armholes. A
        # fitter pins the sleeve to the armhole; so does this.
        held = pins > 0.0
        sleeve_particle = np.zeros(garment.n_points, dtype=bool)
        for panel_id, (lo, hi) in garment.panel_slices.items():
            if _panel_is_sleeve(panel_id, sleeves):
                sleeve_particle[lo:hi] = True
        for seam_id, (lo, hi) in garment.seam_spans.items():
            if seam_id in anchors or hi <= lo:
                continue
            pairs = garment.seams[lo:hi]
            # Basted to where its partner is GOING, not where it is. A
            # particle that is also on an anchored seam - the shoulder corner,
            # end of the shoulder seam and top of the armhole - has a target
            # inboard on the shoulder line; its sleeve partner, basted to the
            # corner's pre-hold position, was held on the wrap cylinder at
            # 248 mm from the axis, exactly the crest of a 243 mm shoulder.
            # The hold then pinned the two halves of the apex pair 40 mm
            # apart and the release snapped them together to whichever side
            # a millimetre of mesh sampling favoured: measured, the same cap
            # went outboard and slid 60 mm down the arm in every walk while
            # the other never moved. `targets` already holds the anchor
            # positions for held particles and the current positions for the
            # rest, so it is the reference for everything.
            a, b = targets[pairs[:, 0]], targets[pairs[:, 1]]
            reference = 0.5 * (a + b)
            if baste_sleeves_to_body:
                only_a = sleeve_particle[pairs[:, 0]] & ~sleeve_particle[pairs[:, 1]]
                only_b = sleeve_particle[pairs[:, 1]] & ~sleeve_particle[pairs[:, 0]]
                reference[only_a] = b[only_a]  # the sleeve goes to the body
                reference[only_b] = a[only_b]
            for side in (0, 1):
                free = ~held[pairs[:, side]]
                pins[pairs[free, side]] = 1.0
                targets[pairs[free, side]] = reference[free]

    if baste and head_mm > 0.0:
        # The sleeve HEAD is basted too: the top of the cap, moved with its
        # apex. With only the cap's edge held, the head - the part that has
        # to lie over the shoulder - settled where the ball's collision left
        # it during the hold, and on the two arms it settled 20 mm apart
        # (mirror images to 2 mm before the hold). Whichever head sat nearer
        # the crest spilled over it when the pins let go and that sleeve slid
        # down the arm in every walk that followed, whatever else changed. A
        # tailor bastes the head over the shoulder before sewing; so does
        # this, and both heads then start the release in the same state.
        rest = garment.rest_points_mm
        for panel_id, (lo, hi) in garment.panel_slices.items():
            if not _panel_is_sleeve(panel_id, sleeves):
                continue
            apex = lo + int(np.argmax(rest[lo:hi, 1]))
            if pins[apex] <= 0.0:
                continue  # no sewn apex to follow
            shift = targets[apex] - garment.points[apex]
            head = lo + np.flatnonzero(rest[lo:hi, 1] >= rest[apex, 1] - float(head_mm))
            head = head[pins[head] <= 0.0]
            pins[head] = 1.0
            targets[head] = garment.points[head] + shift

    held = pins > 0.0
    targets[held], moved = outside_the_body(sdf, targets[held], standoff_m=standoff_m)

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
    # How far the anchored seams moved once let go. Small on a garment that
    # is hooked over the shoulders and closed at the front; large on an open,
    # light, slippery coat sliding down smooth limbs - which is a fact about
    # the coat, and the number that says so.
    anchored = np.zeros(garment.n_points, dtype=bool)
    for seam_id in anchors:
        lo, hi = garment.seam_spans[seam_id]
        anchored[garment.seams[lo:hi].reshape(-1)] = True
    drift = (
        float(np.linalg.norm(result.points[anchored] - targets[anchored], axis=1).mean())
        if anchored.any()
        else 0.0
    )
    result.dressing = {
        "pinned": int(held.sum()),
        "standoff_mm": float(standoff_mm),
        "anchors_lifted_mm": lifted_report.get("mean_shift_mm", 0.0),
        "anchors_by_gradient": lifted_report.get("fell_back_to_gradient", 0),
        "drift_mm": round(drift * 1000.0, 1),
        **moved,
    }
    return result


__all__ = [
    "BodyFrame",
    "dress",
    "frame_from_figure",
    "frame_from_mesh",
    "outside_the_body",
    "shoulder_anchors",
    "shoulder_drop_mm",
    "wrap_arrangement",
]
