"""A fake `adsk` for the Fusion adapter's hermetic tests (A69 P2).

`FakeFusionWire.execute()` EXECUTES the adapter's generated scripts against
this shim - the codegen runs for real in CI (syntax, control flow, the id
map, the unit boundary, the result protocol) with only Fusion's C++ world
faked. The shim speaks exactly the names doc 71 section 3 verified, in
Fusion's own units: centimetres inside, radians for angles, kilograms for
mass. Geometry is arithmetic: a rectangle or circle profile extruded by a
distance is a box or a cylinder whose volume is area x depth; a cut takes
volume from the last body, a join adds to it; a fillet touches nothing but
the timeline. The live `-m dcc` smoke runs the same contract against the
real add-in on the owner's Mac.

A70 (v2): sketch geometry is real objects - lines with shared end points,
circles with centres, points, the projected origin - and the constraints and
dimensions of doc 71 rows 40-42 act on them. The shim SOLVES RECTANGLES AND
CIRCLES ONLY (Law 10): a driving distance dimension moves a rectangle's far
side and re-sizes what was extruded from it, a diameter sets a radius, an
expression naming a user parameter follows it; a constraint the geometry
contradicts is refused (null) rather than solved, and the rectangle call
returns its four lines scrambled so a codegen that trusted their order is
caught (Law 8).
"""

from __future__ import annotations

import base64
import contextlib
import io
import json
import math
import os
import re
import sys
import traceback
import types
import uuid
from typing import Any

from tee.adapters.fusion.wire import FusionWire
from tee.kernel.errors import TeeError

TINY_JPEG = b"\xff\xd8\xff\xe0" + b"\x00" * 32 + b"\xff\xd9"
# a real 1x1 white PNG, so Pillow can re-encode it
TINY_PNG = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+ip1sAAAAASUVORK5CYII="
)
DENSITY_KG_PER_CM3 = 0.00785  # steel, so a mass exists to read back

_UNIT_CM = {"mm": 0.1, "cm": 1.0, "m": 100.0, "in": 2.54, "ft": 30.48}
_UNIT_RAD = {"deg": math.pi / 180.0, "rad": 1.0}


def _token() -> str:
    return "tok-" + uuid.uuid4().hex[:12]


def parse_expression(text: str) -> tuple[float, str]:
    """'120 mm' -> (12.0, 'mm'); '30 deg' -> (radians, 'deg'); '6' -> (6.0, '')."""
    match = re.fullmatch(r"\s*([-+]?\d+(?:\.\d+)?)\s*([a-zA-Z]*)\s*", str(text))
    if not match:
        raise ValueError(f"the shim cannot evaluate the expression {text!r}")
    number, unit = float(match.group(1)), match.group(2)
    if unit in _UNIT_CM:
        return number * _UNIT_CM[unit], unit
    if unit in _UNIT_RAD:
        return number * _UNIT_RAD[unit], unit
    if unit:
        raise ValueError(f"unknown unit {unit!r} in {text!r}")
    return number, ""


# -- adsk.core ---------------------------------------------------------------


class Point3D:
    def __init__(self, x=0.0, y=0.0, z=0.0):
        self.x, self.y, self.z = float(x), float(y), float(z)

    @staticmethod
    def create(x=0.0, y=0.0, z=0.0):
        return Point3D(x, y, z)


class Matrix3D:
    @staticmethod
    def create():
        return Matrix3D()


class ObjectCollection:
    def __init__(self):
        self._items: list = []

    @staticmethod
    def create():
        return ObjectCollection()

    def add(self, item) -> bool:
        self._items.append(item)
        return True

    @property
    def count(self) -> int:
        return len(self._items)

    def item(self, index: int):
        return self._items[index]

    def __iter__(self):
        return iter(self._items)


class ValueInput:
    def __init__(self, value: float, expression: str | None = None, unit: str = ""):
        self.value, self.expression, self.unit = value, expression, unit

    @staticmethod
    def createByString(text: str):
        value, unit = parse_expression(text)
        return ValueInput(value, str(text), unit)

    @staticmethod
    def createByReal(value: float):
        return ValueInput(float(value), None, "")


class CustomEventHandler:
    def __init__(self):
        pass


class Document:
    def __init__(self, name: str):
        self.name = name
        self.isSaved = False
        self.isModified = True


class _Collection:
    """count/item over a list, the Fusion collection convention (doc 71 row 26)."""

    def __init__(self, items: list):
        self._items = items

    @property
    def count(self) -> int:
        return len(self._items)

    def item(self, index: int):
        return self._items[index]

    def __iter__(self):
        return iter(self._items)


# -- adsk.fusion: entities ------------------------------------------------------


class _Entity:
    objectType = "adsk::fusion::Base"

    def __init__(self, design: Design, name: str):
        self.entityToken = _token()
        self.name = name
        self.isValid = True
        self._design = design
        design._register(self)

    def _retire(self) -> None:
        self.isValid = False
        self._design._entities.pop(self.entityToken, None)


class BoundingBox3D:
    def __init__(self, dims_cm: list[float]):
        self.minPoint = Point3D(0.0, 0.0, 0.0)
        self.maxPoint = Point3D(*dims_cm)


class PhysicalProperties:
    def __init__(self, volume: float, area: float, centre: Point3D):
        self.volume = volume
        self.area = area
        self.mass = volume * DENSITY_KG_PER_CM3
        self.density = DENSITY_KG_PER_CM3
        self.centerOfMass = centre


class _Edge:
    def __init__(self, body: BRepBody):
        self.body = body
        self.objectType = "adsk::fusion::BRepEdge"


