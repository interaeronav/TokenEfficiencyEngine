"""Coordinated architectural cut/context views, schedules and cabinet details.

View geometry shares the real model and carries source IDs. Drawing issue
metadata is explicit; absent checker/site information is never fabricated.
"""

from __future__ import annotations

import csv
import hashlib
import html
import itertools
import json
import math
from itertools import pairwise
from pathlib import Path
from typing import Any

from tee.kernel.errors import TeeError

from .exchange import _area, _document, preview

ROOF_ISOMETRIC_BASIS = (
    (1 / math.sqrt(2), 1 / math.sqrt(2), 0.0),
    (-1 / math.sqrt(6), 1 / math.sqrt(6), 2 / math.sqrt(6)),
    (1 / math.sqrt(3), -1 / math.sqrt(3), 1 / math.sqrt(3)),
)


def _roof_project(point: list[float], axonometric: bool) -> list[float]:
    if not axonometric:
        return list(point)
    return [sum(a * b for a, b in zip(point, axis, strict=True)) for axis in ROOF_ISOMETRIC_BASIS]


def _roof_register(document: dict[str, Any]) -> list[dict[str, Any]]:
    """Model quantities and provenance, never assumed drainage or physical metal."""
    from .spatial import base_elevation
    from .systems import roof_meshes, roof_quantities

    rows = []
    for identifier, roof in document["entities"].items():
        if roof["kind"] != "roof":
            continue
        base = base_elevation(roof, document["entities"])
        quantities = roof_quantities(roof, base)
        meshes = roof_meshes(roof, base)
        planes = quantities.get("planes", [])
        pitches = [row["pitch_deg"] for row in planes] if planes else [quantities.get("pitch_deg")]
        provenance = roof.get("provenance", {})
        rows.append(
            {
                "mark": f"R{len(rows) + 1:02d}",
                "id": identifier,
                "name": roof["name"],
                "form": roof["form"],
                "quantities": quantities,
                "plane_pitches_deg": pitches,
                "highest_top_world_mm": quantities["highest_top_world_mm"],
                "lowest_top_world_mm": min(row["top_min_world_mm"] for row in planes)
                if planes
                else min(p[2] for mesh in meshes for p in mesh["vertices"])
                + roof["thickness"]
                / math.cos(math.radians(float(quantities.get("pitch_deg") or 0))),
                "nominal_envelope_thickness_mm": roof["thickness"],
                "source_id": provenance.get("source_id"),
                "source_basis": provenance.get("basis", "NOT RECORDED"),
                "datum_basis": provenance.get(
                    "datum_basis", "Model world Z; source datum not recorded"
                ),
                "provenance": provenance,
                "properties": roof.get("properties", {}),
                "fall_note": "Level model plane; drainage fall not verified."
                if all(pitch == 0 for pitch in pitches)
                else "Pitches are model plane geometry; drainage/outlets not verified.",
                "construction_note": "Thickness is the model envelope, not a measured metal gauge. "
                "Roof structure, junctions, flashing and waterproofing require "
                "separate verification.",
            }
        )
    return rows


def _roof_view(document: dict[str, Any], derived: dict[str, Any], axonometric: bool) -> dict:
    from .view_geometry import visible_edges

    physical = [
        mesh
        for mesh in derived["meshes"]
        if mesh["kind"] != "space" and not mesh.get("nonphysical")
    ]
    transformed = [
        {**mesh, "vertices": [_roof_project(p, axonometric) for p in mesh["vertices"]]}
        for mesh in physical
    ]
    segments = visible_edges(transformed, "plan")
    for segment in segments:
        if segment["kind"] == "roof":
            segment["role"] = "roof"
    name = "roof-axonometric" if axonometric else "roof-plan"
    note = (
        "Southeast isometric roof/building view from model solids; "
        "use orthographic views for dimensions."
        if axonometric
        else "Roof plan from above; actual model roof geometry. R marks refer to the roof register."
    )
    view = _view(name, segments, document["revision"], note)
    view["projection_kind"] = "axonometric" if axonometric else "orthographic-roof-plan"
    view["projection_basis"] = (
        [list(axis) for axis in ROOF_ISOMETRIC_BASIS] if axonometric else None
    )
    view["annotation_search"] = "sheet"
    rows = _roof_register(document)
    requests = []
    for row in rows:
        edges = [segment for segment in segments if segment["id"] == row["id"]]
        row["visible_in_view"] = bool(edges)
        if not edges:
            row["view_note"] = "Occluded in this view; record retained in roof register."
            continue
        anchors = [
            [(a[i] + b[i]) / 2 for i in range(2)]
            for edge in sorted(edges, key=lambda edge: -math.dist(*edge["points"]))
            for a, b in [edge["points"]]
        ]
        requests.append(
            {
                "id": row["id"],
                "kind": "roof",
                "lines": [row["mark"]],
                "anchor": anchors[0],
                "anchors": anchors,
                "normal": [0, -1],
            }
        )
    _plan_annotations(view, document, "", requests)
    view["roof_register"] = rows
    return view


def _roof_register_pages(rows: list[dict]) -> list[list[dict]]:
    """Paginate full roof identity/top-height/pitch/source text without truncation."""
    import textwrap

    pages, page, used = [], [], 0.0
    for row in rows:
        pitches = ", ".join(
            "NOT SET" if pitch is None else f"{pitch:.3f}°" for pitch in row["plane_pitches_deg"]
        )
        columns = [
            [f"{row['mark']} / {row['id']}", row["name"]],
            [
                f"Form: {row['form']}",
                f"Model plane pitches: {pitches}",
                f"Top Z {row['lowest_top_world_mm'] / 1000:+.3f} to "
                f"{row['highest_top_world_mm'] / 1000:+.3f} m",
                f"Nominal envelope {row['nominal_envelope_thickness_mm']:g} mm",
            ],
            [
                f"Source ID: {row['source_id'] or 'NOT RECORDED'}",
                f"Basis: {row['source_basis']}",
                f"Datum: {row['datum_basis']}",
            ],
            [row["fall_note"], row["construction_note"]],
        ]
        lines = [
            [part for value in values for part in textwrap.wrap(value, width=42)]
            for values in columns
        ]
        height = max(map(len, lines)) * 3.3 + 4
        if height > 192:
            raise TeeError(
                "architecture_drawing_limit",
                "A complete roof register row exceeds one sheet.",
                fix="Use concise roof provenance with links to the full source evidence.",
            )
        if page and used + height > 192:
            pages.append(page)
            page, used = [], 0.0
        page.append({"id": row["id"], "mark": row["mark"], "columns": lines, "height_mm": height})
        used += height
    if page:
        pages.append(page)
    return pages


def _point_key(point: list[float] | tuple[float, ...]) -> tuple[float, ...]:
    return tuple(round(float(value), 7) for value in point)


def _cut(mesh: dict[str, Any], axis: int, coordinate: float) -> list[list[list[float]]]:
    """Intersect triangles with the named world plane; retain real boundaries."""
    result = {}
    vertices = mesh["vertices"]
    axes = [index for index in range(3) if index != axis]
    for face in mesh["faces"]:
        points = [vertices[index] for index in face]
        distances = [point[axis] - coordinate for point in points]
        if all(abs(value) < 1e-7 for value in distances):
            continue  # Coplanar faces are a projection, not a section edge.
        hits = {}
        for i, a in enumerate(points):
            b = points[(i + 1) % 3]
            da, db = distances[i], distances[(i + 1) % 3]
            if abs(da) < 1e-7:
                hits[_point_key(a)] = a
            if da * db < 0:
                t = da / (da - db)
                point = [a[j] + t * (b[j] - a[j]) for j in range(3)]
                hits[_point_key(point)] = point
        if len(hits) == 2:
            projected = [[point[index] for index in axes] for point in hits.values()]
            if math.dist(*projected) > 1e-7:
                key = tuple(sorted(_point_key(p) for p in projected))
                result[key] = projected
    return list(result.values())


def _wire(mesh: dict[str, Any], axes: tuple[int, int] = (0, 2)) -> list[list[list[float]]]:
    """Project only mesh edges separating noncoplanar faces, not cap diagonals."""
    vertices = mesh["vertices"]
    edge_normals: dict[tuple, list] = {}
    for face in mesh["faces"]:
        a, b, c = [vertices[index] for index in face]
        ab, ac = [b[i] - a[i] for i in range(3)], [c[i] - a[i] for i in range(3)]
        normal = [
            ab[1] * ac[2] - ab[2] * ac[1],
            ab[2] * ac[0] - ab[0] * ac[2],
            ab[0] * ac[1] - ab[1] * ac[0],
        ]
        length = math.sqrt(sum(value * value for value in normal))
        normal = [value / length for value in normal] if length else [0, 0, 0]
        for first, last in zip(face, face[1:] + face[:1], strict=False):
            edge_normals.setdefault(tuple(sorted((first, last))), []).append(normal)
    result = {}
    for (first, last), normals in edge_normals.items():
        if len(normals) == 2 and abs(sum(a * b for a, b in zip(*normals, strict=False))) > 1 - 1e-9:
            continue
        points = [[vertices[index][axis] for axis in axes] for index in (first, last)]
        if math.dist(*points) > 1e-7:
            result[tuple(sorted(_point_key(point) for point in points))] = points
    return list(result.values())


def _view(
    name: str,
    segments: list[dict],
    revision: int,
    note: str,
    extents: list | tuple = (),
) -> dict[str, Any]:
    """`extents` are extra world points that must fall inside the view.

    Bounds used to come from drawn SEGMENTS alone, so a storey whose geometry
    is a space - a room polygon, which is annotated but never drawn as a
    segment - produced the degenerate {min:[0,0], max:[1,1]} fallback. Every
    paper coordinate then collapsed onto a single point and annotation
    placement failed with `architecture_annotation_crowding` on a sheet that
    was, in fact, empty. A room is part of what a plan must contain even when
    nothing draws its outline.
    """
    if len(segments) > 50000:
        raise TeeError(
            "architecture_drawing_limit",
            "Drawing exceeds 50,000 segments.",
            fix="Export a smaller model.",
        )
    points = [point for segment in segments for point in segment["points"]] + list(extents)
    bounds = (
        {
            "min": [min(p[i] for p in points) for i in range(2)],
            "max": [max(p[i] for p in points) for i in range(2)],
        }
        if points
        else {"min": [0, 0], "max": [1, 1]}
    )
    width = bounds["max"][0] - bounds["min"][0]
    height = bounds["max"][1] - bounds["min"][1]
    return {
        "name": name,
        "revision": revision,
        "units": "mm",
        "segments": segments,
        "bounds": bounds,
        "dimensions": [
            {"name": "projected_width", "value_mm": width},
            {"name": "projected_height", "value_mm": height},
        ],
        "note": note,
    }


def _layout(view: dict[str, Any]) -> tuple[float, Any]:
    bounds = view["bounds"]
    width, height = [max(1, bounds["max"][i] - bounds["min"][i]) for i in range(2)]
    region = view.get("paper_region") or (
        [40, 63.5, 340, 185] if view.get("wall_dimensions") else [27, 48, 365, 185]
    )
    rx, ry, rw, rh = region
    required = max(width / rw, height / rh)
    denominator = next(
        (
            scale
            for scale in (
                1,
                2,
                5,
                10,
                20,
                25,
                50,
                100,
                200,
                500,
                1000,
                2000,
                5000,
                10000,
                20000,
                50000,
                100000,
            )
            if scale >= required
        ),
        max(1, math.ceil(required)),
    )
    x0 = rx + (rw - width / denominator) / 2
    y0 = ry + (rh - height / denominator) / 2

    def paper(point: list[float]) -> tuple[float, float]:
        return (
            x0 + (point[0] - bounds["min"][0]) / denominator,
            y0 + (bounds["max"][1] - point[1]) / denominator,
        )

    return denominator, paper


def _overall_dimensions(view: dict[str, Any]) -> bool:
    return (
        not view.get("wall_dimensions")
        and view.get("scope_role") != "enlarged"
        and view.get("projection_kind") != "axonometric"
    )


def _dimension_rows(view: dict[str, Any]) -> list[dict]:
    rows = [
        *view.get("wall_dimensions", []),
        *view.get("opening_dimensions", []),
        *view.get("room_dimensions", []),
    ]
    return [{**row, "dimension_key": f"{index}:{row['id']}"} for index, row in enumerate(rows)]


