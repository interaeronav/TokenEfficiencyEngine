"""Documents & CAD lane (7.2) - deterministic first, zero tokens.

DXF via ezdxf (DIMENSION.get_measurement() is dimensional ground truth),
vector PDF via pdfplumber (dimension strings + the scale-inference ladder),
raster pages via pypdfium2 + tesseract OCR. Sheet classification is
metadata-first (NCS sheet numbers). See docs/research/11 and 17.
"""

from __future__ import annotations

import itertools
import math
import re
from collections import defaultdict
from pathlib import Path
from typing import Any

from tee.extract.plan import empty_plan, validate_plan
from tee.kernel.errors import TeeError

DXF_EXTRACTOR = ("dxf", "1")
PDF_EXTRACTOR = ("pdf", "1")

# $INSUNITS -> meters per drawing unit (0 = unitless -> calibration needed)
INSUNITS_TO_M = {1: 0.0254, 2: 0.3048, 4: 0.001, 5: 0.01, 6: 1.0, 7: 1000.0, 10: 0.9144, 14: 0.1}

_NCS_CLASS = {"1": "plan", "2": "elevation", "3": "section", "5": "detail"}
_SHEET_RE = re.compile(r"\bA[- ]?(\d)\d{2}\b", re.IGNORECASE)
_KEYWORDS = (
    ("floor plan", "plan"),
    ("site plan", "plan"),
    ("elevation", "elevation"),
    ("section", "section"),
    ("detail", "detail"),
)
# dimension strings: metric mm/cm/m and unadorned mm-style integers
_DIM_RE = re.compile(r"^\s*(\d{1,6}(?:[.,]\d{1,3})?)\s*(mm|cm|m)?\s*$")

_DEFAULT_WALL_HEIGHT = 2.7
_DEFAULT_WALL_THICKNESS = 0.2


def classify_sheet(name: str, text: str) -> dict[str, Any]:
    """Metadata-first sheet classification (research 17): NCS sheet number
    digit, then title keywords; 'unknown' rather than a guess."""
    match = _SHEET_RE.search(name) or _SHEET_RE.search(text[:2000])
    if match and match.group(1) in _NCS_CLASS:
        return {"kind": "sheet", "class": _NCS_CLASS[match.group(1)], "method": "ncs_number"}
    lowered = text[:4000].lower()
    for needle, cls in _KEYWORDS:
        if needle in lowered:
            return {"kind": "sheet", "class": cls, "method": "title_keyword"}
    return {"kind": "sheet", "class": "unknown", "method": "none"}


def parse_dimension_text(text: str) -> float | None:
    """'4200'/'4200 mm'/'4.2 m' -> meters; bare numbers >= 100 read as mm
    (drawing convention), smaller bare numbers are ambiguous -> None."""
    match = _DIM_RE.match(text)
    if not match:
        return None
    value = float(match.group(1).replace(",", "."))
    unit = match.group(2)
    if unit == "mm":
        return value / 1000.0
    if unit == "cm":
        return value / 100.0
    if unit == "m":
        return value
    return value / 1000.0 if value >= 100 else None


# -- DXF ---------------------------------------------------------------------


