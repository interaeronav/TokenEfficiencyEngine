"""Checks and measures: the numbers behind `pk_measure` and `pk_check` (D1 `checks/`).

Every function here takes a raw `TopoDS_Shape` (and, where mass matters, a
material name or a density) and returns a plain dict of rounded numbers -
never an OCCT object, never a picture (Law: text over pixels). The features
layer and the TEE adapter call these; the document never does, because a
check reads geometry and mutates nothing.

Modules: `validity` (BRepCheck + closedness), `mass` (exact GProp measures
and mass from a material card), `wall` (minimum wall by inward ray casting),
`section` (planar section area), `spec` (a spec dict -> verdict + violations,
each naming the fix). OCP is imported lazily inside functions, so
`import partkiln.checks` stays OCP-free (D1: OCP lives in `partkiln.brep`
alone).
"""

from __future__ import annotations

__all__ = ["mass", "section", "spec", "validity", "wall"]