class BRepBody(_Entity):
    objectType = "adsk::fusion::BRepBody"

    def __init__(self, design, component: Component, name: str, dims_cm: list[float], shape: str):
        super().__init__(design, name)
        self.parentComponent = component
        self.dims = list(dims_cm)
        self.shape = shape
        self.volume = self.profile_area * dims_cm[2]
        self.isVisible = True
        self.isSolid = True
        n_edges = 12 if shape == "box" else 2
        self.edges = _Collection([_Edge(self) for _ in range(n_edges)])
        self.faces = _Collection([object()] * (6 if shape == "box" else 3))

    @property
    def profile_area(self) -> float:
        w, h = self.dims[0], self.dims[1]
        return w * h if self.shape == "box" else math.pi * (w / 2.0) ** 2

    @property
    def area(self) -> float:
        w, h, d = self.dims
        return 2.0 * (w * h + h * d + w * d)

    @property
    def boundingBox(self) -> BoundingBox3D:
        return BoundingBox3D(self.dims)

    @property
    def physicalProperties(self) -> PhysicalProperties:
        return PhysicalProperties(self.volume, self.area, Point3D(*(v / 2.0 for v in self.dims)))

    def deleteMe(self) -> bool:
        self.parentComponent._bodies.remove(self)
        self._retire()
        return True


class Profile:
    """A closed region of a sketch, LIVE over its geometry: a rectangle's
    corners or a circle's radius are read when the profile is asked, so a
    dimension that moves them re-sizes what was extruded from it (Law 10)."""

    objectType = "adsk::fusion::Profile"

    def __init__(self, shape: str, *, corners=None, circle=None):
        self.shape = shape
        self._corners = corners  # bl, br, tr, tl SketchPoints
        self._circle = circle

    @property
    def dims(self) -> tuple[float, float]:
        if self.shape == "box":
            bl, br, _tr, tl = self._corners
            return (abs(br.geometry.x - bl.geometry.x), abs(tl.geometry.y - bl.geometry.y))
        d = 2.0 * self._circle.radius
        return (d, d)

    @property
    def area(self) -> float:
        w, h = self.dims
        return w * h if self.shape == "box" else math.pi * (w / 2.0) ** 2

    @property
    def centroid(self) -> tuple[float, float]:
        if self.shape == "box":
            bl, _br, tr, _tl = self._corners
            return ((bl.geometry.x + tr.geometry.x) / 2.0, (bl.geometry.y + tr.geometry.y) / 2.0)
        c = self._circle.centerSketchPoint.geometry
        return (c.x, c.y)


class SketchPoint(_Entity):
    objectType = "adsk::fusion::SketchPoint"

    def __init__(self, design, sketch: Sketch, x: float, y: float):
        super().__init__(design, "")
        self.sketch = sketch
        self.geometry = Point3D(x, y, 0.0)
        self.isFixed = False
        self.isReference = False

    @property
    def worldGeometry(self) -> Point3D:
        return self.geometry

    @property
    def isFullyConstrained(self) -> bool:
        return self.sketch._fixed().get(id(self), (False, False)) == (True, True)

    def deleteMe(self) -> None:
        self.sketch._points.remove(self)
        self._retire()


class SketchLine(_Entity):
    objectType = "adsk::fusion::SketchLine"

    def __init__(self, design, sketch: Sketch, a: SketchPoint, b: SketchPoint):
        super().__init__(design, "")
        self.sketch = sketch
        self.startSketchPoint, self.endSketchPoint = a, b
        self.isConstruction = False
        self.isFixed = False

    @property
    def length(self) -> float:
        a, b = self.startSketchPoint.geometry, self.endSketchPoint.geometry
        return math.hypot(b.x - a.x, b.y - a.y)

    @property
    def isFullyConstrained(self) -> bool:
        return self.startSketchPoint.isFullyConstrained and self.endSketchPoint.isFullyConstrained

    def deleteMe(self) -> None:
        self.sketch._lines.remove(self)
        self.sketch._curves -= 1
        self._retire()


class SketchCircle(_Entity):
    objectType = "adsk::fusion::SketchCircle"

    def __init__(self, design, sketch: Sketch, centre: SketchPoint, radius: float):
        super().__init__(design, "")
        self.sketch = sketch
        self.centerSketchPoint = centre
        self.radius = float(radius)
        self.isConstruction = False

    @property
    def isFullyConstrained(self) -> bool:
        return self.centerSketchPoint.isFullyConstrained and self.sketch._radius_fixed(self)

    def deleteMe(self) -> None:
        self.sketch._circles.remove(self)
        self.sketch._curves -= 1
        self._retire()


class _SketchLines(_Collection):
    def __init__(self, sketch: Sketch):
        super().__init__(sketch._lines)
        self._sketch = sketch

    def addTwoPointRectangle(self, p1, p2):
        sk = self._sketch
        x1, x2 = sorted((p1.x, p2.x))
        y1, y2 = sorted((p1.y, p2.y))
        bl, br, tr, tl = sk._point(x1, y1), sk._point(x2, y1), sk._point(x2, y2), sk._point(x1, y2)
        bottom, right, top, left = (
            sk._line(bl, br),
            sk._line(br, tr),
            sk._line(tr, tl),
            sk._line(tl, bl),
        )
        sk._profiles.append(Profile("box", corners=(bl, br, tr, tl)))
        # row 38 leaves the order unstated; the shim scrambles it so a codegen
        # that trusted an index would be caught (Law 8)
        return _Collection([right, top, left, bottom])

    def addByTwoPoints(self, start, end):
        sk = self._sketch
        a = start if isinstance(start, SketchPoint) else sk._point(start.x, start.y)
        b = end if isinstance(end, SketchPoint) else sk._point(end.x, end.y)
        return sk._line(a, b)


class _SketchCircles(_Collection):
    def __init__(self, sketch: Sketch):
        super().__init__(sketch._circles)
        self._sketch = sketch

    def addByCenterRadius(self, centre, radius: float):
        sk = self._sketch
        c = centre if isinstance(centre, SketchPoint) else sk._point(centre.x, centre.y)
        circle = SketchCircle(sk._design, sk, c, radius)
        sk._circles.append(circle)
        sk._curves += 1
        sk._profiles.append(Profile("cylinder", circle=circle))
        return circle