def _svg(view: dict[str, Any], path: Path, project: str) -> None:
    scale, paper = _layout(view)
    metadata = json.dumps(
        {
            "revision": view["revision"],
            "units": "mm",
            "view": view["name"],
            "dimensions": view["dimensions"],
            "annotations": view.get("annotations", []),
            "issue": view.get("issue", {}),
            "drawing_number": view.get("drawing_number"),
            "wall_dimensions": view.get("wall_dimensions", []),
            "opening_dimensions": view.get("opening_dimensions", []),
            "room_dimensions": view.get("room_dimensions", []),
            "setting_out": view.get("setting_out"),
            "working_dimensions": view.get("working_dimensions", False),
            "opening_marks": view.get("opening_marks", []),
            "scope_role": view.get("scope_role"),
            "plan_scope": view.get("plan_scope"),
            "scope_references": view.get("scope_references", []),
            "scope_locator": view.get("scope_locator"),
            "roof_register": view.get("roof_register", []),
            "projection_kind": view.get("projection_kind"),
            "projection_basis": view.get("projection_basis"),
        }
    )
    issue = {key: html.escape(str(value)) for key, value in view.get("issue", {}).items()}
    lines = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="420mm" height="297mm" '
        'viewBox="0 0 420 297">',
        '<rect x="10" y="10" width="400" height="277" fill="white" '
        'stroke="#333" stroke-width="0.3"/>',
        f"<metadata>{html.escape(metadata)}</metadata>",
        '<g font-family="sans-serif" fill="#111">',
        f'<text x="16" y="21" font-size="5">{html.escape(project[:80])} / '
        f"{html.escape(view['name'])}</text>",
        f'<text x="16" y="29" font-size="3.5">Revision {view["revision"]} | '
        f"model mm | scale 1:{scale:g} at A3</text>",
        f'<text x="16" y="43" font-size="2.5">{html.escape(view["note"][:160])}</text>',
        '<path d="M 10 37 H 410 M 10 265 H 410" fill="none" stroke="#333" stroke-width="0.2"/>',
        f'<text x="16" y="271" font-size="2.8">{issue.get("project_number", "NOT SET")} | '
        f"Issue {issue.get('issue', 'NOT SET')} | {issue.get('issue_date', 'NOT SET')}</text>",
        f'<text x="16" y="277" font-size="2.8">Drawn: {issue.get("drawn_by", "NOT SET")} | '
        f"Checked: {issue.get('checked_by', 'NOT SET')}</text>",
        f'<text x="16" y="283" font-size="2.8">{issue.get("status", "NOT SET")} | '
        f"{html.escape(str(view.get('drawing_number', '')))} | Verify design, "
        f"construction and required approvals.</text></g>",
    ]
    for segment in view["segments"]:
        (x1, y1), (x2, y2) = [paper(p) for p in segment["points"]]
        color, weight, dash = _line_style(segment)
        dash_attribute = f' stroke-dasharray="{dash}"' if dash else ""
        lines.append(
            f'<line data-entity="{html.escape(segment["id"], quote=True)}" '
            f'data-role="{html.escape(segment.get("role", "context"), quote=True)}" '
            f'x1="{x1:.6f}" y1="{y1:.6f}" x2="{x2:.6f}" y2="{y2:.6f}" '
            f'stroke="{color}" stroke-width="{weight}"{dash_attribute}/>'
        )
    low, high = view["bounds"]["min"], view["bounds"]["max"]
    left, bottom = paper(low)
    right, _ = paper(high)
    if _overall_dimensions(view):
        lines.extend(
            [
                f'<path d="M {left} {bottom + 4} V {bottom + 11} '
                f'M {right} {bottom + 4} V {bottom + 11} M {left} {bottom + 8} H {right}" '
                'fill="none" stroke="#53616a" stroke-width="0.2"/>',
                f'<text x="{(left + right) / 2}" y="{bottom + 7}" text-anchor="middle" '
                f'font-family="sans-serif" font-size="3.5">{high[0] - low[0]:g} mm</text>',
            ]
        )
    lines.append("</svg>")
    for item in _sheet_graphics(view):
        if item["type"] == "line":
            a, b = item["points"]
            dash = ' stroke-dasharray="4 2"' if item.get("role") == "section-marker" else ""
            color = "#9b4533" if item.get("role") == "scope-crop" else "#64727c"
            weight = 0.45 if item.get("role") == "scope-crop" else 0.18
            lines.insert(
                -1,
                f'<line x1="{a[0]}" y1="{a[1]}" x2="{b[0]}" y2="{b[1]}" '
                f'stroke="{color}" stroke-width="{weight}"{dash}/>',
            )
        else:
            x, y = item["at"]
            anchor = ' text-anchor="end"' if item.get("align") == "right" else ""
            lines.insert(
                -1,
                f'<text data-role="{html.escape(item.get("role", "reference"), quote=True)}" '
                f'data-reference="{html.escape(item.get("id", ""), quote=True)}" '
                f'x="{x}" y="{y}" font-family="sans-serif" '
                f'font-size="{item["size"]}"{anchor}>{html.escape(item["value"])}</text>',
            )
    lines[-1:-1] = _annotation_svg(view)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _dxf(view: dict[str, Any], path: Path) -> None:
    import ezdxf

    document = ezdxf.new("R2010")
    document.units = ezdxf.units.MM
    document.header["$MEASUREMENT"] = 1
    document.appids.add("TEE_ARCHITECTURE")
    msp = document.modelspace()
    for segment in view["segments"]:
        layer = "AK_" + segment.get("role", "context").upper()
        if layer not in document.layers:
            document.layers.new(layer)
        if segment.get("role") == "overhead":
            if "AK_OVERHEAD_DASH" not in document.linetypes:
                # DXF is model space; use the selected plotted scale for paper dashes.
                scale, _ = _layout(view)
                document.linetypes.new(
                    "AK_OVERHEAD_DASH",
                    dxfattribs={
                        "description": "Above-cut stair extent",
                        "pattern": [3 / scale, 2 / scale, -1 / scale],
                    },
                )
            document.layers.get(layer).dxf.linetype = "AK_OVERHEAD_DASH"
        elif segment.get("role") == "reference":
            if "AK_REFERENCE_DASH" not in document.linetypes:
                scale, _ = _layout(view)
                document.linetypes.new(
                    "AK_REFERENCE_DASH",
                    dxfattribs={
                        "description": "Nonphysical reference: plotted 4 mm dash / 2 mm gap",
                        # A paper length becomes model length by multiplying the
                        # scale denominator; DXF entities here are model-space mm.
                        "pattern": [6 * scale, 4 * scale, -2 * scale],
                    },
                )
            reference_layer = document.layers.get(layer)
            reference_layer.dxf.linetype = "AK_REFERENCE_DASH"
            reference_layer.dxf.lineweight = 18
            reference_layer.dxf.true_color = int("64727c", 16)
        entity = msp.add_line(*segment["points"], dxfattribs={"layer": layer})
        entity.set_xdata(
            "TEE_ARCHITECTURE", [(1000, segment["id"][:200]), (1071, view["revision"])]
        )
    low, high = view["bounds"]["min"], view["bounds"]["max"]
    extent = max(high[0] - low[0], high[1] - low[1], 1)
    text_height = extent / 80
    height_text = _overall_height_text(view)
    scale, _ = _layout(view)
    for angle, p1, p2, base in (
        (0, low, [high[0], low[1]], [(low[0] + high[0]) / 2, low[1] - extent / 15]),
        (90, low, [low[0], high[1]], [low[0] - extent / 15, (low[1] + high[1]) / 2]),
    ):
        if not _overall_dimensions(view) or math.dist(p1, p2) <= 1e-7:
            continue
        dimension = msp.add_linear_dim(
            base=base,
            p1=p1,
            p2=p2,
            angle=angle,
            location=_paper_inverse(view, height_text["centre_mm"])
            if angle == 90 and height_text
            else None,
            text_rotation=0 if angle == 90 else None,
            override={
                "dimtxt": height_text["size"] * scale,
                "dimasz": scale,
                "dimtad": 0,
                "dimgap": 0,
            }
            if angle == 90 and height_text
            else {"dimtxt": text_height, "dimasz": text_height / 2},
        )
        dimension.dimension.set_xdata(
            "TEE_ARCHITECTURE", [(1000, "measured projection mm"), (1071, view["revision"])]
        )
        dimension.render()
    text_positions = {
        item["dimension_key"]: item
        for item in _sheet_graphics(view)
        if item.get("role") == "dimension-text" and "centre_mm" in item
    }
    for row in _dimension_rows(view):
        a, b = row["a"], row["b"]
        base = [
            (a[i] + b[i]) / 2 + row["normal"][i] * row["offset_paper_mm"] * scale for i in range(2)
        ]
        dimension = msp.add_linear_dim(
            base=base,
            p1=a,
            p2=b,
            angle=math.degrees(math.atan2(b[1] - a[1], b[0] - a[0])) % 180,
            location=_paper_inverse(view, text_positions[row["dimension_key"]]["centre_mm"])
            if row["dimension_key"] in text_positions
            else None,
            text_rotation=0 if row["dimension_key"] in text_positions else None,
            override={"dimtxt": 2.4 * scale, "dimasz": scale},
        )
        dimension.dimension.set_xdata(
            "TEE_ARCHITECTURE", [(1000, row["id"]), (1071, view["revision"]), (1000, row["basis"])]
        )
        dimension.render()
    msp.add_text(
        f"{view['name']} | revision {view['revision']} | mm", dxfattribs={"height": text_height}
    ).set_placement((low[0], high[1] + extent / 20))
    _annotation_dxf(view, msp)
    for item in _sheet_graphics(view):
        if item.get("role") == "overall-height-text":
            continue  # The measured DXF DIMENSION carries this positioned value itself.
        if item.get("role") in {"dimension", "dimension-text", "dimension-leader"}:
            continue  # These are associative DXF dimensions above.
        if item["type"] == "line":
            msp.add_line(
                *[_paper_inverse(view, p) for p in item["points"]],
                dxfattribs={"color": 1} if item.get("role") == "scope-crop" else {},
            )
        else:
            from ezdxf.enums import TextEntityAlignment

            scale, _ = _layout(view)
            msp.add_text(item["value"], dxfattribs={"height": item["size"] * scale}).set_placement(
                _paper_inverse(view, item["at"]),
                align=TextEntityAlignment.RIGHT
                if item.get("align") == "right"
                else TextEntityAlignment.LEFT,
            )
    document.saveas(path)


def _csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    # Neutralize spreadsheet formula prefixes without changing numeric quantities.
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    key: (
                        "'" + value
                        if isinstance(value, str)
                        and value.lstrip().startswith(("=", "+", "-", "@"))
                        else value
                    )
                    for key, value in row.items()
                    if key in fields
                }
            )


