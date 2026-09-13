"""Author a radial-channel CAD lesson; analytic stock/void oracles use stdlib.

This is an original geometry study, not reverse-engineered Brembo CAD.
Run from any directory to regenerate the packaged JSON deterministically.
"""

from __future__ import annotations

import json
import math
from pathlib import Path

OUT = (
    Path(__file__).resolve().parents[2]
    / "server/src/tee/adapters/fusion/recipes/cadagent_f1_brake.json"
)
RO, RI, THICKNESS, COUNT = 140.0, 90.0, 28.0, 30


def channel_volume(radius: float, panels: int = 8192) -> float:
    """Integrate the exact annulus/cylinder intersection, not pi*r*r*50."""
    step = math.pi / (2 * panels)

    def at(t: float) -> float:
        tangent = radius * math.sin(t)
        length = math.sqrt(RO * RO - tangent * tangent) - math.sqrt(RI * RI - tangent * tangent)
        return 4 * radius * radius * math.cos(t) ** 2 * length

    terms = [at(0), at(math.pi / 2)]
    terms.extend((4 if i % 2 else 2) * at(i * step) for i in range(1, panels))
    return step / 3 * math.fsum(terms)


def expected(diameter_a: float, diameter_b: float) -> dict:
    stock = math.pi * (RO * RO - RI * RI) * THICKNESS
    rows = []
    for label, diameter, z, seed_angle in (
        ("A", diameter_a, 7.0, 0.0),
        ("B", diameter_b, 21.0, 90.0),
    ):
        radius = diameter / 2
        volume = channel_volume(radius)
        assert abs(volume - channel_volume(radius, 4096)) < 1e-8
        rows.append(
            {
                "row": label,
                "count": COUNT,
                "diameter_mm": diameter,
                "radius_mm": radius,
                "centre_height_mm": z,
                "seed_angle_deg": seed_angle,
                "angles_deg": sorted((seed_angle + i * 12) % 360 for i in range(COUNT)),
                "undirected_axis_angles_deg": sorted(
                    {(seed_angle + i * 12) % 180 for i in range(COUNT)}
                ),
                "faces_per_undirected_axis": 2,
                "centreline_radial_interval_mm": [RI, RO],
                "centreline_length_mm": RO - RI,
                "wall_generator_length_range_mm": [
                    RO - RI,
                    math.sqrt(RO * RO - radius * radius) - math.sqrt(RI * RI - radius * radius),
                ],
                "removed_volume_per_channel_mm3": volume,
            }
        )
    removed = COUNT * math.fsum(row["removed_volume_per_channel_mm3"] for row in rows)
    volume = stock - removed
    moment = stock * THICKNESS / 2 - COUNT * math.fsum(
        row["removed_volume_per_channel_mm3"] * row["centre_height_mm"] for row in rows
    )
    return {
        "bodies": 1,
        "components": 0,
        "features": 6,
        "bbox_mm": [2 * RO, 2 * RO, THICKNESS],
        "min_mm": [-RO, -RO, 0],
        "max_mm": [RO, RO, THICKNESS],
        "volume_mm3": volume,
        "centre_of_mass_mm": [0, 0, moment / volume],
        "stock_volume_mm3": stock,
        "removed_volume_mm3": removed,
        "inner_void_cylinder_count": 2 * COUNT,
        "rows": rows,
        "row_stagger_deg": 6,
        "rim_cylinders": [{"radius_mm": RI, "inner": True}, {"radius_mm": RO, "inner": False}],
        "volume_formula": "pi*(140^2-90^2)*28 - 30*(V(dA/2)+V(dB/2))",
        "channel_volume_formula": (
            "V(r)=4*r^2*integral(t=0..pi/2, "
            "cos(t)^2*(sqrt(140^2-r^2*sin(t)^2)-sqrt(90^2-r^2*sin(t)^2)))"
        ),
        "oracle_evaluation": (
            "Composite Simpson integration after s=r*sin(t), 8192 panels; 4096-panel "
            "agreement better than 1e-8 mm3 per channel. The integral is the exact "
            "curved-rim intersection, its numeric evaluation is approximate."
        ),
        "volume_tolerance_mm3": 0.1,
        "measurement_accuracy": {
            "fusion": "getPhysicalProperties(CalculationAccuracy.VeryHighCalculationAccuracy)",
            "step": "BRepGProp.VolumeProperties_s(shape, props, Eps=1e-10)",
            "reason": (
                "The default non-adaptive OCCT integral missed this exact curved-rim volume "
                "by 11.51 mm3 initially and 47.84 mm3 after revision in the independent "
                "constructed-solid probe. Adaptive integration agreed with the analytic "
                "oracle within 0.000061 mm3. A tighter check needs a tighter measurement."
            ),
        },
    }


