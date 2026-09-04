"""Drawings: hidden-line views, dimensions read back from the model, sheets.

The package a mechanical CAD kernel is judged by. Six modules, one job each:

  `hlr`    exact hidden-line removal - the union of the three visible and the
           three hidden HLR compounds (the measured design: on a filleted part
           `VCompound` can be nearly empty and the tangent lines live in
           `Rg1LineVCompound`), plus half-space sections and detail windows.
  `views`  sheets, the first- / third-angle table, and the layout that turns
           projections in model millimetres into a placed sheet.
  `dims`   every dimension VALUE read from the B-rep (Law 15), each carrying
           both `value_mm` (the model) and `projected_mm` (the drawn geometry)
           and an `agree` verdict; hole tables and parts lists.
  `svg`    our own writer: native lines, circles and `A` arcs, 1 user unit =
           1 mm, byte-identical on repeat.
  `dxf`    ezdxf with REAL `DIMENSION` entities and `$INSUNITS = 4`.
  `pdf`    fpdf2, inside the optional `[pdf]` extra, refusing by name without it.

Importing this package registers `create drawing` and the `drawing` kernel
method (through `verbs`), the same way `partkiln.features` registers its
builders - and costs no OCP: every OCP import in `hlr` and `dims` is inside a
function, and `svg` / `dxf` / `pdf` are imported only when a file is written.
"""

from __future__ import annotations

from partkiln.drawing import hlr as hlr
from partkiln.drawing import views as views

from partkiln.drawing import dims as dims  # isort: skip - views must bind first
from partkiln.drawing import verbs as verbs  # isort: skip - registration goes last
from partkiln.drawing.dims import Dimension, hole_table, measure, parts_list
from partkiln.drawing.hlr import Arc, Polyline, Projection, Segment, ViewFrame, project
from partkiln.drawing.verbs import FORMATS, build_drawing, write_files
from partkiln.drawing.views import Drawing, Sheet, View, angle_for, sheet_named

__all__ = [
    "FORMATS",
    "Arc",
    "Dimension",
    "Drawing",
    "Polyline",
    "Projection",
    "Segment",
    "Sheet",
    "View",
    "ViewFrame",
    "angle_for",
    "build_drawing",
    "dims",
    "hlr",
    "hole_table",
    "measure",
    "parts_list",
    "project",
    "sheet_named",
    "verbs",
    "views",
    "write_files",
]