class _SketchPoints(_Collection):
    def __init__(self, sketch: Sketch):
        super().__init__(sketch._points)
        self._sketch = sketch

    def add(self, point: Point3D) -> SketchPoint:
        return self._sketch._point(point.x, point.y)


class _SketchCurves:
    def __init__(self, sketch: Sketch):
        self.sketchLines = _SketchLines(sketch)
        self.sketchCircles = _SketchCircles(sketch)
        self._sketch = sketch

    @property
    def count(self) -> int:
        return self._sketch._curves


class _Constraint:
    def __init__(self, kind: str, args: tuple):
        self.objectType = "adsk::fusion::" + kind.capitalize() + "Constraint"
        self.kind, self.args = kind, args


def _is_horizontal(line) -> bool:
    return abs(line.startSketchPoint.geometry.y - line.endSketchPoint.geometry.y) < 1e-9


def _is_vertical(line) -> bool:
    return abs(line.startSketchPoint.geometry.x - line.endSketchPoint.geometry.x) < 1e-9


class _GeometricConstraints(_Collection):
    """Row 40's eleven calls. The shim does not solve: a constraint the
    geometry already satisfies is recorded, one it contradicts is refused
    (returns null, as Fusion does when creation fails) - Law 10."""

    def __init__(self, sketch: Sketch):
        super().__init__(sketch._constraints)
        self._sketch = sketch

    def _add(self, kind: str, args: tuple, ok: bool):
        if not ok:
            return None
        c = _Constraint(kind, args)
        self._items.append(c)
        return c

    def addHorizontal(self, line):
        return self._add(
            "horizontal", (line,), isinstance(line, SketchLine) and _is_horizontal(line)
        )

    def addVertical(self, line):
        return self._add("vertical", (line,), isinstance(line, SketchLine) and _is_vertical(line))

    def addParallel(self, l1, l2):
        ok = isinstance(l1, SketchLine) and isinstance(l2, SketchLine)
        return self._add("parallel", (l1, l2), ok)

    def addPerpendicular(self, l1, l2):
        ok = isinstance(l1, SketchLine) and isinstance(l2, SketchLine)
        return self._add("perpendicular", (l1, l2), ok)

    def addCollinear(self, l1, l2):
        ok = isinstance(l1, SketchLine) and isinstance(l2, SketchLine)
        return self._add("collinear", (l1, l2), ok)

    def addEqual(self, c1, c2):
        ok = type(c1) is type(c2) and isinstance(c1, (SketchLine, SketchCircle))
        return self._add("equal", (c1, c2), ok)

    def addTangent(self, c1, c2):
        ok = isinstance(c1, (SketchLine, SketchCircle)) and isinstance(
            c2, (SketchLine, SketchCircle)
        )
        return self._add("tangent", (c1, c2), ok)

    def addConcentric(self, e1, e2):
        ok = isinstance(e1, SketchCircle) and isinstance(e2, SketchCircle)
        return self._add("concentric", (e1, e2), ok)

    def addCoincident(self, point, entity):
        if not isinstance(point, SketchPoint):
            return None
        if isinstance(entity, SketchPoint):
            a, b = point.geometry, entity.geometry
            same = abs(a.x - b.x) < 1e-9 and abs(a.y - b.y) < 1e-9
            return self._add("coincident", (point, entity), same)
        return self._add(
            "coincident", (point, entity), isinstance(entity, (SketchLine, SketchCircle))
        )

    def addMidPoint(self, point, curve):
        ok = isinstance(point, SketchPoint) and isinstance(curve, SketchLine)
        return self._add("midpoint", (point, curve), ok)

    def addSymmetry(self, e1, e2, line):
        ok = type(e1) is type(e2) and isinstance(line, SketchLine)
        return self._add("symmetry", (e1, e2, line), ok)


class DimensionOrientations:
    AlignedDimensionOrientation = 0
    HorizontalDimensionOrientation = 1
    VerticalDimensionOrientation = 2


_DIMENSION_TYPES = {
    "distance": "SketchLinearDimension",
    "diameter": "SketchDiameterDimension",
    "radius": "SketchRadialDimension",
    "angle": "SketchAngularDimension",
}


class SketchDimension(_Entity):
    """Rows 41-42: a dimension whose parameter DRIVES rectangles and circles
    (Law 10): a horizontal / vertical distance between two points moves every
    point sharing the second point's coordinate on that axis - a rectangle's
    far side; a diameter / radius sets the circle's radius; anything else is
    recorded and its value read back, never faked."""

    def __init__(self, design, sketch, kind, ents, orientation, text, driving):
        super().__init__(design, "")
        self.sketch, self.kind, self.ents, self.orientation = sketch, kind, tuple(ents), orientation
        self.objectType = "adsk::fusion::" + _DIMENSION_TYPES[kind]
        self.textPosition = text
        self.isDriving = bool(driving)
        self.isDeletable = True
        self._syncing = False
        self.parameter = None
        if self.isDriving:
            n = design._next("param")
            measured = self._measure()
            if kind == "angle":
                expression, unit = f"{measured * 180.0 / math.pi:g} deg", "deg"
            else:
                expression, unit = f"{measured * 10.0:g} mm", "mm"
            self.parameter = ModelParameter(design, f"d{n}", expression, unit, self._drive)
            design._model_params.append(self.parameter)

    def _measure(self) -> float:
        """The current value from the geometry, in cm or radians."""
        if self.kind == "distance":
            a, b = self.ents[0].geometry, self.ents[1].geometry
            if self.orientation == DimensionOrientations.HorizontalDimensionOrientation:
                return abs(b.x - a.x)
            if self.orientation == DimensionOrientations.VerticalDimensionOrientation:
                return abs(b.y - a.y)
            return math.hypot(b.x - a.x, b.y - a.y)
        if self.kind == "diameter":
            return 2.0 * self.ents[0].radius
        if self.kind == "radius":
            return self.ents[0].radius
        angles = []
        for line in self.ents:
            a, b = line.startSketchPoint.geometry, line.endSketchPoint.geometry
            angles.append(math.atan2(b.y - a.y, b.x - a.x))
        return abs(angles[0] - angles[1]) % math.pi

    @property
    def value(self) -> float:
        return self._measure()

    @value.setter
    def value(self, v: float) -> None:
        self._drive(float(v))

    def _drive(self, v: float) -> None:
        if self._syncing:
            return
        self._syncing = True
        try:
            if self.kind == "distance":
                a, b = self.ents
                ax, ay = a.geometry.x, a.geometry.y
                dx, dy = b.geometry.x - ax, b.geometry.y - ay
                horizontal = (
                    self.orientation == DimensionOrientations.HorizontalDimensionOrientation
                )
                vertical = self.orientation == DimensionOrientations.VerticalDimensionOrientation
                if horizontal or (not vertical and abs(dy) < 1e-9):
                    self.sketch._shift(b, axis=0, to=ax + math.copysign(v, dx or 1.0))
                elif vertical or abs(dx) < 1e-9:
                    self.sketch._shift(b, axis=1, to=ay + math.copysign(v, dy or 1.0))
                else:
                    return  # a diagonal distance: recorded, not solved (Law 10)
            elif self.kind == "diameter":
                self.ents[0].radius = v / 2.0
            elif self.kind == "radius":
                self.ents[0].radius = v
            else:
                return  # an angle: recorded, not solved
            self._design._recompute()
        finally:
            self._syncing = False

    def deleteMe(self) -> None:
        self.sketch._dims.remove(self)
        if self.parameter is not None:
            self._design._model_params.remove(self.parameter)
            self.parameter._retire()
        self._retire()


