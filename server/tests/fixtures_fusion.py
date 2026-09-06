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
    objectType = "adsk::fusion::Profile"

    def __init__(self, area: float, dims: tuple[float, float], shape: str):
        self.area, self.dims, self.shape = area, dims, shape


class _SketchLines:
    def __init__(self, sketch: Sketch):
        self._sketch = sketch

    def addTwoPointRectangle(self, p1: Point3D, p2: Point3D):
        w, h = abs(p2.x - p1.x), abs(p2.y - p1.y)
        self._sketch._profiles.append(Profile(w * h, (w, h), "box"))
        self._sketch._curves += 4
        return [object()] * 4


class _SketchCircles:
    def __init__(self, sketch: Sketch):
        self._sketch = sketch

    def addByCenterRadius(self, centre: Point3D, radius: float):
        r = float(radius)
        self._sketch._profiles.append(Profile(math.pi * r * r, (2 * r, 2 * r), "cylinder"))
        self._sketch._curves += 1
        return object()


class _SketchCurves:
    def __init__(self, sketch: Sketch):
        self.sketchLines = _SketchLines(sketch)
        self.sketchCircles = _SketchCircles(sketch)
        self._sketch = sketch

    @property
    def count(self) -> int:
        return self._sketch._curves


class Sketch(_Entity):
    objectType = "adsk::fusion::Sketch"

    def __init__(self, design, component: Component, plane):
        super().__init__(design, f"Sketch{design._next('sketch')}")
        self.parentComponent = component
        self.referencePlane = plane
        self.isVisible = True
        self._profiles: list[Profile] = []
        self._curves = 0
        self.sketchCurves = _SketchCurves(self)
        self.timelineObject = design.timeline._append(self)

    @property
    def profiles(self):
        return _Collection(self._profiles)

    def deleteMe(self) -> bool:
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
        value, unit = parse_expression(text)
        if not unit and self.unit in _UNIT_CM:
            value *= _UNIT_CM[self.unit]  # a unitless expression takes the parameter's unit
        self._expression = str(text)
        self.value = value
        self._changed()

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
        "DistanceExtentDefinition",
        "BRepBody",
        "Sketch",
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