def _pdf(views: list[dict[str, Any]], path: Path, project: dict[str, Any]) -> dict[str, Any]:
    import copy
    import textwrap

    from fpdf import FPDF

    pdf = FPDF(orientation="L", unit="mm", format="A3")
    pdf.set_auto_page_break(False)
    font = Path("/System/Library/Fonts/Supplemental/Arial Unicode.ttf")
    family = "Architecture" if font.is_file() else "Helvetica"
    if font.is_file():
        pdf.add_font(family, fname=str(font))
    replaced = 0
    issue = views[0]["issue"]

    def text(value: str) -> str:
        nonlocal replaced
        if family == "Helvetica":
            result = value.encode("latin-1", "replace").decode("latin-1")
            replaced += sum(a != b for a, b in zip(value, result, strict=False))
            return result
        return value

    def label(x: float, y: float, value: str, size: float = 9) -> None:
        pdf.set_font(family, size=size)
        pdf.text(x, y, text(value))

    sheet_index = []

    def page(title: str, references: list[str], *, scales: str = "AS SHOWN") -> None:
        pdf.add_page()
        number = pdf.page_no()
        pdf.set_draw_color(55, 70, 80)
        pdf.set_line_width(0.25)
        pdf.rect(10, 10, 400, 277)
        pdf.line(10, 37, 410, 37)
        label(16, 21, project["name"][:80], 13)
        label(16, 31, title[:110], 10)
        label(353, 21, f"S{number:03d}", 13)
        label(328, 31, f"A3 | {scales}", 8)
        pdf.line(10, 265, 410, 265)
        label(
            16,
            271,
            f"Project {issue['project_number']} | Issue {issue['issue']} | {issue['issue_date']}",
            8,
        )
        label(16, 277, f"Drawn: {issue['drawn_by']} | Checked: {issue['checked_by']}", 8)
        label(
            16,
            283,
            f"{issue['status']} | Model revision {views[0]['revision']} | Dimensions "
            f"mm unless stated",
            8,
        )
        label(270, 271, f"Client: {issue['client']}"[:75], 8)
        label(270, 277, f"Site: {issue['site']}"[:75], 8)
        label(270, 283, "Verify design, specification and approval requirements.", 7)
        sheet_index.append({"sheet": f"S{number:03d}", "title": title, "views": references})

    architecture = [view for view in views if view.get("sheet_kind") not in {"panel", "assembly"}]
    groups = [(view["name"], [view], "architectural") for view in architecture]
    cabinet_ids = sorted({v["cabinet_id"] for v in views if v.get("sheet_kind") == "assembly"})
    for cabinet_id in cabinet_ids:
        assemblies = [
            v for v in views if v.get("sheet_kind") == "assembly" and v["cabinet_id"] == cabinet_id
        ]
        groups.append((f"Cabinet {cabinet_id} / coordinated assembly", assemblies, "assembly"))
        panels = [
            v for v in views if v.get("sheet_kind") == "panel" and v["cabinet_id"] == cabinet_id
        ]
        for index in range(0, len(panels), 4):
            groups.append(
                (
                    f"Cabinet {cabinet_id} / part details "
                    f"{index + 1}-{min(index + 4, len(panels))}",
                    panels[index : index + 4],
                    "panels",
                )
            )
    rows = views[0].get("object_schedule", [])
    roof_rows = next((view["roof_register"] for view in views if "roof_register" in view), [])
    roof_pages = _roof_register_pages(roof_rows)
    schedule_title = (
        "Opening and cabinet schedule"
        if any(row["mark"].startswith("F") for row in rows)
        else "Door, window and cabinet schedule"
    )
    register = (
        [title for title, _, _ in groups]
        + [
            f"{schedule_title} / rows {i + 1}-{min(i + 24, len(rows))}"
            for i in range(0, len(rows), 24)
        ]
        + [f"Roof register / {index + 1}" for index in range(len(roof_pages))]
    )
    # Index is an actual issue record, not a decorative cover or fabricated signoff.
    for offset in range(0, max(1, len(register)), 28):
        page("Drawing register and project specification", [])
        label(17, 47, "SHEET / VIEW CONTENT", 10)
        index_pages = max(1, math.ceil(len(register) / 28))
        for index, title in enumerate(register[offset : offset + 28], offset):
            label(
                17,
                56 + (index - offset) * 5.4,
                f"S{index_pages + index + 1:03d}   {title}"[:100],
                8,
            )
        label(240, 48, "Drawing conventions", 10)
        for i, value in enumerate(
            [
                "Heavy: material cut by the named plane.",
                "Fine: visible geometry beyond or below the cut.",
                "Concealed edges are removed analytically.",
                "D/W/C tags refer to the object schedule.",
                "Door arcs show explicitly specified operation.",
                "Glazing and furnishing are diagrammatic.",
                "R marks identify roofs in the full roof register.",
            ]
        ):
            label(240, 57 + 5 * i, value, 8)
        facts = project.get("facts", {})
        notes = facts.get("drawing", {}).get("notes", [])
        specs = facts.get("specifications", {})
        values = (
            [f"{key}: {value}" for key, value in specs.items()]
            if isinstance(specs, dict)
            else [str(specs)]
        )
        if isinstance(notes, list):
            values.extend(str(value) for value in notes)
        label(240, 96, "Explicit specification / outstanding decisions", 9)
        y = 104
        for value in values or ["Construction specification: NOT SET"]:
            for line in textwrap.wrap(value, width=68):
                if y > 252:
                    raise TeeError(
                        "architecture_drawing_spec",
                        "Project notes exceed the register column.",
                        fix="Shorten drawing notes; keep the complete specification "
                        "in the project information export.",
                    )
                label(240, y, line, 7)
                y += 4
            y += 2

    for title, members, kind in groups:
        page(title, [member["name"] for member in members])
        for index, original in enumerate(members):
            view = copy.deepcopy(original)
            if kind == "panels":
                column, row = index % 2, index // 2
                x, y = 17 + 199 * column, 47 + 107 * row
                label(
                    x,
                    y,
                    f"{view['drawing_number']}  {view['panel']['role']} / {view['panel']['id']}"[
                        :105
                    ],
                    8,
                )
                view["paper_region"] = [x + 28, y + 7, 135, 53]
                view["detail_origin"] = [x, y + 76]
                if len(view.get("detail_lines", [])) > 9:
                    raise TeeError(
                        "architecture_drawing_limit",
                        "Panel detail exceeds the bounded machining notes area.",
                        fix="Split dense machining into a dedicated manufacturing "
                        "drawing before issue.",
                    )
            elif kind == "assembly":
                x = 17 + index * 130
                label(x, 48, view["name"], 9)
                view["paper_region"] = [x + 12, 64, 106, 155]
                view["detail_origin"] = [x, 242]
            scale, paper = _layout(view)
            if kind != "architectural":
                rx, ry, _, _ = view["paper_region"]
                label(rx, ry - 2, f"1:{scale:g}", 7)
            else:
                label(
                    17,
                    44,
                    f"{view['drawing_number']} | Scale 1:{scale:g} | {view['note']}"[:170],
                    7,
                )
            for segment in view["segments"]:
                a, b = [paper(point) for point in segment["points"]]
                color, weight, dash = _line_style(segment)
                pdf.set_draw_color(*(int(color[i : i + 2], 16) for i in (1, 3, 5)))
                pdf.set_line_width(weight)
                if dash:
                    dash_length, gap_length = (float(value) for value in dash.split())
                    pdf.set_dash_pattern(dash=dash_length, gap=gap_length)
                else:
                    pdf.set_dash_pattern()
                pdf.line(*a, *b)
            pdf.set_dash_pattern()
            pdf.set_draw_color(78, 95, 105)
            pdf.set_line_width(0.15)
            low, high = view["bounds"]["min"], view["bounds"]["max"]
            left, bottom = paper(low)
            right, top = paper(high)
            if _overall_dimensions(view):
                pdf.line(left, bottom + 5, right, bottom + 5)
                for x in (left, right):
                    pdf.line(x, bottom + 2, x, bottom + 7)
                pdf.line(left - 8, top, left - 8, bottom)
                for y in (top, bottom):
                    pdf.line(left - 10, y, left - 2, y)
                label((left + right) / 2, bottom + 4, f"{high[0] - low[0]:g}", 7)
            for item in _sheet_graphics(view):
                if item["type"] == "line":
                    pdf.set_draw_color(
                        *(155, 69, 51) if item.get("role") == "scope-crop" else (92, 108, 118)
                    )
                    pdf.set_line_width(0.45 if item.get("role") == "scope-crop" else 0.16)
                    if item.get("role") == "section-marker":
                        pdf.set_dash_pattern(dash=4, gap=2)
                    pdf.line(*item["points"][0], *item["points"][1])
                    pdf.set_dash_pattern()
                else:
                    x, y = item["at"]
                    if item.get("align") == "right":
                        pdf.set_font(family, size=item["size"] * 72 / 25.4)
                        x -= pdf.get_string_width(text(item["value"]))
                    label(x, y, item["value"], item["size"] * 72 / 25.4)
            _annotation_pdf(pdf, view, family, text)
        if kind == "assembly":
            label(
                17,
                253,
                "Assembly dimensions follow model envelopes; see identified part "
                "sheets for grain, edges and machining. Hardware/source acceptance is separate.",
                8,
            )

    rows = views[0].get("object_schedule", [])
    for offset in range(0, len(rows), 24):
        page(schedule_title, [])
        headers = [
            (17, "Mark / object"),
            (104, "Authored dimensions mm"),
            (184, "Level / sill / head mm"),
            (278, "Type / operation / specification"),
        ]
        for x, value in headers:
            label(x, 49, value, 9)
        for index, row in enumerate(rows[offset : offset + 24]):
            y = 59 + index * 7.5
            for (x, _), key in zip(headers, ("identity", "size", "levels", "spec"), strict=True):
                label(x, y, row[key][:76], 7)
            pdf.set_draw_color(205, 212, 217)
            pdf.line(16, y + 2, 402, y + 2)
        label(
            16,
            253,
            "Opening dimensions describe authored apertures, not manufacturer or order sizes.",
            8,
        )
    for index, roof_page in enumerate(roof_pages, 1):
        page(f"Roof register / {index}", [])
        columns = [
            (16, "Roof identity"),
            (116, "Authored roof geometry"),
            (216, "Source provenance"),
            (316, "Unverified construction / falls"),
        ]
        for x, title in columns:
            label(x, 49, title, 9)
        y = 58.0
        for row in roof_page:
            for (x, _), lines in zip(columns, row["columns"], strict=True):
                for line_index, value in enumerate(lines):
                    label(x, y + line_index * 3.3, value, 7)
            y += row["height_mm"]
            pdf.set_draw_color(205, 212, 217)
            pdf.line(16, y - 2, 402, y - 2)
        label(
            16,
            256,
            "Heights are model world Z; plane pitches come from geometry. "
            "Roof envelope volume is not fabricated steel quantity.",
            8,
        )
    pdf.output(str(path))
    return {
        "status": "written",
        "pages": pdf.page_no(),
        "font_substitutions": replaced,
        "sheet_index": sheet_index,
    }


def _architectural_views(
    document: dict[str, Any], derived: dict[str, Any], requested: set[str] | None = None
) -> tuple[list[dict[str, Any]], list[dict]]:
    """One generation path for file exports and the read-only interactive client."""
    from .view_geometry import visible_edges

    entities, revision = document["entities"], document["revision"]
    meshes = derived["meshes"]
    names = []
    settings = document["project"].get("facts", {}).get("drawing", {})
    if not isinstance(settings, dict):
        raise TeeError(
            "architecture_drawing_spec",
            "project.facts.drawing must be an object.",
            fix="Supply explicit drawing settings as an object.",
        )
    if type(settings.get("working_dimensions", False)) is not bool:
        raise TeeError(
            "architecture_drawing_spec",
            "working_dimensions must be a boolean.",
            fix="Set drawing.working_dimensions to true or false.",
        )
    views = []
    for identifier, storey in entities.items():
        if storey["kind"] != "storey":
            continue
        view_name = f"plan-{identifier}"
        requests = _annotation_requests(document, identifier)
        from .drawing_scopes import clipped_segments, contains, plan_scopes

        scopes = plan_scopes(settings, identifier, requests)
        plan_names = [view_name, *[f"{view_name}-{scope['id']}" for scope in scopes]]
        names.extend(plan_names)
        if requested is not None and not requested.intersection(plan_names):
            continue
        relative_cut = settings.get("plan_cut_height_mm", min(1200, storey["height"] / 2))
        if (
            isinstance(relative_cut, bool)
            or not isinstance(relative_cut, (int, float))
            or not math.isfinite(relative_cut)
            or not 0 < relative_cut < storey["height"]
        ):
            raise TeeError(
                "architecture_drawing_spec",
                "Plan cut must lie inside the storey.",
                fix="Set drawing.plan_cut_height_mm between zero and storey height.",
            )
        cut_z = storey["elevation"] + relative_cut
        scoped = [
            mesh
            for mesh in meshes
            if _storey(entities[mesh["id"]], entities) == identifier
            or (
                entities[mesh["id"]]["kind"] == "stair"
                and entities[mesh["id"]]["top_storey"] == identifier
            )
        ]
        # A swing door is drawn in its documented symbolic plan position; its
        # closed 3D leaf remains in elevations/sections and all model exports.
        scoped = [
            mesh
            for mesh in scoped
            if not (
                mesh.get("material_role") == "leaf"
                and entities[mesh["id"]].get("properties", {}).get("assembly", {}).get("operation")
                == "swing"
            )
        ]
        segments = visible_edges(scoped, "plan", -cut_z)
        segments += _opening_symbols(document, identifier, cut_z)
        segments += [
            {
                "id": entity["id"],
                "kind": "virtual_boundary",
                "role": "reference",
                "points": [entity["start"], entity["end"]],
            }
            for entity in entities.values()
            if entity["kind"] == "virtual_boundary" and entity["storey"] == identifier
        ]
        overhead = _stair_overhead(document, identifier, cut_z)
        segments += overhead
        overall = _view(
            view_name,
            segments,
            revision,
            f"Cut Z={cut_z:g} mm. Heavy=cut; fine=below-cut context. "
            + ("Dashed stair outline=above cut. " if overhead else "")
            + "Door arcs need explicit swing.",
            extents=[
                point
                for entity in entities.values()
                if entity["kind"] == "space" and entity.get("storey") == identifier
                for point in entity["polygon"]
            ],
        )
        overall["cut_z_mm"] = cut_z
        overall["wall_dimensions"] = _wall_dimensions(document, identifier)
        overall["opening_dimensions"] = _slab_opening_dimensions(document, identifier)
        if scopes:
            overall["scope_role"] = "coordination"
            overall["scope_references"] = [
                {**scope, "view": f"{view_name}-{scope['id']}"} for scope in scopes
            ]
            overall["note"] += " Overall coordination; all labels on named enlarged plans."
            overall["annotations"] = []
        else:
            _plan_annotations(overall, document, identifier, requests)
        if requested is None or view_name in requested:
            views.append(overall)
        for scope in scopes:
            name = f"{view_name}-{scope['id']}"
            if requested is not None and name not in requested:
                continue
            bounds = scope["bounds_mm"]
            detail = _view(
                name,
                clipped_segments(segments, bounds),
                revision,
                f"{scope['id']} enlarged plan: {scope['title']}. "
                f"Cut Z={cut_z:g} mm. Context clipped; see {view_name}. "
                "Crop extents are not building dimensions.",
            )
            # Named world extents remain fixed even when the nearest physical
            # edge ends before the crop. Crop dimensions are never called wall dimensions.
            detail["bounds"] = {"min": bounds[:2], "max": bounds[2:]}
            detail["dimensions"] = [
                {"name": "scope_width", "value_mm": bounds[2] - bounds[0]},
                {"name": "scope_height", "value_mm": bounds[3] - bounds[1]},
            ]
            detail["scope_role"] = "enlarged"
            detail["plan_scope"] = {**scope, "parent_view": view_name}
            detail["paper_region"] = [35, 55, 285, 180]
            detail["scope_locator"] = {
                "bounds": overall["bounds"],
                "lines": [
                    [wall["start"], wall["end"]]
                    for wall in entities.values()
                    if wall["kind"] == "wall" and wall["storey"] == identifier
                ],
                "scope_bounds_mm": bounds,
                "id": scope["id"],
            }
            detail["cut_z_mm"] = cut_z
            detail["wall_dimensions"] = [
                row
                for row in overall["wall_dimensions"]
                if contains(bounds, row["a"]) and contains(bounds, row["b"])
            ]
            detail["opening_dimensions"] = [
                row
                for row in overall["opening_dimensions"]
                if contains(bounds, row["a"]) and contains(bounds, row["b"])
            ]
            selected = [row for row in requests if row["id"] in scope["annotation_ids"]]
            if settings.get("working_dimensions") is True:
                from .setting_out import aperture_references, room_boundary

                # Every visible context aperture gets its own local reference.
                selected = [
                    row
                    for row in requests
                    if row["id"] in scope["annotation_ids"]
                    or ("anchor" in row and contains(bounds, row["anchor"]))
                ]
                subject = entities[scope["subject_id"]] if "subject_id" in scope else None
                if subject and subject["kind"] == "space":
                    setting = room_boundary(subject, entities)
                    setting["apertures"] = [
                        row
                        for row in aperture_references(entities, identifier)
                        if contains(bounds, row["a"]) and contains(bounds, row["b"])
                    ]
                    detail["setting_out"] = setting
                    detail["room_dimensions"] = setting["dimensions"]
                    detail["working_dimensions"] = True
                    from .spatial import space_environment

                    location = "Exterior" if space_environment(subject) == "exterior" else "Space"
                    detail["note"] = (
                        f"{location} {scope['id']}. Cut Z={cut_z:g} mm. "
                        "Boundary dimensions in model mm; "
                        "clipped context. Finishes and survey control unverified."
                    )
                    detail["wall_dimensions"] = []
                    selected += [
                        {
                            "id": f"{subject['id']}:{vertex['mark']}",
                            "kind": "setting_out_vertex",
                            "source_entity_id": subject["id"],
                            "lines": [vertex["mark"]],
                            "anchor": vertex["xy_mm"],
                            "normal": [1, 0],
                        }
                        for vertex in setting["vertices"]
                    ]
            detail["_scope_annotation_requests"] = selected
            views.append(detail)
    if any(entity["kind"] == "roof" for entity in entities.values()):
        names[1:1] = ["roof-plan", "roof-axonometric"]
        for name, axonometric in (("roof-plan", False), ("roof-axonometric", True)):
            if requested is None or name in requested:
                views.append(_roof_view(document, derived, axonometric))
    bounds = derived["bounds"]
    sections = settings.get(
        "sections",
        [
            {
                "id": "A",
                "axis": "y",
                "coordinate_mm": (bounds["min"][1] + bounds["max"][1]) / 2,
                "direction": "positive",
            },
            {
                "id": "B",
                "axis": "x",
                "coordinate_mm": (bounds["min"][0] + bounds["max"][0]) / 2,
                "direction": "positive",
            },
        ]
        if bounds
        else [],
    )
    if not isinstance(sections, list) or len(sections) > 12:
        raise TeeError(
            "architecture_drawing_spec",
            "Specify at most twelve section planes.",
            fix="Use drawing.sections with named axis/coordinate/direction objects.",
        )
    section_ids = set()
    for section in sections:
        if not isinstance(section, dict):
            raise TeeError(
                "architecture_drawing_spec",
                "Section must be an object.",
                fix="Set id, axis, coordinate_mm and direction.",
            )
        sid, axis, coordinate = section.get("id"), section.get("axis"), section.get("coordinate_mm")
        direction = section.get("direction", "positive")
        if (
            not isinstance(sid, str)
            or not sid.isalnum()
            or len(sid) > 12
            or sid in section_ids
            or axis not in {"x", "y"}
            or direction not in {"positive", "negative"}
            or isinstance(coordinate, bool)
            or not isinstance(coordinate, (int, float))
            or not math.isfinite(coordinate)
        ):
            raise TeeError(
                "architecture_drawing_spec",
                "Invalid or duplicate section specification.",
                fix="Use unique alphanumeric id, x/y axis, finite coordinate_mm and "
                "positive/negative direction.",
            )
        section_ids.add(sid)
        names.append(f"section-{sid}")
        if requested is not None and f"section-{sid}" not in requested:
            continue
        camera = {
            ("x", "positive"): "west",
            ("x", "negative"): "east",
            ("y", "positive"): "south",
            ("y", "negative"): "north",
        }[axis, direction]
        depth = coordinate if direction == "positive" else -coordinate
        view = _view(
            f"section-{sid}",
            visible_edges(meshes, camera, depth),
            revision,
            f"{sid}-{sid} | world {axis.upper()}={coordinate:g} mm | looking "
            f"{direction} {axis.upper()}. "
            "Heavy=cut material; fine=visible beyond; space volumes omitted.",
        )
        view["section"] = dict(section)
        _levels(view, entities)
        views.append(view)
    for camera in ("south", "north", "east", "west"):
        names.append("elevation-" + camera)
        if requested is not None and "elevation-" + camera not in requested:
            continue
        view = _view(
            "elevation-" + camera,
            visible_edges(meshes, camera),
            revision,
            f"{camera.title()} exterior elevation | opaque-surface visibility; "
            f"concealed edges removed. "
            "S/H in metres above host storey FFL; glazing is diagrammatic.",
        )
        _levels(view, entities)
        _opening_view_marks(view, document, camera)
        views.append(view)
    views.sort(key=lambda view: names.index(view["name"]))
    issue = _issue(document)
    for view in views:
        view["drawing_number"] = f"A{names.index(view['name']) + 1:03d}"
        view["issue"] = issue
        if view["name"].startswith("plan-"):
            view["section_markers"] = _section_markers(view, sections)
            if view.get("scope_role") == "enlarged":
                _plan_annotations(
                    view,
                    document,
                    view["plan_scope"]["storey"],
                    view.pop("_scope_annotation_requests"),
                )
    return views, sections