class _SketchDimensions(_Collection):
    def __init__(self, sketch: Sketch):
        super().__init__(sketch._dims)
        self._sketch = sketch

    def _add(self, kind, ents, orientation, text, driving):
        d = SketchDimension(
            self._sketch._design, self._sketch, kind, ents, orientation, text, driving
        )
        self._items.append(d)
        return d

    def addDistanceDimension(self, p1, p2, orientation, textPoint, isDriving=True):
        if not (isinstance(p1, SketchPoint) and isinstance(p2, SketchPoint)):
            return None
        return self._add("distance", (p1, p2), orientation, textPoint, isDriving)

    def addDiameterDimension(self, entity, textPoint, isDriving=True):
        if not isinstance(entity, SketchCircle):
            return None
        return self._add("diameter", (entity,), 0, textPoint, isDriving)

    def addRadialDimension(self, entity, textPoint, isDriving=True):
        if not isinstance(entity, SketchCircle):
            return None
        return self._add("radius", (entity,), 0, textPoint, isDriving)

    def addAngularDimension(self, l1, l2, textPoint, isDriving=True):
        if not (isinstance(l1, SketchLine) and isinstance(l2, SketchLine)):
            return None
        return self._add("angle", (l1, l2), 0, textPoint, isDriving)


class Sketch(_Entity):
    objectType = "adsk::fusion::Sketch"

    def __init__(self, design, component: Component, plane):
        super().__init__(design, f"Sketch{design._next('sketch')}")
        self.parentComponent = component
        self.referencePlane = plane
        self.isVisible = True
        self._profiles: list[Profile] = []
        self._points: list[SketchPoint] = []
        self._lines: list[SketchLine] = []
        self._circles: list[SketchCircle] = []
        self._constraints: list[_Constraint] = []
        self._dims: list[SketchDimension] = []
        self._curves = 0
        # Fusion's projected origin: a sketch point that is not in _points
        self.originPoint = SketchPoint(design, self, 0.0, 0.0)
        self.sketchCurves = _SketchCurves(self)
        self.timelineObject = design.timeline._append(self)

    # -- geometry the shim owns ----------------------------------------------

    def _point(self, x: float, y: float) -> SketchPoint:
        p = SketchPoint(self._design, self, x, y)
        self._points.append(p)
        return p

    def _line(self, a: SketchPoint, b: SketchPoint) -> SketchLine:
        line = SketchLine(self._design, self, a, b)
        self._lines.append(line)
        self._curves += 1
        return line

    def _shift(self, point: SketchPoint, *, axis: int, to: float) -> None:
        """Move `point` along one axis together with every point sharing its
        coordinate there - a rectangle's far side moves as one (Law 10)."""
        old = point.geometry.x if axis == 0 else point.geometry.y
        for p in self._points:
            here = p.geometry.x if axis == 0 else p.geometry.y
            if abs(here - old) < 1e-9:
                if axis == 0:
                    p.geometry.x = to
                else:
                    p.geometry.y = to

    def _fixed(self) -> dict[int, tuple[bool, bool]]:
        """Which coordinates the constraints and dimensions pin, propagated
        from the origin - honest for rectangles, silent about the rest."""
        fixed: dict[int, list[bool]] = {id(self.originPoint): [True, True]}
        for p in self._points:
            fixed.setdefault(id(p), [False, False])

        def tie(a, b, axis):
            if fixed[id(a)][axis] or fixed[id(b)][axis]:
                fixed[id(a)][axis] = fixed[id(b)][axis] = True

        while True:
            before = {k: tuple(v) for k, v in fixed.items()}
            for c in self._constraints:
                if c.kind == "coincident" and isinstance(c.args[1], SketchPoint):
                    tie(c.args[0], c.args[1], 0)
                    tie(c.args[0], c.args[1], 1)
                elif c.kind == "horizontal":
                    tie(c.args[0].startSketchPoint, c.args[0].endSketchPoint, 1)
                elif c.kind == "vertical":
                    tie(c.args[0].startSketchPoint, c.args[0].endSketchPoint, 0)
            for d in self._dims:
                if d.kind == "distance" and d.isDriving:
                    if d.orientation == DimensionOrientations.HorizontalDimensionOrientation:
                        tie(d.ents[0], d.ents[1], 0)
                    elif d.orientation == DimensionOrientations.VerticalDimensionOrientation:
                        tie(d.ents[0], d.ents[1], 1)
            if {k: tuple(v) for k, v in fixed.items()} == before:
                break
        return {k: tuple(v) for k, v in fixed.items()}

    def _radius_fixed(self, circle: SketchCircle) -> bool:
        return any(
            d.kind in ("diameter", "radius") and d.isDriving and d.ents[0] is circle
            for d in self._dims
        )

    # -- the API surface ---------------------------------------------------------

    @property
    def profiles(self):
        return _Collection(self._profiles)

    @property
    def sketchPoints(self):
        return _SketchPoints(self)

    @property
    def geometricConstraints(self):
        return _GeometricConstraints(self)

    @property
    def sketchDimensions(self):
        return _SketchDimensions(self)

    @property
    def isFullyConstrained(self) -> bool:
        fixed = self._fixed()
        return all(fixed[id(p)] == (True, True) for p in self._points) and all(
            self._radius_fixed(c) for c in self._circles
        )

    def deleteMe(self) -> bool:
        for d in list(self._dims):
            d.deleteMe()
        for e in (*self._points, *self._lines, *self._circles, self.originPoint):
            e._retire()
        self.parentComponent._sketches.remove(self)
        self._design.timeline._drop(self)
        self._retire()
        return True


