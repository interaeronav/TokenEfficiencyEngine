"""Owned headless building/scan/shop workflow; no DCC, model or paid calls."""

from __future__ import annotations

import hashlib
import json
import math
import time
from datetime import UTC, datetime
from pathlib import Path

from tee.architecture.service import ArchitectureService


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    project = root / "output/architecture/house-example" / stamp
    project.mkdir(parents=True, exist_ok=False)
    service = ArchitectureService(project)
    started = time.monotonic()
    house = service.create("Compact modern house — review example", "compact-house")
    mid = house["model_id"]
    initial = service.state(mid)
    service.edit(
        mid, [{"op": "update", "id": "cabinet", "changes": {"width": 1200}}], 1
    )
    service.undo(mid, 2)
    reopened = ArchitectureService(project).state(mid)
    assert reopened["document_id"] == initial["document_id"]
    assert reopened["entities"] == initial["entities"] and reopened["revision"] == 3
    shop = service.query(
        mid,
        "cabinet",
        "cabinet",
        {
            "sheet_width": 1220,
            "sheet_height": 2440,
            "kerf": 3.2,
        },
    )
    result = service.export(mid)
    preview = service.preview(mid)
    check = service.check(mid)
    assert check["regulatory"]["status"] == "not_verified"

    # Real independent IFC and GLB readers inspect the generated artifacts.
    import ifcopenshell
    import ifcopenshell.geom
    import ifcopenshell.util.shape
    import trimesh

    output = Path(result["directory"])
    model = ifcopenshell.open(output / "building.ifc")
    assert len(model.by_type("IfcSpace")) == 2
    assert len(model.by_type("IfcRelVoidsElement")) == 4
    wall_volume = 0.0
    for wall in model.by_type("IfcWall"):
        # Keep the SWIG owner alive while reading its geometry buffer.
        shape = ifcopenshell.geom.create_shape(ifcopenshell.geom.settings(), wall)
        wall_volume += ifcopenshell.util.shape.get_volume(shape.geometry)
    assert math.isfinite(wall_volume) and wall_volume > 0
    glb = trimesh.load(output / "building.glb", force="scene")
    assert glb.bounds.shape == (2, 3) and glb.bounds[1][0] < 11

    # Promote a measured reference face in a separate owned survey model.
    scan = project / "wall.xyz"
    scan.write_text(
        "\n".join(f"{x * 200} 50 {z * 200}" for x in range(21) for z in range(15))
        + "\n"
    )
    survey = service.create("Owned scan conversion example")["model_id"]
    service.edit(
        survey,
        [
            {
                "op": "create",
                "entity": {
                    "id": "ground",
                    "kind": "storey",
                    "name": "Ground",
                    "elevation": 0,
                    "height": 2800,
                },
            }
        ],
        0,
    )
    imported = service.import_source(survey, "wall.xyz", "mm", 1)
    candidates = service.candidates(survey, imported["import_id"])
    selected = next(
        c for c in candidates["proposal"]["candidates"] if c["kind"] == "wall"
    )
    promoted = service.promote(
        survey,
        imported["import_id"],
        selected["id"],
        "ground",
        {
            "height": 2800,
            "thickness": 200,
            "centreline_offset_mm": -100,
            "id": "measured_wall",
        },
        1,
    )
    assert promoted["revision"] == 2
    assert (
        service.query(survey, "measured_wall")["entity"]["provenance"]["status"]
        == "explicitly_promoted"
    )
    report = {
        "scope": "owned headless workflow and real independent export readers",
        "passed": True,
        "seconds": round(time.monotonic() - started, 3),
        "project": str(project),
        "house": house,
        "current_revision": 3,
        "wall_volume_m3": wall_volume,
        "wall_junctions": preview["wall_junctions"],
        "shop": shop,
        "export": result,
        "check": check,
        "scan": {
            "source_sha256": hashlib.sha256(scan.read_bytes()).hexdigest(),
            "candidate": selected,
            "promotion": promoted,
        },
        "models_invoked": False,
        "paid_inference": False,
        "dcc_contact": False,
    }
    (project / "evidence.json").write_text(json.dumps(report, indent=2) + "\n")
    (root / "output/architecture/headless-smoke.json").write_text(
        json.dumps(
            {
                "passed": True,
                "latest_evidence": str(project / "evidence.json"),
                "seconds": report["seconds"],
                "export_directory": str(output),
            },
            indent=2,
        )
        + "\n"
    )
    print(
        json.dumps(
            {
                "passed": True,
                "seconds": report["seconds"],
                "evidence": str(project / "evidence.json"),
            }
        )
    )


if __name__ == "__main__":
    main()