def extract_dxf(path: Path, frame: str) -> list[dict[str, Any]]:
    import ezdxf

    try:
        doc = ezdxf.readfile(str(path))
    except (OSError, ezdxf.DXFStructureError) as exc:
        raise TeeError("bad_dxf", f"Cannot parse DXF: {exc}") from exc
    msp = doc.modelspace()
    facts: list[dict[str, Any]] = []

    insunits = int(doc.header.get("$INSUNITS", 0))
    meters_per_unit = INSUNITS_TO_M.get(insunits)
    facts.append(
        {
            "kind": "units",
            "frame": frame,
            "insunits": insunits,
            "meters_per_unit": meters_per_unit,
            "calibration_needed": meters_per_unit is None,
        }
    )
    if meters_per_unit is None:
        # unitless drawing: record the question instead of guessing (7.2)
        facts.append(
            {
                "kind": "question",
                "frame": frame,
                "question": "DXF has $INSUNITS=0 (unitless). What is one drawing "
                "unit in millimeters? (typical: 1 unit = 1 mm)",
                "assumption": {"meters_per_unit": 0.001, "confidence": "assumed"},
            }
        )
        meters_per_unit = 0.001
    scale = meters_per_unit

    # ground-truth dimensions
    for dim in msp.query("DIMENSION"):
        try:
            measurement = dim.get_measurement()
        except Exception:
            continue
        if isinstance(measurement, (int, float)):
            facts.append(
                {
                    "kind": "dimension",
                    "frame": frame,
                    "tier": "dimension_text",
                    "value_m": round(float(measurement) * scale, 4),
                    "dimtype": int(dim.dxf.dimtype) & 7,
                    "layer": dim.dxf.layer,
                }
            )

    plan = empty_plan(frame)
    plan["levels"] = [
        {
            "index": 0,
            "name": "Level 0",
            "elevation_z": 0.0,
            "floor_to_floor": None,
            "ceiling_height": _DEFAULT_WALL_HEIGHT,
            "plate_height": None,
        }
    ]
    plan["scale"] = {"method": "insunits", "meters_per_unit": scale, "confidence": 0.9}

    wall_count = 0
    for pline in msp.query("LWPOLYLINE"):
        layer = pline.dxf.layer.upper()
        points = [(p[0] * scale, p[1] * scale) for p in pline.get_points("xy")]
        if "WALL" in layer:
            thickness = _DEFAULT_WALL_THICKNESS
            width = pline.dxf.get("const_width", 0)
            if width:
                thickness = float(width) * scale
            segments = list(itertools.pairwise(points))
            if pline.closed and len(points) > 2:
                segments.append((points[-1], points[0]))
            for a, b in segments:
                if math.hypot(b[0] - a[0], b[1] - a[1]) < 0.05:
                    continue
                wall_count += 1
                plan["walls"].append(
                    {
                        "id": f"w{wall_count}",
                        "level": 0,
                        "a": [round(a[0], 4), round(a[1], 4)],
                        "b": [round(b[0], 4), round(b[1], 4)],
                        "thickness": round(thickness, 3),
                        "height": _DEFAULT_WALL_HEIGHT,
                    }
                )
        elif "ROOM" in layer and pline.closed:
            plan["rooms"].append(
                {
                    "id": f"r{len(plan['rooms']) + 1}",
                    "level": 0,
                    "name": None,
                    "polygon": [[round(x, 4), round(y, 4)] for x, y in points],
                }
            )

    # room labels: TEXT/MTEXT inside room polygons
    labels = []
    for text in list(msp.query("TEXT")) + list(msp.query("MTEXT")):
        content = (text.dxf.get("text", "") or getattr(text, "text", "")).strip()
        insert = text.dxf.get("insert", None)
        if content and insert is not None:
            labels.append((content, (insert[0] * scale, insert[1] * scale)))
    for room in plan["rooms"]:
        for content, point in labels:
            if _point_in_polygon(point, room["polygon"]):
                room["name"] = content
                break

    for opening in _openings_from_layers(msp, scale, plan["walls"]):
        plan["openings"].append(opening)

    validate_plan(plan)
    facts.append({"kind": "plan", "frame": frame, "tier": "drawing_geometry", "plan": plan})
    return facts


def _openings_from_layers(msp, scale: float, walls: list[dict]) -> list[dict[str, Any]]:
    """Openings from POINT/INSERT entities on DOOR*/WINDOW* layers: snapped
    to the nearest wall as parametric t (FML convention)."""
    out: list[dict[str, Any]] = []
    for entity in msp:
        layer = entity.dxf.get("layer", "").upper()
        kind = "door" if "DOOR" in layer else "window" if "WINDOW" in layer else None
        if kind is None:
            continue
        # POINT carries `location`, INSERT carries `insert`; ezdxf raises on
        # attribute names foreign to the entity type, so probe with hasattr
        location = None
        for attr in ("insert", "location"):
            if entity.dxf.hasattr(attr):
                location = entity.dxf.get(attr)
                break
        if location is None:
            continue
        px, py = location[0] * scale, location[1] * scale
        best = None
        for wall in walls:
            t, dist = _project_to_segment((px, py), wall["a"], wall["b"])
            if 0.0 <= t <= 1.0 and (best is None or dist < best[1]):
                best = (wall["id"], dist, t)
        if best and best[1] < 0.5:
            out.append(
                {
                    "id": f"o{len(out) + 1}",
                    "wall": best[0],
                    "t": round(best[2], 3),
                    "width": 0.9 if kind == "door" else 1.2,
                    "kind": kind,
                    "sill": 0.0 if kind == "door" else 0.9,
                    "head": 2.1,
                }
            )
    return out


# -- vector PDF --------------------------------------------------------------


