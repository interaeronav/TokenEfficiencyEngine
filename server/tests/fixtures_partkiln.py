"""A `KernelClient` made of arithmetic, so the partkiln adapter is testable anywhere.

A66 P4. `FakeKernel` implements the thirteen-method Protocol from
`partkiln/client.py` over boxes and cylinders computed by hand - no partkiln,
no OCP, no subprocess. That is what lets `TestPartkilnAdapterContract` run on
a CI box with neither the kernel nor a 250 MB OCCT wheel, and it is the
`fixtures_freecad.py` pattern: fake the C++ world, run the real code above it.

The arithmetic is not decorative. A rectangular extrude is `area x distance`;
a hole is `pi/4 d^2 depth` per instance; a fillet of radius r on a vertical
edge of height h removes `(1 - pi/4) r^2 h`; a chamfer removes `d^2/2 h`. On
F1 (100x60x10, four vertical edges) those give -34.336 for r2 and -80.000 for
d2 - the same numbers the real kernel pins - so a test written against the
fake is testing the same shape of answer, not a stub.

What the fake models faithfully, because the adapter depends on it:

* **A feature tree that regenerates.** Features keep their RAW props, so a
  `param_set` or a `set` re-resolves every one of them and reports Law 14's
  blast radius under `regen` - `changed` with a delta, `unchanged`, `failed`.
* **Atomic batches.** `apply` marks the state, and one refusal restores it,
  so the adapter's "the kernel already rolled back" claim is true here too.
* **`create object`** - the contract's generic kind - lands as a named BOM
  virtual component whose name survives a snapshot/restore round trip.
* **A closed verb set.** `verbs` answers create/set/delete/param_set only, so
  `export` and `check` take the adapter's deferred-method path, which is what
  production does whenever the kernel has not registered them as verbs.
"""

from __future__ import annotations

import copy
import hashlib
import json
import math
import re
from pathlib import Path
from typing import Any

# ISO 273 medium/close/free for the sizes the fixtures use. Real numbers with
# a real source, because a fake that invents 6.5 mm teaches the wrong habit.
CLEARANCE = {
    "M3": {"close": 3.2, "normal": 3.4, "loose": 3.6},
    "M4": {"close": 4.3, "normal": 4.5, "loose": 4.8},
    "M5": {"close": 5.3, "normal": 5.5, "loose": 5.8},
    "M6": {"close": 6.4, "normal": 6.6, "loose": 7.0},
    "M8": {"close": 8.4, "normal": 9.0, "loose": 10.0},
}
MATERIALS = {
    "steel_s275": {"density_kg_m3": 7850.0, "E_n_mm2": 210000.0, "honesty": "standard"},
    "aluminium_6082": {"density_kg_m3": 2700.0, "E_n_mm2": 70000.0, "honesty": "datasheet"},
}
UNITS_MM = {"mm": 1.0, "cm": 10.0, "m": 1000.0, "in": 25.4, "inch": 25.4, "ft": 304.8}
_NUMBER = re.compile(r"^\s*(-?\d+(?:\.\d+)?)\s*([a-z]*)\s*$", re.IGNORECASE)
VERBS = ("create", "delete", "param_set", "set")
METHODS = (
    "bom",
    "check",
    "drawing",
    "export",
    "flat",
    "import",
    "lint",
    "materials",
    "measure",
    "ping",
    "probe",
    "query",
    "script",
    "standards",
    "verbs",
)


class KernelRefusal(Exception):
    """What `partkiln.document.CommandError` looks like from outside: a code,
    a message that names the geometry, and the exact fix. Deliberately NOT a
    `TeeError` - the adapter's job is to map a foreign refusal into one, and
    a test that hands it a TeeError never exercises that map."""

    def __init__(self, code: str, message: str, fix: str = "") -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.fix = fix


def _blank() -> dict[str, Any]:
    return {
        "name": "untitled",
        "params": {},
        "order": [],
        "rows": {},
        "history": [],
        "current_part": None,
    }