def drawing_index(document_dict: dict[str, Any]) -> list[dict[str, Any]]:
    """Lightweight names for the shared GUI/export views; no mesh or drawing work."""
    from .drawing_scopes import plan_scopes

    document = _document(document_dict)
    settings = document["project"].get("facts", {}).get("drawing", {})
    if not isinstance(settings, dict):
        raise TeeError(
            "architecture_drawing_spec",
            "project.facts.drawing must be an object.",
            fix="Supply explicit drawing settings as an object.",
        )
    rows = []
    for identifier, storey in document["entities"].items():
        if storey["kind"] != "storey":
            continue
        scopes = plan_scopes(settings, identifier, _annotation_requests(document, identifier))
        name = f"plan-{identifier}"
        rows.append(
            {
                "name": name,
                "title": f"{storey['name']} / overall plan",
                "storey": identifier,
                "scope_role": "coordination" if scopes else "plan",
            }
        )
        rows.extend(
            {
                "name": f"{name}-{scope['id']}",
                "title": f"{scope['id']} / {scope['title']}",
                "storey": identifier,
                "scope_role": "enlarged",
            }
            for scope in scopes
        )
    if any(entity["kind"] == "roof" for entity in document["entities"].values()):
        rows[1:1] = [
            {"name": "roof-plan", "title": "Roof plan / source-linked geometry"},
            {"name": "roof-axonometric", "title": "Roof / building axonometric"},
        ]
    sections = settings.get("sections", [{"id": "A"}, {"id": "B"}])
    if not isinstance(sections, list) or any(not isinstance(row, dict) for row in sections):
        raise TeeError(
            "architecture_drawing_spec",
            "Sections must be a list of objects.",
            fix="Set named drawing.sections objects.",
        )
    rows.extend(
        {"name": f"section-{section.get('id', '')}", "title": f"Section {section.get('id', '')}"}
        for section in sections
    )
    rows.extend(
        {"name": f"elevation-{camera}", "title": f"{camera.title()} elevation"}
        for camera in ("south", "north", "east", "west")
    )
    return rows


def drawing_view(document_dict: dict[str, Any], view_name: str) -> dict[str, Any]:
    """Read-only coordinated view: model-mm segments and paper-mm annotations.

    Shares the export generator and visibility engine, but creates only the named
    plan, roof, section or elevation. It writes no files and generates no cabinet sheets.
    """
    if not isinstance(view_name, str) or len(view_name) > 160:
        raise TeeError(
            "architecture_drawing_view",
            "Invalid drawing view name.",
            fix="Name plan-{storey}, roof-plan, roof-axonometric, "
            "elevation-{south|north|east|west}, or section-{id}.",
        )
    document = _document(document_dict)
    views, _ = _architectural_views(document, preview(document), {view_name})
    if not views or not views[0]["segments"]:
        raise TeeError(
            "architecture_drawing_view",
            "Drawing view is unknown or has no physical geometry.",
            fix="Name an existing storey plan, roof view, configured section, "
            "or exterior elevation.",
        )
    view = views[0]
    scale, paper = _layout(view)
    view["model_to_paper"] = {
        "scale": 1 / scale,
        "origin_mm": list(paper([0, 0])),
        "y_direction": -1,
    }
    view["scale_denominator"] = scale
    view["paper_mm"] = [420, 297]
    view["paper_graphics"] = _sheet_graphics(view)
    return view


