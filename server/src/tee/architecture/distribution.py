"""Explicit pipe/duct topology with measured mating geometry, in millimetres.

IFC4 fixed ports nest under their element. Their Axis follows FLOW: a SINK
points into its product, whereas a SOURCE points away. Outward physical normals
are checked separately. No hydraulic, thermal, electrical or capacity solver.
"""

from __future__ import annotations

import math
from collections import defaultdict
from typing import Any

from .members import frame
from .model import ArchitectureError, _point, number

SYSTEM_TYPES = {
    "AIRCONDITIONING",
    "CHILLEDWATER",
    "COMPRESSEDAIR",
    "CONDENSERWATER",
    "DOMESTICCOLDWATER",
    "DOMESTICHOTWATER",
    "DRAINAGE",
    "EXHAUST",
    "FIREPROTECTION",
    "GAS",
    "HEATING",
    "RAINWATER",
    "REFRIGERATION",
    "SEWAGE",
    "STORMWATER",
    "VENT",
    "VENTILATION",
    "WASTEWATER",
    "WATERSUPPLY",
}
FLOW = {"SOURCE", "SINK", "SOURCEANDSINK", "NOTDEFINED"}


def _fail(message: str) -> None:
    raise ArchitectureError("ak_distribution", message, "Correct the named service definition.")


def _text(value: Any, field: str, limit: int = 160) -> None:
    if not isinstance(value, str) or not value.strip() or len(value) > limit:
        _fail(f"{field} needs nonempty text up to {limit} characters.")


def _rows(spec: dict, key: str, limit: int, fields: set[str]) -> list[dict]:
    rows = spec.get(key, [])
    if not isinstance(rows, list) or len(rows) > limit:
        _fail(f"distribution.{key} needs a list of at most {limit} rows.")
    seen = set()
    for row in rows:
        if not isinstance(row, dict) or set(row) != fields:
            _fail(f"distribution.{key} row needs exactly: {', '.join(sorted(fields))}.")
        _text(row["id"], key + ".id", 80)
        if row["id"] in seen:
            _fail(f"Duplicate {key} id {row['id']}.")
        seen.add(row["id"])
    return rows


def definitions(state: dict) -> tuple[list[dict], list[dict], list[dict], dict[str, str]]:
    if "distribution" not in state["project"]["facts"]:
        return [], [], [], {}
    from shapely.geometry import Point, Polygon

    spec = state["project"]["facts"].get("distribution", {})
    if not isinstance(spec, dict) or set(spec) - {"systems", "ports", "connections"}:
        _fail("distribution accepts systems, ports and connections only.")
    systems = _rows(spec, "systems", 32, {"id", "name", "system_type", "entity_ids", "source"})
    ports = _rows(spec, "ports", 128, {"id", "entity_id", "end", "profile_point", "flow_direction"})
    links = _rows(spec, "connections", 64, {"id", "ports", "tolerance_mm", "source"})
    entities = state["entities"]
    assignments: dict[str, str] = {}
    for system in systems:
        _text(system["name"], "system.name")
        _text(system["source"], "system.source", 1000)
        if not isinstance(system["system_type"], str) or system["system_type"] not in SYSTEM_TYPES:
            _fail("system_type must name a supported IFC4 pipe/duct service type.")
        ids = system["entity_ids"]
        if not isinstance(ids, list) or not ids or len(ids) > 128:
            _fail("System entity_ids needs 1-128 distinct native pipe/duct members.")
        for identifier in ids:
            if not isinstance(identifier, str) or identifier not in entities:
                _fail("System entity_ids references an unknown member.")
            entity = entities[identifier]
            if entity["kind"] != "member" or entity["role"] not in {"pipe", "duct"}:
                _fail("Distribution systems currently accept pipe/duct members only.")
            if identifier in assignments:
                _fail(f"Member {identifier} is repeated or assigned to more than one system.")
            assignments[identifier] = system["id"]
    ends = set()
    for port in ports:
        identifier = port["entity_id"]
        if not isinstance(identifier, str) or identifier not in assignments:
            _fail("Port entity_id must belong to a declared distribution system.")
        if not isinstance(port["end"], str) or port["end"] not in {"start", "end"}:
            _fail("Port end must be start or end of its member.")
        end = (identifier, port["end"])
        if end in ends:
            _fail(
                "Each member end may carry only one port; model branching with explicit fittings."
            )
        ends.add(end)
        _point(port["profile_point"], "port.profile_point")
        outer = Polygon(entities[identifier]["profile"])
        if outer.centroid.distance(Point(port["profile_point"])) > 1e-7:
            _fail(
                "Fixed endpoint profile_point must equal the outer-profile centroid "
                "in this version."
            )
        if not isinstance(port["flow_direction"], str) or port["flow_direction"] not in FLOW:
            _fail("Port flow_direction must be SOURCE, SINK, SOURCEANDSINK or NOTDEFINED.")
    indexed = {p["id"]: p for p in ports}
    connected = set()
    for link in links:
        pair = link["ports"]
        if (
            not isinstance(pair, list)
            or len(pair) != 2
            or any(not isinstance(p, str) or p not in indexed for p in pair)
        ):
            _fail("Connection ports must name two known distinct ports.")
        if pair[0] == pair[1] or indexed[pair[0]]["entity_id"] == indexed[pair[1]]["entity_id"]:
            _fail("Connection ports must belong to different members.")
        if any(p in connected for p in pair):
            _fail("A port cannot connect to multiple other ports.")
        connected.update(pair)
        if number(link["tolerance_mm"], "connection.tolerance_mm") < 0:
            _fail("Connection tolerance_mm must be nonnegative and explicitly supplied.")
        _text(link["source"], "connection.source", 1000)
    return systems, ports, links, assignments