class _Sketches(_Collection):
    def __init__(self, component: Component):
        super().__init__(component._sketches)
        self._component = component

    def add(self, plane) -> Sketch:
        sketch = Sketch(self._component._design, self._component, plane)
        self._items.append(sketch)
        return sketch


class ConstructionPlane:
    objectType = "adsk::fusion::ConstructionPlane"

    def __init__(self, name: str):
        self.name = name


class FeatureOperations:
    JoinFeatureOperation = 0
    CutFeatureOperation = 1
    IntersectFeatureOperation = 2
    NewBodyFeatureOperation = 3
    NewComponentFeatureOperation = 4


class ExtentDirections:
    PositiveExtentDirection = 0
    NegativeExtentDirection = 1


class DesignTypes:
    DirectDesignType = 0
    ParametricDesignType = 1


class Parameter(_Entity):
    objectType = "adsk::fusion::Parameter"

    def __init__(self, design, name: str, expression: str, unit: str, comment: str = ""):
        super().__init__(design, name)
        self.unit = unit
        self.comment = comment
        self.isDeletable = True
        self._expression = ""
        self.value = 0.0
        self.expression = expression  # runs the setter

    @property
    def expression(self) -> str:
        return self._expression

    @expression.setter
    def expression(self, text: str) -> None:
        text = str(text)
        ref = None
        if text.strip().isidentifier():  # "width": a reference to a user parameter
            ref = self._design.userParameters.itemByName(text.strip())
        if ref is not None and ref is not self:
            value = ref.value
            self._depends_on = ref.name
        else:
            value, unit = parse_expression(text)
            if not unit and self.unit in _UNIT_CM:
                value *= _UNIT_CM[self.unit]  # a unitless expression takes the parameter's unit
            self._depends_on = None
        self._expression = text
        self.value = value
        self._changed()
        self._design._propagate(self)

    def _changed(self) -> None:
        return None


class UserParameter(Parameter):
    objectType = "adsk::fusion::UserParameter"

    def deleteMe(self) -> bool:
        self._design._user_params.remove(self)
        self._retire()
        return True


class ModelParameter(Parameter):
    objectType = "adsk::fusion::ModelParameter"

    def __init__(self, design, name, expression, unit, on_change):
        self._on_change = on_change
        super().__init__(design, name, expression, unit)

    def _changed(self) -> None:
        if getattr(self, "_on_change", None) is not None:
            self._on_change(self.value)


class _UserParameters(_Collection):
    def __init__(self, design: Design):
        super().__init__(design._user_params)
        self._design = design

    def add(self, name: str, value: ValueInput, units: str, comment: str = ""):
        if self.itemByName(name) is not None:
            return None
        expression = value.expression or f"{value.value:g}"
        param = UserParameter(self._design, name, expression, units, comment)
        self._items.append(param)
        return param

    def itemByName(self, name: str):
        return next((p for p in self._items if p.name == name), None)


class _ParameterList(_Collection):
    def __init__(self, design: Design):
        super().__init__(design._user_params + design._model_params)

    def itemByName(self, name: str):
        return next((p for p in self._items if p.name == name), None)


class DistanceExtentDefinition:
    objectType = "adsk::fusion::DistanceExtentDefinition"

    def __init__(self, value: ValueInput):
        self._value = value
        self.distance: ModelParameter | None = None

    @staticmethod
    def create(value: ValueInput):
        return DistanceExtentDefinition(value)


class ExtrudeFeatureInput:
    def __init__(self, profile, operation: int):
        self.profile = profile
        self.operation = operation
        self.extent: DistanceExtentDefinition | None = None
        self.direction = ExtentDirections.PositiveExtentDirection

    def setOneSideExtent(self, extent, direction, taper_angle=None) -> bool:
        self.extent, self.direction = extent, direction
        return True

    def setDistanceExtent(self, *args):  # retired September 2022: a script must never call it
        raise RuntimeError("setDistanceExtent is retired; use setOneSideExtent")


class _Feature(_Entity):
    def __init__(self, design, component: Component, name: str):
        super().__init__(design, name)
        self.parentComponent = component
        self.isSuppressed = False
        self.errorOrWarningMessage = ""
        self.healthState = 0
        self._bodies: list[BRepBody] = []
        self._created: list[BRepBody] = []
        self.timelineObject = design.timeline._append(self)

    @property
    def bodies(self):
        return _Collection(self._bodies)

    def deleteMe(self) -> bool:
        for body in list(self._created):
            if body.isValid:
                body.deleteMe()
        self.parentComponent._features.remove(self)
        self._design.timeline._drop(self)
        self._retire()
        return True