def extract_pdf(path: Path, frame_prefix: str) -> list[dict[str, Any]]:
    import pdfplumber

    facts: list[dict[str, Any]] = []
    with pdfplumber.open(str(path)) as pdf:
        for number, page in enumerate(pdf.pages, 1):
            frame = f"{frame_prefix}:page{number}"
            words = page.extract_words()
            text = " ".join(w["text"] for w in words)
            is_vector = _is_vector_page(page)
            facts.append({"kind": "page", "frame": frame, "index": number, "vector": is_vector})
            facts.append({**classify_sheet(path.name, text), "frame": frame})
            if is_vector:
                facts.extend(_extract_vector_page(page, frame))
            else:
                facts.extend(_extract_raster_page(page, frame))
    return facts


def _is_vector_page(page) -> bool:
    full_image = any(
        (img["x1"] - img["x0"]) * (img["bottom"] - img["top"])
        > 0.8 * float(page.width) * float(page.height)
        for img in page.images
    )
    return (len(page.lines) + len(page.rects)) >= 10 and not full_image


def _extract_vector_page(page, frame: str) -> list[dict[str, Any]]:
    facts: list[dict[str, Any]] = []
    words = page.extract_words()
    # pdfplumber's x0/y0/x1/y1 are already PDF-native (origin bottom-left,
    # y up) - exactly the plan convention, so no flip
    lines = [(ln["x0"], ln["y0"], ln["x1"], ln["y1"]) for ln in page.lines]

    # dimension strings paired with the nearest parallel line -> scale fit
    pairs: list[tuple[float, float]] = []  # (meters, points)
    for word in words:
        meters = parse_dimension_text(word["text"])
        if meters is None:
            continue
        cx = (word["x0"] + word["x1"]) / 2
        cy = page.height - (word["top"] + word["bottom"]) / 2
        line = _nearest_line((cx, cy), lines)
        if line is None:
            continue
        length_pts = math.hypot(line[2] - line[0], line[3] - line[1])
        if length_pts < 10:
            continue
        pairs.append((meters, length_pts))
        facts.append(
            {
                "kind": "dimension",
                "frame": frame,
                "tier": "dimension_text",
                "value_m": meters,
                "text": word["text"],
                "segment_pts": round(length_pts, 2),
            }
        )

    scale_fact = _fit_scale(pairs)
    if scale_fact is not None:
        scale_fact["frame"] = frame
        facts.append(scale_fact)
        meters_per_pt = scale_fact["meters_per_point"]
        walls = _walls_from_lines(lines, meters_per_pt)
        if walls:
            plan = empty_plan(frame)
            plan["levels"] = [
                {
                    "index": 0,
                    "name": "Level 0",
                    "elevation_z": 0.0,
                    "floor_to_floor": None,
                    "ceiling_height": _DEFAULT_WALL_HEIGHT,
                    "plate_height": None,
                }
            ]
            plan["scale"] = {
                "method": scale_fact["method"],
                "meters_per_point": meters_per_pt,
                "confidence": scale_fact["confidence"],
            }
            plan["walls"] = walls
            validate_plan(plan)
            facts.append({"kind": "plan", "frame": frame, "tier": "drawing_geometry", "plan": plan})
    return facts


def _extract_raster_page(page, frame: str) -> list[dict[str, Any]]:
    """Scanned page: OCR dimension strings (word boxes + confidence). Wall
    reconstruction from raster is out of core scope (research 11)."""
    facts: list[dict[str, Any]] = []
    try:
        import pytesseract

        image = page.to_image(resolution=200).original
        data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)
    except Exception as exc:
        facts.append({"kind": "note", "frame": frame, "note": f"OCR unavailable: {exc}"})
        return facts
    for text, conf in zip(data["text"], data["conf"], strict=False):
        meters = parse_dimension_text(text.strip()) if text.strip() else None
        if meters is not None and float(conf) > 40:
            facts.append(
                {
                    "kind": "dimension",
                    "frame": frame,
                    "tier": "dimension_text",
                    "value_m": meters,
                    "text": text.strip(),
                    "ocr_confidence": float(conf) / 100.0,
                }
            )
    return facts