def export_drawings(document_dict: dict[str, Any], directory: Path) -> dict[str, Any]:
    from .view_geometry import visible_edges

    document = _document(document_dict)
    derived = preview(document)
    entities, revision = document["entities"], document["revision"]
    meshes = derived["meshes"]
    views, sections = _architectural_views(document, derived)
    panel_rows = []
    for identifier, entity in entities.items():
        if entity["kind"] != "cabinet":
            continue
        from .cabinets import panels, schedule

        cabinet_meshes = _cabinet_local_meshes(
            [mesh for mesh in meshes if mesh["id"] == identifier], entity
        )
        production = schedule(entity)
        for camera, title in (("south", "front"), ("east", "side"), ("plan", "plan")):
            assembly_view = _view(
                f"cabinet-{identifier}-{title}",
                visible_edges(cabinet_meshes, camera),
                revision,
                f"{entity['name']} | {title} assembly | panels and clearances from "
                f"model; verify hardware specification.",
            )
            assembly_view["cabinet_id"] = identifier
            assembly_view["sheet_kind"] = "assembly"
            assembly_view["coordinate_system"] = (
                "cabinet-local: front at negative Y; datum at origin"
            )
            views.append(assembly_view)

        for panel in panels(entity):
            panel_rows.append(
                {
                    "cabinet_id": identifier,
                    "panel_id": panel["id"],
                    "role": panel["role"],
                    "blank_width_mm": panel["width"],
                    "blank_height_mm": panel["height"],
                    "finished_width_mm": panel["finished_width"],
                    "finished_height_mm": panel["finished_height"],
                    "thickness_mm": panel["thickness"],
                    "grain": panel["grain"],
                    "material": panel["material"],
                    **{f"edge_{side}_mm": value for side, value in panel["edges"].items()},
                    "revision": revision,
                }
            )
            width, height = panel["width"], panel["height"]
            polygon = [[0, 0], [width, 0], [width, height], [0, height]]
            segments = [
                {"id": panel["id"], "kind": "cabinet", "points": [a, b]}
                for a, b in zip(polygon, polygon[1:] + polygon[:1], strict=False)
            ]
            views.append(
                _view(
                    "panel-" + panel["id"],
                    segments,
                    revision,
                    f"Cut blank {width:g} x {height:g} x {panel['thickness']:g} mm; "
                    f"grain {panel['grain']}; verify machining separately.",
                )
            )
            views[-1]["sheet_kind"] = "panel"
            detailed_panel = {
                **panel,
                "machining": [
                    op for op in production.get("machining", []) if op.get("part_id") == panel["id"]
                ],
            }
            views[-1]["panel"] = detailed_panel
            views[-1]["cabinet_id"] = identifier
            _panel_detail(views[-1], detailed_panel)
            if len(panel_rows) > 500:
                raise TeeError(
                    "architecture_drawing_limit",
                    "Drawing set exceeds 500 cabinet panels.",
                    fix="Export fewer cabinet assemblies at once.",
                )
    for number, view in enumerate(views, 1):
        view["drawing_number"] = (
            f"A{number:03d}"
            if view.get("sheet_kind") not in {"panel", "assembly"}
            else f"J{number:03d}"
        )
        view["issue"] = _issue(document)
        if not view["segments"]:
            raise TeeError(
                "architecture_empty_drawing",
                f"View {view['name']} contains no visible geometry.",
                fix="Choose a section through physical model geometry or add the "
                "missing model objects.",
            )
    if not views:
        raise TeeError(
            "architecture_empty_drawing",
            "No architectural views can be produced from an empty model.",
            fix="Add physical model objects before exporting drawings.",
        )
    views[0]["object_schedule"] = _object_schedule(document)
    for view in views:
        if view["name"].startswith("plan-"):
            view["section_markers"] = _section_markers(view, sections)
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    files = []
    for view in views:
        for extension, writer in (("svg", _svg), ("dxf", _dxf)):
            path = directory / (view["name"] + "." + extension)
            if extension == "svg":
                writer(view, path, document["project"]["name"])
            else:
                writer(view, path)
            files.append(path)
    panel_path = directory / "cabinet-cutlist.csv"
    _csv(
        panel_path,
        panel_rows,
        [
            "revision",
            "cabinet_id",
            "panel_id",
            "role",
            "blank_width_mm",
            "blank_height_mm",
            "finished_width_mm",
            "finished_height_mm",
            "thickness_mm",
            "grain",
            "material",
            "edge_left_mm",
            "edge_right_mm",
            "edge_top_mm",
            "edge_bottom_mm",
        ],
    )
    files.append(panel_path)
    schedule = []
    for identifier, entity in entities.items():
        row = {
            "revision": revision,
            "id": identifier,
            "kind": entity["kind"],
            "name": entity["name"],
            "storey": entity.get("storey", ""),
            "width_mm": entity.get("width", ""),
            "height_mm": entity.get("height", ""),
            "thickness_mm": entity.get("thickness", ""),
        }
        if entity["kind"] == "space":
            from .spatial import space_environment

            row["environment"] = space_environment(entity)
            row["conditioned"] = entity.get("conditioned")
        if entity["kind"] == "wall":
            row["length_mm"] = math.dist(entity["start"], entity["end"])
        if "polygon" in entity:
            row["area_m2"] = (
                sum(
                    abs(_area(part))
                    for part in [entity["polygon"], *entity.get("additional_polygons", [])]
                )
                / 1e6
            )
        if entity["kind"] == "slab":
            from .penetrations import slab_quantities

            quantities = slab_quantities(entity, entities)
            row.update(
                {
                    key: quantities[key]
                    for key in ("gross_area_m2", "opening_area_m2", "net_area_m2", "net_volume_m3")
                }
            )
            row["area_m2"] = quantities["net_area_m2"]
        elif entity["kind"] == "slab_opening":
            host = entities[entity["slab"]]
            row.update(host=host["id"], storey=host["storey"], thickness_mm=host["thickness"])
        schedule.append(row)
    schedule_path = directory / "schedule.csv"
    _csv(
        schedule_path,
        schedule,
        [
            "revision",
            "id",
            "kind",
            "name",
            "storey",
            "width_mm",
            "height_mm",
            "thickness_mm",
            "length_mm",
            "area_m2",
            "environment",
            "conditioned",
            "host",
            "gross_area_m2",
            "opening_area_m2",
            "net_area_m2",
            "net_volume_m3",
        ],
    )
    files.append(schedule_path)
    measured_rooms = {
        view["setting_out"]["id"]: view["setting_out"] for view in views if view.get("setting_out")
    }
    if measured_rooms:
        boundary_rows = []
        aperture_rows = {}
        for room_id, setting in measured_rooms.items():
            for row in setting["dimensions"]:
                boundary_rows.append(
                    {
                        "room": room_id,
                        "dimension": row["id"],
                        "from": row["from"],
                        "to": row["to"],
                        "x1_mm": row["a"][0],
                        "y1_mm": row["a"][1],
                        "x2_mm": row["b"][0],
                        "y2_mm": row["b"][1],
                        "length_mm": row["value_mm"],
                        "base_world_mm": setting["base_world_mm"],
                        "revision": revision,
                        "basis": row["basis"],
                    }
                )
            for row in setting["apertures"]:
                aperture_rows[row["id"]] = {
                    **row,
                    "revision": revision,
                    "x1_mm": row["a"][0],
                    "y1_mm": row["a"][1],
                    "x2_mm": row["b"][0],
                    "y2_mm": row["b"][1],
                }
        path = directory / "room-setting-out.csv"
        _csv(path, boundary_rows, list(boundary_rows[0]))
        files.append(path)
        if aperture_rows:
            path = directory / "aperture-setting-out.csv"
            _csv(
                path,
                list(aperture_rows.values()),
                [
                    "id",
                    "host",
                    "revision",
                    "x1_mm",
                    "y1_mm",
                    "x2_mm",
                    "y2_mm",
                    "authored_aperture_width_mm",
                    "authored_aperture_height_mm",
                    "sill_world_mm",
                    "head_world_mm",
                    "nominal_source_width_mm",
                    "operation",
                    "source_operation",
                    "clear_opening_width_mm",
                    "clear_opening_basis",
                ],
            )
            files.append(path)
    pdf_path = directory / "review-set.pdf"
    try:
        pdf = _pdf(views, pdf_path, document["project"])
        files.append(pdf_path)
    except (ImportError, OSError, ValueError) as exc:
        pdf = {"status": "not_written", "reason": type(exc).__name__}
    manifest = {
        "revision": revision,
        "units": "mm",
        "project": document["project"]["name"],
        "views": [
            {
                key: view.get(key, [])
                for key in (
                    "name",
                    "bounds",
                    "dimensions",
                    "wall_dimensions",
                    "opening_dimensions",
                    "room_dimensions",
                    "setting_out",
                    "working_dimensions",
                    "note",
                    "annotations",
                    "drawing_number",
                    "cut_z_mm",
                    "section",
                    "level_marks",
                    "opening_marks",
                    "section_markers",
                    "object_schedule",
                    "panel",
                    "issue",
                    "scope_role",
                    "plan_scope",
                    "scope_references",
                    "scope_locator",
                    "paper_region",
                    "roof_register",
                    "projection_kind",
                    "projection_basis",
                )
            }
            for view in views
        ],
        "section_planes": sections,
        "annotation_coverage": {
            entity_id: [
                view["name"]
                for view in views
                if any(label["id"] == entity_id for label in view.get("annotations", []))
            ]
            for entity_id in sorted(
                {label["id"] for view in views for label in view.get("annotations", [])}
            )
        },
        "panels": len(panel_rows),
        "pdf": pdf,
        "wall_junctions": derived["wall_junctions"],
        "wall_joins": derived["wall_joins"],
        "files": [
            {
                "name": path.name,
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                "bytes": path.stat().st_size,
            }
            for path in files
        ],
        "limitations": [
            "Initial review drawings; jurisdiction-specific sheet standards unverified.",
            "Orthographic opaque-surface visibility uses analytical edge intervals; "
            "glazing is diagrammatic.",
            "Door/window construction appears only when explicitly supplied; swing "
            "symbols require operation/handing.",
            "Panel blank schedules are not a manufacturer or CNC approval.",
            "Inspect wall_joins/wall_junctions; other-element intersections remain unverified.",
        ],
    }
    manifest_path = directory / "drawing-manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
    return {
        "directory": str(directory),
        "revision": revision,
        "views": len(views),
        "panels": len(panel_rows),
        "manifest": str(manifest_path),
        "files": len(files) + 1,
        "pdf": pdf,
        "limitations": manifest["limitations"],
    }


def _storey(entity: dict[str, Any], entities: dict[str, Any]) -> str | None:
    return (
        entities[entity["wall"]]["storey"] if entity["kind"] == "opening" else entity.get("storey")
    )


def _cabinet_local_meshes(meshes: list[dict], cabinet: dict[str, Any]) -> list[dict]:
    angle = -math.radians(cabinet.get("properties", {}).get("rotation_deg", 0))
    origin = cabinet["origin"]
    result = []
    for mesh in meshes:
        vertices = []
        for point in mesh["vertices"]:
            x, y = point[0] - origin[0], point[1] - origin[1]
            vertices.append(
                [
                    x * math.cos(angle) - y * math.sin(angle),
                    x * math.sin(angle) + y * math.cos(angle),
                    point[2] - origin[2],
                ]
            )
        result.append({**mesh, "vertices": vertices})
    return result


def _issue(document: dict[str, Any]) -> dict[str, str]:
    values = document["project"].get("facts", {}).get("drawing", {})
    fields = (
        "project_number",
        "issue",
        "issue_date",
        "status",
        "drawn_by",
        "checked_by",
        "site",
        "client",
    )
    return {
        key: str(values[key])[:160] if values.get(key) is not None else "NOT SET" for key in fields
    }


def _marks(document: dict[str, Any]) -> dict[str, str]:
    counts = {"D": 0, "W": 0, "C": 0, "V": 0, "F": 0}
    result = {}
    for identifier, entity in sorted(document["entities"].items()):
        prefix = (
            "C"
            if entity["kind"] == "cabinet"
            else "F"
            if entity["kind"] == "slab_opening"
            else "V"
            if entity["kind"] == "virtual_boundary"
            else {"door": "D", "window": "W", "void": "V"}.get(entity.get("fill"))
        )
        if prefix:
            counts[prefix] += 1
            result[identifier] = f"{prefix}{counts[prefix]:02d}"
    return result


def _object_schedule(document: dict[str, Any]) -> list[dict[str, str]]:
    entities, marks = document["entities"], _marks(document)
    result = []
    for identifier, mark in marks.items():
        entity = entities[identifier]
        row = {"id": identifier, "mark": mark, "identity": f"{mark} {entity['name']}"}
        if entity["kind"] == "opening":
            wall = entities[entity["wall"]]
            level = entities[wall["storey"]]
            assembly = entity.get("properties", {}).get("assembly", {})
            row["size"] = f"W{entity['width']:g} x H{entity['height']:g}"
            row["levels"] = (
                f"FFL{level['elevation']:g} / S{wall.get('base_offset', 0) + entity['sill']:g} / "
                f"H{wall.get('base_offset', 0) + entity['sill'] + entity['height']:g}"
            )
            type_id = entity.get("properties", {}).get("bim", {}).get("type_id", "type NOT SET")
            operation = assembly.get("operation", "operation NOT SET")
            row["spec"] = f"{type_id} / {operation}"
        elif entity["kind"] == "virtual_boundary":
            row["size"] = f"W{math.dist(entity['start'], entity['end']):g} x H{entity['height']:g}"
            row["levels"] = (
                f"Base Z{entities[entity['storey']]['elevation'] + entity.get('base_offset', 0):g}"
            )
            row["spec"] = "Nonphysical reference / fill unmodelled"
        elif entity["kind"] == "slab_opening":
            slab = entities[entity["slab"]]
            level = entities[slab["storey"]]
            row["size"] = f"Area {abs(_area(entity['polygon'])) / 1e6:.3f} m²"
            row["levels"] = (
                f"Top Z{level['elevation'] + slab.get('base_offset', 0):g}; "
                f"through {slab['thickness']:g} mm"
            )
            row["spec"] = f"Floor void / host {slab['name']}"
        else:
            row["size"] = f"W{entity['width']:g} x D{entity['depth']:g} x H{entity['height']:g}"
            row["levels"] = f"Base Z{entity['origin'][2]:g}"
            row["spec"] = f"{entity.get('material', 'material NOT SET')}"
        result.append(row)
    return result


def _opening_view_marks(view: dict[str, Any], document: dict[str, Any], camera: str) -> None:
    from .view_geometry import project

    entities, marks = document["entities"], _marks(document)
    visible = {segment["id"] for segment in view["segments"]}
    view["opening_marks"] = []
    for identifier in sorted(visible):
        entity = entities[identifier]
        if entity["kind"] != "opening":
            continue
        wall = entities[entity["wall"]]
        length = math.dist(wall["start"], wall["end"])
        t = (entity["offset"] + entity["width"] / 2) / length
        point = [wall["start"][i] + t * (wall["end"][i] - wall["start"][i]) for i in range(2)]
        base = wall.get("base_offset", 0)
        point.append(
            entities[wall["storey"]]["elevation"] + base + entity["sill"] + entity["height"] / 2
        )
        view["opening_marks"].append(
            {
                "id": identifier,
                "mark": marks[identifier],
                "anchor": project(point, camera)[:2],
                "sill_mm": base + entity["sill"],
                "head_mm": base + entity["sill"] + entity["height"],
            }
        )


def _section_markers(view: dict[str, Any], sections: list[dict]) -> list[dict]:
    result = []
    low, high = view["bounds"]["min"], view["bounds"]["max"]
    for section in sections:
        value = section["coordinate_mm"]
        if section["axis"] == "x" and low[0] <= value <= high[0]:
            points = [[value, low[1]], [value, high[1]]]
        elif section["axis"] == "y" and low[1] <= value <= high[1]:
            points = [[low[0], value], [high[0], value]]
        else:
            continue
        result.append(
            {
                "id": section["id"],
                "points": points,
                "direction": section.get("direction", "positive"),
            }
        )
    return result


def _slab_opening_dimensions(document: dict[str, Any], storey: str) -> list[dict]:
    rows = []
    entities = document["entities"]
    for entity in entities.values():
        if entity["kind"] != "slab_opening" or entities[entity["slab"]]["storey"] != storey:
            continue
        polygon = entity["polygon"]
        sign = 1 if _area(polygon) > 0 else -1
        for a, b in zip(polygon, polygon[1:] + polygon[:1], strict=True):
            length = math.dist(a, b)
            rows.append(
                {
                    "id": entity["id"],
                    "a": a,
                    "b": b,
                    "value_mm": length,
                    "normal": [sign * (b[1] - a[1]) / length, -sign * (b[0] - a[0]) / length],
                    "offset_paper_mm": 4.0,
                    "basis": "authored slab opening boundary",
                }
            )
    return rows


def _wall_dimensions(document: dict[str, Any], storey: str) -> list[dict]:
    entities = document["entities"]
    walls = [e for e in entities.values() if e["kind"] == "wall" and e["storey"] == storey]
    points = [p for wall in walls for p in (wall["start"], wall["end"])]
    if not points:
        return []
    centre = [(min(p[i] for p in points) + max(p[i] for p in points)) / 2 for i in range(2)]
    result = []
    for wall in walls:
        if wall.get("properties", {}).get("is_external") is not True:
            continue
        a, b = wall["start"], wall["end"]
        length = math.dist(a, b)
        u = [(b[i] - a[i]) / length for i in range(2)]
        normal = [-u[1], u[0]]
        if sum(normal[i] * ((a[i] + b[i]) / 2 - centre[i]) for i in range(2)) < 0:
            normal = [-v for v in normal]
        positions = {0.0, length}
        for opening in entities.values():
            if opening["kind"] == "opening" and opening["wall"] == wall["id"]:
                positions.update([opening["offset"], opening["offset"] + opening["width"]])
        locations = sorted(positions)
        for start, end in itertools.pairwise(locations):
            result.append(
                {
                    "id": wall["id"],
                    "a": [a[i] + start * u[i] for i in range(2)],
                    "b": [a[i] + end * u[i] for i in range(2)],
                    "value_mm": end - start,
                    "offset_paper_mm": 7.0,
                    "normal": normal,
                    "basis": "host centreline and rough-opening jambs",
                }
            )
        result.append(
            {
                "id": wall["id"],
                "a": a,
                "b": b,
                "value_mm": length,
                "offset_paper_mm": 14.0,
                "normal": normal,
                "basis": "overall host centreline",
            }
        )
    return result


