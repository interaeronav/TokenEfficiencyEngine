"""Blend-shape animation: record a body changing, and drape the whole way.

An avatar's shape parameters are keyframes like any other channel. Record a
few, interpolate between them, and the garment is solved ALONG the sequence -
carrying the cloth's positions and its history forward from frame to frame,
which is the whole point. Re-draping each frame from the arrangement would
give a garment that pops between shapes; continuing the solve gives one that
is dragged by the body underneath it, which is what a body changing shape
does to clothes.

The honest cost is stated: the collision field has to be rebaked whenever the
body changes, and that dominates. `frame_seconds` in the report separates the
solve from the rebake so nobody optimises the wrong one.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field, replace
from typing import Any

import numpy as np

PHENOTYPES = ("gender", "age", "muscle", "weight", "height", "proportions")


@dataclass(slots=True)
class Keyframe:
    """A body shape at a moment. Values run 0..1, Anny's own range."""

    time_s: float
    values: dict[str, float] = field(default_factory=dict)
    label: str = ""

    def __post_init__(self) -> None:
        unknown = set(self.values) - set(PHENOTYPES) - {"stature_m"}
        if unknown:
            raise ValueError(
                f"unknown blend shape(s) {sorted(unknown)}; channels: "
                f"{', '.join(PHENOTYPES)} (plus stature_m)."
            )


@dataclass(slots=True)
class BlendTrack:
    """A sequence of shapes, interpolated."""

    keys: list[Keyframe] = field(default_factory=list)
    ease: bool = True  # smoothstep between keys rather than a linear ramp

    def __post_init__(self) -> None:
        self.keys = sorted(self.keys, key=lambda k: k.time_s)
        if len({k.time_s for k in self.keys}) != len(self.keys):
            raise ValueError("two keyframes share a time; a track cannot branch")

    @property
    def duration(self) -> float:
        return self.keys[-1].time_s - self.keys[0].time_s if self.keys else 0.0

    def record(self, time_s: float, label: str = "", **values: float) -> BlendTrack:
        """Add a keyframe. Chainable, because recording is done in a line."""
        self.keys.append(Keyframe(time_s, dict(values), label))
        self.keys.sort(key=lambda k: k.time_s)
        return self

    def channels(self) -> list[str]:
        seen: set[str] = set()
        for key in self.keys:
            seen |= set(key.values)
        return sorted(seen)

    def at(self, time_s: float) -> dict[str, float]:
        """The shape at a moment, interpolated between the keys around it."""
        if not self.keys:
            return {}
        if time_s <= self.keys[0].time_s:
            return dict(self.keys[0].values)
        if time_s >= self.keys[-1].time_s:
            return dict(self.keys[-1].values)
        for before, after in zip(self.keys, self.keys[1:], strict=False):
            if before.time_s <= time_s <= after.time_s:
                span = after.time_s - before.time_s
                t = 0.0 if span <= 0 else (time_s - before.time_s) / span
                if self.ease:
                    t = t * t * (3.0 - 2.0 * t)  # smoothstep: no velocity jump
                out: dict[str, float] = {}
                for channel in set(before.values) | set(after.values):
                    low = before.values.get(channel, after.values.get(channel, 0.5))
                    high = after.values.get(channel, low)
                    out[channel] = low + (high - low) * t
                return out
        return dict(self.keys[-1].values)

    def sample(self, fps: float = 12.0) -> list[tuple[float, dict[str, float]]]:
        count = max(round(self.duration * fps) + 1, 1)
        times = np.linspace(self.keys[0].time_s, self.keys[-1].time_s, count)
        return [(float(t), self.at(float(t))) for t in times]

    def as_dict(self) -> dict[str, Any]:
        return {
            "keys": [{"time_s": k.time_s, "label": k.label, "values": k.values} for k in self.keys],
            "duration_s": self.duration,
            "channels": self.channels(),
            "ease": self.ease,
        }


@dataclass(slots=True)
class AnimationFrame:
    time_s: float
    values: dict[str, float]
    points: np.ndarray
    body_seconds: float
    solve_seconds: float
    report: dict[str, Any] = field(default_factory=dict)
    # the body's mean velocity over the interval that ENDED at this frame
    # (m/s, world), zero for the first frame
    body_velocity: np.ndarray | None = None
    # how far any body vertex moved between the previous pose and this one,
    # body-local (the blend's own accuracy knob: see `animate`)
    sweep_mm: float = 0.0
    field_seconds: float = 0.0


def _body_and_offset(built) -> tuple[Any, np.ndarray]:
    """A body_factory may return a mesh, or (mesh, offset): the mesh is
    BODY-LOCAL and the offset is where it stands in the world - travel, the
    gait's rise, the figure's standing lift - applied as a rigid placement of
    the baked field rather than baked into it."""
    if isinstance(built, tuple):
        mesh, offset = built
        return mesh, np.asarray(offset, dtype=np.float64)
    return built, np.zeros(3, dtype=np.float64)