def create(kind: str, name: str, alias: str | None, **props: object) -> dict:
    op = {"op": "create", "kind": kind, "name": name, "props": props}
    if alias:
        op["as"] = alias
    return op


def recipe() -> dict:
    ops = [
        create("param", "A79B_channel_A", None, value="6 mm", units="mm"),
        create("param", "A79B_channel_B", None, value="6 mm", units="mm"),
        create("sketch", "Brake disc outer stock", "stock", plane="XY", circles=[[0, 0, RO]]),
        create(
            "extrude", "Authored ventilated annulus", "disc", sketch="@stock", distance=THICKNESS
        ),
        create(
            "hole",
            "Disc inner clearance",
            "clearance",
            body="@disc",
            face="+z",
            at=[0, 0],
            diameter=2 * RI,
            through=True,
        ),
    ]
    for label, plane, centre in (("A", "YZ", [-7, 0]), ("B", "XZ", [0, -21])):
        alias = label.lower()
        ops.extend(
            [
                create(
                    "sketch",
                    f"Row {label} radial-channel seed",
                    f"row_{alias}",
                    plane=plane,
                    circles=[[*centre, 3]],
                    dims=[
                        {"type": "diameter", "of": ["c0"], "expression": f"A79B_channel_{label}"}
                    ],
                ),
                create(
                    "extrude",
                    f"Row {label} radial passage",
                    f"cut_{alias}",
                    sketch=f"@row_{alias}",
                    distance=150,
                    operation="cut",
                ),
                create(
                    "circular_pattern",
                    f"Thirty row {label} radial passages",
                    f"channels_{alias}",
                    features=[f"@cut_{alias}.feature"],
                    axis="z",
                    count=COUNT,
                    angle=360,
                ),
            ]
        )
    ops.extend(
        {"op": "set", "id": f"@{alias}", "props": {"visible": False}}
        for alias in ("stock", "row_a", "row_b")
    )
    return {
        "topic": "cadagent_f1_brake",
        "title": "F1-inspired disc with sixty radial cooling channels in staggered rows",
        "intent": (
            "Cut two independently driven radial channel seeds through an annulus, "
            "pattern their feature history into staggered rows, then change both "
            "diameters and verify the void geometry and the shifted centre of mass."
        ),
        "provenance": {
            "kind": "original instructional geometry",
            "source": "https://www.brembo.com/en/motorsport/formula1/ventilation-holes",
            "accessed": "2026-09-10",
            "source_supports": (
                "Brembo describes radial internal ventilation channels, their progression "
                "from a single row to multiple rows, and the thermal/structural trade-off. "
                "Real discs have used hundreds and then over a thousand channels."
            ),
            "authored": (
                "All dimensions, sixty-channel count, two-row layout, circular "
                "cross-sections, stagger and revision values here are authored for this "
                "lesson. They are not Brembo or team CAD and establish no current regulation "
                "compliance."
            ),
        },
        "ops": ops,
        "expected": expected(6, 6),
        "check": (
            "Preflight, then run creation once in a separate empty parametric document. "
            "Measure one solid, six healthy features, the stock bounds and analytic "
            "volume. Identify exactly sixty reversed cylindrical faces of radius 3 mm at "
            "z=7/z21 with thirty directions per row and 6-degree stagger. Read the "
            "actual sketch circle world centres and cylinder axes: API-created YZ sketch "
            "local(-7,0) must be world(0,0,7); XZ local(0,-21) must be world(0,0,21). "
            "The two seeds cut along +x and +y. Opposite radial passages share the same "
            "infinite cylinder axis, so expect two faces per undirected axis; the "
            "channel mouths must open at both the 90 mm and 140 mm rims. Export STEP, "
            "independently measure it, reopen F3D and repeat the checks."
        ),
        "revision": {
            "ops": [
                {"op": "param_set", "name": "A79B_channel_A", "expression": "7 mm"},
                {"op": "param_set", "name": "A79B_channel_B", "expression": "8 mm"},
            ],
            "expected": expected(7, 8),
            "check": (
                "In the same design, revise the two named parameters. Row A becomes thirty "
                "radius 3.5 mm void cylinders at z=7; row B becomes thirty radius 4 mm void "
                "cylinders at z=21. The diameter dimensions retain their parameter "
                "expressions. All six features stay healthy, bounds and channel directions "
                "stay fixed, removed volume rises, and centre of mass shifts below z14 "
                "because the upper row loses more stock. Verify the analytic volume and "
                "centre of mass, then repeat both export round trips."
            ),
        },
        "exports": [
            {
                "name": "fu_export",
                "args": {"format": fmt, "out": f"/absolute/output/cadagent_f1_brake.{fmt}"},
            }
            for fmt in ("step", "f3d")
        ],
        "export_evidence": {
            "fusion_version": "2705.1.15",
            "native_f3d_reopen": "passed; editable features and drivers retained",
            "revised_fusion_step_volume_error_mm3": 12.8021874967,
            "revised_fusion_step_exact_volume_match": False,
            "exact_volume_tolerance_mm3": 0.1,
            "finding": (
                "Fusion STEP approximates the curved channel mouths. All sixty passages "
                "remain, but the revised export fails the unchanged analytic volume gate. "
                "Keep its approximate verdict separate from the passing native model."
            ),
            "independent_reference": (
                "benchmarks/fixtures/build_f1_brake_reference.py rebuilds the authored "
                "dimensions using OCCT and checks every channel's shared-edge adjacency "
                "to both rims, volume and centre of mass after STEP readback. Run with "
                "the partkiln sidecar Python and --recipe PATH --out NEW_DIRECTORY. "
                "This is a separate ideal reference, never a repaired Fusion export."
            ),
        },
        "lessons": [
            (
                "A ventilation passage is radial and inside the disc. Axial perforations "
                "through the friction faces would be a different geometry and do not "
                "demonstrate this source's mechanism."
            ),
            (
                "The circle is drawn in a root plane through the empty central opening; a "
                "150 mm one-sided cut reaches beyond the 140 mm outer rim. No hole is "
                "started on a curved face, which the typed hole tool does not support."
            ),
            (
                "A 30-instance full circle has 12-degree pitch. Seeds on orthogonal axes "
                "differ by 90 degrees, or seven and a half pitches, creating a 6-degree row "
                "stagger with existing root-plane operations."
            ),
            (
                "Parameterise the sketch diameter before cutting and pattern the cut "
                "feature. Each revision propagates through its own sketch, cut and 29 "
                "dependent copies."
            ),
            (
                "The annular rims trim a channel obliquely. "
                "pi*r^2*(outer_radius-inner_radius) is only an approximation; use the stated "
                "intersection integral to check volume independently."
            ),
            (
                "Count inner cylindrical faces and verify their axes, row heights and radial "
                "mouths. Overall volume alone cannot tell a radial channel from another void "
                "with the same volume."
            ),
            (
                "Request high-accuracy Fusion physical properties and adaptive STEP mass "
                "integration. The default OCCT volume overload uses exact surfaces but "
                "still approximates their integral; it measurably misses this check."
            ),
            (
                "A precise integral of an approximate export is still the wrong geometry. "
                "Report the measured STEP volume error separately; retain the native F3D "
                "and original STEP, and label the independently rebuilt ideal reference."
            ),
        ],
        "limits": [
            (
                "This is a geometry lesson, not a brake design for manufacture, a "
                "thermal/structural simulation, or a validated carbon-carbon material model. "
                "No braking-performance or regulation-compliance claim follows from these "
                "solids."
            ),
            (
                "The bell, floating attachment hardware, splines, caliper, pads, ducts and "
                "material assignment are omitted. Its central opening is a clearance "
                "boundary, not a completed mounting interface."
            ),
            (
                "The count is deliberately reduced to sixty for a replayable lesson. "
                "Contemporary carbon-disc microchannel density and non-circular or curved "
                "passages are not reproduced."
            ),
            (
                "The three sketch locations are authored numeric geometry; only the two "
                "channel diameters are driven. This lesson does not claim fully constrained "
                "sketches or a driven outside diameter/thickness."
            ),
            (
                "Use an empty parametric root design with unused A79B_ parameter names. Cut "
                "operations intersect any body in their path; root-native pattern scope and "
                "no extra bodies are part of the setup."
            ),
            (
                "Verify API sketch axes on the installed build before trusting the first "
                "seed. Sketch coordinates are local, and YZ/XZ labels do not mean local "
                "x/local y directly match the displayed world axes."
            ),
            (
                "Aliases belong to the creation batch only; the revision uses stable "
                "parameter names. Replace /absolute/output with an existing absolute "
                "directory and export the whole design with no body-id of argument."
            ),
        ],
    }


if __name__ == "__main__":
    OUT.write_text(json.dumps(recipe(), indent=2) + "\n")
    print(OUT)