def _level_callouts(view: dict[str, Any]) -> list[dict]:
    """Distribute complete level text; each leader still touches its true world Z.

    Isotonic placement minimizes vertical shifts subject to disjoint text blocks.
    A narrow margin wraps the full label rather than shrinking or losing values.
    Global levels outside the view are explicitly listed without fictitious
    ticks or leaders. Physical geometry, scale and in-view elevations are unchanged.
    """
    import textwrap

    marks = view.get("level_marks", [])
    if not marks:
        return []
    _, paper = _layout(view)
    left, bottom = paper(view["bounds"]["min"])
    _, drawing_top = paper(view["bounds"]["max"])
    right = left - 21
    available = right - 13
    font, leading, gap = 2.3, 2.875, 2.0
    keyed = available < 30
    if keyed:
        # Wide elevations may leave no full-text side column. Keep the geometry
        # at its original scale and use linked Lnn marks plus a complete text key
        # in free paper above/below the physical viewport.
        right = max(left - 12, 13 + 3 * font * 0.8)
        available = right - 13
    entries = []
    for mark in marks:
        _, y = paper([view["bounds"]["min"][0], mark["z_mm"]])
        outside = not (
            view["bounds"]["min"][1] - 1e-7 <= mark["z_mm"] <= view["bounds"]["max"][1] + 1e-7
            and 47 <= y <= 262
        )
        label = ("Outside view: " if outside else "") + mark["label"]
        lines = [""] if keyed else textwrap.wrap(label, width=max(1, int(available / (font * 0.8))))
        height = font + (len(lines) - 1) * leading
        desired_top = y - 2 - height
        if outside:
            desired_top = min(258 - height, max(50, desired_top))
        entries.append(
            {
                "mark": mark,
                "anchor": [left - 8, y],
                "lines": lines,
                "height": height,
                "desired_top": desired_top,
                "outside_view": outside,
                "reference_label": label,
            }
        )
    entries.sort(key=lambda row: row["anchor"][1])
    if keyed:
        for index, row in enumerate(entries, 1):
            row["lines"] = [f"L{index:02d}"]
            row["key_lines"] = textwrap.wrap(f"L{index:02d} {row['reference_label']}", width=88)
        key_height = sum(len(row["key_lines"]) * leading + gap for row in entries)
        key_top = bottom + 18
        if key_top + key_height > 258:
            key_top = drawing_top - 12 - key_height
        if key_top < 52 or key_top + key_height > 258:
            raise TeeError(
                "architecture_annotation_crowding",
                "Complete level key cannot fit outside the view.",
                fix="Use a smaller named view or separate level schedule; none were omitted.",
            )
        for row in entries:
            row["key_baselines"] = [key_top + i * leading for i in range(len(row["key_lines"]))]
            key_top += len(row["key_lines"]) * leading + gap
    blocks, offset = [], 0.0
    for index, row in enumerate(entries):
        row["offset"] = offset
        blocks.append({"indices": [index], "value": row["desired_top"] - offset})
        while len(blocks) > 1 and blocks[-2]["value"] > blocks[-1]["value"]:
            b, a = blocks.pop(), blocks.pop()
            count = len(a["indices"]) + len(b["indices"])
            blocks.append(
                {
                    "indices": a["indices"] + b["indices"],
                    "value": (a["value"] * len(a["indices"]) + b["value"] * len(b["indices"]))
                    / count,
                }
            )
        offset += row["height"] + gap
    for block in blocks:
        for index in block["indices"]:
            entries[index]["top"] = block["value"] + entries[index]["offset"]
    span = entries[-1]["top"] + entries[-1]["height"] - entries[0]["top"]
    if span > 208:
        raise TeeError(
            "architecture_annotation_crowding",
            "Complete level labels exceed the sheet margin.",
            fix="Split the requested levels across named views; no level text was omitted.",
        )
    shift = max(0, 50 - entries[0]["top"])
    shift -= max(0, entries[-1]["top"] + entries[-1]["height"] + shift - 258)
    result = []
    for row in entries:
        top = row["top"] + shift
        middle = top + row["height"] / 2
        width = max(len(value) for value in row["lines"]) * font * 0.8
        result.append(
            {
                "id": row["mark"]["id"],
                "label": row["mark"]["label"],
                "z_mm": row["mark"]["z_mm"],
                "anchor_mm": None if row["outside_view"] else row["anchor"],
                "outside_view": row["outside_view"],
                "lines": [] if keyed and row["outside_view"] else row["lines"],
                "font_mm": font,
                "box_mm": [right - width, top, right, top + row["height"]],
                "baselines_mm": []
                if keyed and row["outside_view"]
                else [top + font + i * leading for i in range(len(row["lines"]))],
                "leader_mm": []
                if row["outside_view"]
                else [[right + 1, middle], row["anchor"]]
                if keyed
                else [[right + 2, middle], [left - 11, middle], row["anchor"]],
                **(
                    {"key_lines": row["key_lines"], "key_baselines_mm": row["key_baselines"]}
                    if keyed
                    else {}
                ),
            }
        )
    return result


def _overall_height_text(view: dict[str, Any], callouts: list[dict] | None = None) -> dict | None:
    """Place the measured height value clear of exact level ticks and leaders.

    The dimension endpoints and model viewport do not move. SVG, PDF and the
    GUI consume this paper primitive; DXF uses its location for the measured
    DIMENSION text. Roof height often puts the midpoint next to wall-head levels.
    """
    if not _overall_dimensions(view):
        return None
    _, paper = _layout(view)
    low, high = view["bounds"]["min"], view["bounds"]["max"]
    left, bottom = paper(low)
    _, top = paper(high)
    size = 2.5
    value = f"{high[1] - low[1]:g}"
    width = len(value) * size * 0.8
    x, desired = max(13, left - 18), (top + bottom) / 2
    callouts = _level_callouts(view) if callouts is None else callouts
    occupied = [row["box_mm"] for row in callouts if row["lines"]]
    geometry = [list(line) for row in callouts for line in pairwise(row["leader_mm"])]
    for row in callouts:
        if row["anchor_mm"] is not None:
            _, y = row["anchor_mm"]
            geometry.extend(
                [
                    [[left - 8, y], [left - 1, y]],
                    [[left - 5, y], [left - 3, y - 1.5]],
                    [[left - 3, y - 1.5], [left - 1, y]],
                ]
            )
    for delta in [0, *[sign * step for step in range(4, 213, 4) for sign in (-1, 1)]]:
        baseline = desired + delta
        box = [x - 1, baseline - size - 1, x + width + 1, baseline + 1]
        if box[1] < 48 or box[3] > 262:
            continue
        if any(_box_overlap(box, prior) for prior in occupied):
            continue
        if any(_segment_box(line, box) for line in geometry):
            continue
        return {
            "type": "text",
            "role": "overall-height-text",
            "at": [x, baseline],
            "value": value,
            "size": size,
            "box_mm": box,
            "centre_mm": [x + width / 2, baseline - size / 2],
            "measurement_mm": high[1] - low[1],
        }
    raise TeeError(
        "architecture_annotation_crowding",
        "Overall height value cannot fit clear of complete level annotations.",
        fix="Use a smaller named view; no dimensions or level references were omitted.",
    )


def _sheet_graphics(view: dict[str, Any], *, detail: bool = True) -> list[dict]:
    """Shared paper-space datums, grain, dimension references and issue fields."""
    items = []
    _, paper = _layout(view)
    low, high = view["bounds"]["min"], view["bounds"]["max"]
    left, bottom = paper(low)
    right, top = paper(high)

    def line(a: list | tuple, b: list | tuple, role: str = "reference") -> None:
        items.append({"type": "line", "points": [a, b], "role": role})

    def text(x: float, y: float, value: str, size: float = 2.5) -> None:
        items.append({"type": "text", "at": [x, y], "value": value, "size": size})

    locator = view.get("scope_locator")
    if locator:
        bounds = locator["bounds"]
        low_xy = [min(bounds["min"][i], locator["scope_bounds_mm"][i]) for i in range(2)]
        high_xy = [max(bounds["max"][i], locator["scope_bounds_mm"][i + 2]) for i in range(2)]
        ratio = max((high_xy[0] - low_xy[0]) / 58, (high_xy[1] - low_xy[1]) / 31, 1)

        def locate(point: list[float]) -> list[float]:
            return [340 + (point[0] - low_xy[0]) / ratio, 246 - (point[1] - low_xy[1]) / ratio]

        for points in locator["lines"]:
            line(locate(points[0]), locate(points[1]), "scope-locator")
        xmin, ymin, xmax, ymax = locator["scope_bounds_mm"]
        corners = [[xmin, ymin], [xmax, ymin], [xmax, ymax], [xmin, ymax]]
        for a, b in zip(corners, corners[1:] + corners[:1], strict=True):
            line(locate(a), locate(b), "scope-crop")
        text(338, 252, f"{locator['id']} / key plan", 2.5)
        text(338, 256, "Wall centrelines / not to scale", 2.0)

    callouts = _level_callouts(view)
    height_text = _overall_height_text(view, callouts)
    if height_text:
        items.append(height_text)
    for callout in callouts:
        if callout["anchor_mm"] is not None:
            _, y = callout["anchor_mm"]
            line([left - 8, y], [left - 1, y], "level-tick")
            line([left - 5, y], [left - 3, y - 1.5], "level-tick")
            line([left - 3, y - 1.5], [left - 1, y], "level-tick")
        for a, b in pairwise(callout["leader_mm"]):
            line(a, b, "level-leader")
        for baseline, value in zip(callout["baselines_mm"], callout["lines"], strict=True):
            text(callout["box_mm"][2], baseline, value, callout["font_mm"])
            items[-1].update(
                role="level-text",
                align="right",
                id=callout["id"],
                z_mm=callout["z_mm"],
                outside_view=callout["outside_view"],
            )
        for baseline, value in zip(
            callout.get("key_baselines_mm", []), callout.get("key_lines", []), strict=True
        ):
            text(16, baseline, value, callout["font_mm"])
            items[-1].update(
                role="level-key",
                id=callout["id"],
                z_mm=callout["z_mm"],
                outside_view=callout["outside_view"],
            )
    if view.get("working_dimensions"):
        from .dimension_layout import dimension_graphics

        items += dimension_graphics(
            _dimension_rows(view),
            paper,
            view["segments"],
            [[333, 208, 404, 260], [331, 49, 404, 201]],
        )
        setting = view["setting_out"]
        if len(setting["vertices"]) > 32:
            raise TeeError(
                "architecture_setting_out_limit",
                "Room setting-out table exceeds 32 vertices.",
                fix="Use named scopes for individual room parts; full model data is retained.",
            )
        text(334, 56, "BOUNDARY SETTING-OUT / mm", 2.4)
        text(334, 61, "Point          X                 Y", 2.2)
        for index, vertex in enumerate(setting["vertices"]):
            y = 66 + index * 4
            text(334, y, vertex["mark"], 2.2)
            text(349, y, f"{vertex['xy_mm'][0]:.3f}".rstrip("0").rstrip("."), 2.2)
            text(377, y, f"{vertex['xy_mm'][1]:.3f}".rstrip("0").rstrip("."), 2.2)
        y = 71 + len(setting["vertices"]) * 4
        text(334, y, f"Base Z {setting['base_world_mm']:g}", 2.2)
        text(334, y + 5, "Authored boundary; finishes", 2.1)
        text(334, y + 9, "and survey control unverified.", 2.1)
    for dimension in [] if view.get("working_dimensions") else _dimension_rows(view):
        a, b = [list(paper(dimension[key])) for key in ("a", "b")]
        n = [dimension["normal"][0], -dimension["normal"][1]]
        offset = dimension["offset_paper_mm"]
        x, y = [[point[i] + n[i] * offset for i in range(2)] for point in (a, b)]
        line(x, y, "dimension")
        for point in (a, b):
            line(
                [point[i] + n[i] * 2 for i in range(2)],
                [point[i] + n[i] * (offset + 2) for i in range(2)],
                "dimension",
            )
        text(
            (x[0] + y[0]) / 2 + n[0] * 1.5 - 2,
            (x[1] + y[1]) / 2 + n[1] * 1.5 - 0.8,
            f"{dimension['value_mm']:g}",
            2.4,
        )
        items[-1]["role"] = "dimension-text"
    for row in view.get("opening_marks", []):
        x, y = paper(row["anchor"])
        text(x - 3, y - 4, row["mark"], 2.6)
        text(x - 7, y, f"S {row['sill_mm'] / 1000:+.3f}", 2.1)
        text(x - 7, y + 3, f"H {row['head_mm'] / 1000:+.3f}", 2.1)
    for marker in view.get("section_markers", []):
        a, b = [paper(p) for p in marker["points"]]
        line(a, b, "section-marker")
        for x, y in (a, b):
            text(x - 3, y - 2, marker["id"] + "-" + marker["id"], 2.8)
            items[-1]["role"] = "section-marker-text"
    panel = view.get("panel")
    if panel:
        x, y = paper([(low[0] + high[0]) / 2, (low[1] + high[1]) / 2])
        horizontal = panel["grain"] == "width"
        if panel["grain"] != "none":
            half = min(6, (right - left if horizontal else bottom - top) * 0.3)
            start, end = (
                ([x - half, y], [x + half, y]) if horizontal else ([x, y + half], [x, y - half])
            )
            line(start, end, "grain")
            if horizontal:
                line([end[0] - 2, y - 1], end, "grain")
                line([end[0] - 2, y + 1], end, "grain")
            else:
                line([x - 1, end[1] + 2], end, "grain")
                line([x + 1, end[1] + 2], end, "grain")
        text(left - 7, bottom + 2, "0,0", 2)
    if detail:
        x, y = view.get("detail_origin", [16, 244])
        for index, value in enumerate(view.get("detail_lines", [])):
            text(x, y + index * 3.2, value[:150], 2.3)
    return items


