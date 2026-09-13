"""Opt-in CADAgent lessons for a faulty then repaired native duct interface."""

from __future__ import annotations


def build_operations() -> list[dict]:
    entities = [
        {"id": "ground", "kind": "storey", "name": "Ground", "elevation": 1200, "height": 3000}
    ]
    for identifier, origin in [("a", [10000, 20000, 100]), ("b", [10615, 20820, 100])]:
        entities.append(
            {
                "id": identifier,
                "name": "Duct " + identifier,
                "kind": "member",
                "storey": "ground",
                "role": "duct",
                "origin": origin,
                "profile": [[-100, -50], [100, -50], [100, 50], [-100, 50]],
                "holes": [[[-98, -48], [-98, 48], [98, 48], [98, -48]]],
                "length": 1000,
                "axis": [0.6, 0.8, 0],
                "x_direction": [-0.8, 0.6, 0],
            }
        )
    distribution = {
        "systems": [
            {
                "id": "vent",
                "name": "Isolated ventilation geometry study",
                "system_type": "VENTILATION",
                "entity_ids": ["a", "b"],
                "source": "TEE synthetic lesson; section and thickness are authored examples",
            }
        ],
        "ports": [
            {
                "id": identifier + "_" + end,
                "entity_id": identifier,
                "end": end,
                "profile_point": [0, 0],
                "flow_direction": "SINK" if end == "start" else "SOURCE",
            }
            for identifier in ("a", "b")
            for end in ("start", "end")
        ],
        "connections": [
            {
                "id": "join",
                "ports": ["a_end", "b_start"],
                "tolerance_mm": 0.1,
                "source": "Explicit study interface tolerance; no manufacturer acceptance",
            }
        ],
    }
    return [{"op": "create", "entity": entity} for entity in entities] + [
        {"op": "project", "changes": {"facts": {"distribution": distribution}}}
    ]
