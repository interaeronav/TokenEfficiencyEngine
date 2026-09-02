"""The Part: a feature list, the body it produces, its names, and its regen.

`regen(doc, from_index)` rebuilds the features from `from_index` in order
against the shape the previous feature left, and answers per feature
changed / unchanged / failed with the change in that feature's own
contribution (Law 14: an edit reports its blast radius). 'unchanged' means
the feature's `signature()` - its delta_mm3 to 3 dp, the names it made, its
resolved counts - is the same as before; the fillet on F2 stays 'unchanged'
when the plate thickness changes because it still rolls the same edge with
the same radius, while the through holes 'change' because they now remove
more. A feature whose rebuild refuses becomes `failed` with the refusal as
its error and the body passes through it, so the model sees exactly which
feature the edit broke instead of a whole-document refusal.

Everything the wire sees is a scalar (`summary()` is the D7 `part:` row);
the fingerprint is `brep.fingerprint.shape_fingerprint` (rounded before
hashing, identical in two processes - measured). A part restored from a
`.brep` cache (D3) has `cached = True`, features without shapes, and rebuilds
from 0 on its first edit. OCP is imported inside functions only.
"""

from __future__ import annotations

import copy
from dataclasses import dataclass, field
from typing import Any

from partkiln.document import CommandError
from partkiln.features.base import Feature, bbox_fields, build, r3
from partkiln.naming import Inventory, NameTable, build_inventory