def _line_style(segment: dict[str, Any]) -> tuple[str, float, str | None]:
    role = segment.get("role", "context")
    return {
        "cut": ("#182b38", 0.50, None),
        "symbol": ("#365e78", 0.20, None),
        "machining": ("#9b4533", 0.25, None),
        "blank": ("#64727c", 0.18, "2 1"),
        "overhead": ("#64727c", 0.18, "2 1"),
        "reference": ("#64727c", 0.18, "4 2"),
        "roof": ("#455c68", 0.35, None),
        "grain": ("#64727c", 0.18, None),
    }.get(role, ("#3c505e", 0.18, None))


def _levels(view: dict[str, Any], entities: dict[str, Any]) -> None:
    view["level_marks"] = []
    for entity in entities.values():
        if entity["kind"] == "storey":
            heads = sorted(
                {
                    wall.get("base_offset", 0) + wall["height"]
                    for wall in entities.values()
                    if wall["kind"] == "wall" and wall["storey"] == entity["id"]
                }
            )
            for suffix, z in [
                ("FFL", entity["elevation"]),
                *[("wall head", entity["elevation"] + height) for height in heads],
            ]:
                view["level_marks"].append(
                    {
                        "id": entity["id"],
                        "z_mm": z,
                        "label": f"{entity['name']} {suffix} {z / 1000:+.3f} m",
                    }
                )


def _stair_overhead(document: dict[str, Any], storey: str, cut_z: float) -> list[dict]:
    """Show the true plan extent beyond the cut; never dimension a clipped fragment as a flight."""
    from .systems import stair_dimensions

    result = []
    for entity in document["entities"].values():
        if entity["kind"] != "stair" or storey not in {entity["storey"], entity["top_storey"]}:
            continue
        dims = stair_dimensions(entity, document["entities"])
        if cut_z >= dims["top_world_mm"]:
            continue
        start = max(
            0,
            min(
                dims["flight_run_mm"],
                (cut_z - dims["bottom_world_mm"] + dims["waist_vertical_mm"])
                / dims["riser_height_mm"]
                * entity["going"],
            ),
        )
        end, width = dims["flight_run_mm"] + entity["landing_depth"], entity["width"]
        c, s = (
            math.cos(math.radians(entity["direction_deg"])),
            math.sin(math.radians(entity["direction_deg"])),
        )
        points = [
            [entity["start"][0] + c * x - s * y, entity["start"][1] + s * x + c * y]
            for x, y in [(start, 0), (end, 0), (end, width), (start, width)]
        ]
        for a, b in pairwise(points):
            result.append(
                {
                    "id": entity["id"],
                    "kind": "stair",
                    "part": "overhead",
                    "role": "overhead",
                    "points": [a, b],
                }
            )
    return result


def _opening_symbols(document: dict[str, Any], storey: str, cut_z: float) -> list[dict]:
    """Plan conventions follow authored host coordinates and explicit operation."""
    result = []
    entities = document["entities"]
    for entity in entities.values():
        if entity["kind"] != "opening" or _storey(entity, entities) != storey:
            continue
        wall = entities[entity["wall"]]
        bottom = entities[storey]["elevation"] + wall.get("base_offset", 0) + entity["sill"]
        if not bottom <= cut_z <= bottom + entity["height"]:
            continue
        length = math.dist(wall["start"], wall["end"])
        u = [(wall["end"][i] - wall["start"][i]) / length for i in range(2)]
        n = [-u[1], u[0]]
        assembly = entity.get("properties", {}).get("assembly", {})

        def point(
            along: float,
            across: float = 0,
            *,
            wall: dict = wall,
            entity: dict = entity,
            u: list = u,
            n: list = n,
        ) -> list[float]:
            return [
                wall["start"][i] + (entity["offset"] + along) * u[i] + across * n[i]
                for i in range(2)
            ]

        def add(
            a: list[float], b: list[float], symbol: str, *, identifier: str = entity["id"]
        ) -> None:
            result.append(
                {
                    "id": identifier,
                    "kind": "opening",
                    "role": "symbol",
                    "symbol": symbol,
                    "points": [a, b],
                }
            )

        if entity["fill"] == "window" and not assembly:
            # Semantic glazing symbol, not an invented physical frame thickness.
            add(point(0), point(entity["width"]), "window-symbol-unmodelled-assembly")
        if entity["fill"] != "door" or assembly.get("operation") != "swing":
            continue
        if assembly.get("hinge") not in {"start", "end"} or assembly.get("swing_side") not in {
            "left",
            "right",
        }:
            continue
        frame = float(assembly.get("frame_width_mm", 0))
        gap = float(assembly.get("clearance_mm", 0))
        clear = entity["width"] - 2 * frame - 2 * gap
        if clear <= 0:
            continue
        at_start = assembly["hinge"] == "start"
        side = 1 if assembly["swing_side"] == "left" else -1
        across = (
            -wall["thickness"] / 2
            + float(assembly.get("reveal_mm", 0))
            + float(assembly.get("frame_depth_mm", 0)) / 2
        )
        hinge = point(frame + gap if at_start else entity["width"] - frame - gap, across)
        closed = u if at_start else [-v for v in u]
        opened = [side * v for v in n]
        tip = [hinge[i] + clear * opened[i] for i in range(2)]
        add(hinge, tip, "door-open-leaf")
        arc = [
            [
                hinge[i]
                + clear
                * (math.cos(t * math.pi / 2) * closed[i] + math.sin(t * math.pi / 2) * opened[i])
                for i in range(2)
            ]
            for t in [index / 24 for index in range(25)]
        ]
        for a, b in itertools.pairwise(arc):
            add(a, b, "door-swing")
    return result


def _panel_detail(view: dict[str, Any], panel: dict[str, Any]) -> None:
    fw, fh = panel["finished_width"], panel["finished_height"]
    edges = panel.get("edges", {})

    def rectangle(
        x: float, y: float, w: float, h: float, role: str, identifier: str | None = None
    ) -> list[dict]:
        polygon = [[x, y], [x + w, y], [x + w, y + h], [x, y + h]]
        return [
            {"id": identifier or panel["id"], "kind": "cabinet", "role": role, "points": [a, b]}
            for a, b in zip(polygon, polygon[1:] + polygon[:1], strict=False)
        ]

    view["segments"] = rectangle(0, 0, fw, fh, "context")
    left, bottom = float(edges.get("left", 0)), float(edges.get("bottom", 0))
    if panel["width"] != fw or panel["height"] != fh:
        view["segments"] += rectangle(left, bottom, panel["width"], panel["height"], "blank")
    view["bounds"] = {"min": [0, 0], "max": [fw, fh]}
    view["dimensions"] = [
        {"name": "finished_width", "value_mm": fw},
        {"name": "finished_height", "value_mm": fh},
        {"name": "cut_width", "value_mm": panel["width"]},
        {"name": "cut_height", "value_mm": panel["height"]},
    ]
    for operation in panel.get("machining", []):
        u, v = operation["u_mm"], operation["v_mm"]
        if operation["type"] == "drill":
            radius = operation["diameter_mm"] / 2
            points = [
                [u + radius * math.cos(i * math.tau / 32), v + radius * math.sin(i * math.tau / 32)]
                for i in range(33)
            ]
            view["segments"] += [
                {"id": operation["id"], "kind": "machining", "role": "machining", "points": [a, b]}
                for a, b in itertools.pairwise(points)
            ]
        elif operation["type"] == "pocket":
            view["segments"] += rectangle(
                u, v, operation["width_mm"], operation["height_mm"], "machining", operation["id"]
            )
    view["detail_lines"] = [
        f"Part {panel['id']} | {panel['role']} | thickness {panel['thickness']:g} mm",
        f"FINISHED {fw:g} x {fh:g} | CUT {panel['width']:g} x {panel['height']:g} mm",
        f"Material: {panel['material']}",
        "Edges mm: "
        + "; ".join(
            f"{edge}={edges.get(edge, 0):g}" for edge in ("left", "right", "top", "bottom")
        ),
        f"Grain: {panel['grain']} | datum lower left; U right, V up; front-view coordinates",
    ]
    if not panel.get("machining"):
        view["detail_lines"].append("Machining / hardware fixing: NOT SPECIFIED")
    for op in panel.get("machining", []):
        shape = (
            f"diameter {op['diameter_mm']:g}"
            if op["type"] == "drill"
            else f"{op['width_mm']:g} x {op['height_mm']:g}"
        )
        view["detail_lines"].append(
            f"{op['id']}: {op['face']} {op['type']} {shape}; U{op['u_mm']:g} "
            f"V{op['v_mm']:g} depth {op['depth_mm']:g} mm"
        )


def _box_overlap(a: list[float], b: list[float], margin: float = 1.0) -> bool:
    return not (
        a[2] + margin <= b[0]
        or b[2] + margin <= a[0]
        or a[3] + margin <= b[1]
        or b[3] + margin <= a[1]
    )


def _segment_box(points: list[list[float]], box: list[float]) -> bool:
    """Exact line/rectangle clipping, not a sampled collision check."""
    enter, leave = 0.0, 1.0
    a, b = points
    for axis in range(2):
        delta = b[axis] - a[axis]
        if abs(delta) < 1e-12:
            if not box[axis] <= a[axis] <= box[axis + 2]:
                return False
            continue
        first, last = sorted(((box[axis] - a[axis]) / delta, (box[axis + 2] - a[axis]) / delta))
        enter, leave = max(enter, first), min(leave, last)
        if enter > leave:
            return False
    return True


def _paper_inverse(view: dict[str, Any], point: list[float]) -> list[float]:
    scale, paper = _layout(view)
    low = view["bounds"]["min"]
    left, bottom = paper(low)
    return [low[0] + (point[0] - left) * scale, low[1] + (bottom - point[1]) * scale]


def _inside_polygon_box(view: dict[str, Any], polygon: list[list[float]], box: list[float]) -> bool:
    from .exchange import _intersection_area, _triangles

    a, b = _paper_inverse(view, box[:2]), _paper_inverse(view, box[2:])
    rectangle = [[a[0], b[1]], [b[0], b[1]], [b[0], a[1]], [a[0], a[1]]]
    expected = abs(_area(rectangle))
    covered = sum(
        _intersection_area(rectangle, [polygon[i] for i in triangle])
        for triangle in _triangles(polygon)
    )
    return abs(covered - expected) <= max(1e-5, expected * 1e-9)


