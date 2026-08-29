"""A FreeCAD shim + fake wire for the P4 adapter's hermetic tests.

FakeFcWire.py() EXECUTES the adapter's generated scripts against this
shim - the codegen runs for real in CI (syntax, control flow, the JSON
read-back protocol), with only FreeCAD's C++ world faked. The live
`-m dcc` smoke runs the same contract against the real bridge.
"""

from __future__ import annotations

import contextlib
import io
import json
import pickle
import sys
from typing import Any

from tee.adapters.freecad.wire import FreeCADWire

TINY_JPEG = b"\xff\xd8\xff\xe0" + b"\x00" * 32 + b"\xff\xd9"


class Vector:
    def __init__(self, x=0.0, y=0.0, z=0.0):
        self.x, self.y, self.z = float(x), float(y), float(z)


class Rotation:
    def __init__(self, axis=None, angle=0.0):
        self.Axis, self.Angle = axis or Vector(0, 0, 1), angle

    def __mul__(self, other):
        return self


class Placement:
    def __init__(self, base=None, rotation=None):
        self.Base = base or Vector()
        self.Rotation = rotation or Rotation()


class FakeObj:
    def __init__(self, type_id: str, name: str):
        self.Name = name
        self.Label = name
        self.TypeId = type_id
        self.Placement = Placement()
        self.Visibility = True
        self._geometry: list[Any] = []
        self._props: list[str] = []

    def addProperty(self, prop_type: str, name: str):
        self._props.append(name)
        setattr(self, name, None)
        return self

    def addGeometry(self, geo, construction=False):
        self._geometry.append(geo)

    def addView(self, view):
        self._geometry.append(view)

    # the live 1.1.3 lesson, encoded: a dimension answers 0.0 until it is
    # touched and the document recomputed in a LATER dispatch
    def touch(self):
        self._touched = True

    def getRawValue(self):
        return getattr(self, "_settled_value", 0.0)


class LineSegment:
    def __init__(self, a: Vector, b: Vector):
        self.a, self.b = a, b


class FakeDoc:
    def __init__(self, name: str):
        self.Name = name
        self.Objects: list[FakeObj] = []
        self._recomputes = 0

    def addObject(self, type_id: str, name: str) -> FakeObj:
        taken = {o.Name for o in self.Objects}
        actual, i = name, 0
        while actual in taken:
            i += 1
            actual = f"{name}{i:03d}"
        obj = FakeObj(type_id, actual)
        self.Objects.append(obj)
        return obj

    def getObject(self, name: str) -> FakeObj | None:
        return next((o for o in self.Objects if o.Name == name), None)

    def removeObject(self, name: str) -> None:
        self.Objects = [o for o in self.Objects if o.Name != name]

    def recompute(self) -> None:
        self._recomputes += 1
        for obj in self.Objects:
            if getattr(obj, "_touched", False) and "Dim" in obj.TypeId:
                obj._settled_value = 111.0  # settles only after touch+recompute

    def saveCopy(self, path: str) -> None:
        with open(path, "wb") as fh:
            pickle.dump(self, fh)


class FakeFreeCAD:
    Vector = Vector
    Rotation = Rotation
    Placement = Placement

    def __init__(self):
        self.docs: dict[str, FakeDoc] = {}

    def getDocument(self, name: str) -> FakeDoc:
        if name not in self.docs:
            raise KeyError(name)
        return self.docs[name]

    def newDocument(self, name: str) -> FakeDoc:
        doc = FakeDoc(name)
        self.docs[name] = doc
        return doc

    def closeDocument(self, name: str) -> None:
        self.docs.pop(name, None)

    def openDocument(self, path: str) -> FakeDoc:
        with open(path, "rb") as fh:
            doc = pickle.load(fh)
        self.docs[doc.Name] = doc
        return doc

    def Version(self):
        return ["9", "9", "fake"]

    def getResourceDir(self):
        return "/fake-resources"


class _FakeView:
    def viewIsometric(self):
        return None

    def saveImage(self, path: str, w: int, h: int, bg: str) -> None:
        with open(path, "wb") as fh:
            fh.write(TINY_JPEG)


class _FakeGuiDoc:
    def activeView(self):
        return _FakeView()


class FakeFreeCADGui:
    def getDocument(self, name: str):
        return _FakeGuiDoc()

    def activeDocument(self):
        return _FakeGuiDoc()


class FakeFcWire(FreeCADWire):
    """The adapter's whole wire surface, hermetic. Scripts exec here."""

    def __init__(self):
        self.app = FakeFreeCAD()
        self.gui = FakeFreeCADGui()
        self.executed: list[str] = []

    def ping(self) -> bool:
        return True

    def list_documents(self) -> list[str]:
        return sorted(self.app.docs)

    def create_document(self, name: str) -> str:
        actual = name.replace(" ", "_")
        self.app.newDocument(actual)
        return actual

    def py(self, code: str) -> str:
        self.executed.append(code)
        buffer = io.StringIO()
        # generated scripts use real `import FreeCAD` statements, so the
        # shims must sit in sys.modules for the exec (any object satisfies
        # the import machinery once it is the sys.modules entry)
        app = self.app

        class _TechDraw:
            @staticmethod
            def makeExtentDim(view, edges, direction):
                doc = next(d for d in app.docs.values() if view in d.Objects)
                return doc.addObject("TechDraw::DrawViewDimExtent", "DimExtent")

            @staticmethod
            def writeDXFPage(page, path):
                with open(path, "wb") as fh:
                    fh.write(b"0\nSECTION\n" + b"x" * 600)

        class _TechDrawGui:
            @staticmethod
            def exportPageAsSvg(page, path):
                with open(path, "wb") as fh:
                    fh.write(b"<svg>" + b"x" * 600 + b"</svg>")

            @staticmethod
            def exportPageAsPdf(page, path):
                with open(path, "wb") as fh:
                    fh.write(b"%PDF-1.4\n" + b"x" * 600)

        shims = {
            "FreeCAD": self.app,
            "FreeCADGui": self.gui,
            "Part": type("Part", (), {"LineSegment": LineSegment}),
            "Sketcher": type("Sketcher", (), {}),
            "TechDraw": _TechDraw,
            "TechDrawGui": _TechDrawGui,
        }
        saved = {name: sys.modules.get(name) for name in shims}
        sys.modules.update(shims)
        try:
            with contextlib.redirect_stdout(buffer):
                exec(code, {"json": json})
        finally:
            for name, module in saved.items():
                if module is None:
                    sys.modules.pop(name, None)
                else:
                    sys.modules[name] = module
        return buffer.getvalue()