class ExtrudeFeature(_Feature):
    objectType = "adsk::fusion::ExtrudeFeature"

    def __init__(self, design, component, inp: ExtrudeFeatureInput):
        super().__init__(design, component, f"Extrude{design._next('extrude')}")
        self.extentOne = inp.extent
        self.operation = inp.operation
        profiles = list(inp.profile) if isinstance(inp.profile, ObjectCollection) else [inp.profile]
        sign = -1.0 if inp.direction == ExtentDirections.NegativeExtentDirection else 1.0
        depth = abs(inp.extent._value.value)
        self._profiles = profiles
        self._depth = depth
        self._sign = sign
        n = design._next("param")
        self.extentOne.distance = ModelParameter(
            design, f"d{n}", inp.extent._value.expression or f"{depth:g} cm", "mm", self._redepth
        )
        design._model_params.append(self.extentOne.distance)
        self._apply(depth)

    def _apply(self, depth: float) -> None:
        component = self.parentComponent
        op = self.operation
        if op in (
            FeatureOperations.CutFeatureOperation,
            FeatureOperations.JoinFeatureOperation,
        ) and (component._bodies):
            target = component._bodies[-1]
            delta = sum(p.area for p in self._profiles) * depth
            if op == FeatureOperations.CutFeatureOperation:
                target.volume = max(target.volume - delta, 0.0)
            else:
                target.volume += delta
                target.dims[2] += depth
            self._bodies = [target]
            return
        for profile in self._profiles:
            body = BRepBody(
                self._design,
                component,
                f"Body{self._design._next('body')}",
                [profile.dims[0], profile.dims[1], depth],
                profile.shape,
            )
            component._bodies.append(body)
            self._bodies.append(body)
            self._created.append(body)

    def _redepth(self, depth_cm: float) -> None:
        for body in self._created:
            if body.isValid:
                body.dims[2] = depth_cm
                body.volume = body.profile_area * depth_cm
        self._depth = depth_cm

    def _resize(self) -> None:
        """The sketch moved (a dimension drove it): the bodies this extrude
        created follow their live profiles, as a parametric recompute would."""
        for body, profile in zip(self._created, self._profiles, strict=False):
            if body.isValid:
                body.dims[0], body.dims[1] = profile.dims
                body.volume = profile.area * body.dims[2]


class _ExtrudeFeatures(_Collection):
    def __init__(self, component: Component):
        super().__init__(component._features)
        self._component = component

    def createInput(self, profile, operation: int) -> ExtrudeFeatureInput:
        return ExtrudeFeatureInput(profile, operation)

    def add(self, inp: ExtrudeFeatureInput):
        if inp.extent is None:
            return None
        feature = ExtrudeFeature(self._component._design, self._component, inp)
        self._items.append(feature)
        return feature


class _EdgeSetInputs:
    def __init__(self):
        self.sets: list[tuple[ObjectCollection, ValueInput, bool]] = []

    def addConstantRadiusEdgeSet(self, edges, radius: ValueInput, is_tangent_chain: bool):
        self.sets.append((edges, radius, bool(is_tangent_chain)))
        return object()


class FilletFeatureInput:
    def __init__(self):
        self.edgeSetInputs = _EdgeSetInputs()


class FilletFeature(_Feature):
    objectType = "adsk::fusion::FilletFeature"

    def __init__(self, design, component, inp: FilletFeatureInput):
        super().__init__(design, component, f"Fillet{design._next('fillet')}")
        edges, radius, _tangent = inp.edgeSetInputs.sets[0]
        self.radius_cm = radius.value
        bodies: list[BRepBody] = []
        for edge in edges:
            if edge.body not in bodies:
                bodies.append(edge.body)
        self._bodies = bodies


class _FilletFeatures(_Collection):
    def __init__(self, component: Component):
        super().__init__(component._features)
        self._component = component

    def createInput(self) -> FilletFeatureInput:
        return FilletFeatureInput()

    def add(self, inp: FilletFeatureInput):
        if not inp.edgeSetInputs.sets or inp.edgeSetInputs.sets[0][0].count == 0:
            return None
        feature = FilletFeature(self._component._design, self._component, inp)
        self._items.append(feature)
        return feature


class _Features(_Collection):
    def __init__(self, component: Component):
        super().__init__(component._features)
        self.extrudeFeatures = _ExtrudeFeatures(component)
        self.filletFeatures = _FilletFeatures(component)


class Occurrence(_Entity):
    objectType = "adsk::fusion::Occurrence"

    def __init__(self, design, parent: Component, component: Component):
        self.component = component  # before _Entity sets name, which the property forwards
        super().__init__(design, component.name)
        self._parent = parent
        self.timelineObject = design.timeline._append(self)

    @property
    def name(self) -> str:  # the browser name follows the component's
        return self.component.name

    @name.setter
    def name(self, value: str) -> None:
        self.component.name = value

    @property
    def bRepBodies(self):
        return _Collection(self.component._bodies)

    def deleteMe(self) -> bool:
        self._parent._occurrences.remove(self)
        for body in list(self.component._bodies):
            body._retire()
        self._design.timeline._drop(self)
        self._retire()
        return True


class _Occurrences(_Collection):
    def __init__(self, component: Component):
        super().__init__(component._occurrences)
        self._component = component

    def addNewComponent(self, transform) -> Occurrence:
        design = self._component._design
        component = Component(design, f"Component{design._next('component')}")
        occurrence = Occurrence(design, self._component, component)
        self._items.append(occurrence)
        return occurrence


class Component:
    objectType = "adsk::fusion::Component"

    def __init__(self, design: Design, name: str):
        self._design = design
        self.name = name
        self.entityToken = _token()
        self._sketches: list[Sketch] = []
        self._features: list[_Feature] = []
        self._bodies: list[BRepBody] = []
        self._occurrences: list[Occurrence] = []
        self.xYConstructionPlane = ConstructionPlane("XY")
        self.xZConstructionPlane = ConstructionPlane("XZ")
        self.yZConstructionPlane = ConstructionPlane("YZ")

    @property
    def sketches(self):
        return _Sketches(self)

    @property
    def features(self):
        return _Features(self)

    @property
    def bRepBodies(self):
        return _Collection(self._bodies)

    @property
    def occurrences(self):
        return _Occurrences(self)

    @property
    def physicalProperties(self) -> PhysicalProperties:
        volume = sum(b.volume for b in self._bodies)
        area = sum(b.area for b in self._bodies)
        return PhysicalProperties(volume, area, Point3D())

    @property
    def boundingBox(self) -> BoundingBox3D:
        dims = [0.0, 0.0, 0.0]
        for body in self._bodies:
            dims = [max(a, b) for a, b in zip(dims, body.dims, strict=True)]
        return BoundingBox3D(dims)


