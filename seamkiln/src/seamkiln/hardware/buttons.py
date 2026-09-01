"""Buttons and buttonholes: a two-part fastener, and what fastening one does.

A button is not one object. It is a button on one panel and a buttonhole on
the other, and until something joins them they are two unrelated lumps. That
join is the "fasten" gesture: you pick a button, you pick a buttonhole, and
the simulation pulls the two panels together and holds them there.

What that means in constraints, and why each part is there:

  the shank    the button sits ON the cloth and the thread passes THROUGH it,
               so a fastened button holds the two panels a real distance
               apart - the shank height plus both cloth thicknesses. Not
               zero. A placket with the panels at zero separation is a placket
               with the fabric occupying the same space as itself.
  the thread   a few millimetres of it, and it is not rigid. A shirt button
               swivels; a rivet does not. `thread_mm` is the difference.
  the collision the button is a solid disc that the cloth cannot pass through.
               Modelled as a rim of constraints round the hole rather than a
               separate collider, because the cloth it has to stay out of is
               the cloth it is sewn to.

Types, all of which are the trade's and not invented here:

  2-hole / 4-hole  sew-through. The classic shirt and jacket button.
  shank            a loop on the back instead of holes; stands off the cloth,
                   which is why coats use them - thick cloth needs the room.
  snap             two interlocking halves, no thread. Fastens by pressure and
                   POPS at a load, which is the one type here that can fail.
  rivet            permanent. Cannot be unfastened, and refuses to be.
  toggle           a bar through a loop. Long, low, and it swivels freely.

Custom assets, because a studio has its own:
  * a button modelled elsewhere arrives as an OBJ and is registered by its
    measured bounding box and volume - which is where its WEIGHT comes from,
    rather than from a number somebody typed.
  * a buttonhole arrives as a black-and-white PNG with a transparent
    background: black is the hole. It is read as a mask and reduced to the
    hole's outline, which is what the placement and the collision rim need.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np

from seamkiln.drape.garment import GarmentMesh
from seamkiln.hardware.trim import MM_PER_LIGNE, Trim, button_trim

# type -> (holes, has a shank, can be undone, thread is rigid)
TYPES: dict[str, tuple[int, bool, bool, bool]] = {
    "2-hole": (2, False, True, False),
    "4-hole": (4, False, True, False),
    "shank": (0, True, True, False),
    "snap": (0, False, True, True),
    "rivet": (0, False, False, True),
    "toggle": (2, True, True, False),
}


@dataclass(slots=True)
class ButtonSpec:
    """One button, as a supplier would describe it plus what physics needs."""

    kind: str = "4-hole"
    ligne: float = 24.0  # 24L = 15.2 mm, the shirt-front default
    material: str = "polyester"
    thickness_mm: float = 3.0
    shank_mm: float = 0.0  # stand-off; a shank button has one by definition
    thread_mm: float = 2.5  # how much slack the thread allows
    # Override the mass instead of deriving it from the disc's volume. Set by
    # a custom OBJ (measured) or by a user who has one on a scale.
    mass_g: float | None = None
    collision_mm: float | None = None  # defaults to the button's own diameter
    mesh_path: str = ""  # a custom OBJ, if this is a studio's own button

    def __post_init__(self) -> None:
        if self.kind not in TYPES:
            raise ValueError(f"unknown button type {self.kind!r}. Known: {', '.join(TYPES)}")
        if self.ligne <= 0.0:
            raise ValueError(f"button size must be positive, got {self.ligne}L")
        if TYPES[self.kind][1] and self.shank_mm <= 0.0:
            # A shank button or a toggle without a shank is a flat button, and
            # the stand-off is the whole reason either type exists.
            self.shank_mm = 3.5

    @property
    def diameter_mm(self) -> float:
        return self.ligne * MM_PER_LIGNE

    @property
    def holes(self) -> int:
        return TYPES[self.kind][0]

    @property
    def undoable(self) -> bool:
        return TYPES[self.kind][2]

    @property
    def rigid_thread(self) -> bool:
        return TYPES[self.kind][3]

    def trim(self) -> Trim:
        return button_trim(self.material)

    def mass_kg(self) -> float:
        """Grams, from the disc's own volume - not from a typed-in number.

        A 24L polyester 4-hole comes out at 0.75 g, which is what a shirt
        button weighs. Ten of them down a front is 7.5 g, about the same as a
        nylon zipper of the same length, which is the useful comparison.
        """
        if self.mass_g is not None:
            return self.mass_g / 1000.0
        r = self.diameter_mm / 2000.0
        volume = math.pi * r * r * (self.thickness_mm / 1000.0)
        if self.shank_mm:  # the shank is a stub of roughly a third the radius
            volume += math.pi * (r / 3.0) ** 2 * (self.shank_mm / 1000.0)
        return volume * self.trim().density_kg_m3

    def stand_off_m(self, cloth_mm: float) -> float:
        """How far apart a fastened button holds the two panels, metres."""
        return (self.shank_mm + self.thread_mm + 2.0 * cloth_mm) / 1000.0

    def collision_m(self) -> float:
        return (self.collision_mm or self.diameter_mm) / 1000.0


@dataclass(slots=True)
class Buttonhole:
    """A hole, on a panel, at a point. `length_mm` is along the slit."""

    panel: str
    index: int  # the particle it is centred on
    length_mm: float
    angle_deg: float = 0.0  # 0 = horizontal, 90 = vertical
    mask_path: str = ""  # a custom PNG, if this is a studio's own shape

    def fits(self, button: ButtonSpec) -> bool:
        """A hole must be LONGER than the button is wide, or it will not pass.

        The trade rule is diameter + thickness; the thickness is what has to
        turn through the slit edge-on.
        """
        return self.length_mm >= button.diameter_mm + button.thickness_mm - 0.5


@dataclass(slots=True)
class Fastening:
    """A button fastened to a buttonhole: the pair, and the load between them."""

    id: str
    button: ButtonSpec
    button_at: int  # particle index on the button's panel
    hole: Buttonhole
    stand_off_m: float
    popped: bool = False
    meta: dict[str, Any] = field(default_factory=dict)

    def summary(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "type": self.button.kind,
            "size": f"{self.button.ligne:g}L ({self.button.diameter_mm:.1f} mm)",
            "material": self.button.material,
            "mass_g": round(self.button.mass_kg() * 1000.0, 3),
            "hole_mm": round(self.hole.length_mm, 1),
            "stand_off_mm": round(self.stand_off_m * 1000.0, 2),
            "undoable": self.button.undoable,
            "popped": self.popped,
        }


def place(
    garment: GarmentMesh,
    points: np.ndarray,
    *,
    panel: str,
    at: tuple[float, float],
) -> int:
    """The nearest particle on `panel` to a point on the FLAT pattern, in mm.

    Placement is done in 2D because that is where a button is placed - on the
    pattern piece, next to the edge, before anything is sewn. Placing in 3D
    would mean the button moves when the garment moves, which is not what a
    button sewn to a specific spot does.
    """
    if panel not in garment.panel_slices:
        raise ValueError(f"no panel {panel!r} (have: {', '.join(sorted(garment.panel_slices))})")
    lo, hi = garment.panel_slices[panel]
    flat = garment.rest_points_mm[lo:hi]
    return lo + int(np.argmin(np.linalg.norm(flat - np.asarray(at, dtype=np.float64), axis=1)))


def hole(
    garment: GarmentMesh,
    *,
    panel: str,
    at: tuple[float, float],
    button: ButtonSpec | None = None,
    length_mm: float | None = None,
    angle_deg: float = 0.0,
    mask_path: str = "",
) -> Buttonhole:
    """Cut a buttonhole. Sized to the button unless you say otherwise."""
    spec = button or ButtonSpec()
    length = length_mm if length_mm is not None else spec.diameter_mm + spec.thickness_mm
    return Buttonhole(
        panel=panel,
        index=place(garment, garment.points, panel=panel, at=at),
        length_mm=float(length),
        angle_deg=float(angle_deg),
        mask_path=mask_path,
    )


def fasten(
    garment: GarmentMesh,
    button_at: int,
    buttonhole: Buttonhole,
    *,
    button: ButtonSpec | None = None,
    cloth_mm: float = 0.35,
    id: str = "",
) -> Fastening:
    """The Fasten Button gesture: pick a button, pick a hole, done.

    Refuses a hole the button will not go through, which is the mistake worth
    catching - a 15.2 mm button and a 14 mm hole look fine on a screen and
    cannot be done up on a body.
    """
    spec = button or ButtonSpec()
    if not buttonhole.fits(spec):
        need = spec.diameter_mm + spec.thickness_mm
        raise ValueError(
            f"a {spec.ligne:g}L {spec.kind} is {spec.diameter_mm:.1f} mm across and "
            f"{spec.thickness_mm:.1f} mm thick; it will not pass a "
            f"{buttonhole.length_mm:.1f} mm hole. Cut the hole to {need:.1f} mm."
        )
    return Fastening(
        id=id or f"button@{button_at}",
        button=spec,
        button_at=int(button_at),
        hole=buttonhole,
        stand_off_m=spec.stand_off_m(cloth_mm),
    )


def unfasten(fastening: Fastening) -> Fastening:
    """Undo one. A rivet refuses, because a rivet is permanent."""
    if not fastening.button.undoable:
        raise ValueError(
            f"a {fastening.button.kind} cannot be undone - that is what makes it a "
            f"{fastening.button.kind}. Remove it from the fastening list to take it off."
        )
    fastening.popped = True
    fastening.meta["undone"] = True
    return fastening


def apply(garment: GarmentMesh, fastenings: list[Fastening], name: str = "buttons") -> GarmentMesh:
    """Write every fastened button into the garment as constraints and weight."""
    live = [f for f in fastenings if not f.popped]
    if not live:
        garment.detach(name)
        garment.detach(f"{name}:rim")
        return garment

    pairs = np.asarray([[f.button_at, f.hole.index] for f in live], dtype=np.int32)
    rest = np.asarray([f.stand_off_m for f in live], dtype=np.float64)

    added = np.zeros(garment.n_points, dtype=np.float64)
    for f in live:
        # Half on the button, half on the hole: a fastened button's weight is
        # carried by both panels, which is the point of fastening it.
        added[f.button_at] += f.button.mass_kg() * 0.5
        added[f.hole.index] += f.button.mass_kg() * 0.5

    # A sewn-through button swivels, a rivet does not. Softening the thread is
    # how that reads: a rivet's is rigid, a shirt button's gives.
    compliance = 0.0 if all(f.button.rigid_thread for f in live) else 4.0
    garment.attach(name, pairs, rest, compliance=compliance, added_mass=added, kind="button")

    # The rim: the cloth immediately round the hole cannot collapse through
    # the button, so it is held out at the button's radius. Without it the
    # placket puckers into the hole and the button appears to sink into the
    # cloth it is holding.
    #
    # This needs particles INSIDE the button's footprint, and a 15.2 mm button
    # on a 9 mm mesh has almost none - four buttons produced a rim of one
    # constraint. Rather than quietly do nothing, a fastening whose rim cannot
    # be resolved says so on itself, and says what mesh would resolve it.
    rim_pairs: list[tuple[int, int]] = []
    rim_rest: list[float] = []
    for f in live:
        radius = f.button.collision_m() / 2.0
        lo, hi = garment.panel_slices[f.hole.panel]
        flat = garment.rest_points_mm[lo:hi]
        centre = garment.rest_points_mm[f.hole.index]
        d = np.linalg.norm(flat - centre, axis=1) / 1000.0
        ring = np.nonzero((d > radius * 0.5) & (d <= radius))[0] + lo
        f.meta.pop("rim_unresolved", None)
        if ring.size < 3:
            f.meta["rim_unresolved"] = (
                f"{ring.size} cloth point(s) inside a {f.button.diameter_mm:.1f} mm "
                f"button; mesh at {f.button.diameter_mm / 3.0:.0f} mm or finer to "
                "resolve the rim"
            )
        for k in ring:
            rim_pairs.append((f.hole.index, int(k)))
            rim_rest.append(float(d[k - lo]))
    if rim_pairs:
        garment.attach(
            f"{name}:rim",
            np.asarray(rim_pairs, dtype=np.int32),
            np.asarray(rim_rest, dtype=np.float64),
            compliance=1.0,
            kind="button-rim",
        )
    else:
        garment.detach(f"{name}:rim")
    return garment


def check_pops(
    garment: GarmentMesh, points: np.ndarray, fastenings: list[Fastening], *, hold_n: float = 25.0
) -> list[Fastening]:
    """Snaps pop. Everything else holds or tears the cloth first.

    A snap fastener releases at a measured load - the trade calls it "snap
    strength" and quotes it in newtons. Here it is read off the constraint's
    own violation: how far past its rest length the fastening is being pulled,
    times a stiffness. Only snaps can pop; a sewn button that is overloaded
    pulls the cloth, which is the tearing module's problem, not this one.
    """
    for f in fastenings:
        if f.popped or f.button.kind != "snap":
            continue
        span = float(np.linalg.norm(points[f.button_at] - points[f.hole.index]))
        # 2 kN/m is a placket's local stiffness - plausible, not measured, and
        # the reason `hold_n` is an argument rather than a constant.
        load = max(span - f.stand_off_m, 0.0) * 2000.0
        if load > hold_n:
            f.popped = True
            f.meta["popped_at_n"] = round(load, 1)
    return fastenings


def register_obj(path: str | Path, *, material: str = "polyester", **kw: Any) -> ButtonSpec:
    """Register a studio's own button from an OBJ.

    The size, thickness and WEIGHT come off the mesh - measured, not typed.
    That is the whole reason to register geometry rather than a number: a
    button someone modelled has a volume, and a volume times a density is a
    mass that will be right.
    """
    import trimesh

    mesh = trimesh.load(str(path), force="mesh")
    if not isinstance(mesh, trimesh.Trimesh) or mesh.is_empty:
        raise ValueError(f"{path} does not contain a mesh")
    extent = np.asarray(mesh.extents, dtype=np.float64)
    # An OBJ carries no units. A button is a flat disc, so the SHORT axis is
    # its thickness and the other two are its face - and that is a shape fact,
    # not a units guess, so it works whether the file is in mm or metres.
    order = np.argsort(extent)
    thickness, diameter = float(extent[order[0]]), float(extent[order[2]])
    scale = 1.0 if diameter > 1.0 else 1000.0  # metres -> mm, if it looks like metres
    thickness, diameter = thickness * scale, diameter * scale
    volume = float(abs(mesh.volume)) * (scale / 1000.0) ** 3
    density = button_trim(material).density_kg_m3
    return ButtonSpec(
        ligne=diameter / MM_PER_LIGNE,
        material=material,
        thickness_mm=thickness,
        mass_g=volume * density * 1000.0,
        mesh_path=str(path),
        **kw,
    )


def register_mask(path: str | Path, *, pixels_per_mm: float = 4.0) -> dict[str, Any]:
    """Register a custom buttonhole from a black-and-white transparent PNG.

    Black is the hole. Transparent is not - a transparent pixel is nothing,
    and treating it as hole would make every PNG one enormous buttonhole. So
    the mask is (opaque AND dark), and the two are checked separately because
    getting that wrong is silent.
    """
    from PIL import Image

    img = Image.open(str(path)).convert("RGBA")
    a = np.asarray(img, dtype=np.uint8)
    opaque = a[..., 3] > 127
    dark = a[..., :3].mean(axis=2) < 128
    mask = opaque & dark
    if not mask.any():
        raise ValueError(
            f"{path} has no opaque dark pixels, so there is no hole in it. A "
            "buttonhole mask is BLACK where the hole is, on a transparent "
            "background - white-on-transparent gives an empty mask."
        )
    ys, xs = np.nonzero(mask)
    height = (ys.max() - ys.min() + 1) / pixels_per_mm
    width = (xs.max() - xs.min() + 1) / pixels_per_mm
    return {
        "path": str(path),
        "length_mm": round(float(max(width, height)), 2),
        "width_mm": round(float(min(width, height)), 2),
        "angle_deg": 0.0 if width >= height else 90.0,
        "open_area_mm2": round(float(mask.sum()) / pixels_per_mm**2, 2),
        "pixels_per_mm": pixels_per_mm,
    }
