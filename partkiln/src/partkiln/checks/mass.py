"""Exact mass properties from `BRepGProp`, in the units the wire promises.

Volume mm3, area mm2, lengths mm, mass grams - every number rounded to 3 dp
BEFORE it leaves (determinism is a feature: two kernels print the same
digit). Measured (A66 P0a, this Mac): F1 = 59 214.602 mm3 / 15 357.080 mm2 /
COM (50, 30, 5) / bbox [100, 60, 10]; F6 in steel_s275 (7850 kg/m3, EN
1993-1-1 3.2.6) = block 238.869 g, pin 24.662 g.

Inertia: `BRepGProp` returns second moments of VOLUME in mm5. Multiplied by
a density in kg/m3 they become kg mm2 after the 1e-9 m3/mm3 factor - so
`inertia_kg_mm2` exists only when a density is known and `inertia_mm5`
always does. Both are about the centre of mass (the number a designer
wants; the origin form is one parallel-axis step away and stated as such).
"""

from __future__ import annotations

from typing import Any

from partkiln.document import CommandError

# kg/m3 x mm5 -> kg mm2: one mm3 is 1e-9 m3.
_MM3_PER_M3 = 1e-9


def _r3(x: float) -> float:
    return round(float(x), 3) + 0.0


def _round_matrix(m: tuple[tuple[float, ...], ...], scale: float = 1.0) -> list[list[float]]:
    return [[_r3(v * scale) for v in row] for row in m]


def resolve_density(
    material: str | None, density_kg_m3: float | None
) -> tuple[float | None, str | None, str]:
    """(density, material key, honesty).

    An explicit density wins over the card (honesty `override`) so a
    designer can price an unlisted alloy; a material alone reads the card
    (`partkiln.materials`, refusing an unknown name with the list); neither
    -> (None, None, "none") and `mass_g` is absent rather than invented.
    """
    if density_kg_m3 is not None:
        if density_kg_m3 <= 0:
            raise CommandError(
                f"density_kg_m3 must be > 0, got {density_kg_m3}. "
                "Fix: pass the material density in kg/m3 (steel is 7850).",
                code="pk_needs",
            )
        key = None
        if material:
            from partkiln import materials

            key = materials.resolve(material)
        return float(density_kg_m3), key, "override"
    if material:
        from partkiln import materials

        key = materials.resolve(material)
        leaf = materials.card(key)["properties"]["density"]
        return float(leaf["value"]), key, str(leaf["honesty"])
    return None, None, "none"


def mass_properties(
    shape: Any,
    material: str | None = None,
    density_kg_m3: float | None = None,
) -> dict[str, Any]:
    """{volume_mm3, area_mm2, com_mm, bbox_mm, bbox_min, bbox_max, inertia_mm5,
    principal_mm5, inertia_kg_mm2?, mass_g?, density_kg_m3?, material, honesty}.

    `mass_g` and `inertia_kg_mm2` appear only when a density is known; the
    caller sees `honesty` (`standard_value`, `datasheet`, `typical_range`,
    `derived` from the card, `override` for an explicit density, `none`).
    """
    from OCP.BRepGProp import BRepGProp
    from OCP.gp import gp_Pnt
    from OCP.GProp import GProp_GProps

    from partkiln.brep import shapes

    # `VolumeProperties_s` integrates the divergence theorem over whatever
    # faces it is given, so an OPEN shell returns a plausible non-zero
    # "volume" (measured: five faces of a 30x30x10 box -> 7 200). The solid
    # count is the honest gate, not the number.
    if shapes.counts(shape)["solids"] < 1:
        raise CommandError(
            "the shape has no solid (an open shell or a face set): it is not a solid, so its "
            "volume would be a fiction. Fix: measure a solid (validate() names the free edges).",
            code="pk_needs",
        )
    props = GProp_GProps()
    BRepGProp.VolumeProperties_s(shape, props)
    volume = props.Mass()
    c = props.CentreOfMass()
    com = (c.X(), c.Y(), c.Z())
    about_com = GProp_GProps(gp_Pnt(*com))
    BRepGProp.VolumeProperties_s(shape, about_com)
    m = about_com.MatrixOfInertia()
    inertia = tuple(tuple(m.Value(i, j) for j in (1, 2, 3)) for i in (1, 2, 3))
    principal = about_com.PrincipalProperties().Moments()
    x0, y0, z0, x1, y1, z1 = shapes.bbox(shape)
    density, key, honesty = resolve_density(material, density_kg_m3)
    out: dict[str, Any] = {
        "volume_mm3": _r3(volume),
        "area_mm2": _r3(shapes.area(shape)),
        "com_mm": [_r3(v) for v in com],
        "bbox_mm": [_r3(x1 - x0), _r3(y1 - y0), _r3(z1 - z0)],
        "bbox_min": [_r3(x0), _r3(y0), _r3(z0)],
        "bbox_max": [_r3(x1), _r3(y1), _r3(z1)],
        "inertia_mm5": _round_matrix(inertia),
        "principal_mm5": [_r3(v) for v in principal],
        "material": key,
        "honesty": honesty,
    }
    if density is not None:
        out["density_kg_m3"] = _r3(density)
        out["mass_g"] = _r3(volume * density * 1e-6)
        out["inertia_kg_mm2"] = _round_matrix(inertia, density * _MM3_PER_M3)
    return out


__all__ = ["mass_properties", "resolve_density"]
