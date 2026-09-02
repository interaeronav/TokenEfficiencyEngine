"""Hand-built `BRepTools_History` per feature: how a name survives a regen.

Measured (A66 P0a, OCP 7.9.3): `History()` exists ONLY on `BRepAlgoAPI_*`,
`BRepFeat_MakeCylindricalHole` and `ShapeUpgrade_UnifySameDomain`. Every
other builder (`MakePrism/MakeRevol/MakeFillet/MakeChamfer/DraftAngle/
MakePipeShell/ThruSections/MakeThickSolid/MakeDPrism/Transform`) exposes
only per-sub-shape `Generated(s)/Modified(s)/IsDeleted(s)`, and
`BRepTools_History` binds `Generated/Modified/IsRemoved/Merge/AddGenerated/
AddModified/Remove` - there is NO `IsDeleted` on it. So `record()` walks the
input's unique vertices, edges, faces and solids (the four supported types)
and asks the builder about each one, and `merge()` chains the ready-made
histories of booleans and unify. The pinned case: fillet r2 on F1's four
vertical corners generates one face per corner, nothing for the seam,
modifies the six touched faces once each and leaves the cylinder wall alone
(7 faces -> 11).

`follow()` is what naming.py uses at regen: a sub-shape's successor is its
Modified image if any, else its Generated image, else itself when the
history is silent about it (OCCT records only what changed), and nothing
when it was removed.
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence

from partkiln.brep import require_ocp

require_ocp()

from OCP.BRepTools import BRepTools_History  # noqa: E402
from OCP.Standard import Standard_Failure  # noqa: E402
from OCP.TopAbs import TopAbs_EDGE, TopAbs_FACE, TopAbs_SOLID, TopAbs_VERTEX  # noqa: E402
from OCP.TopExp import TopExp  # noqa: E402
from OCP.TopoDS import TopoDS_Shape  # noqa: E402
from OCP.TopTools import TopTools_IndexedMapOfShape  # noqa: E402

from partkiln.brep.shapes import as_list as _as_list  # noqa: E402

_SUPPORTED = (TopAbs_VERTEX, TopAbs_EDGE, TopAbs_FACE, TopAbs_SOLID)


def _unique(shape: TopoDS_Shape, kind: int) -> list[TopoDS_Shape]:
    m = TopTools_IndexedMapOfShape()
    TopExp.MapShapes_s(shape, kind, m)
    return [m.FindKey(i) for i in range(1, m.Extent() + 1)]


def _ask(algo: object, method: str, s: TopoDS_Shape) -> list[TopoDS_Shape]:
    """A builder's Generated/Modified for one sub-shape; an OCCT refusal for a
    type the builder does not track (Standard_NoSuchObject and kin) means
    "no relation", which is what an empty list says."""
    try:
        return _as_list(getattr(algo, method)(s))
    except Standard_Failure:
        return []


class HistoryMap:
    """A `BRepTools_History` with the four queries naming.py needs.

    Wraps rather than subclasses because OCP handles are not subclassable
    in a way that survives `Merge`.
    """

    def __init__(self, history: BRepTools_History | None = None) -> None:
        self._h = history if history is not None else BRepTools_History()

    @property
    def raw(self) -> BRepTools_History:
        return self._h

    def merge(self, other: HistoryMap | BRepTools_History) -> HistoryMap:
        """Chain `other` AFTER this map (a boolean's or unify's own history)."""
        self._h.Merge(other.raw if isinstance(other, HistoryMap) else other)
        return self

    def generated(self, subshape: TopoDS_Shape) -> list[TopoDS_Shape]:
        if not BRepTools_History.IsSupportedType_s(subshape):
            return []
        return _as_list(self._h.Generated(subshape))

    def modified(self, subshape: TopoDS_Shape) -> list[TopoDS_Shape]:
        if not BRepTools_History.IsSupportedType_s(subshape):
            return []
        return _as_list(self._h.Modified(subshape))

    def is_removed(self, subshape: TopoDS_Shape) -> bool:
        if not BRepTools_History.IsSupportedType_s(subshape):
            return False
        return bool(self._h.IsRemoved(subshape))

    def successors(self, subshape: TopoDS_Shape) -> list[TopoDS_Shape]:
        """Modified images, else generated ones (a consumed fillet edge leads
        to its fillet face), else nothing if removed, else the shape itself
        (the history is silent about untouched shapes)."""
        mod = self.modified(subshape)
        if mod:
            return mod
        gen = self.generated(subshape)
        if gen:
            return gen
        if self.is_removed(subshape):
            return []
        return [subshape]


def record(algo: object, inputs: Sequence[TopoDS_Shape]) -> HistoryMap:
    """Build the map for a builder-API feature from its per-sub-shape answers.

    For every unique vertex / edge / face / solid of every input:
    `IsDeleted` -> `Remove`; each `Generated` -> `AddGenerated`; each
    `Modified` -> `AddModified`. A builder that already has `History()`
    (booleans, unify) is merged instead - use `from_algo`.
    """
    h = BRepTools_History()
    for shape in inputs:
        for kind in _SUPPORTED:
            for s in _unique(shape, kind):
                # Generated is read BEFORE Remove: a filleted edge is both
                # "deleted" (it no longer exists) and the parent of the new
                # face, exactly as a boolean's own history records a consumed
                # tool face - and Remove only unbinds Modified images.
                for g in _ask(algo, "Generated", s):
                    if not g.IsSame(s):
                        h.AddGenerated(s, g)
                try:
                    deleted = bool(algo.IsDeleted(s))  # type: ignore[attr-defined]
                except Standard_Failure:
                    deleted = False
                if deleted:
                    h.Remove(s)
                    continue
                for m in _ask(algo, "Modified", s):
                    if not m.IsSame(s):
                        h.AddModified(s, m)
    return HistoryMap(h)


def from_algo(history: BRepTools_History) -> HistoryMap:
    """Wrap a boolean's / unify's own `History()` (merged, so it is a copy)."""
    h = BRepTools_History()
    h.Merge(history)
    return HistoryMap(h)


def follow(subshape: TopoDS_Shape, maps: Iterable[HistoryMap]) -> list[TopoDS_Shape]:
    """Successors of `subshape` through a chain of maps, oldest first.

    Fan-out is kept (a face split by a hole becomes two); a removal anywhere
    along the chain ends that branch, so an empty result means "gone" and
    naming.py falls back to the fingerprint, then refuses with candidates.
    """
    current = [subshape]
    for m in maps:
        nxt: list[TopoDS_Shape] = []
        for s in current:
            for t in m.successors(s):
                if not any(t.IsSame(u) for u in nxt):
                    nxt.append(t)
        current = nxt
        if not current:
            break
    return current


__all__ = ["HistoryMap", "follow", "from_algo", "record"]