@dataclass
class Part:
    name: str
    material: str | None = None
    features: list[Feature] = field(default_factory=list)
    names: NameTable = field(default_factory=NameTable)
    # Names a regen, rename or delete dropped: a reference to one is answered by
    # fingerprint when the geometry is still there, else refused with the event.
    stale: NameTable = field(default_factory=NameTable)
    shape: Any = field(default=None, repr=False, compare=False)
    cached: bool = False
    consumed_by: str | None = None
    _inventory: Inventory | None = field(default=None, repr=False, compare=False)
    _inventory_shape: Any = field(default=None, repr=False, compare=False)

    def __deepcopy__(self, memo: dict[int, Any]) -> Part:
        twin = Part(self.name, self.material)
        twin.features = [copy.deepcopy(f, memo) for f in self.features]
        twin.names = self.names.copy()
        twin.stale = self.stale.copy()
        twin.shape = self.shape
        twin.cached = self.cached
        twin.consumed_by = self.consumed_by
        twin._inventory = self._inventory
        twin._inventory_shape = self._inventory_shape
        return twin

    # -- lookups ----------------------------------------------------------

    def has_feature(self, fid: str) -> bool:
        return any(f.id == fid for f in self.features)

    def feature(self, ref: str) -> Feature:
        fid = str(ref)[5:] if str(ref).startswith("feat:") else str(ref)
        for f in self.features:
            if f.id == fid:
                return f
        known = ", ".join(f"feat:{f.id}" for f in self.features) or "(none)"
        raise CommandError(
            f"no feature {ref!r} in part {self.name}. Features: {known}.", code="pk_ref_unknown"
        )

    def index_of(self, fid: str) -> int:
        for i, f in enumerate(self.features):
            if f.id == fid:
                return i
        raise CommandError(f"no feature {fid!r} in part {self.name}.", code="pk_ref_unknown")

    def invalidate(self) -> None:
        self._inventory = None
        self._inventory_shape = None

    def retire(self, entries: list[Any]) -> None:
        for e in entries:
            self.stale.add(e)

    def event_for(self, fid: str) -> str:
        """What happened to a feature whose names are stale (for `pk_ref_stale`)."""
        feature = next((f for f in self.features if f.id == fid), None)
        if feature is None:
            return f"removed: feature {fid} was deleted or renamed"
        if feature.suppressed:
            return f"removed by {feature.kind} {fid} being suppressed"
        if feature.status == "failed":
            return f"removed: {feature.kind} {fid} failed ({feature.error[:80]})"
        return "not in the current body"

    def inventory(self) -> Inventory:
        """Faces and edges of the current shape, named; cached per shape."""
        if self.shape is None:
            raise CommandError(
                f"part {self.name} has no body yet; nothing to select on. Extrude a sketch first.",
                code="pk_ref_empty",
            )
        if (
            self._inventory is None
            or self._inventory_shape is None
            or not self._inventory_shape.IsSame(self.shape)
        ):
            self._inventory = build_inventory(self)
            self._inventory_shape = self.shape
        return self._inventory

    def names_snapshot(self) -> dict[str, Any]:
        """Every current face name with the fingerprint of the face AS IT IS NOW
        (D3: the entry's own key is the face at creation, before later features
        trimmed it; a restore that matches by fingerprint needs today's key)."""
        if self.shape is None:
            return self.names.as_dict()
        from partkiln.naming import NameEntry, key_of

        inv = self.inventory()
        out: dict[str, Any] = {}
        for name, i in sorted(inv.aliases.items()):
            entry = self.names.get(name) or self.names.get(name.split("[", 1)[0])
            feature = entry.feature if entry is not None else self.name
            role = entry.role if entry is not None else name.split(".", 1)[-1]
            index = entry.index if entry is not None else 0
            out[name] = NameEntry(
                name, "face", feature, role, index, key_of(inv.faces[i])
            ).as_dict()
        return out

    def history_maps(self) -> dict[int, Any]:
        return {
            i: f.history for i, f in enumerate(self.features) if f.active and f.history is not None
        }

    # -- numbers ----------------------------------------------------------

    def volume(self) -> float:
        from partkiln.brep import shapes

        return shapes.volume(self.shape) if self.shape is not None else 0.0

    def mass_g(self) -> float | None:
        if self.material is None or self.shape is None:
            return None
        from partkiln.materials import mass_g

        return mass_g(self.material, self.volume())

    def fingerprint(self) -> str:
        if self.shape is None:
            return "empty"
        from partkiln.brep import fingerprint

        return fingerprint.shape_fingerprint(self.shape)

    def summary(self) -> dict[str, Any]:
        """The D7 `part:` row - scalars only - plus one concise row per feature."""
        out: dict[str, Any] = {
            "id": f"part:{self.name}",
            "kind": "body",
            "material": self.material,
            "features": len(self.features),
            "cached": self.cached,
        }
        if self.consumed_by:
            out["consumed_by"] = self.consumed_by
        if self.shape is None:
            out.update(
                {"volume_mm3": 0.0, "solids": 0, "faces": 0, "edges": 0, "fingerprint": "empty"}
            )
        else:
            from partkiln.brep import shapes

            counts = shapes.counts(self.shape)
            out.update(
                {
                    "volume_mm3": r3(self.volume()),
                    "area_mm2": r3(shapes.area(self.shape)),
                    **bbox_fields(shapes.bbox(self.shape)),
                    "com_mm": [r3(c) for c in shapes.centre_of_mass(self.shape)],
                    "solids": counts["solids"],
                    "faces": counts["faces"],
                    "edges": counts["edges"],
                    "valid": shapes.is_valid(self.shape),
                    "names": len(self.names),
                    "fingerprint": self.fingerprint(),
                }
            )
            mass = self.mass_g()
            if mass is not None:
                out["mass_g"] = mass
        out["tree"] = [f.row() for f in self.features]
        return out

    # -- building -----------------------------------------------------------

    def add_feature(self, doc: Any, feature: Feature, assumed: dict[str, Any]) -> dict[str, Any]:
        """Append and build one feature; a refusal removes it again and re-raises."""
        if self.has_feature(feature.id):
            raise CommandError(
                f"feature {feature.id!r} already exists in part {self.name}. Use set to change "
                "it, or pick another name.",
                code="pk_ref_ambiguous",
            )
        if self.cached:
            self.regen(doc, 0)
        index = len(self.features)
        self.features.append(feature)
        try:
            build(doc, self, feature, index, assumed)
        except CommandError:
            self.features.pop()
            self.retire(self.names.drop_feature(feature.id))
            raise
        self._register_deps(doc, feature)
        return feature.details()

    def _register_deps(self, doc: Any, feature: Feature) -> None:
        fid = f"feat:{feature.id}"
        for name, users in doc.params.users.items():
            if name not in feature.param_deps:
                users.discard(fid)
        for name in feature.param_deps:
            doc.params.users.setdefault(name, set()).add(fid)

    def regen(self, doc: Any, from_index: int = 0) -> dict[str, Any]:
        """Rebuild features[from_index:] and report the blast radius (Law 14)."""
        if self.cached:
            from_index = 0
            self.cached = False
        from_index = max(0, min(from_index, len(self.features)))
        before = {f.id: f.signature() for f in self.features[from_index:]}
        self.retire(self.names.drop_from(from_index))
        self.shape = self.features[from_index - 1].shape if from_index > 0 else None
        self.invalidate()
        changed: list[dict[str, Any]] = []
        unchanged: list[str] = []
        failed: list[dict[str, Any]] = []
        for i in range(from_index, len(self.features)):
            feature = self.features[i]
            assumed: dict[str, Any] = {}
            prior = feature.signature() if feature.id in before else None
            try:
                build(doc, self, feature, i, assumed)
            except CommandError as exc:
                feature.status = "failed"
                feature.error = str(exc)
                feature.shape, feature.history = self.shape, None
                feature.volume, feature.delta_mm3 = self.volume(), 0.0
                failed.append({"feature": feature.id, "error": str(exc), "code": exc.code})
                continue
            self._register_deps(doc, feature)
            if feature.suppressed:
                unchanged.append(feature.id)
                continue
            if prior is not None and prior == feature.signature():
                unchanged.append(feature.id)
            else:
                old_delta = (
                    before[feature.id][1]
                    if feature.id in before and before[feature.id][0] == "ok"
                    else 0.0
                )
                changed.append(
                    {
                        "feature": feature.id,
                        "delta_mm3": r3(feature.delta_mm3 - old_delta),
                        "faces": feature.faces,
                    }
                )
        report: dict[str, Any] = {
            "changed": changed,
            "unchanged": len(unchanged),
            "failed": failed,
            "volume_mm3": r3(self.volume()),
            "faces": self.features[-1].faces if self.features else 0,
            "fingerprint": self.fingerprint(),
        }
        if unchanged and len(unchanged) <= 8:
            report["unchanged_features"] = unchanged
        return report


__all__ = ["Part"]