# -- the timeline --------------------------------------------------------------


class TimelineObject:
    def __init__(self, timeline: Timeline, entity):
        self._timeline = timeline
        self.entity = entity
        self.isGroup = False
        self.isRolledBack = False

    @property
    def name(self) -> str:
        return self.entity.name

    @property
    def index(self) -> int:
        return self._timeline._items.index(self) if self in self._timeline._items else -1

    @property
    def isSuppressed(self) -> bool:
        return bool(getattr(self.entity, "isSuppressed", False))

    @property
    def errorOrWarningMessage(self) -> str:
        return str(getattr(self.entity, "errorOrWarningMessage", ""))


class Timeline:
    def __init__(self):
        self._items: list[TimelineObject] = []
        self._marker = 0

    def _append(self, entity) -> TimelineObject:
        obj = TimelineObject(self, entity)
        at_end = self._marker == len(self._items)
        self._items.append(obj)
        if at_end:
            self._marker = len(self._items)
        return obj

    def _drop(self, entity) -> None:
        self._items = [o for o in self._items if o.entity is not entity]
        self._marker = min(self._marker, len(self._items))

    @property
    def count(self) -> int:
        return len(self._items)

    def item(self, index: int) -> TimelineObject:
        return self._items[index]

    @property
    def markerPosition(self) -> int:
        return self._marker

    @markerPosition.setter
    def markerPosition(self, value: int) -> None:
        self._marker = max(0, min(int(value), len(self._items)))

    def deleteAllAfterMarker(self) -> bool:
        for obj in list(self._items[self._marker :]):
            entity = obj.entity
            if entity.isValid:
                entity.deleteMe()  # each deleteMe drops its own timeline object
        self._items = self._items[: self._marker]
        return True

    def moveToEnd(self) -> bool:
        self._marker = len(self._items)
        return True

    def moveToBeginning(self) -> bool:
        self._marker = 0
        return True


# -- export / import / viewport ------------------------------------------------


class _ExportOptions:
    def __init__(self, fmt: str, filename: str, geometry, unit_type: int):
        self.format = fmt
        self.filename = filename
        self.geometry = geometry
        self.unitType = unit_type


class ExportManager:
    def __init__(self, design: Design):
        self._design = design
        self.exports: list[_ExportOptions] = []

    def createSTEPExportOptions(self, filename: str, geometry=None):
        return _ExportOptions("step", filename, geometry, 2)

    def createFusionArchiveExportOptions(self, filename: str, geometry=None):
        return _ExportOptions("f3d", filename, geometry, 2)

    def createSTLExportOptions(self, geometry, filename: str = ""):
        return _ExportOptions("stl", filename, geometry, 2)

    def createOBJExportOptions(self, geometry, filename: str = ""):
        return _ExportOptions("obj", filename, geometry, 2)  # 2 = centimeters, the OBJ default

    def execute(self, options: _ExportOptions) -> bool:
        geometry = options.geometry or self._design.rootComponent
        bodies = (
            [geometry]
            if isinstance(geometry, BRepBody)
            else list(getattr(geometry, "_bodies", []) or geometry.bRepBodies)
        )
        dims = bodies[0].dims if bodies else [1.0, 1.0, 1.0]
        header = {
            "step": "ISO-10303-21;",
            "f3d": "FUSION-ARCHIVE",
            "stl": "solid tee",
            "obj": "# obj",
        }
        os.makedirs(os.path.dirname(options.filename) or ".", exist_ok=True)
        with open(options.filename, "w", encoding="utf-8") as fh:
            fh.write(
                header[options.format] + "\n# tee-shim " + json.dumps({"dims_cm": dims}) + "\n"
            )
        self.exports.append(options)
        return True


class _ImportOptions:
    def __init__(self, fmt: str, filename: str):
        self.format, self.filename = fmt, filename


class ImportManager:
    def __init__(self, app: Application):
        self._app = app

    def createSTEPImportOptions(self, filename: str):
        return _ImportOptions("step", filename)

    def createFusionArchiveImportOptions(self, filename: str):
        return _ImportOptions("f3d", filename)

    def createIGESImportOptions(self, filename: str):
        return _ImportOptions("iges", filename)

    def createSATImportOptions(self, filename: str):
        return _ImportOptions("sat", filename)

    def importToTarget2(self, options: _ImportOptions, target: Component):
        if not os.path.isfile(options.filename):
            return None
        dims = [1.0, 1.0, 1.0]
        with open(options.filename, encoding="utf-8", errors="replace") as fh:
            for line in fh:
                if line.startswith("# tee-shim "):
                    dims = json.loads(line[len("# tee-shim ") :])["dims_cm"]
        design = target._design
        body = BRepBody(design, target, f"Body{design._next('body')}", dims, "box")
        target._bodies.append(body)
        out = ObjectCollection.create()
        out.add(body)
        return out