def _fit_scale(pairs: list[tuple[float, float]]) -> dict[str, Any] | None:
    """Least-squares meters-per-point through the origin over (m, pts)
    pairs; the top rung of the scale ladder."""
    if len(pairs) < 2:
        return None
    num = sum(m * p for m, p in pairs)
    den = sum(p * p for m, p in pairs)
    if den <= 0:
        return None
    meters_per_pt = num / den
    residuals = [abs(m - meters_per_pt * p) for m, p in pairs]
    spread = max(residuals) if residuals else 0.0
    confidence = 0.9 if spread < 0.05 else 0.6 if spread < 0.25 else 0.3
    return {
        "kind": "scale",
        "method": "dimension_fit",
        "meters_per_point": round(meters_per_pt, 8),
        "pairs": len(pairs),
        "max_residual_m": round(spread, 4),
        "confidence": confidence,
    }


def _walls_from_lines(
    lines: list[tuple[float, float, float, float]], meters_per_pt: float
) -> list[dict[str, Any]]:
    """Axis-aligned wall reconstruction: parallel line pairs 0.05-0.5 m apart
    become centerline walls. Covers typical plan exports; angled walls are a
    VLM-pass concern."""
    horizontals: dict[float, list[tuple[float, float, float]]] = defaultdict(list)
    verticals: dict[float, list[tuple[float, float, float]]] = defaultdict(list)
    for x0, y0, x1, y1 in lines:
        length = math.hypot(x1 - x0, y1 - y0)
        if length * meters_per_pt < 0.4:
            continue
        if abs(y1 - y0) < 0.5:
            horizontals[round((y0 + y1) / 2, 1)].append((min(x0, x1), max(x0, x1), (y0 + y1) / 2))
        elif abs(x1 - x0) < 0.5:
            verticals[round((x0 + x1) / 2, 1)].append((min(y0, y1), max(y0, y1), (x0 + x1) / 2))

    walls: list[dict[str, Any]] = []

    def pair_up(groups, vertical: bool) -> None:
        keys = sorted(groups)
        used: set[float] = set()
        for i, k1 in enumerate(keys):
            if k1 in used:
                continue
            for k2 in keys[i + 1 :]:
                if k2 in used:
                    continue
                gap_m = abs(k2 - k1) * meters_per_pt
                if gap_m > 0.5:
                    break
                if gap_m < 0.05:
                    continue
                for lo1, hi1, pos1 in groups[k1]:
                    for lo2, hi2, pos2 in groups[k2]:
                        lo, hi = max(lo1, lo2), min(hi1, hi2)
                        if (hi - lo) * meters_per_pt < 0.4:
                            continue
                        center = (pos1 + pos2) / 2
                        a_pt, b_pt = (
                            ((center, lo), (center, hi))
                            if vertical
                            else ((lo, center), (hi, center))
                        )
                        walls.append(
                            {
                                "id": f"w{len(walls) + 1}",
                                "level": 0,
                                "a": [
                                    round(a_pt[0] * meters_per_pt, 4),
                                    round(a_pt[1] * meters_per_pt, 4),
                                ],
                                "b": [
                                    round(b_pt[0] * meters_per_pt, 4),
                                    round(b_pt[1] * meters_per_pt, 4),
                                ],
                                "thickness": round(gap_m, 3),
                                "height": _DEFAULT_WALL_HEIGHT,
                            }
                        )
                        used.add(k1)
                        used.add(k2)
                if k1 in used:
                    break

    pair_up(horizontals, vertical=False)
    pair_up(verticals, vertical=True)
    return walls


# -- shared geometry helpers -------------------------------------------------


def _nearest_line(point, lines):
    best, best_dist = None, 1e9
    for line in lines:
        mx, my = (line[0] + line[2]) / 2, (line[1] + line[3]) / 2
        dist = math.hypot(point[0] - mx, point[1] - my)
        if dist < best_dist:
            best, best_dist = line, dist
    return best if best_dist < 80 else None


def _project_to_segment(point, a, b) -> tuple[float, float]:
    ax, ay, bx, by = a[0], a[1], b[0], b[1]
    dx, dy = bx - ax, by - ay
    length_sq = dx * dx + dy * dy
    if length_sq == 0:
        return 0.0, math.hypot(point[0] - ax, point[1] - ay)
    t = ((point[0] - ax) * dx + (point[1] - ay) * dy) / length_sq
    px, py = ax + t * dx, ay + t * dy
    return t, math.hypot(point[0] - px, point[1] - py)


def _point_in_polygon(point, polygon) -> bool:
    x, y = point
    inside = False
    j = len(polygon) - 1
    for i in range(len(polygon)):
        xi, yi = polygon[i]
        xj, yj = polygon[j]
        if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / (yj - yi) + xi:
            inside = not inside
        j = i
    return inside