def validate_distribution(state: dict) -> None:
    definitions(state)


def _port_geometry(port: dict, entities: dict) -> dict:
    member = entities[port["entity_id"]]
    x, y, z = frame(member)
    base = [*member["origin"]]
    base[2] += entities[member["storey"]]["elevation"]
    u, v = port["profile_point"]
    along = member["length"] if port["end"] == "end" else 0
    normal_sign = 1 if port["end"] == "end" else -1
    outward = [normal_sign * n for n in z]
    return {
        "world_mm": [base[i] + x[i] * u + y[i] * v + z[i] * along for i in range(3)],
        "outward": outward,
        "profile_x": x,
        "profile_y": y,
        "flow_axis": [n * (-1 if port["flow_direction"] == "SINK" else 1) for n in outward],
        "base_world_mm": base,
        "axis": z,
        "along_mm": along,
    }


def _section(port: dict, entities: dict, datum: dict) -> Any:
    from shapely.geometry import Polygon

    member = entities[port["entity_id"]]
    geometry = _port_geometry(port, entities)

    def project(ring: list) -> list[list[float]]:
        points = []
        for u, v in ring:
            world = [
                geometry["base_world_mm"][i]
                + geometry["profile_x"][i] * u
                + geometry["profile_y"][i] * v
                + geometry["axis"][i] * geometry["along_mm"]
                - datum["world_mm"][i]
                for i in range(3)
            ]
            points.append(
                [sum(world[i] * datum[k][i] for i in range(3)) for k in ("profile_x", "profile_y")]
            )
        return points

    return Polygon(project(member["profile"]), [project(r) for r in member.get("holes", [])])


def report(state: dict) -> dict:
    systems, ports, links, assignments = definitions(state)
    entities = state["entities"]
    indexed = {p["id"]: p for p in ports}
    geometry = {p["id"]: _port_geometry(p, entities) for p in ports}
    linked = {p for link in links for p in link["ports"]}
    connections = []
    measured_connected = set()
    graph: dict[str, set[str]] = defaultdict(set)
    for link in links:
        a, b = [indexed[p] for p in link["ports"]]
        ga, gb = [geometry[p] for p in link["ports"]]
        gap = math.dist(ga["world_mm"], gb["world_mm"])
        same_system = assignments[a["entity_id"]] == assignments[b["entity_id"]]
        same_role = entities[a["entity_id"]]["role"] == entities[b["entity_id"]]["role"]
        opposed = (
            abs(sum(x * y for x, y in zip(ga["outward"], gb["outward"], strict=True)) + 1) <= 1e-8
        )
        x_aligned = (
            abs(sum(x * y for x, y in zip(ga["profile_x"], gb["profile_x"], strict=True)) - 1)
            <= 1e-8
        )
        section_error, section_ok = None, False
        if opposed and x_aligned:
            sa, sb = _section(a, entities, ga), _section(b, entities, ga)
            section_error = sa.boundary.hausdorff_distance(sb.boundary)
            section_ok = (
                len(sa.interiors) == len(sb.interiors)
                and section_error <= link["tolerance_mm"] + 1e-7
            )
        flow_ok = {a["flow_direction"], b["flow_direction"]} == {"SOURCE", "SINK"}
        checks = {
            "same_system": same_system,
            "same_service_role": same_role,
            "endpoint_distance": gap <= link["tolerance_mm"] + 1e-7,
            "opposed_physical_normals": opposed,
            "profile_axes_aligned": x_aligned,
            "mating_section": section_ok,
            "explicit_opposite_flow": flow_ok,
        }
        passed = all(checks.values())
        if passed:
            measured_connected.update(link["ports"])
            graph[a["entity_id"]].add(b["entity_id"])
            graph[b["entity_id"]].add(a["entity_id"])
        connections.append(
            {
                **link,
                "status": "geometrically_connected" if passed else "not_connected",
                "gap_mm": gap,
                "section_boundary_error_mm": section_error,
                "checks": checks,
            }
        )
    system_rows = []
    for system in systems:
        remaining = set(system["entity_ids"])
        components = []
        while remaining:
            todo = [min(remaining)]
            component = set()
            while todo:
                node = todo.pop()
                if node in component:
                    continue
                component.add(node)
                todo.extend(graph[node] - component)
            remaining -= component
            components.append(sorted(component))
        system_rows.append(
            {
                **system,
                "connected_components": components,
                "unconnected_ports": [
                    p["id"]
                    for p in ports
                    if assignments[p["entity_id"]] == system["id"]
                    and p["id"] not in measured_connected
                ],
                "ends_without_ports": [
                    {"entity_id": eid, "end": end}
                    for eid in system["entity_ids"]
                    for end in ["start", "end"]
                    if not any(p["entity_id"] == eid and p["end"] == end for p in ports)
                ],
                "engineering_status": "not_verified",
            }
        )
    return {
        "document_id": state["document_id"],
        "revision": state["revision"],
        "systems": system_rows,
        "ports": [
            {
                **p,
                "system_id": assignments[p["entity_id"]],
                "world_mm": geometry[p["id"]]["world_mm"],
                "outward": geometry[p["id"]]["outward"],
                "flow_axis": geometry[p["id"]]["flow_axis"],
                "connection_declared": p["id"] in linked,
                "connection_measured": p["id"] in measured_connected,
            }
            for p in ports
        ],
        "connections": connections,
        "configured": bool(systems),
        "scope": (
            "Endpoint/profile/topology checks only; fittings, seals, supports, "
            "flow/pressure sizing and compliance not verified."
        ),
    }