class Viewport:
    def __init__(self, jpg_supported: bool = True):
        self.jpg_supported = jpg_supported
        self.fits = 0
        self.saved: list[tuple[str, int, int]] = []

    def fit(self) -> bool:
        self.fits += 1
        return True

    def saveAsImageFile(self, filename: str, width: int, height: int) -> bool:
        if filename.lower().endswith(".jpg") and not self.jpg_supported:
            return False
        self.saved.append((filename, width, height))
        os.makedirs(os.path.dirname(filename) or ".", exist_ok=True)
        with open(filename, "wb") as fh:
            if filename.lower().endswith(".png"):
                fh.write(TINY_PNG)
            else:
                fh.write(TINY_JPEG + b"\0" * (width * height // 64))  # bigger renders cost more
        return True


# -- the design and the application ---------------------------------------------


class Design:
    objectType = "adsk::fusion::Design"

    def __init__(self, *, parametric: bool = True):
        self._entities: dict[str, Any] = {}
        self._counters: dict[str, int] = {}
        self._user_params: list[UserParameter] = []
        self._model_params: list[ModelParameter] = []
        self.timeline = Timeline()
        self.designType = (
            DesignTypes.ParametricDesignType if parametric else DesignTypes.DirectDesignType
        )
        self.rootComponent = Component(self, "Root")
        self.exportManager = ExportManager(self)

    @staticmethod
    def cast(obj):
        return obj if isinstance(obj, Design) else None

    def _register(self, entity) -> None:
        self._entities[entity.entityToken] = entity

    def _next(self, what: str) -> int:
        self._counters[what] = self._counters.get(what, 0) + 1
        return self._counters[what]

    def _propagate(self, param: Parameter) -> None:
        """A parameter changed: every parameter whose expression names it is
        re-evaluated (and drives its geometry), as Fusion's recompute does."""
        for other in list(self._model_params) + list(self._user_params):
            if other is not param and getattr(other, "_depends_on", None) == param.name:
                other.expression = other.expression

    def _recompute(self) -> None:
        stack = [self.rootComponent]
        while stack:
            comp = stack.pop()
            for feature in comp._features:
                resize = getattr(feature, "_resize", None)
                if resize is not None:
                    resize()
            stack.extend(o.component for o in comp._occurrences)

    @property
    def userParameters(self):
        return _UserParameters(self)

    @property
    def allParameters(self):
        return _ParameterList(self)

    def findEntityByToken(self, token: str):
        entity = self._entities.get(token)
        return [entity] if entity is not None and entity.isValid else []


class Application:
    _current: Application | None = None

    def __init__(self, design: Design | None, *, jpg_supported: bool = True):
        self.activeProduct = design
        self.activeDocument = Document("Untitled") if design is not None else None
        self.activeViewport = Viewport(jpg_supported) if design is not None else None
        self.importManager = ImportManager(self)
        self.version = "2.0.99999 (shim)"
        self.isStartupComplete = True
        self.logged: list[str] = []

    @classmethod
    def get(cls):
        return cls._current

    def log(self, message: str) -> None:
        self.logged.append(str(message))


def _modules(app: Application) -> dict[str, types.ModuleType]:
    core = types.ModuleType("adsk.core")
    for name in (
        "Application",
        "Point3D",
        "Matrix3D",
        "ObjectCollection",
        "ValueInput",
        "Document",
    ):
        setattr(core, name, globals()[name])
    core.CustomEventHandler = CustomEventHandler
    fusion = types.ModuleType("adsk.fusion")
    for name in (
        "Design",
        "DesignTypes",
        "FeatureOperations",
        "ExtentDirections",
        "DimensionOrientations",
        "DistanceExtentDefinition",
        "BRepBody",
        "Sketch",
        "SketchPoint",
        "SketchLine",
        "SketchCircle",
        "SketchDimension",
        "Component",
        "Occurrence",
        "ExtrudeFeature",
        "FilletFeature",
        "UserParameter",
        "ModelParameter",
        "Timeline",
    ):
        setattr(fusion, name, globals()[name])
    adsk = types.ModuleType("adsk")
    adsk.core, adsk.fusion = core, fusion
    Application._current = app
    return {"adsk": adsk, "adsk.core": core, "adsk.fusion": fusion}


PING_CODE = """\
import adsk.core, adsk.fusion
_app = adsk.core.Application.get()
_doc = _app.activeDocument
_design = adsk.fusion.Design.cast(_app.activeProduct)
_kind = None
if _design is not None:
    _kind = ("parametric" if _design.designType == adsk.fusion.DesignTypes.ParametricDesignType
             else "direct")
result = {"product": "Fusion", "version": str(_app.version),
          "document": _doc.name if _doc is not None else None, "design": _kind,
          "ids": len(_tee.get("ids", {}))}
"""


class FakeFusionWire(FusionWire):
    """The adapter's whole wire surface, hermetic. Scripts exec here against
    the shim, with the bridge's persistent `_tee` dict, and a failure raises
    the wire's own `fusion_bridge_error` with the traceback's tail."""

    def __init__(self, *, design: bool = True, parametric: bool = True, jpg_supported: bool = True):
        super().__init__(port=0)
        self.app = Application(
            Design(parametric=parametric) if design else None, jpg_supported=jpg_supported
        )
        self.namespace: dict[str, Any] = {"_tee": {}}
        self.executed: list[str] = []

    @property
    def design(self) -> Design:
        return self.app.activeProduct

    def probe(self) -> bool:
        try:
            self.ping()
            return True
        except TeeError:
            return False

    def ping(self) -> dict[str, Any]:
        return self.execute(PING_CODE)

    def execute(self, code: str, *, strict_json: bool = True, timeout: float | None = None):
        self.executed.append(code)
        shims = _modules(self.app)
        saved = {name: sys.modules.get(name) for name in shims}
        sys.modules.update(shims)
        scope: dict[str, Any] = {"result": {}, "_tee": self.namespace["_tee"]}
        stdout = io.StringIO()
        try:
            with contextlib.redirect_stdout(stdout):
                exec(code, scope)
        except Exception:
            tail = "\n".join(traceback.format_exc().strip().splitlines()[-4:])
            raise TeeError(
                "fusion_bridge_error", tail[:600], fix="The message is Fusion's own."
            ) from None
        finally:
            for name, module in saved.items():
                if module is None:
                    sys.modules.pop(name, None)
                else:
                    sys.modules[name] = module
        result = scope.get("result")
        if not isinstance(result, dict):
            raise TeeError("fusion_bridge_error", "the `result` variable must be a dict", fix="")
        return json.loads(json.dumps(result)) if strict_json else result
