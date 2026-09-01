"""Run the Cusick test end to end: specimen, disc, drape, coefficient."""

from __future__ import annotations

from typing import Any

import numpy as np

from seamkiln.drape.body import cusick_pedestal, sdf_from_mesh
from seamkiln.drape.cusick import (
    DISC_DIAMETER_MM,
    SPECIMEN_DIAMETER_MM,
    drape_coefficient,
    specimen,
)
from seamkiln.drape.environment import Environment
from seamkiln.drape.garment import Placement, build_garment
from seamkiln.drape.solve import DrapeSettings, drape


def run(
    fabric: str = "cotton_poplin",
    *,
    particle_distance: float = 6.0,
    frames: int = 400,
    substeps: int = 20,
    environment: Environment | None = None,
    specimen_diameter_mm: float = SPECIMEN_DIAMETER_MM,
    disc_diameter_mm: float = DISC_DIAMETER_MM,
    stand_height_m: float = 0.30,
    pin_radius_mm: float = 10.0,
) -> dict[str, Any]:
    """One virtual drape test. Returns the coefficient and how it was got."""
    pattern = specimen(specimen_diameter_mm)
    pedestal = cusick_pedestal(disc_diameter_mm / 1000.0, stand_height_m)
    sdf = sdf_from_mesh(pedestal, voxel_mm=3.0, pad_mm=140.0, source="cusick pedestal")

    # laid flat, centred, one millimetre above the disc - the specimen starts
    # where a technician lays it, not somewhere the solver finds convenient
    flat = Placement(
        flat=True,
        centre_angle_deg=0.0,
        origin_m=np.array([0.0, stand_height_m + 0.006, 0.0]),
        rotation=np.array([[1.0, 0.0, 0.0], [0.0, 0.0, 1.0], [0.0, -1.0, 0.0]]),
    )
    garment = build_garment(
        pattern, {"SPECIMEN": flat}, particle_distance=particle_distance, relax_passes=2
    )
    # The instrument has a CENTRING PIN through a hole in the specimen, and
    # so does this: without it a limp specimen slides off the 180 mm disc, the
    # shadow drops below the disc's own area, and the drape coefficient comes
    # back 0.000 - which reads as "infinitely limp" and actually means "the
    # specimen fell on the floor".
    radius = np.linalg.norm(garment.points[:, [0, 2]], axis=1)
    pins = (radius < pin_radius_mm / 1000.0).astype(np.float64)

    result = drape(
        garment,
        sdf,
        pins=pins,
        fabric=fabric,
        settings=DrapeSettings(
            frames=frames,
            substeps=substeps,
            friction=0.30,
            thickness_mm=0.5,
            environment=environment,
        ),
    )
    coefficient = drape_coefficient(
        result.points,
        garment.triangles,
        specimen_diameter_mm=specimen_diameter_mm,
        disc_diameter_mm=disc_diameter_mm,
    )
    return {
        "fabric": fabric,
        **coefficient.as_dict(),
        "particles": garment.n_points,
        "pinned": int(pins.sum()),
        "seconds": round(result.seconds, 2),
        "environment": result.environment["name"],
        "points": result.points,
        "triangles": garment.triangles,
    }