def _annotation_requests(document: dict[str, Any], storey: str) -> list[dict]:
    from .exchange import _triangles

    entities = document["entities"]
    marks = _marks(document)
    # Default FULL, not marks. The `space` branch below emits its name and area
    # unconditionally, with no compact path at all, so a "marks" default made
    # plan annotations internally inconsistent: rooms carried full text while
    # the openings and cabinets beside them collapsed to W01/C01. Nothing in
    # the tree ever set `annotation_style` either - this line was its only
    # reader - so the compact branch was unreachable by configuration and
    # untested, while the only annotation test expects full text. The knob is
    # kept, so a caller can still ask for marks explicitly.
    compact = (
        document["project"].get("facts", {}).get("drawing", {}).get("annotation_style", "marks")
        != "full"
    )
    requests = []
    for identifier, entity in entities.items():
        kind = entity["kind"]
        if kind == "opening":
            wall = entities[entity["wall"]]
            if wall["storey"] != storey:
                continue
            length = math.dist(wall["start"], wall["end"])
            ux, uy = [(wall["end"][i] - wall["start"][i]) / length for i in range(2)]
            mid = entity["offset"] + entity["width"] / 2
            anchor = [wall["start"][0] + ux * mid, wall["start"][1] + uy * mid]
            lines = [
                f"{entity['name']} [{identifier}]",
                f"Opening W {entity['width']:g} x H {entity['height']:g} mm",
            ]
            if entity["fill"] == "window":
                lines.append(f"Sill {wall.get('base_offset', 0) + entity['sill']:g} mm above FFL")
            if compact:
                lines = [marks[identifier]]
            requests.append(
                {
                    "id": identifier,
                    "kind": kind,
                    "lines": lines,
                    "anchor": anchor,
                    "normal": [-uy, -ux],
                }
            )  # paper Y is inverted
        elif kind == "slab_opening" and entities[entity["slab"]]["storey"] == storey:
            from shapely.geometry import Polygon

            point = Polygon(entity["polygon"]).representative_point()
            requests.append(
                {
                    "id": identifier,
                    "kind": kind,
                    "lines": [f"{marks[identifier]} FLOOR VOID"]
                    if compact
                    else [
                        f"Floor void [{identifier}]",
                        f"{abs(_area(entity['polygon'])) / 1e6:.3f} m² through slab",
                    ],
                    "anchor": [point.x, point.y],
                    "normal": [0, -1],
                }
            )
        elif kind == "virtual_boundary" and entity["storey"] == storey:
            requests.append(
                {
                    "id": identifier,
                    "kind": kind,
                    "lines": [entity["name"], "Nonphysical reference", "Fill unmodelled"],
                    "anchor": [(entity["start"][i] + entity["end"][i]) / 2 for i in range(2)],
                    "normal": [0, -1],
                }
            )
        elif entity.get("storey") == storey and kind == "space":
            from .spatial import space_environment

            polygons = [entity["polygon"], *entity.get("additional_polygons", [])]
            polygon = entity["polygon"]
            triangles = [[part[i] for i in tri] for part in polygons for tri in _triangles(part)]
            centres = [
                [sum(p[i] for p in tri) / 3 for i in range(2)]
                for tri in sorted(triangles, key=lambda tri: abs(_area(tri)), reverse=True)
            ]
            total = sum(abs(_area(tri)) for tri in triangles)
            centroid = [
                sum(abs(_area(tri)) * sum(p[i] for p in tri) / 3 for tri in triangles) / total
                for i in range(2)
            ]
            requests.insert(
                0,
                {
                    "id": identifier,
                    "kind": kind,
                    "lines": [entity["name"], f"{total / 1e6:.2f} m²"]
                    + (["EXTERIOR"] if space_environment(entity) == "exterior" else []),
                    "centres": [centroid, *centres],
                    "polygon": polygon,
                    "polygons": polygons,
                },
            )
        elif entity.get("storey") == storey and kind == "cabinet":
            angle = math.radians(entity.get("properties", {}).get("rotation_deg", 0))
            c, sn = math.cos(angle), math.sin(angle)
            requests.append(
                {
                    "id": identifier,
                    "kind": kind,
                    "lines": [marks[identifier]]
                    if compact
                    else [
                        f"{entity['name']} [{identifier}]",
                        f"Cabinet {entity['width']:g} x {entity['depth']:g} x "
                        f"{entity['height']:g} mm",
                    ],
                    "anchor": [
                        entity["origin"][0] + entity["width"] / 2 * c - entity["depth"] / 2 * sn,
                        entity["origin"][1] + entity["width"] / 2 * sn + entity["depth"] / 2 * c,
                    ],
                    "normal": [-sn, -c],
                }
            )
    return requests


def _plan_annotations(
    view: dict[str, Any],
    document: dict[str, Any],
    storey: str,
    requests: list[dict] | None = None,
) -> None:
    import textwrap

    from .drawing_scopes import contains

    requests = _annotation_requests(document, storey) if requests is None else requests
    scope_bounds = (
        [*view["bounds"]["min"], *view["bounds"]["max"]]
        if view.get("scope_role") == "enlarged"
        else None
    )
    if len(requests) > 80:
        raise TeeError(
            "architecture_annotation_limit",
            "Plan exceeds 80 annotation blocks.",
            fix="Split the drawing scope into smaller documents/storeys.",
        )
    _, paper = _layout(view)
    left, bottom = paper(view["bounds"]["min"])
    right, top = paper(view["bounds"]["max"])
    occupied = (
        []
        if not _overall_dimensions(view)
        else [
            [left, bottom + 3, right, bottom + 11],
            [left - 26, (top + bottom) / 2 - 5, left + 1, (top + bottom) / 2 + 2],
        ]
    )
    if view.get("scope_locator"):
        occupied.append([333, 208, 404, 260])
    if view.get("working_dimensions"):
        occupied.append([331, 49, 404, 201])
    annotations = []
    leaders = []
    anchor_boxes = {
        request["id"]: [anchor[0] - 1, anchor[1] - 1, anchor[0] + 1, anchor[1] + 1]
        for request in requests
        if "anchor" in request
        for anchor in [list(paper(request["anchor"]))]
    }
    geometry = [[list(paper(point)) for point in segment["points"]] for segment in view["segments"]]
    for item in _sheet_graphics(view, detail=False):
        if item.get("role") in {"dimension", "dimension-leader", "section-marker"}:
            geometry.append([list(p) for p in item["points"]])
        elif item.get("role") in {"dimension-text", "section-marker-text", "overall-height-text"}:
            x, y = item["at"]
            occupied.append([x, y - item["size"], x + item["size"] * len(item["value"]), y + 1])
    for request in requests:
        lines = [part for line in request["lines"] for part in textwrap.wrap(line, width=28)]
        if len(lines) > 6:
            raise TeeError(
                "architecture_annotation_limit",
                f"Label {request['id']} exceeds six lines.",
                fix="Shorten its name or ID before exporting drawings.",
            )
        font = 3.0
        line_widths = [
            font * sum(1.0 if ord(c) > 255 or c in "WM@" else 0.8 for c in line) for line in lines
        ]
        width, height = max(line_widths) + 2, len(lines) * font * 1.25 + 2
        candidates = []
        external_centres = set()
        if request["kind"] == "space":
            candidates = [
                (list(paper(point)), point)
                for point in request["centres"]
                if scope_bounds is None or contains(scope_bounds, point)
            ]
            # Search additional placements, while acceptance remains exact
            # polygon containment and line/rectangle collision clipping below.
            for polygon in request["polygons"]:
                low_room = [min(p[i] for p in polygon) for i in range(2)]
                high_room = [max(p[i] for p in polygon) for i in range(2)]
                for ix in range(1, 10):
                    for iy in range(1, 10):
                        point = [
                            low_room[0] + (high_room[0] - low_room[0]) * ix / 10,
                            low_room[1] + (high_room[1] - low_room[1]) * iy / 10,
                        ]
                        if scope_bounds is None or contains(scope_bounds, point):
                            candidates.append((list(paper(point)), point))
            if view.get("scope_role") == "enlarged":
                # A narrow passage cannot contain a readable multiline name.
                # Enlarged views may use a leader from a verified interior point;
                # font size and complete text stay unchanged.
                from shapely.geometry import Point, Polygon

                polygons = [Polygon(polygon) for polygon in request["polygons"]]
                source = next(
                    point
                    for point in request["centres"]
                    if any(polygon.contains(Point(point)) for polygon in polygons)
                    and (scope_bounds is None or contains(scope_bounds, point))
                )
                anchor = list(paper(source))
                for offset in (20, 35, 50, 75, 100, 140):
                    for dx, dy in (
                        (1, 0),
                        (-1, 0),
                        (0, 1),
                        (0, -1),
                        (1, 1),
                        (-1, 1),
                        (1, -1),
                        (-1, -1),
                    ):
                        centre = [anchor[0] + dx * offset, anchor[1] + dy * offset]
                        candidates.append((centre, source))
                        external_centres.add(tuple(centre))
        else:
            normal = request["normal"]
            centre = [(left + right) / 2, (top + bottom) / 2]
            for source in request.get("anchors", [request["anchor"]]):
                anchor = list(paper(source))
                outward = (
                    1 if sum(normal[i] * (anchor[i] - centre[i]) for i in range(2)) >= 0 else -1
                )
                for sign in (outward, -outward):
                    for offset in (14, 20, 28, 38, 50):
                        for lateral in (0, 20, -20, 40, -40, 60, -60):
                            candidates.append(
                                (
                                    [
                                        anchor[0] + sign * offset * normal[0] + lateral * normal[1],
                                        anchor[1] + sign * offset * normal[1] - lateral * normal[0],
                                    ],
                                    source,
                                )
                            )
        if view.get("scope_role") == "enlarged" or view.get("annotation_search") == "sheet":
            source = (
                next(point for centre, point in candidates if tuple(centre) in external_centres)
                if request["kind"] == "space"
                else request["anchor"]
            )
            anchor = list(paper(source))
            # Deterministic free-paper search after preferred local positions.
            # Exact box/line and leader/label checks still decide acceptance.
            free = [
                [20 + width / 2 + ix * 12, 54 + height / 2 + iy * 12]
                for ix in range(max(0, int((376 - width) / 12) + 1))
                for iy in range(max(0, int((201 - height) / 12) + 1))
            ]
            for centre in sorted(free, key=lambda point: math.dist(point, anchor)):
                candidates.append((centre, source))
                if request["kind"] == "space":
                    external_centres.add(tuple(centre))
        selected = None
        for centre, source in candidates:
            box = [
                centre[0] - width / 2,
                centre[1] - height / 2,
                centre[0] + width / 2,
                centre[1] + height / 2,
            ]
            if box[0] < 13 or box[1] < 47 or box[2] > 403 or box[3] > 262:
                continue
            if any(_box_overlap(box, prior) for prior in occupied):
                continue
            if any(
                _box_overlap(box, reserve)
                for identifier, reserve in anchor_boxes.items()
                if identifier != request["id"]
            ):
                continue
            external_space = tuple(centre) in external_centres
            if (
                request["kind"] == "space"
                and not external_space
                and scope_bounds
                and not all(
                    contains(scope_bounds, _paper_inverse(view, point))
                    for point in (box[:2], box[2:])
                )
            ):
                continue
            if (
                request["kind"] == "space"
                and not external_space
                and not any(
                    _inside_polygon_box(view, polygon, box) for polygon in request["polygons"]
                )
            ):
                continue
            if any(_segment_box(line, box) for line in geometry + leaders):
                continue
            leader = None
            if request["kind"] != "space" or external_space:
                anchor = list(paper(source))
                edge = [max(box[i], min(anchor[i], box[i + 2])) for i in range(2)]
                leader = [anchor, edge]
                if any(_segment_box(leader, prior) for prior in occupied):
                    continue
            selected = {
                "id": request["id"],
                "kind": request["kind"],
                "revision": view["revision"],
                "lines": lines,
                "font_mm": font,
                "line_widths_mm": line_widths,
                "box_mm": box,
                "anchor_mm": source,
                "leader_mm": leader,
                "placement": "leader" if leader else "interior",
                **(
                    {"source_entity_id": request["source_entity_id"]}
                    if "source_entity_id" in request
                    else {}
                ),
                **({"space_parts": len(request["polygons"])} if request["kind"] == "space" else {}),
            }
            break
        if selected is None:
            raise TeeError(
                "architecture_annotation_crowding",
                f"Cannot place {request['id']} without a label/line collision.",
                fix="Set drawing.plan_scope_mode='rooms' or use explicit plan_scopes; "
                "no annotations were omitted.",
            )
        annotations.append(selected)
        occupied.append(selected["box_mm"])
        if selected["leader_mm"]:
            leaders.append(selected["leader_mm"])
    view["annotations"] = annotations


def _annotation_svg(view: dict[str, Any]) -> list[str]:
    result = []
    for label in view.get("annotations", []):
        left, top, right, bottom = label["box_mm"]
        if label["leader_mm"]:
            a, b = label["leader_mm"]
            result.append(
                f'<line x1="{a[0]}" y1="{a[1]}" x2="{b[0]}" y2="{b[1]}" '
                'stroke="#36556b" stroke-width="0.2"/>'
            )
        result.append(
            f'<g data-label="{html.escape(label["id"], quote=True)}">'
            f'<rect x="{left}" y="{top}" width="{right - left}" '
            f'height="{bottom - top}" fill="white"/>'
        )
        for index, line in enumerate(label["lines"]):
            baseline = top + 1 + label["font_mm"] * (1 + index * 1.25)
            result.append(
                f'<text x="{left + 1}" y="{baseline}" font-family="sans-serif" '
                f'font-size="{label["font_mm"]}" fill="#16384c">{html.escape(line)}</text>'
            )
        result.append("</g>")
    return result


def _annotation_dxf(view: dict[str, Any], msp: Any) -> None:
    scale, _ = _layout(view)
    for label in view.get("annotations", []):
        if label["leader_mm"]:
            a, b = [_paper_inverse(view, point) for point in label["leader_mm"]]
            msp.add_line(a, b)
        left, top, _, _ = label["box_mm"]
        for index, line in enumerate(label["lines"]):
            baseline = top + 1 + label["font_mm"] * (1 + index * 1.25)
            entity = msp.add_text(line, dxfattribs={"height": label["font_mm"] * scale})
            entity.set_placement(_paper_inverse(view, [left + 1, baseline]))
            entity.set_xdata("TEE_ARCHITECTURE", [(1000, label["id"]), (1071, label["revision"])])


def _annotation_pdf(pdf: Any, view: dict[str, Any], family: str, text: Any) -> None:
    for label in view.get("annotations", []):
        left, top, right, bottom = label["box_mm"]
        if label["leader_mm"]:
            a, b = label["leader_mm"]
            pdf.set_draw_color(54, 85, 107)
            pdf.line(*a, *b)
        pdf.set_fill_color(255, 255, 255)
        pdf.rect(left, top, right - left, bottom - top, style="F")
        pdf.set_text_color(22, 56, 76)
        pdf.set_font(family, size=label["font_mm"] * 72 / 25.4)
        for index, line in enumerate(label["lines"]):
            baseline = top + 1 + label["font_mm"] * (1 + index * 1.25)
            pdf.text(left + 1, baseline, text(line))
    pdf.set_text_color(0, 0, 0)