def _local_vector(matrix: Any, vector: list[float]) -> list[float]:
    return [float(sum(vector[i] * matrix[i, j] for i in range(3))) for j in range(3)]


def export_ifc(file: Any, state: dict, products: dict) -> dict:
    from .exchange import _guid

    result = report(state)
    failed = [r["id"] for r in result["connections"] if r["status"] != "geometrically_connected"]
    if failed:
        _fail(
            "IFC cannot assert unverified connections: "
            + ", ".join(failed[:5])
            + ". Read distribution connections."
        )
    systems, ports, links, assignments = definitions(state)
    created_systems, created_ports = {}, {}
    nested: dict[str, list] = defaultdict(list)

    def guid(identifier: str) -> str:
        return _guid("distribution:" + identifier, state["document_id"])

    for system in systems:
        created_systems[system["id"]] = file.create_entity(
            "IfcDistributionSystem",
            GlobalId=guid("system:" + system["id"]),
            Name=system["name"],
            Description=system["source"],
            PredefinedType=system["system_type"],
        )
    for port in ports:
        element = products[port["entity_id"]]
        member = state["entities"][port["entity_id"]]
        from ifcopenshell.util.placement import get_local_placement

        geometry = _port_geometry(port, state["entities"])
        matrix = get_local_placement(element.ObjectPlacement)

        point = _local_vector(matrix, [geometry["world_mm"][i] - matrix[i, 3] for i in range(3)])
        local = file.create_entity(
            "IfcAxis2Placement3D",
            Location=file.create_entity("IfcCartesianPoint", Coordinates=point),
            Axis=file.create_entity(
                "IfcDirection", DirectionRatios=_local_vector(matrix, geometry["flow_axis"])
            ),
            RefDirection=file.create_entity(
                "IfcDirection", DirectionRatios=_local_vector(matrix, geometry["profile_x"])
            ),
        )
        placement = file.create_entity(
            "IfcLocalPlacement", PlacementRelTo=element.ObjectPlacement, RelativePlacement=local
        )
        system = created_systems[assignments[port["entity_id"]]]
        product = file.create_entity(
            "IfcDistributionPort",
            GlobalId=guid("port:" + port["id"]),
            Name=port["id"],
            ObjectPlacement=placement,
            FlowDirection=port["flow_direction"],
            PredefinedType=member["role"].upper(),
            SystemType=system.PredefinedType,
        )
        created_ports[port["id"]] = product
        nested[port["entity_id"]].append(product)
    for identifier, children in nested.items():
        file.create_entity(
            "IfcRelNests",
            GlobalId=guid("nests:" + identifier),
            RelatingObject=products[identifier],
            RelatedObjects=children,
        )
    for system in systems:
        members = [products[i] for i in system["entity_ids"]]
        members += [
            created_ports[p["id"]] for p in ports if assignments[p["entity_id"]] == system["id"]
        ]
        file.create_entity(
            "IfcRelAssignsToGroup",
            GlobalId=guid("assign:" + system["id"]),
            RelatedObjects=members,
            RelatingGroup=created_systems[system["id"]],
        )
    for link in links:
        a, b = [created_ports[p] for p in link["ports"]]
        if a.FlowDirection == "SINK":
            a, b = b, a
        file.create_entity(
            "IfcRelConnectsPorts",
            GlobalId=guid("connect:" + link["id"]),
            RelatingPort=a,
            RelatedPort=b,
            Description=link["source"],
        )
    return {
        "systems": len(systems),
        "ports": len(ports),
        "connections": len(links),
        "scope": result["scope"],
    }
