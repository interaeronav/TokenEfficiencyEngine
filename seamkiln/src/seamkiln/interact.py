"""Pulling cloth around by hand, at a rate that makes it worth doing.

The incumbents' selling point is that you can grab a draped garment and pull
it. What makes that useful is not the grabbing - it is that the cloth answers
while your hand is still moving. So this module is as much about the clock as
about the gesture, and it reports its own measured rate rather than claiming
one.

What made it possible: `drape` used to rebuild the whole constraint graph on
every call - colouring it, flattening it, building the bending quads and the
vertex-to-triangle index. That is invisible on a 280-frame settle and it was
most of the budget on a one-frame drag step. Measured on a t-shirt:

    4,549 particles   56.2 ms rebuilt (18 fps)   23.2 ms prepared (43 fps)
    7,441 particles   77.1 ms rebuilt (13 fps)   21.3 ms prepared (47 fps)

Note the second row: prepared, the FINER mesh is faster per step, because the
saving is a fixed setup cost and the kernel itself parallelises. The output is
bit-identical either way - same fingerprint, zero position difference - so
this is a cache, not an approximation.

A grip is feathered, not a clamp: full hold at the centre easing to nothing at
the rim, because fingers are not clamps and a hard edge shows up as a crease
that nobody put there.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any

import numpy as np

from seamkiln.drape.garment import GarmentMesh
from seamkiln.drape.solve import BodySDF, DrapeSettings, Prepared, drape, prepare


@dataclass(slots=True)
class Handle:
    """What the hand is holding: which particles, how firmly, and where."""

    indices: np.ndarray  # int64
    weights: np.ndarray  # float64, 1 at the centre easing to 0 at the rim
    grabbed_at: np.ndarray  # float64 [3] - where the grab started
    at: np.ndarray  # float64 [3] - where it is now
    radius_mm: float

    def __len__(self) -> int:
        return int(self.indices.shape[0])

    @property
    def travel_mm(self) -> float:
        return float(np.linalg.norm(self.at - self.grabbed_at)) * 1000.0

    def summary(self) -> dict[str, Any]:
        return {
            "holding": len(self),
            "radius_mm": self.radius_mm,
            "travel_mm": round(self.travel_mm, 2),
            "at": [round(float(v), 4) for v in self.at],
        }


@dataclass(slots=True)
class LiveSession:
    """A draped garment you can pull on, with the graph prepared once.

    Velocity is carried across steps deliberately. Without it the cloth
    restarts from rest on every step and a drag feels like dragging treacle -
    which is not a look, it is the integrator forgetting.
    """

    garment: GarmentMesh
    sdf: BodySDF
    fabric: str = "cotton_jersey"
    settings: DrapeSettings = field(default_factory=lambda: DrapeSettings(frames=1, substeps=12))
    _prepared: Prepared | None = None
    _velocity: np.ndarray | None = None
    _steps: int = 0
    _seconds: float = 0.0
    _settles: int = 0
    _settle_seconds: float = 0.0

    def __post_init__(self) -> None:
        self._prepared = prepare(self.garment, fabric=self.fabric, settings=self.settings)

    # -- the gestures ----------------------------------------------------------

    def grab(self, at: tuple[float, float, float], *, radius_mm: float = 40.0) -> Handle:
        """Take hold of the cloth near a point in the world - what a click is."""
        centre = np.asarray(at, dtype=np.float64)
        radius = radius_mm / 1000.0
        distance = np.linalg.norm(self.garment.points - centre, axis=1)
        inside = np.nonzero(distance <= radius)[0]
        if inside.size == 0:
            nearest = float(distance.min()) * 1000.0
            raise ValueError(
                f"no cloth within {radius_mm:g} mm of {np.round(centre, 3).tolist()}; "
                f"the nearest is {nearest:.0f} mm away. Grab closer, or widen the grip."
            )
        weights = 1.0 - (distance[inside] / max(radius, 1e-9)) ** 2
        return Handle(
            indices=inside.astype(np.int64),
            weights=weights,
            grabbed_at=centre.copy(),
            at=centre.copy(),
            radius_mm=float(radius_mm),
        )

    def drag(self, handle: Handle, to: tuple[float, float, float], *, steps: int = 1) -> Handle:
        """Move the hand and let the cloth answer. ONE interactive step."""
        target = np.asarray(to, dtype=np.float64)
        offset = target - handle.at
        handle.at = target
        mask = np.zeros(self.garment.n_points, dtype=np.float64)
        mask[handle.indices] = handle.weights
        goal = self.garment.points.copy()
        goal[handle.indices] += offset * handle.weights[:, None]
        self._step(pins=mask, pin_target=goal, frames=steps)
        return handle

    def release(self, handle: Handle | None = None, *, frames: int = 40) -> dict[str, Any]:
        """Let go, and let it settle. The hand stops; gravity does not."""
        return self._step(pins=None, pin_target=None, frames=frames, settling=True)

    def fold(
        self,
        at: tuple[float, float, float],
        *,
        depth_mm: float = 40.0,
        direction: tuple[float, float, float] = (0.0, 0.0, -1.0),
        radius_mm: float = 50.0,
        settle: int = 30,
    ) -> dict[str, Any]:
        """Push a fold in by hand: grab, push, let go.

        A fold set this way is not a decoration painted on - it is cloth that
        was moved and then released, so it stays only to the extent the fabric
        will hold it. Measured on a tee front, a 45 mm push held for 40 frames
        after letting go:

            silk habotai   pushed 20.3 mm, kept 14.1 mm   (69%)
            cotton poplin  pushed 25.0 mm, kept 23.4 mm   (94%)
            denim 12 oz    pushed 20.3 mm, kept 18.1 mm   (89%)
            wool suiting   pushed 23.6 mm, kept 13.9 mm   (59%)

        Note that this does NOT order by stiffness, and the tempting story -
        "stiff fabrics hold a fold" - is not what the numbers say. Two things
        fight: stiffness resists the cloth springing back, and WEIGHT pulls the
        fold out. The same 45 mm hand movement also moves each fabric a
        different distance in the first place, which is why `pushed_mm` is
        reported next to `held_mm` rather than assumed equal to the request.
        """
        handle = self.grab(at, radius_mm=radius_mm)
        push = np.asarray(direction, dtype=np.float64)
        push = push / max(float(np.linalg.norm(push)), 1e-12) * (depth_mm / 1000.0)
        axis = push / max(float(np.linalg.norm(push)), 1e-12)
        before = self.garment.points.copy()
        self.drag(handle, tuple(np.asarray(at) + push), steps=6)
        after_push = self.garment.points.copy()
        report = self.release(handle, frames=settle)

        # Measured ALONG THE PUSH AXIS, not as a distance. Total displacement
        # is the wrong instrument and it said so loudly: every fabric came out
        # holding 150-200% of the push, because the settle after letting go is
        # mostly the cloth falling, and a fold pushed sideways plus a hem
        # dropping downward is a longer vector than either on its own.
        # Projecting on the axis the fold was pushed along leaves gravity out
        # of the number, which is where it belongs.
        def along(now: np.ndarray) -> float:
            return float(((now[handle.indices] - before[handle.indices]) @ axis).mean())

        pushed, held = along(after_push), along(self.garment.points)
        return {
            **report,
            "pushed_mm": round(pushed * 1000.0, 2),
            "held_mm": round(held * 1000.0, 2),
            "held_fraction": round(held / pushed, 3) if abs(pushed) > 1e-9 else 0.0,
            "fabric": self.fabric,
        }

    def ease(self, seam_id: str, mm: float) -> dict[str, Any]:
        """Adjust a stitch: let a seam out, or take it in, by millimetres.

        This one is NOT interactive-rate and does not pretend to be. Changing a
        rest length changes the constraint data the prepared graph was built
        around, so the graph is rebuilt - about 30 ms. That is the right trade:
        you drag cloth continuously and you adjust a stitch discretely, and
        nobody scrubs a seam allowance at 60 fps.
        """
        if seam_id not in self.garment.seam_spans:
            known = ", ".join(sorted(self.garment.seam_spans)) or "none"
            raise ValueError(f"no seam {seam_id!r} on this garment (have: {known}).")
        lo, hi = self.garment.seam_spans[seam_id]
        self.garment.seam_rest = self.garment.seam_rest.copy()
        self.garment.seam_rest[lo:hi] = np.maximum(self.garment.seam_rest[lo:hi] + mm / 1000.0, 0.0)
        self._prepared = prepare(self.garment, fabric=self.fabric, settings=self.settings)
        report = self._step(pins=None, pin_target=None, frames=40, settling=True)
        pairs = self.garment.seams[lo:hi]
        mine = np.linalg.norm(
            self.garment.points[pairs[:, 0]] - self.garment.points[pairs[:, 1]], axis=1
        )
        # THIS seam's gap, not the garment's. Eases are cumulative, so the
        # number that answers "did that do what I asked" is the one for the
        # seam that was touched.
        return {
            **report,
            "seam": seam_id,
            "eased_mm": mm,
            "this_seam_mean_mm": round(float(mine.mean()) * 1000.0, 3),
            "this_seam_max_mm": round(float(mine.max()) * 1000.0, 3),
            "rest_mean_mm": round(float(self.garment.seam_rest[lo:hi].mean()) * 1000.0, 3),
            "garment_seam_gaps": self.garment.seam_gaps_mm(self.garment.points),
        }

    # -- the clock -------------------------------------------------------------

    def rate(self) -> dict[str, Any]:
        """What this session ACTUALLY achieved. Measured, never claimed."""
        if not self._steps:
            return {"steps": 0}
        per_step = self._seconds / self._steps * 1000.0
        out = {
            "steps": self._steps,
            "ms_per_step": round(per_step, 2),
            "fps": round(1000.0 / per_step, 1),
            "particles": self.garment.n_points,
            "interactive": per_step <= 100.0,
        }
        if self._settles:
            # Kept SEPARATE, because averaging them together is a lie in both
            # directions: a 40-frame settle took the reported rate of a 43 fps
            # drag down to 2.2 fps, which describes neither.
            out["settles"] = self._settles
            out["ms_per_settle"] = round(self._settle_seconds / self._settles * 1000.0, 2)
        return out

    def _step(self, *, pins, pin_target, frames: int, settling: bool = False) -> dict[str, Any]:
        options = DrapeSettings(
            frames=max(int(frames), 1),
            substeps=self.settings.substeps,
            dt=self.settings.dt,
            damping=self.settings.damping,
            friction=self.settings.friction,
            thickness_mm=self.settings.thickness_mm,
            environment=self.settings.environment,
            grain_angle_deg=self.settings.grain_angle_deg,
            seam_compliance=self.settings.seam_compliance,
            fibre=self.settings.fibre,
        )
        started = time.perf_counter()
        result = drape(
            self.garment,
            self.sdf,
            fabric=self.fabric,
            settings=options,
            pins=pins,
            pin_target=pin_target,
            prepared=self._prepared,
            velocity=self._velocity,
        )
        elapsed = time.perf_counter() - started
        if settling:
            self._settles += 1
            self._settle_seconds += elapsed
        else:
            self._steps += 1
            self._seconds += elapsed
        self.garment.points = result.points
        # Carry the velocity, or the cloth restarts from rest every step and
        # the drag feels like treacle. This is why `drape` takes one.
        self._velocity = result.velocity
        return {
            "ms": round(elapsed * 1000.0, 2),
            "frames": options.frames,
            "worn": result.contact.get("worn"),
            "max_seam_gap_mm": result.seam_gaps["max_gap_mm"],
        }


__all__ = ["Handle", "LiveSession"]