def _sweep_mm(previous, current) -> float:
    """How far the body's SURFACE moved between two body-local poses: for
    every vertex of the new pose, the distance to the nearest vertex of the
    old one, and the largest of those. Correspondence-free on purpose - a
    merged capsule body keeps its vertex count between poses but not its
    vertex order, and matching by index reported a 338 mm "sweep" on a walk
    whose fastest limb moved a third of that."""
    if previous is None:
        return 0.0
    from scipy.spatial import cKDTree

    a = np.asarray(previous.vertices, dtype=np.float64)
    b = np.asarray(current.vertices, dtype=np.float64)
    nearest, _ = cKDTree(a).query(b, workers=-1)
    return float(nearest.max()) * 1000.0


def animate(
    garment,
    track: BlendTrack,
    *,
    fabric: str = "cotton_jersey",
    fps: float = 8.0,
    frames_per_step: int | None = None,
    voxel_mm: float = 12.0,
    body_factory=None,
    settings=None,
    advance=None,
) -> list[AnimationFrame]:
    """Solve the garment along the track, with the body moving THROUGH each frame.

    `advance(time_s) -> [x, y, z]` moves the WHOLE body through the world as
    it animates. Without it a walk happens on the spot - which is fine for a
    drape test and wrong for a shot, because a body that swings its legs
    without travelling is skating.

    `body_factory(values)` builds the body for a shape - Anny by default, so
    the caller does not have to know about it, but replaceable so the stand-in
    mannequin (or any other body) can be animated in a test without a model
    download. It may return a mesh, or `(mesh, offset)`: the mesh body-local
    and the offset (a gait's rise, a figure's standing lift) a rigid
    placement, which the solver carries exactly and for free. A factory with
    `rigid = True` is baked once.

    The body used to move between frames as a JUMP: rebake, teleport the
    garment by the travel, solve on a body standing still. Each jump up into
    the cloth resolved as a full push in one substep, and nothing on the way
    down pulled the cloth back - a jersey tee rode up 16 mm per walking stride
    and 40 per running stride, without saturating. Now every frame's bake is
    the END of one interval and the START of the next: the solver gets the
    previous placement, the next one, and a per-substep schedule between them
    (`BodyMotion.between`), so the rigid part is exact and a deforming body is
    a surface that moves continuously through the frame. The garment is never
    teleported - the contact carries it - and the cloth's velocity is carried
    from frame to frame, seeded with the body's travel so a gait has no first
    frame. K samples in, K frames out; frame 0 is the settle on the first pose.

    The blend's own accuracy: two fields blended cell for cell pinch a limb of
    radius R that moves delta within a frame by about delta^2 / 8R, which is
    below the field's own half-voxel whenever delta <= 2 sqrt(voxel R) - 41 mm
    per frame for a 42 mm forearm on a 10 mm voxel. `sweep_mm` on each frame
    and `max_sweep_mm` in the report say where a body stands against that; the
    honest knob is fps, because the error falls with delta squared.
    """
    from seamkiln.drape.body import BodyMotion, sdf_from_mesh
    from seamkiln.drape.solve import DrapeSettings, drape, prepare

    if not track.keys:
        raise ValueError("an empty track animates nothing")
    if body_factory is None:

        def body_factory(values: dict[str, float]):
            from seamkiln.drape.anny_body import anny_body

            stature = values.get("stature_m", 1.75)
            return anny_body(
                stature_m=stature,
                **{k: v for k, v in values.items() if k in PHENOTYPES},
            )

    options = settings or DrapeSettings()
    # How much CLOTH TIME one animation frame gets. This is not a free
    # parameter: the body advances 1/fps seconds between frames, so the cloth
    # must advance 1/fps seconds too.
    #
    # It was a free parameter, and that was a real bug with a measured cost. A
    # run gait at 8 fps with the old default of 60 steps gave the cloth 1.0 s
    # of gravity for every 0.125 s the body moved - eight times too much - and
    # a t-shirt SLID 270 MM DOWN the body over one stride while every frame
    # still reported `worn=True`, because it was still touching. Matching the
    # two took the slip to 37 mm at 8 fps and 13 mm at 16 fps; at 32 fps the
    # shirt is thrown 19 mm UP, which is what a run does to a shirt.
    #
    # The lesson for anyone tempted to raise this for accuracy: accuracy comes
    # from `substeps`, which subdivides the same second of cloth time. `frames`
    # buys MORE SECONDS, and more seconds than the body took is not accuracy,
    # it is a different animation.
    natural = max(round((1.0 / fps) / options.dt), 1)
    if frames_per_step is None:
        frames_per_step = natural
    elif abs(frames_per_step - natural) > max(1, natural // 5):
        raise ValueError(
            f"frames_per_step={frames_per_step} gives the cloth "
            f"{frames_per_step * options.dt:.3f} s per animation frame while the body "
            f"advances {1.0 / fps:.3f} s. The garment will slide - measured at 270 mm "
            f"down a body in one stride when this was 8x out. Use {natural} (or leave "
            f"it unset), and raise `substeps` if you want a more accurate solve."
        )
    options = replace(options, frames=frames_per_step)
    steps = options.frames * options.substeps
    samples = list(track.sample(fps))
    rigid = bool(getattr(body_factory, "rigid", False))

    # Every body first, body-local: milliseconds each, and their union is the
    # one lattice every frame's field is baked on so two frames can blend.
    started = time.perf_counter()
    built = [_body_and_offset(body_factory(values)) for _, values in samples]
    build_seconds = time.perf_counter() - started
    bounds = None
    if not rigid:
        lows = np.min([np.asarray(mesh.bounds[0]) for mesh, _ in built], axis=0)
        highs = np.max([np.asarray(mesh.bounds[1]) for mesh, _ in built], axis=0)
        bounds = (lows, highs)

    prepared = prepare(garment, fabric=fabric, settings=options)
    out: list[AnimationFrame] = []
    field = None
    previous = None
    previous_mesh = None
    previous_time = None
    velocity = None
    for index, (time_s, values) in enumerate(samples):
        mesh, local = built[index]
        started = time.perf_counter()
        if field is None or not rigid:
            field = sdf_from_mesh(mesh, voxel_mm=voxel_mm, bounds=bounds)
        field_seconds = time.perf_counter() - started
        travel = np.asarray(advance(time_s), dtype=np.float64) if advance is not None else 0.0
        placed = field.moved(travel + local)
        sweep = _sweep_mm(previous_mesh, mesh) if not rigid else 0.0

        if previous is None:
            # frame 0: the settle on the first pose, then the cloth starts
            # already moving with the body - a gait has no first frame
            result = drape(garment, placed, fabric=fabric, settings=options, prepared=prepared)
            body_velocity = np.zeros(3, dtype=np.float64)
            if advance is not None and len(samples) > 1:
                t1 = samples[1][0]
                body_velocity = (
                    np.asarray(advance(t1), dtype=np.float64) - np.asarray(advance(time_s))
                ) / max(t1 - time_s, 1e-9)
            velocity = result.velocity + body_velocity[None, :]
        else:
            motion = BodyMotion.between(previous, placed, steps=steps)
            result = drape(
                garment,
                previous,
                fabric=fabric,
                settings=options,
                prepared=prepared,
                velocity=velocity,
                motion=motion,
            )
            velocity = result.velocity
            body_velocity = (placed.translation - previous.translation) / max(
                time_s - previous_time, 1e-9
            )
        garment.points = result.points
        previous, previous_mesh, previous_time = placed, mesh, time_s
        out.append(
            AnimationFrame(
                time_s=time_s,
                values=values,
                points=result.points.copy(),
                body_seconds=field_seconds + (build_seconds if index == 0 else 0.0),
                solve_seconds=result.seconds,
                report=result.report(),
                body_velocity=body_velocity,
                sweep_mm=round(sweep, 1),
                field_seconds=field_seconds,
            )
        )
    return out


def animation_report(frames: list[AnimationFrame]) -> dict[str, Any]:
    """What the sequence cost and whether it stayed sane, compactly."""
    if not frames:
        return {"frames": 0}
    body = sum(f.body_seconds for f in frames)
    solve = sum(f.solve_seconds for f in frames)
    speeds = [float(np.linalg.norm(f.body_velocity)) for f in frames if f.body_velocity is not None]
    return {
        "frames": len(frames),
        "duration_s": round(frames[-1].time_s - frames[0].time_s, 3),
        "body_seconds": round(body, 2),
        "solve_seconds": round(solve, 2),
        "rebake_share": round(body / max(body + solve, 1e-9), 3),
        "worn_throughout": all(f.report["contact"]["worn"] for f in frames),
        "worst_penetration_mm": round(
            max(f.report["penetration"]["deepest_penetration_mm"] for f in frames), 2
        ),
        "max_body_speed_ms": round(max(speeds), 3) if speeds else 0.0,
        "max_sweep_mm": round(max(f.sweep_mm for f in frames), 1),
        "note": "the collision field is rebaked whenever the body changes; "
        "`rebake_share` says how much of the time that was. The body moves "
        "continuously within each frame; `max_sweep_mm` is the largest move "
        "of any body vertex between poses, the blend's own accuracy knob",
    }