class FakeKernel:
    """The partkiln `KernelClient` Protocol, in arithmetic."""

    def __init__(self) -> None:
        self.state = _blank()
        self.calls: list[tuple[str, dict[str, Any]]] = []  # every call(), for spies
        self.applied: list[list[dict[str, Any]]] = []  # every apply(), for spies
        self.closed = False
        self._snaps = 0

    # -- liveness ----------------------------------------------------------

    def probe(self) -> bool:
        return True

    def info(self) -> dict[str, Any]:
        return {
            "mode": "fake",
            "partkiln": "0.1.0-fake",
            "ocp": False,
            "occt": None,
            "warm": True,
            "name": self.state["name"],
            "commands": len(self.state["history"]),
            "fingerprint": self.fingerprint(),
            "parts": sum(1 for i in self.state["rows"] if i.startswith("part:")),
            "assemblies": 1 if any(i.startswith("cmp:") for i in self.state["rows"]) else 0,
            "drawings": sum(1 for i in self.state["rows"] if i.startswith("dwg:")),
        }

    def warm(self) -> dict[str, Any]:
        return {"import_s": 0.0, "rss_mb": 0.0, "occt": None, "mode": "fake", "ocp": False}

    def shutdown(self) -> None:
        self.closed = True

    # -- commands ----------------------------------------------------------

    def apply(self, commands: list[dict[str, Any]]) -> dict[str, Any]:
        """One transaction: a refusal at command k restores the state that
        existed before command 0 (Law 16), which is what lets the adapter say
        "the kernel rolled the batch back" without checking."""
        self.applied.append([dict(c) for c in commands])
        mark = copy.deepcopy(self.state)
        results: list[dict[str, Any]] = []
        try:
            for command in commands:
                results.append(self._one(dict(command)))
                self.state["history"].append(json.loads(json.dumps(command, default=str)))
        except Exception:
            self.state = mark
            raise
        return {
            "results": results,
            "fingerprint": self.fingerprint(),
            "commands": len(self.state["history"]),
        }

    def entities(self) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = [
            {
                "id": "doc",
                "kind": "doc",
                "name": self.state["name"],
                "units": "mm",
                "parts": sum(1 for i in self.state["rows"] if i.startswith("part:")),
                "commands": len(self.state["history"]),
                "fingerprint": self.fingerprint(),
            }
        ]
        rows.extend(
            {k: v for k, v in self.state["rows"][eid].items() if k not in ("raw", "spec")}
            for eid in self.state["order"]
        )
        return copy.deepcopy(rows)

    def detail(self, entity_id: str) -> dict[str, Any]:
        row = self.state["rows"].get(entity_id)
        if row is None and entity_id != "doc":
            raise KernelRefusal(
                "pk_ref_unknown",
                f"no entity {entity_id!r}.",
                fix=f"Known: {', '.join(self.state['order']) or '(none)'}.",
            )
        if entity_id == "doc":
            return dict(self.entities()[0])
        return {k: v for k, v in copy.deepcopy(row).items() if k != "raw"}

    def script(self) -> dict[str, Any]:
        return {
            "partkiln_script": 1,
            "name": self.state["name"],
            "commands": copy.deepcopy(self.state["history"]),
        }

    def fingerprint(self) -> str:
        payload = [
            [eid, round(float(self.state["rows"][eid].get("volume_mm3") or 0.0), 6)]
            for eid in sorted(self.state["order"])
        ]
        blob = json.dumps([payload, sorted(self.state["params"].items())], default=str)
        return hashlib.sha256(blob.encode()).hexdigest()[:16]

    # -- checkpoints (D3: the script is the state) -------------------------

    def snapshot(self, label: str, dir: str | Path) -> dict[str, Any]:
        directory = Path(dir)
        directory.mkdir(parents=True, exist_ok=True)
        stem = "".join(c if c.isalnum() or c in "_.-" else "_" for c in label) or "checkpoint"
        self._snaps += 1
        path = directory / f"{stem}-{len(self.state['history'])}-{self._snaps}.json"
        payload = {
            "partkiln_snapshot": 1,
            "label": label,
            "script": self.script(),
            "fingerprint": self.fingerprint(),
            "parts": {},
            "state": copy.deepcopy(self.state),
        }
        path.write_text(json.dumps(payload, indent=1, default=str), encoding="utf-8")
        return {
            "label": label,
            "path": str(path),
            "commands": len(self.state["history"]),
            "fingerprint": self.fingerprint(),
            "brep": False,
        }

    def restore(self, payload: dict[str, Any]) -> None:
        path = Path(str((payload or {}).get("path") or ""))
        if not path.is_file():
            raise KernelRefusal(
                "pk_checkpoint_missing",
                f"checkpoint {path} is gone.",
                fix="It may have been removed by tee_purge; take a new one.",
            )
        data = json.loads(path.read_text(encoding="utf-8"))
        self.state = copy.deepcopy(data["state"])

    def discard(self, payload: dict[str, Any]) -> None:
        path = Path(str((payload or {}).get("path") or ""))
        if path.is_file():
            path.unlink()

    # -- the generic door --------------------------------------------------

    def call(self, method: str, params: dict[str, Any]) -> Any:
        self.calls.append((str(method), dict(params or {})))
        handler = getattr(self, f"_m_{str(method).replace('import', 'import_')}", None)
        if handler is None:
            raise KernelRefusal(
                "pk_bad_op",
                f"unknown method {method!r}. The kernel answers: {', '.join(METHODS)}.",
                fix="call one of those.",
            )
        return handler(dict(params or {}))

    def _m_ping(self, params: dict[str, Any]) -> dict[str, Any]:
        return {"alive": True}

    def _m_probe(self, params: dict[str, Any]) -> dict[str, Any]:
        return {"alive": True, "ocp": False, "formats": ["step", "stl", "svg", "dxf"]}

    def _m_verbs(self, params: dict[str, Any]) -> dict[str, Any]:
        return {
            "verbs": list(VERBS),
            "kinds": ["part", "sketch", "extrude", "hole", "fillet", "chamfer", "object"],
        }

    def _m_lint(self, params: dict[str, Any]) -> dict[str, Any]:
        """Reads the batch; applies nothing. The spy in the adapter tests
        asserts exactly that by checking `applied` stayed empty."""
        problems: list[dict[str, Any]] = []
        for index, op in enumerate(params.get("batch") or []):
            if not isinstance(op, dict):
                problems.append({"at": index, "code": "pk_bad_request", "fix": "each op is {}"})
                continue
            if op.get("op") not in ("create", "set", "delete", "param_set", "export", "check"):
                problems.append(
                    {"at": index, "code": "pk_bad_op", "fix": f"verbs: {', '.join(VERBS)}"}
                )
            for key, value in (op.get("props") or {}).items():
                if isinstance(value, str) and _NUMBER.match(value):
                    try:
                        self._length(value)
                    except KernelRefusal as exc:
                        problems.append(
                            {"at": index, "prop": key, "code": exc.code, "fix": exc.fix}
                        )
        return {"ok": not problems, "problems": problems, "ops": len(params.get("batch") or [])}

    def _m_query(self, params: dict[str, Any]) -> dict[str, Any]:
        selector = str(params.get("selector") or "")
        names = self._resolve(selector) if selector else []
        return {
            "selector": selector,
            "names": names,
            "count": len(names),
            "tree": [eid for eid in self.state["order"] if eid.startswith("feat:")],
        }

    def _m_measure(self, params: dict[str, Any]) -> dict[str, Any]:
        what = str(params.get("what") or "mass")
        row = self.state["rows"].get(str(params.get("of") or ""), {})
        volume = float(row.get("volume_mm3") or 0.0)
        card = MATERIALS.get(str(params.get("material") or row.get("material") or "steel_s275"))
        density = float(params.get("density_kg_m3") or (card or {}).get("density_kg_m3") or 7850.0)
        if what == "mass":
            return {
                "what": "mass",
                "of": params.get("of"),
                "volume_mm3": round(volume, 3),
                "mass_g": round(volume * density / 1e6, 3),
                "density_kg_m3": density,
            }
        if what == "interference":
            return {"what": "interference", "pairs": [], "interference_mm3": 0.0}
        return {"what": what, "of": params.get("of"), "volume_mm3": round(volume, 3)}

    def _m_check(self, params: dict[str, Any]) -> dict[str, Any]:
        spec = dict(params.get("spec") or {})
        row = self.state["rows"].get(str(params.get("of") or ""), {})
        violations = []
        want = spec.get("volume_mm3")
        got = round(float(row.get("volume_mm3") or 0.0), 3)
        if want is not None and abs(float(want) - got) > 1e-3:
            violations.append(
                {"rule": "volume_mm3", "got": got, "limit": want, "fix": "adjust the feature"}
            )
        verdict = "pass" if not violations else "fail"
        if violations and params.get("strict"):
            raise KernelRefusal(
                "pk_op_failed",
                f"check failed: {violations[0]['rule']} got {violations[0]['got']}.",
                fix=str(violations[0]["fix"]),
            )
        return {"verdict": verdict, "violations": violations}

    def _m_standards(self, params: dict[str, Any]) -> dict[str, Any]:
        size = str(params.get("size") or "M6").upper()
        fit = str(params.get("fit") or "normal")
        row = CLEARANCE.get(size)
        if row is None:
            raise KernelRefusal(
                "pk_bad_request",
                f"no clearance row for {size}.",
                fix=f"Sizes: {', '.join(sorted(CLEARANCE))}.",
            )
        return {
            "size": size,
            "kind": str(params.get("kind") or "clearance"),
            "fit": fit,
            "dia_mm": row[fit],
            "source": "ISO 273 via bd_warehouse (Apache-2.0)",
        }

    def _m_materials(self, params: dict[str, Any]) -> dict[str, Any]:
        name = params.get("name")
        if name:
            card = MATERIALS.get(str(name))
            if card is None:
                raise KernelRefusal(
                    "pk_bad_request",
                    f"no material card {name!r}.",
                    fix=f"Cards: {', '.join(sorted(MATERIALS))}.",
                )
            return {"name": name, **card}
        return {"materials": {k: dict(v) for k, v in MATERIALS.items()}}

    def _m_bom(self, params: dict[str, Any]) -> dict[str, Any]:
        rows = []
        for eid in self.state["order"]:
            row = self.state["rows"][eid]
            if eid.startswith(("part:", "obj:")):
                rows.append(
                    {
                        "part": row.get("name"),
                        "qty": 1,
                        "material": row.get("material"),
                        "virtual": eid.startswith("obj:"),
                    }
                )
        return {"rows": rows, "parts": len(rows)}

    def _m_drawing(self, params: dict[str, Any]) -> dict[str, Any]:
        out = params.get("out")
        views = params.get("views") or [{"name": "front", "dir": "front"}]
        written = []
        if out:
            path = Path(str(out))
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(
                '<svg xmlns="http://www.w3.org/2000/svg" width="297mm" height="210mm"></svg>',
                encoding="utf-8",
            )
            written.append(str(path))
        return {
            "id": f"dwg:{params.get('name') or 'sheet1'}",
            "files": written,
            "views": [v.get("name") for v in views],
            "sheet": params.get("sheet") or "A4L",
            "projected_agree": True,
        }

    def _m_export(self, params: dict[str, Any]) -> dict[str, Any]:
        fmt = str(params.get("format") or "step")
        out = params.get("out")
        if not out:
            raise KernelRefusal(
                "pk_needs", "export needs out: a path.", fix='pass out="out/part.step".'
            )
        path = Path(str(out))
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f"FAKE-{fmt.upper()}\n", encoding="utf-8")
        return {
            "path": str(path),
            "bytes": path.stat().st_size,
            "format": fmt,
            "units": "mm",
            "declares_units": fmt in ("step", "glb", "3mf"),
            "roundtrip": {"volume_ok": True},
        }

    def _m_flat(self, params: dict[str, Any]) -> dict[str, Any]:
        k = float(params.get("k") or 0.44)
        return {"k": k, "ba_mm": round(90 * math.pi / 180 * (2 + k * 2), 3), "bends": 1}

    def _m_import_(self, params: dict[str, Any]) -> dict[str, Any]:
        name = str(params.get("name") or "imported")
        self._put(
            f"part:{name}",
            {
                "kind": "body",
                "name": name,
                "volume_mm3": 1000.0,
                "faces": 6,
                "edges": 12,
                "valid": True,
                "features": [],
                "height": 10.0,
            },
        )
        return {"id": f"part:{name}", "solids": 1, "units": "mm", "valid": True}

    def _m_script(self, params: dict[str, Any]) -> dict[str, Any]:
        return {**self.script(), "fingerprint": self.fingerprint()}

    # -- the command interpreter -------------------------------------------

    def _one(self, command: dict[str, Any]) -> dict[str, Any]:
        op = command.get("op")
        if op == "create":
            return self._create(command)
        if op == "set":
            return self._set(command)
        if op == "delete":
            return self._delete(command)
        if op == "param_set":
            return self._param_set(command)
        raise KernelRefusal(
            "pk_bad_op",
            f"unknown op {op!r}.",
            fix=f"partkiln accepts: {', '.join(VERBS)}.",
        )

    def _create(self, command: dict[str, Any]) -> dict[str, Any]:
        kind = str(command.get("kind"))
        props = dict(command.get("props") or {})
        name = str(command.get("name") or props.get("name") or f"{kind}{len(self.state['order'])}")
        if kind == "part":
            eid = f"part:{name}"
            self._put(
                eid,
                {
                    "kind": "body",
                    "name": name,
                    "material": props.get("material"),
                    "volume_mm3": 0.0,
                    "faces": 0,
                    "edges": 0,
                    "valid": True,
                    "features": [],
                    "height": 0.0,
                },
            )
            self.state["current_part"] = eid
            return {"id": eid, "kind": "body", "volume_mm3": 0.0}
        if kind == "sketch":
            eid = f"sk:{name}"
            area, entities = self._profile_area(props)
            self._put(
                eid,
                {
                    "kind": "sketch",
                    "name": name,
                    "plane": str(props.get("plane") or "XY"),
                    "entities": entities,
                    "constraints": 0,
                    "dof": 0,
                    "status": "ok",
                    "closed": True,
                    "area_mm2": round(area, 3),
                    "raw": props,
                },
            )
            return {"id": eid, "kind": "sketch", "area_mm2": round(area, 3), "dof": 0}
        if kind == "object":
            eid = f"obj:{name}"
            self._put(eid, {"kind": "object", "name": name, "virtual": True, **props})
            return {"id": eid, "kind": "object", "bom": "virtual component"}
        if kind in ("extrude", "hole", "fillet", "chamfer"):
            return self._feature(kind, name, props)
        eid = f"{_PREFIX.get(kind, 'obj')}:{name}"
        self._put(eid, {"kind": kind, "name": name, **props})
        return {"id": eid, "kind": kind}

    def _feature(self, kind: str, name: str, props: dict[str, Any]) -> dict[str, Any]:
        part_id = str(props.get("part") or self.state["current_part"] or "")
        if not part_id:
            part_id = f"part:{name}"
            self._put(
                part_id,
                {
                    "kind": "body",
                    "name": name,
                    "material": None,
                    "volume_mm3": 0.0,
                    "faces": 0,
                    "edges": 0,
                    "valid": True,
                    "features": [],
                    "height": 0.0,
                },
            )
            self.state["current_part"] = part_id
        eid = f"feat:{name}"
        self._put(eid, {"kind": kind, "name": name, "part": part_id, "raw": dict(props)})
        self.state["rows"][part_id]["features"].append(eid)
        report = self._rebuild(part_id)
        broken = next((f for f in report["failed"] if f["feature"] == name), None)
        if broken is not None:
            # A feature that cannot be built at all REFUSES now; only an edit
            # to an existing tree reports a failure and carries on (Law 14 is
            # about blast radius, not about accepting a broken create).
            self.state["order"].remove(eid)
            self.state["rows"].pop(eid, None)
            self.state["rows"][part_id]["features"].remove(eid)
            self._rebuild(part_id)
            raise KernelRefusal(broken["code"], broken["error"], broken["fix"])
        row = self.state["rows"][eid]
        return {
            "id": eid,
            "kind": kind,
            "part": part_id,
            "status": "ok",
            "volume_mm3": self.state["rows"][part_id]["volume_mm3"],
            "delta_mm3": row["delta_mm3"],
            "faces": self.state["rows"][part_id]["faces"],
            "assumed": row.get("assumed") or {},
            "resolved": row.get("resolved") or {},
            "regen": {part_id: report} if report["changed"] else None,
        }

    def _set(self, command: dict[str, Any]) -> dict[str, Any]:
        eid = str(command.get("id"))
        props = dict(command.get("props") or {})
        if eid == "doc":
            self.state["name"] = str(props.get("name") or self.state["name"])
            return {"id": "doc", "changed": sorted(props)}
        row = self.state["rows"].get(eid)
        if row is None:
            raise KernelRefusal(
                "pk_ref_unknown",
                f"no entity {eid!r} to set.",
                fix=f"Known ids: {', '.join(self.state['order']) or '(none)'}.",
            )
        if "name" in props:
            row["name"] = str(props["name"])
        if "raw" in row:
            row["raw"].update({k: v for k, v in props.items() if k != "name"})
        else:
            row.update({k: v for k, v in props.items() if k != "name"})
        part_id = row.get("part") or (eid if eid.startswith("part:") else None)
        out: dict[str, Any] = {"id": eid, "changed": sorted(props)}
        if part_id:
            report = self._rebuild(str(part_id))
            out["part"] = part_id
            out["regen"] = {str(part_id): report}
        return out

    def _delete(self, command: dict[str, Any]) -> dict[str, Any]:
        eid = str(command.get("id"))
        row = self.state["rows"].get(eid)
        if row is None:
            raise KernelRefusal(
                "pk_ref_unknown",
                f"no entity {eid!r} to delete.",
                fix=f"Known ids: {', '.join(self.state['order']) or '(none)'}.",
            )
        dependents = [f for f in self.state["order"] if self.state["rows"][f].get("part") == eid]
        if dependents and not command.get("cascade"):
            raise KernelRefusal(
                "pk_delete_blocked",
                f"{eid} still carries {len(dependents)} feature(s): {', '.join(dependents)}.",
                fix='pass {"props": {"cascade": true}} to delete them with it.',
            )
        gone = [eid, *dependents] if command.get("cascade") else [eid]
        part_id = row.get("part")
        for victim in gone:
            self.state["order"].remove(victim)
            self.state["rows"].pop(victim, None)
        if part_id and part_id in self.state["rows"]:
            self.state["rows"][part_id]["features"] = [
                f for f in self.state["rows"][part_id]["features"] if f not in gone
            ]
            report = self._rebuild(str(part_id))
            return {"deleted": eid, "cascaded": gone[1:], "part": part_id, **report}
        return {"deleted": eid, "cascaded": gone[1:]}

    def _param_set(self, command: dict[str, Any]) -> dict[str, Any]:
        changed = []
        assumed: dict[str, Any] = {}
        for name, raw in dict(command.get("params") or {}).items():
            old = self.state["params"].get(name)
            value, bare = self._length(raw)
            if bare:
                assumed.setdefault("units", "bare numbers read as mm (Law 12)")
            self.state["params"][name] = value
            changed.append({"name": name, "old": old, "new": value})
        regen = {
            part: self._rebuild(part) for part in self.state["order"] if part.startswith("part:")
        }
        out: dict[str, Any] = {"changed": changed, "regen": {k: v for k, v in regen.items() if v}}
        if assumed:
            out["assumed"] = assumed
        return out

    # -- geometry, by arithmetic -------------------------------------------

    def _rebuild(self, part_id: str) -> dict[str, Any]:
        """Re-resolve every feature of a part from its RAW props and report
        Law 14's blast radius: what changed, by how much, and what did not."""
        part = self.state["rows"].get(part_id)
        if part is None:
            return {"changed": [], "unchanged": 0, "failed": [], "volume_mm3": 0.0}
        volume = 0.0
        faces = 0
        height = 0.0
        changed: list[dict[str, Any]] = []
        unchanged = 0
        failed: list[dict[str, Any]] = []
        for eid in list(part["features"]):
            row = self.state["rows"].get(eid)
            if row is None:
                continue
            before = row.get("delta_mm3")
            try:
                delta, added, spec = self._delta(row, height)
            except KernelRefusal as exc:
                failed.append(
                    {
                        "feature": row["name"],
                        "error": exc.message,
                        "code": exc.code,
                        "fix": exc.fix,
                    }
                )
                row["status"] = "failed"
                continue
            row.update(spec)
            row["delta_mm3"] = round(delta, 3)
            row["status"] = "ok"
            volume += delta
            faces += added
            if row["kind"] == "extrude" and spec.get("distance"):
                height = max(height, float(spec["distance"]))
            if before is None or abs(float(before) - row["delta_mm3"]) > 1e-6:
                changed.append(
                    {"feature": row["name"], "delta_mm3": row["delta_mm3"], "faces": added}
                )
            else:
                unchanged += 1
        part["volume_mm3"] = round(volume, 3)
        part["faces"] = faces
        # An Euler-ish stand-in: enough for a diff to carry a count (and it
        # lands F1's 15 for 7 faces), never a topology claim.
        part["edges"] = max(3 * faces - 6, 0)
        part["height"] = height
        return {
            "changed": changed,
            "unchanged": unchanged,
            "failed": failed,
            "volume_mm3": part["volume_mm3"],
            "faces": faces,
        }

    def _delta(self, row: dict[str, Any], height: float) -> tuple[float, int, dict[str, Any]]:
        kind = row["kind"]
        raw = dict(row.get("raw") or {})
        spec: dict[str, Any] = {}
        if kind == "extrude":
            sketch = self.state["rows"].get(f"sk:{raw.get('sketch')}")
            if sketch is None:
                raise KernelRefusal(
                    "pk_ref_unknown",
                    f"extrude {row['name']}: no sketch {raw.get('sketch')!r}.",
                    fix="create the sketch first.",
                )
            if raw.get("distance") is None:
                raise KernelRefusal(
                    "pk_needs",
                    f"extrude {row['name']}: distance is required.",
                    fix='pass {"distance": "10mm"} or {"to": "<face>"}.',
                )
            distance, bare = self._length(raw["distance"])
            spec = {"distance": distance, "sketch": sketch["id"]}
            if bare:
                spec["assumed"] = {"units": "mm"}
            volume = float(sketch["area_mm2"]) * distance
            cut = str(raw.get("mode") or "").lower() == "cut"
            return (-volume if cut else volume), (0 if cut else 6), spec
        if kind == "hole":
            at = raw.get("at") or [[0, 0]]
            count = len(at) if isinstance(at, list) else 1
            if raw.get("dia") is not None:
                dia, _ = self._length(raw["dia"])
                spec["assumed"] = {}
            else:
                std = str(raw.get("std") or "M6 clearance normal").split()
                dia = CLEARANCE.get(std[0].upper(), CLEARANCE["M6"])[
                    std[2] if len(std) > 2 else "normal"
                ]
                spec["assumed"] = {
                    "dia": f"{dia}mm from ISO 273 {std[-1]} (bd_warehouse, Apache-2.0)",
                    "depth": "through",
                }
            depth = height or 10.0
            if raw.get("depth") not in (None, "through"):
                depth, _ = self._length(raw["depth"], depth)
            spec.update({"dia": dia, "depth": depth, "count": count})
            spec["resolved"] = {str(raw.get("on") or "part.end"): 1}
            return -math.pi / 4 * dia * dia * depth * count, count, spec
        edges = raw.get("edges")
        count = len(edges) if isinstance(edges, list) else self._edge_count(str(edges or ""))
        spec["resolved"] = {str(edges): count} if isinstance(edges, str) else {}
        if kind == "fillet":
            if raw.get("r") is None:
                raise KernelRefusal(
                    "pk_needs",
                    f"fillet {row['name']}: r has no safe default.",
                    fix='pass {"r": "5mm"} - a fillet radius is design intent.',
                )
            radius, _ = self._length(raw["r"])
            spec["r"] = radius
            return -(1 - math.pi / 4) * radius * radius * (height or 10.0) * count, count, spec
        if raw.get("d") is None:
            raise KernelRefusal(
                "pk_needs",
                f"chamfer {row['name']}: d has no safe default.",
                fix='pass {"d": "1mm"}.',
            )
        depth, _ = self._length(raw["d"])
        spec["d"] = depth
        return -(depth * depth / 2) * (height or 10.0) * count, count, spec

    def _edge_count(self, selector: str) -> int:
        """The fake's whole topology: a rectangular extrude has four vertical
        edges and one outer loop per cap. Enough for the adapter to prove it
        reports `resolved` counts; nowhere near enough to be a CAD kernel."""
        if not selector:
            return 1
        if "dir=Z" in selector:
            return 4
        if "loop=outer" in selector:
            return 4
        return 1

    def _resolve(self, selector: str) -> list[str]:
        head, _, _ = selector.partition(":")
        count = self._edge_count(selector)
        return [f"{head or 'part'}.edge[{i}]" for i in range(count)]

    def _profile_area(self, props: dict[str, Any]) -> tuple[float, int]:
        profiles = props.get("profile")
        if isinstance(profiles, dict):
            profiles = [profiles]
        area = 0.0
        entities = 0
        for index, profile in enumerate(profiles or []):
            if not isinstance(profile, dict):
                continue
            if "rect" in profile:
                w, _ = self._length(profile["rect"][0])
                h, _ = self._length(profile["rect"][1])
                one, edges = w * h, 4
            elif "circle" in profile:
                d, _ = self._length(profile["circle"])
                one, edges = math.pi * d * d / 4, 1
            elif "slot" in profile:
                length, _ = self._length(profile["slot"][0])
                width, _ = self._length(profile["slot"][1])
                one, edges = (length - width) * width + math.pi * width * width / 4, 4
            else:
                one, edges = 0.0, len(profile.get("poly") or [])
            area += one if index == 0 else -one
            entities += edges
        return area, entities

    def _length(self, value: Any, default: float | None = None) -> tuple[float, bool]:
        """`("12mm"|12|"W"|"0.5in") -> (mm, was_a_bare_number)`. Law 12: a
        bare number is millimetres and the diff says so once; an unknown
        suffix refuses and NAMES the suffixes this kernel takes."""
        if value is None:
            if default is None:
                raise KernelRefusal("pk_needs", "a length is required.", fix='pass e.g. "10mm".')
            return float(default), False
        if isinstance(value, int | float) and not isinstance(value, bool):
            return float(value), True
        text = str(value).strip()
        if text in self.state["params"]:
            return float(self.state["params"][text]), False
        match = _NUMBER.match(text)
        if match is None:
            raise KernelRefusal(
                "pk_bad_expr",
                f"cannot read {text!r} as a length.",
                fix=f"Use a number, a unit-suffixed string ({', '.join(sorted(UNITS_MM))}), "
                f"or a parameter name ({', '.join(sorted(self.state['params'])) or 'none set'}).",
            )
        number, suffix = float(match.group(1)), match.group(2).lower()
        if not suffix:
            return number, True
        if suffix not in UNITS_MM:
            raise KernelRefusal(
                "pk_unit_unknown",
                f"unknown unit {suffix!r} in {text!r}.",
                fix=f"Accepted: {', '.join(sorted(UNITS_MM))} (and deg/rad for angles).",
            )
        return number * UNITS_MM[suffix], False

    def _put(self, eid: str, row: dict[str, Any]) -> None:
        if eid not in self.state["rows"]:
            self.state["order"].append(eid)
        self.state["rows"][eid] = {"id": eid, **row}


_PREFIX = {
    "component": "cmp",
    "mate": "mate",
    "joint": "jt",
    "drawing": "dwg",
    "sheet": "sheet",
    "plane": "plane",
    "axis": "axis",
    "point": "point",
}

__all__ = ["CLEARANCE", "MATERIALS", "METHODS", "VERBS", "FakeKernel", "KernelRefusal"]
