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
) -> list[AnimationFrame]:
    """Solve the garment along the track, carrying the cloth forward.

    `body_factory(values)` builds the body for a shape - Anny by default, so
    the caller does not have to know about it, but replaceable so the stand-in
    mannequin (or any other body) can be animated in a test without a model
    download.
    """
    from seamkiln.drape.body import sdf_from_mesh
    from seamkiln.drape.solve import DrapeSettings, drape

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
    out: list[AnimationFrame] = []
    points = None
    for time_s, values in track.sample(fps):
        started = time.perf_counter()
        body = body_factory(values)
        sdf = sdf_from_mesh(body, voxel_mm=voxel_mm)
        body_seconds = time.perf_counter() - started

        if points is not None:
            # carry the cloth forward: the garment is DRAGGED by the body
            # changing under it, not re-draped from scratch, which would pop
            garment.points = points
        result = drape(garment, sdf, fabric=fabric, settings=options)
        points = result.points.copy()
        out.append(
            AnimationFrame(
                time_s=time_s,
                values=values,
                points=points,
                body_seconds=body_seconds,
                solve_seconds=result.seconds,
                report=result.report(),
            )
        )
    return out


def animation_report(frames: list[AnimationFrame]) -> dict[str, Any]:
    """What the sequence cost and whether it stayed sane, compactly."""
    if not frames:
        return {"frames": 0}
    body = sum(f.body_seconds for f in frames)
    solve = sum(f.solve_seconds for f in frames)
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
        "note": "the collision field is rebaked whenever the body changes; "
        "`rebake_share` says how much of the time that was",
    }
