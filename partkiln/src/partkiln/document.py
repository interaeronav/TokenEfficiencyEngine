"""The document: one command model, shared by every client.

seamkiln's architecture, carried over whole (A66 script, "Context"): a
Document holds the model, every mutation is a Command, every Command is
recorded, `script()` hands the list back and `replay(script)` rebuilds the
same model - checked by `fingerprint()`, not by eye. The incumbent's
automation is a Windows COM API or a metered cloud sandbox; here the script
IS the product, and there is no path through any interface (TEE batch, a
future GUI) that a script cannot take.

Law 16: the checkpoint is the script. A command that refuses leaves the
document exactly as it was - `apply` snapshots the model state and restores
it on a `CommandError`, so a batch can never half-land.

The verb table is closed and enumerable (D5): an unknown op lists every
verb. It is also open to the later phases by import - `register_verb` and
`register_kind` let P2's features and P3's assemblies add themselves without
this file knowing they exist, and `fingerprint_sources` / `dependency_sources`
are the two hooks they append to. P2c fills the `parts` container: the
verbs live in `partkiln.features` and are imported lazily the first time a
`create` names a kind this file does not know, so `import partkiln` stays
OCP-free. D3: `snapshot()` writes the script (the checkpoint) plus one
`.brep` per part (a cache), and `restore()` takes the cache only when every
file exists and the recomputed fingerprint matches - otherwise it replays,
which is the law. Nothing here imports OCP, Qt or tee.
"""

from __future__ import annotations

import copy
import json
import re
import time
from collections.abc import Callable
from dataclasses import dataclass, field, fields
from hashlib import sha256
from pathlib import Path
from typing import Any

SCRIPT_VERSION = 1

# D5: a name is short, lower-case, and safe in a selector.
_NAME = re.compile(r"^[a-z0-9_]{1,24}$")
# The D7 id prefixes P3's assembly verbs own: `set`/`delete` route to them.
_ASSEMBLY_IDS = ("cmp:", "mate:", "jt:", "asm")
# Keys the wire shape puts beside the props; never a parameter name.
_WIRE_KEYS = ("kind", "name", "id")
# The document settings every recorded command was interpreted under (Law 12:
# a bare number is the DOCUMENT's millimetre or degree). They ride in the
# script so a `regen()` or a `replay()` rebuilds the same geometry rather than
# re-reading the same commands under whatever `set doc` said last.
_SETTINGS: tuple[str, ...] = ("units", "angle_unit", "standard", "drawing_angle", "strict_units")


class CommandError(ValueError):
    """A command that cannot be carried out. Always names the reason and the fix.

    `code` is the D8 refusal code (`pk_bad_op`, `pk_unit_kind`, ...) for the
    adapter; the message is for the model that has to act on it.
    """

    def __init__(self, message: str, *, code: str = "pk_op_failed") -> None:
        super().__init__(message)
        self.code = code


@dataclass(frozen=True, slots=True)
class Command:
    op: str
    args: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {"op": self.op, "args": dict(self.args)}

    @staticmethod
    def from_dict(raw: dict[str, Any]) -> Command:
        """Accept both the script shape `{op, args}` and TEE's wire shape
        `{op, kind, name, id, props}`. On the wire, `kind`/`name`/`id` are
        folded INTO args (they stay addressable as `args["kind"]`) and
        `props` is merged over them."""
        if not isinstance(raw, dict) or "op" not in raw:
            raise CommandError(
                f"{raw!r} has no 'op'. Every command names a verb.", code="pk_bad_op"
            )
        args = raw.get("args")
        if args is None:
            args = {k: v for k, v in raw.items() if k not in ("op", "props", "args")}
            props = raw.get("props") or {}
            if not isinstance(props, dict):
                raise CommandError("'props' must be an object of field: value.", code="pk_bad_op")
            args.update(props)
        elif not isinstance(args, dict):
            raise CommandError("'args' must be an object of field: value.", code="pk_bad_op")
        return Command(op=str(raw["op"]), args=dict(args))


Handler = Callable[["Document", dict[str, Any], dict[str, Any]], dict[str, Any]]

# The phase modules that register verbs and `create` kinds, in the order a
# refusal should list them. They are imported the FIRST time a command names
# something this file does not know (an unknown op or an unknown create kind),
# so `import partkiln` stays OCP-free and a P1 document never pays for the
# feature, assembly, drawing or sheet-metal layers. Each import is guarded:
# a phase that is not built yet (its package has no `verbs` module) is simply
# skipped, and the refusal that follows names only what is actually served.
_VERB_MODULES = (
    "partkiln.features",
    "partkiln.assembly.verbs",
    "partkiln.drawing.verbs",
    "partkiln.sheetmetal.verbs",
    # `create import` lives with the `pk_import` backend, and a REPLAY in a
    # fresh process (a checkpoint restored anywhere but the kernel that took
    # it) has to find that kind or the imported body cannot be rebuilt - so
    # the methods module is loaded here too, not only by `LocalKernel.call`.
    "partkiln.methods",
)
_MODULES_LOADED = [False]

_VERBS: dict[str, Handler] = {}
_KINDS: dict[str, Handler] = {}  # `create` kinds: sketch here; part/extrude/... from P2 on


def load_verb_modules() -> tuple[str, ...]:
    """Import every phase module once; returns the ones that were there.

    Idempotent and cheap after the first call. An `ImportError` means the
    phase does not ship in this build (or its optional dependency is
    missing), which is a gap to be named, never a crash inside `apply`.
    """
    if _MODULES_LOADED[0]:
        return _VERB_MODULES
    import importlib

    loaded: list[str] = []
    for name in _VERB_MODULES:
        try:
            importlib.import_module(name)
        except ImportError:
            continue
        loaded.append(name)
    _MODULES_LOADED[0] = True
    return tuple(loaded)


def register_verb(name: str) -> Callable[[Handler], Handler]:
    """Add a verb by importing the module that defines it."""

    def wrap(handler: Handler) -> Handler:
        _VERBS[name] = handler
        return handler

    return wrap


def register_kind(name: str) -> Callable[[Handler], Handler]:
    """Add a `create` kind the same way."""

    def wrap(handler: Handler) -> Handler:
        _KINDS[name] = handler
        return handler

    return wrap


def __getattr__(name: str) -> Any:
    # `VERBS` is a tuple that is always current, even after P2 registers
    # more verbs; a module attribute computed at import would go stale.
    if name == "VERBS":
        return tuple(sorted(_VERBS))
    if name == "KINDS":
        return tuple(sorted(_KINDS))
    raise AttributeError(name)


def _new_params() -> Any:
    from partkiln.params import Params

    return Params()


@dataclass
class Document:
    """A mechanical CAD document, and the script that produced it.

    `parts`, `assemblies`, `drawings` and `sheets` are containers for the
    later phases, keyed by name: `parts[name]` will hold a P2 Part (feature
    list + cached shape), `assemblies[name]` a P3 Assembly (components,
    mates, joints), `drawings[name]` a P5a Drawing (views, dims, files) and
    `sheets[name]` a P5b Sheet (flat + bends). P1 creates none of them.
    """

    name: str = "untitled"
    units: str = "mm"
    angle_unit: str = "deg"
    standard: str = "ISO"
    drawing_angle: str = "first"
    strict_units: bool = False
    params: Any = field(default_factory=_new_params)
    sketches: dict[str, Any] = field(default_factory=dict)
    parts: dict[str, Any] = field(default_factory=dict)
    assemblies: dict[str, Any] = field(default_factory=dict)
    drawings: dict[str, Any] = field(default_factory=dict)
    sheets: dict[str, Any] = field(default_factory=dict)
    datums: dict[str, Any] = field(default_factory=dict)
    history: list[Command] = field(default_factory=list)
    restored_via: str = ""
    # P2+ append callables here: each returns bytes that join the fingerprint.
    fingerprint_sources: list[Callable[[Document], bytes]] = field(default_factory=list)
    # P2+ append callables here: each returns the ids that depend on an id.
    dependency_sources: list[Callable[[Document, str], list[str]]] = field(default_factory=list)
    _echoed: set[str] = field(default_factory=set, repr=False, compare=False)
    # The settings the commands in `history` were recorded under. `set doc`
    # moves the live settings; this does not - it is what `script()` writes and
    # what `regen()`/`replay()` restore before the first command (defect 1).
    _origin: dict[str, Any] = field(default_factory=dict, repr=False, compare=False)
    # D3 restore: {part name: {shape, names}} consumed by `create part` during a replay.
    _cache: dict[str, Any] = field(default_factory=dict, repr=False, compare=False)
    _cache_building: bool = field(default=False, repr=False, compare=False)

    def __post_init__(self) -> None:
        """Pin the settings the script will be recorded under, and tell the
        parameter table what a bare number in an expression means."""
        if not self._origin:
            self._origin = self.settings()
        self.params.default_unit = self.units
        self.params.default_angle_unit = self.angle_unit

    def settings(self) -> dict[str, Any]:
        """The five document settings that decide what a command MEANS."""
        return {key: getattr(self, key) for key in _SETTINGS}

    # -- the script ---------------------------------------------------------

    def script(self) -> dict[str, Any]:
        """Everything needed to rebuild this document, and nothing else.

        `settings` is the unit/standard state the commands were RECORDED
        under, not today's: a script recorded in mm and then switched to
        inches replays as the millimetre model it was (Law 12, Law 16).
        """
        return {
            "partkiln_script": SCRIPT_VERSION,
            "name": self.name,
            "settings": dict(self._origin),
            "commands": [c.as_dict() for c in self.history],
        }

    def save_script(self, path: str | Path) -> Path:
        destination = Path(path)
        destination.write_text(json.dumps(self.script(), indent=2), encoding="utf-8")
        return destination

    @classmethod
    def replay(
        cls,
        script: dict[str, Any] | str | Path,
        overrides: dict[str, Any] | None = None,
        cache: dict[str, Any] | None = None,
    ) -> Document:
        """Rebuild a document from a script. Same script in, same fingerprint out.

        `overrides` is the part family in one argument: `{"t": "8mm"}` rewrites
        the value of `t` in every `param_set` command that sets it, BEFORE the
        replay, so the whole model regenerates against the new value. A name
        no `param_set` in the script sets is refused - a silent no-op would be
        a family member that quietly is not one.
        """
        if isinstance(script, str | Path):
            script = json.loads(Path(script).read_text(encoding="utf-8"))
        version = script.get("partkiln_script")
        if version != SCRIPT_VERSION:
            raise CommandError(
                f"script version {version!r} is not {SCRIPT_VERSION}. "
                "Re-export it from the version of partkiln that wrote it.",
                code="pk_bad_op",
            )
        commands = [Command.from_dict(raw) for raw in script.get("commands", [])]
        if overrides:
            commands, unmatched = _override(commands, overrides)
            if unmatched:
                names = sorted(
                    {k for c in commands if c.op == "param_set" for k in _assignments(c.args)}
                )
                raise CommandError(
                    f"overrides name {', '.join(sorted(unmatched))}, which no param_set in the "
                    f"script sets. Script parameters: {', '.join(names) or '(none)'}. "
                    "Add a param_set for it first.",
                    code="pk_ref_unknown",
                )
        document = cls(name=str(script.get("name", "replayed")), **_script_settings(script))
        if cache:
            document._cache = dict(cache)
        for command in commands:
            document.apply(command)
        document._cache = {}
        return document

    def fingerprint(self) -> str:
        """16 hex of sha256 over the model, rounded before hashing (rule 7).

        Name and settings, parameters (name, value to 6 dp), every sketch's
        tag-sorted solved coordinates to 6 dp, then whatever the later phases
        registered in `fingerprint_sources`, in registration order.
        """
        payload = {
            "name": self.name,
            "units": self.units,
            "angle_unit": self.angle_unit,
            "standard": self.standard,
            "drawing_angle": self.drawing_angle,
            "strict_units": self.strict_units,
            "params": [
                [p.name, round(p.value, 6) + 0.0] for p in sorted(self.params, key=lambda p: p.name)
            ],
            "sketches": {
                name: {
                    "plane": sk.plane,
                    "coords": sk.coordinates(),
                    # What a batch can change and the solve cannot erase
                    # (defect 3): two sketches that solve to the same points
                    # are not the same sketch if one line is construction, one
                    # curve is an arc, one constraint is missing or one
                    # dimension is driven instead of driving.
                    "entities": [_hash_row(sk.entities[t]) for t in sorted(sk.entities)],
                    "constraints": [_hash_row(c) for c in sk.constraints],
                    "dims": [_hash_row(d) for d in sk.dims],
                }
                for name, sk in sorted(self.sketches.items())
            },
            "datums": [
                [d.name, d.kind, _r6(d.origin), _r6(d.direction)]
                for d in sorted(self.datums.values(), key=lambda d: d.name)
            ],
        }
        if self.parts:
            from partkiln.features import fingerprint_payload

            payload["parts"] = fingerprint_payload(self)
        if self.assemblies:
            # Same shape as the parts hook, and the same reason it is a hook:
            # D3 says the poses (rounded to 1e-6) join the fingerprint, and a
            # document with no assembly must hash exactly as it did before P3
            # existed - so the key appears only when there is one.
            from partkiln.assembly.verbs import fingerprint_payload as assembly_payload

            payload["assemblies"] = assembly_payload(self)
        parts = [json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()]
        parts.extend(source(self) for source in self.fingerprint_sources)
        return sha256(b"|".join(parts)).hexdigest()[:16]

    # -- applying commands --------------------------------------------------

    def apply(self, command: Command | dict[str, Any]) -> dict[str, Any]:
        """Carry out one command and record it. The ONLY way state changes."""
        if isinstance(command, dict):
            command = Command.from_dict(command)
        handler = _VERBS.get(command.op)
        if handler is None:
            # A later phase may own this verb: load them, then decide.
            load_verb_modules()
            handler = _VERBS.get(command.op)
        if handler is None:
            raise CommandError(
                f"unknown op {command.op!r}. partkiln accepts: {', '.join(sorted(_VERBS))}.",
                code="pk_bad_op",
            )
        snapshot = self._snapshot()
        assumed: dict[str, Any] = {}
        try:
            result = handler(self, dict(command.args), assumed)
        except CommandError:
            self._restore(snapshot)
            raise
        except Exception as exc:
            # A handler bug is still a failed command: Law 16 says a failed
            # batch never advances state, and rule 6 says the caller gets one
            # line naming it, not a traceback.
            self._restore(snapshot)
            raise CommandError(
                f"{command.op} failed inside the kernel: {type(exc).__name__}: {exc}. "
                "The document is unchanged; report this with the command that caused it.",
                code="pk_op_failed",
            ) from exc
        if assumed:
            result.setdefault("assumed", {}).update(assumed)
        self.history.append(command)
        return result

    def regen(self, from_index: int = 0) -> dict[str, Any]:
        """Re-derive the model from its own history.

        P1 keeps no per-command cache, so every command is re-run from the
        first; `from_index` is where the edit that asked for the regen sits,
        and the report counts from there. P2's B-rep cache (D3) is what will
        make the index save work.

        Two laws meet here. Law 12: the replay starts from the settings the
        commands were RECORDED under (`_origin`), not from whatever `set doc`
        said last - otherwise the same commands rebuild a different model and
        still call it the same fingerprint. Law 16: a failed regen never
        advances state - the whole document is put back exactly as it was and
        the refusal names the command that stopped it.
        """
        if not 0 <= from_index <= len(self.history):
            raise CommandError(
                f"from_index {from_index} is outside the history (0..{len(self.history)}).",
                code="pk_ref_unknown",
            )
        history = list(self.history)
        saved = self._snapshot()
        self._reset_to_origin()
        index = 0
        try:
            for index, command in enumerate(history):  # noqa: B007 - named in the refusal
                self.apply(command)
        except CommandError as exc:
            self._restore(saved)
            raise CommandError(
                f"regen stopped at command {index} of {len(history)} "
                f"({_label(command)}): {exc} Nothing was rebuilt: the document keeps its "
                "parts, sketches, parameters and history exactly as they were.",
                code=exc.code,
            ) from exc
        return {
            "reapplied": len(history) - from_index,
            "commands": len(history),
            "fingerprint": self.fingerprint(),
        }

    def _reset_to_origin(self) -> None:
        """Empty every container and put the settings back to the ones the
        history was recorded under - the state the first command saw."""
        for key, value in self._origin.items():
            if key in _SETTINGS:
                setattr(self, key, value)
        self.params = _new_params()
        self.params.default_unit = self.units
        self.params.default_angle_unit = self.angle_unit
        self.sketches, self.parts, self.assemblies = {}, {}, {}
        self.drawings, self.sheets, self.datums = {}, {}, {}
        self.history.clear()
        self._echoed = set()

    def _snapshot(self) -> tuple[Any, ...]:
        settings = (
            self.name,
            self.units,
            self.angle_unit,
            self.standard,
            self.drawing_angle,
            self.strict_units,
        )
        model = (
            self.params,
            self.sketches,
            self.parts,
            self.assemblies,
            self.drawings,
            self.sheets,
            self.datums,
        )
        return settings, copy.deepcopy(model), set(self._echoed), list(self.history)

    def _restore(self, snapshot: tuple[Any, ...]) -> None:
        settings, model, echoed, history = snapshot
        self._echoed = echoed
        # The history rides along so a caller that replays the WHOLE script
        # (regen, a batch rollback) can be put back whole; inside `apply` the
        # command is recorded after the handler, so this is a no-op there.
        self.history[:] = history
        (
            self.name,
            self.units,
            self.angle_unit,
            self.standard,
            self.drawing_angle,
            self.strict_units,
        ) = settings
        (
            self.params,
            self.sketches,
            self.parts,
            self.assemblies,
            self.drawings,
            self.sheets,
            self.datums,
        ) = model

    def summary(self) -> dict[str, Any]:
        """Compact state. Never geometry - hard rule 1, in the core itself."""
        return {
            "name": self.name,
            "units": self.units,
            "angle": self.drawing_angle,
            "standard": self.standard,
            "params": len(self.params),
            "sketches": [
                {
                    "id": f"sk:{name}",
                    "plane": sk.plane,
                    "dof": sk.solution.dof if sk.solution is not None else None,
                    "status": sk.solution.status if sk.solution is not None else "unsolved",
                    "closed": sk.closed(),
                }
                for name, sk in sorted(self.sketches.items())
            ],
            "parts": [self.parts[n].summary() for n in sorted(self.parts)],
            "datums": [self.datums[n].as_dict() for n in sorted(self.datums)],
            "assemblies": len(self.assemblies),
            "drawings": len(self.drawings),
            "sheets": len(self.sheets),
            "commands": len(self.history),
            "fingerprint": self.fingerprint(),
        }

    # -- D7: the entity rows ------------------------------------------------

    def entities(self) -> list[dict[str, Any]]:
        """Every entity a batch can change, one concise row (~20 tok) each.

        The A65 lesson, applied here: what is not a row is invisible to the
        scene cache, so parameters, datums, sketches, features, bodies,
        components, mates, joints, the assembly, and whatever the drawing and
        sheet-metal phases put in their containers all get one. Scalars only -
        never a coordinate list, never a mesh (hard rule 1); `detail(id)` is
        the opt-in second look.
        """
        rows: list[dict[str, Any]] = [self._doc_row()]
        for param in sorted(self.params, key=lambda p: p.name):
            row = param.as_dict()
            rows.append(
                {
                    "id": f"param:{param.name}",
                    "kind": "param",
                    "name": param.name,
                    "value": row["value"],
                    "unit": row["unit"],
                    "expr": row["expr"],
                    "used_by": len(self.params.used_by(param.name)),
                }
            )
        for name in sorted(self.datums):
            datum = self.datums[name]
            row = dict(datum.as_dict())
            row.setdefault("name", name)
            rows.append(row)
        for name in sorted(self.sketches):
            rows.append(_sketch_row(self, name, self.sketches[name]))
        for name in sorted(self.parts):
            part = self.parts[name]
            rows.append(_part_row(part))
            rows.extend(_feature_row(self, part, f) for f in part.features)
        for attr, prefix in _CONTAINERS:
            container = getattr(self, attr, None) or {}
            for name in sorted(container):
                rows.extend(_container_rows(container[name], name, prefix))
        return rows

    def detail(self, entity_id: str) -> dict[str, Any]:
        """One entity in full - still scalars only (D7: `tee_entity_detail` adds
        numbers, never geometry). An unknown id names the ids that exist."""
        eid = str(entity_id)
        if eid == "doc":
            out = self._doc_row()
            out["params"] = self.params.names()
            out["part_names"] = sorted(self.parts)
            out["sketch_names"] = sorted(self.sketches)
            out["restored_via"] = self.restored_via
            return out
        prefix, _, name = eid.partition(":")
        if prefix == "param":
            param = self.params.get(name)
            return {
                "id": eid,
                "kind": "param",
                **param.as_dict(),
                "used_by": self.params.used_by(name),
            }
        if prefix in ("plane", "axis", "point") and name in self.datums:
            return {**self.datums[name].as_dict(), "name": name}
        if prefix == "sk" or eid in self.sketches:
            sketch = self.sketch(eid)
            return {
                **_sketch_row(self, sketch.name, sketch),
                "dims": [d.describe() for d in sketch.dims],
                "constraints": [c.describe() for c in sketch.constraints],
                "params": sorted(sketch.param_deps),
            }
        if prefix == "part" and name in self.parts:
            part = self.parts[name]
            return {**part.summary(), "name": name, "used_by": self.dependents_of(eid)}
        if prefix == "feat":
            for part in self.parts.values():
                if part.has_feature(name):
                    feature = part.feature(name)
                    return {
                        **_feature_row(self, part, feature),
                        **feature.details(),
                        "args": {k: v for k, v in feature.args.items() if _scalar(v)},
                        "downstream": self.dependents_of(eid),
                    }
        for attr, container_prefix in _CONTAINERS:
            container = getattr(self, attr, None) or {}
            for item_name in sorted(container):
                item = container[item_name]
                own = getattr(item, "detail", None)
                if callable(own):
                    try:
                        found = own(eid)
                    except CommandError:
                        continue
                    if found:
                        return dict(found)
                if eid in (container_prefix, f"{container_prefix}:{item_name}"):
                    rows = _container_rows(item, item_name, container_prefix)
                    if rows:
                        return dict(rows[0])
        known = ", ".join(str(row["id"]) for row in self.entities())[:600]
        raise CommandError(
            f"no entity {eid!r}. Entities: {known}.",
            code="pk_ref_unknown",
        )

    def _doc_row(self) -> dict[str, Any]:
        parts = sum(1 for _ in self.parts)
        return {
            "id": "doc",
            "kind": "doc",
            "name": self.name,
            "units": self.units,
            "angle": self.drawing_angle,
            "standard": self.standard,
            "strict_units": self.strict_units,
            "parts": parts,
            "sketches": len(self.sketches),
            "features": sum(len(p.features) for p in self.parts.values()),
            "components": sum(_component_count(a) for a in self.assemblies.values()),
            "assemblies": len(self.assemblies),
            "drawings": len(self.drawings),
            "sheets": len(self.sheets),
            "script_commands": len(self.history),
            "fingerprint": self.fingerprint(),
        }

    def dependents_of(self, entity_id: str) -> list[str]:
        """Ids that would break if `entity_id` went. P1 has none; P2's
        features register themselves through `dependency_sources`."""
        found: list[str] = []
        for source in self.dependency_sources:
            found.extend(source(self, entity_id))
        if self.parts:
            from partkiln.features import dependents

            found.extend(dependents(self, entity_id))
        return sorted(set(found))

    # -- D3: the checkpoint is the script, the B-rep is a cache ----------------

    def snapshot(self, label: str, directory: str | Path) -> dict[str, Any]:
        """Write `<label>-<ms>.json` (script, fingerprint, names per part) and one
        `<label>-<ms>-<part>.brep` per part with a body. Scalars back:
        `{label, path, commands, fingerprint, brep, caches}` (the KernelClient
        shape).

        `caches` names the `.brep` siblings this call wrote, as file names
        beside `path` - short enough to stay a scalar row (D3), and the only
        way `discard()` can clear a cache it did not open the json to find.
        """
        folder = Path(directory)
        folder.mkdir(parents=True, exist_ok=True)
        stem = re.sub(r"[^A-Za-z0-9_.-]+", "_", str(label)).strip("._-") or "checkpoint"
        json_path = folder / f"{stem}-{int(time.time() * 1000)}.json"
        bump = 0
        while json_path.exists():
            bump += 1
            json_path = folder / f"{stem}-{int(time.time() * 1000)}-{bump}.json"
        parts: dict[str, Any] = {}
        caches: list[str] = []
        for name in sorted(self.parts):
            part = self.parts[name]
            entry: dict[str, Any] = {"material": part.material, "names": part.names_snapshot()}
            if part.shape is not None:
                from partkiln.exchange.brep_io import write_brep

                path = folder / f"{json_path.stem}-{name}.brep"
                write_brep(part.shape, path)
                entry["brep"] = path.name
                caches.append(path.name)
            else:
                entry["brep"] = None
            parts[name] = entry
        payload = {
            "partkiln_snapshot": 1,
            "label": label,
            "script": self.script(),
            "fingerprint": self.fingerprint(),
            "parts": parts,
        }
        json_path.write_text(json.dumps(payload, indent=1), encoding="utf-8")
        return {
            "label": label,
            "path": str(json_path),
            "commands": len(self.history),
            "fingerprint": payload["fingerprint"],
            "brep": bool(caches),
            "caches": caches,
        }

    @classmethod
    def restore(cls, payload: dict[str, Any] | str | Path) -> Document:
        """Rebuild from a snapshot: the `.brep` fast path when every file is
        there and the fingerprint matches, else a full replay of the script.
        A replay whose fingerprint still differs from the recorded one refuses
        `pk_checkpoint_mismatch` (the file was edited or written by another
        version); the caller keeps its own document."""
        if isinstance(payload, dict):
            if not payload.get("path"):
                raise CommandError(
                    "restore needs the payload snapshot() returned (it carries the path).",
                    code="pk_needs",
                )
            path = Path(str(payload["path"]))
        else:
            path = Path(payload)
        if not path.is_file():
            raise CommandError(
                f"no checkpoint at {path}. It was discarded or never written; tee_purge "
                "clears stale ones.",
                code="pk_checkpoint_missing",
            )
        data = _checkpoint_data(path)
        script = data["script"]
        cache: dict[str, Any] | None = {}
        parts = data.get("parts")
        for name, entry in (parts if isinstance(parts, dict) else {}).items():
            if not isinstance(entry, dict):
                # A hand-edited or foreign checkpoint: no usable cache, so
                # replay the script - which is the law anyway (D3).
                cache = None
                break
            if entry.get("brep") is None:
                cache[name] = {"shape": None, "names": entry.get("names") or {}}
                continue
            brep_path = path.parent / str(entry["brep"])
            if not brep_path.is_file():
                cache = None
                break
            from partkiln.exchange.brep_io import read_brep

            try:
                shape = read_brep(brep_path)
            except CommandError:
                cache = None
                break
            cache[name] = {"shape": shape, "names": entry.get("names") or {}}
        if cache is not None:
            document = cls.replay(script, cache=cache)
            if document.fingerprint() == data.get("fingerprint"):
                document.restored_via = "cache"
                return document
        document = cls.replay(script)
        document.restored_via = "replay"
        recorded = data.get("fingerprint")
        if recorded and document.fingerprint() != recorded:
            raise CommandError(
                f"checkpoint {path.name} recorded fingerprint {recorded} but its script replays "
                f"to {document.fingerprint()}: the file was edited or written by another "
                "partkiln. Take a new checkpoint.",
                code="pk_checkpoint_mismatch",
            )
        return document

    # -- the unit boundary (Law 12) -----------------------------------------

    def assume_once(self, assumed: dict[str, Any], key: str, value: Any) -> None:
        """Echo a document default the FIRST time a command leans on it."""
        if key not in self._echoed:
            self._echoed.add(key)
            assumed[key] = value

    def length(self, value: Any, assumed: dict[str, Any], deps: set[str] | None = None) -> float:
        """A length in mm from a number, a unit literal, or a parameter expression."""
        return self._quantity(value, assumed, deps, "length")

    def angle(self, value: Any, assumed: dict[str, Any], deps: set[str] | None = None) -> float:
        """An angle in degrees, same contract."""
        return self._quantity(value, assumed, deps, "angle")

    def _quantity(
        self, value: Any, assumed: dict[str, Any], deps: set[str] | None, kind: str
    ) -> float:
        from partkiln import params as _params
        from partkiln import units

        parse = units.parse_length if kind == "length" else units.parse_angle
        default = self.units if kind == "length" else self.angle_unit
        if isinstance(value, str) and not units.is_literal(value):
            evaluated = self.params.evaluate(value)
            if deps is not None:
                deps.update(evaluated.depends_on)
            if evaluated.kind == (_params.ANGLE if kind == "length" else _params.LENGTH):
                raise CommandError(
                    f"{value!r} is an {evaluated.kind}, not a {kind}.", code="pk_unit_kind"
                )
            if evaluated.kind == _params.SCALAR:
                return self._bare(evaluated.value, assumed, kind)
            return evaluated.value
        if isinstance(value, str) and units.has_unit(value):
            return parse(value, default=default)
        if isinstance(value, str):
            return self._bare(
                parse(value, default="mm" if kind == "length" else "deg"), assumed, kind
            )
        if isinstance(value, bool) or not isinstance(value, int | float):
            raise CommandError(
                f"{value!r} is not a {kind}. Write a number, a unit literal (12mm, 30deg) "
                "or a parameter expression (W/2).",
                code="pk_unit_unknown",
            )
        return self._bare(float(value), assumed, kind)

    def _bare(self, magnitude: float, assumed: dict[str, Any], kind: str) -> float:
        from partkiln import units

        if self.strict_units:
            # Refuse in the kind that was ASKED for: telling a model to write
            # "90mm" where an angle belongs costs a round trip and teaches the
            # wrong lesson (Law 12: a bare number is mm OR deg, by kind).
            parse = units.parse_length if kind == "length" else units.parse_angle
            return parse(magnitude, default=None)  # refuses: pk_unitless
        if kind == "length":
            self.assume_once(assumed, "units", self.units)
            return units.parse_length(magnitude, default=self.units)
        self.assume_once(assumed, "angle_unit", self.angle_unit)
        return units.parse_angle(magnitude, default=self.angle_unit)

    # -- lookups ------------------------------------------------------------

    def sketch(self, ref: str) -> Any:
        name = str(ref)[3:] if str(ref).startswith("sk:") else str(ref)
        sketch = self.sketches.get(name)
        if sketch is None:
            known = ", ".join(f"sk:{n}" for n in sorted(self.sketches)) or "(none)"
            raise CommandError(f"no sketch {ref!r}. Sketches: {known}.", code="pk_ref_unknown")
        return sketch

    def new_name(self, args: dict[str, Any], kind: str, taken: dict[str, Any]) -> str:
        raw = args.get("name")
        if raw is None or raw == "":
            n = len(taken) + 1
            while f"{kind}{n}" in taken:
                n += 1
            return f"{kind}{n}"
        name = str(raw)
        if not _NAME.match(name):
            raise CommandError(
                f"name {name!r} is not allowed: 1-24 characters from a-z 0-9 _ .",
                code="pk_needs",
            )
        if name in taken:
            raise CommandError(
                f"{kind} {name!r} already exists. Use set to change it, or pick another name.",
                code="pk_ref_ambiguous",
            )
        return name


def _checkpoint_data(path: Path) -> dict[str, Any]:
    """The checkpoint object at `path`, or one refusal that names the fix.

    D8/rule 6: a truncated, empty or foreign file is a checkpoint problem, not
    a JSONDecodeError or a KeyError out of the middle of `restore()`.
    """
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, ValueError) as exc:
        raise CommandError(
            f"checkpoint {path.name} is not readable partkiln JSON ({type(exc).__name__}). "
            "It was truncated or written by something else; take a new checkpoint "
            "(tee_purge clears stale ones).",
            code="pk_checkpoint_missing",
        ) from exc
    if not isinstance(data, dict) or not isinstance(data.get("script"), dict):
        raise CommandError(
            f"checkpoint {path.name} carries no 'script', so there is nothing to replay "
            "(D3: the checkpoint IS the script). Take a new checkpoint; tee_purge clears "
            "stale ones.",
            code="pk_checkpoint_missing",
        )
    return data


def _r6(v: Any) -> list[float]:
    return [round(float(c), 6) + 0.0 for c in v]


def _hash_row(item: Any) -> list[Any]:
    """One sketch entity, constraint or dimension as fingerprint input.

    The kind first, then every field of it, rounded before hashing (rule 7) so
    a second process agrees exactly. `expr` is deliberately left out: it is the
    source text a value came from, and the value itself is already here.
    """
    row: list[Any] = [type(item).__name__.lower()]
    for spec in fields(item):
        if spec.name == "expr":
            continue
        value = getattr(item, spec.name)
        if isinstance(value, bool) or not isinstance(value, float):
            row.append(list(value) if isinstance(value, tuple) else value)
        else:
            row.append(round(value, 6) + 0.0)
    return row


def _label(command: Command) -> str:
    """`create sketch rib` - enough of a command to find it in the script."""
    bits = [command.op]
    bits.extend(str(command.args[k]) for k in ("kind", "id", "name") if command.args.get(k))
    return " ".join(bits)


def _script_settings(script: dict[str, Any]) -> dict[str, Any]:
    """The document settings a script was recorded under.

    A script written before the key existed replays as the mm/deg/ISO document
    it was written by - which is exactly what `Document()` already defaults to,
    so an empty answer is the right one.
    """
    from partkiln import units

    raw = script.get("settings")
    if raw is None:
        return {}
    if not isinstance(raw, dict):
        raise CommandError(
            "a script's 'settings' is an object like {units: 'mm', angle_unit: 'deg'}.",
            code="pk_bad_op",
        )
    out: dict[str, Any] = {}
    for key in _SETTINGS:
        if key not in raw:
            continue
        value = raw[key]
        if key == "units":
            out[key] = units.canonical_unit(str(value), "length")
        elif key == "angle_unit":
            out[key] = units.canonical_unit(str(value), "angle")
        elif key == "strict_units":
            out[key] = bool(value)
        else:
            out[key] = str(value)
    return out


# -- D7 rows --------------------------------------------------------------------

# The containers the later phases fill, with their id prefixes. `exports` is
# read the same tolerant way if a phase adds one; a container this Document
# does not have is simply not there (getattr -> None).
_CONTAINERS: tuple[tuple[str, str], ...] = (
    ("assemblies", "asm"),
    ("drawings", "dwg"),
    ("sheets", "sheet"),
    ("exports", "export"),
)


def _scalar(value: Any) -> bool:
    """True for what may ride in a row: a number, a string, a flag, or a short
    list of them. A coordinate list is not a scalar and never goes on the wire."""
    if value is None or isinstance(value, str | int | float | bool):
        return True
    if isinstance(value, list | tuple):
        return len(value) <= 6 and all(
            v is None or isinstance(v, str | int | float | bool) for v in value
        )
    return False


def _sketch_row(doc: Document, name: str, sketch: Any) -> dict[str, Any]:
    report = sketch.report()
    return {
        "id": f"sk:{name}",
        "kind": "sketch",
        "name": name,
        "plane": sketch.plane,
        "entities": report["entities"],
        "constraints": report["constraints"],
        "dof": report["dof"],
        "status": report["status"],
        "closed": report["closed"],
        "area_mm2": report["area_mm2"],
        "used_by": len(doc.dependents_of(f"sk:{name}")),
    }


def _part_row(part: Any) -> dict[str, Any]:
    """The `part:` row (D7): the summary minus what only `detail()` needs.

    A row is a listing, not a report - the feature tree, the two bbox corners
    and the name count are all in `detail(id)`, and leaving them out of every
    listing is most of what keeps a twelve-feature part under 400 tokens.
    """
    drop = ("tree", "bbox_min", "bbox_max", "names")
    row = {k: v for k, v in part.summary().items() if k not in drop}
    if not row.get("cached"):
        row.pop("cached", None)
    row["name"] = part.name
    return row


def _feature_row(doc: Document, part: Any, feature: Any) -> dict[str, Any]:
    """The `feat:` row: the feature's own contribution, plus its blast radius.

    `parent` carries the part (the id is not repeated as `part`), and a flag
    or a count that is zero is left out: a row says what IS, and silence is
    the default.
    """
    row: dict[str, Any] = {
        "id": f"feat:{feature.id}",
        "kind": feature.kind,
        "parent": f"part:{part.name}",
        "status": "suppressed" if feature.suppressed else feature.status,
        "volume_mm3": round(float(feature.volume), 3) + 0.0,
        "delta_mm3": round(float(feature.delta_mm3), 3) + 0.0,
        "faces": feature.faces,
        "edges": feature.edges,
    }
    if feature.suppressed:
        row["suppressed"] = True
    if feature.names:
        row["roles"] = len(feature.names)
    downstream = len(doc.dependents_of(f"feat:{feature.id}"))
    if downstream:
        row["downstream"] = downstream
    if feature.refs:
        row["refs"] = list(feature.refs)[:4]
    params = {k: v for k, v in feature.args.items() if _scalar(v)}
    if params:
        row["params"] = params
    if feature.status == "failed" and feature.error:
        row["error"] = feature.error[:200]
    return row


def _component_count(assembly: Any) -> int:
    """How many components a container holds, wherever it keeps them (the P3
    container wraps an `Assembly`; a bare `Assembly` is read directly)."""
    for holder in (assembly, getattr(assembly, "asm", None)):
        components = getattr(holder, "components", None)
        if isinstance(components, dict):
            return len(components)
    return 0


def _container_rows(item: Any, name: str, prefix: str) -> list[dict[str, Any]]:
    """Rows for one container entry, read tolerantly.

    A phase that knows its own D7 rows offers `entity_rows()` and owns the
    answer; anything else is read through whatever compact report it has
    (`summary` / `report` / `as_dict`), and a list of dicts that carry their
    own `id` inside that report becomes child rows (a drawing's views and
    dimensions), because what is not a row is invisible to the scene cache.
    """
    own = getattr(item, "entity_rows", None)
    if callable(own):
        return [dict(row) for row in own() if isinstance(row, dict) and row.get("id")]
    body: dict[str, Any] | None = None
    for attr in ("summary", "report", "as_dict"):
        method = getattr(item, attr, None)
        if callable(method):
            out = method()
            if isinstance(out, dict):
                body = out
                break
    head: dict[str, Any] = {"id": f"{prefix}:{name}", "kind": prefix, "name": name}
    if body is None:
        return [head]
    head["id"] = str(body.get("id") or head["id"])
    head["kind"] = str(body.get("kind") or prefix)
    children: list[dict[str, Any]] = []
    for key, value in body.items():
        if key in ("id", "kind", "name"):
            continue
        if (
            isinstance(value, list)
            and value
            and all(isinstance(v, dict) and v.get("id") for v in value)
        ):
            for child in value:
                row = dict(child)
                row.setdefault("parent", head["id"])
                children.append(row)
            head[key] = len(value)
        else:
            head[key] = value
    return [head, *children]


# -- overrides ------------------------------------------------------------------


def _assignments(args: dict[str, Any]) -> dict[str, Any]:
    """The {name: value} pairs of a param_set, wherever the wire put them."""
    inner = args.get("params")
    if isinstance(inner, dict):
        return dict(inner)
    return {k: v for k, v in args.items() if k not in _WIRE_KEYS}


def _override(commands: list[Command], overrides: dict[str, Any]) -> tuple[list[Command], set[str]]:
    unmatched = set(overrides)
    rewritten: list[Command] = []
    for command in commands:
        if command.op != "param_set":
            rewritten.append(command)
            continue
        args = dict(command.args)
        inner = args.get("params")
        target = inner if isinstance(inner, dict) else args
        target = dict(target)
        for name, value in overrides.items():
            if name in target:
                target[name] = value
                unmatched.discard(name)
        if isinstance(inner, dict):
            args["params"] = target
        else:
            args = target
        rewritten.append(Command(command.op, args))
    return rewritten, unmatched


# -- verbs ------------------------------------------------------------------------


@register_verb("set")
def _v_set(doc: Document, args: dict[str, Any], assumed: dict[str, Any]) -> dict[str, Any]:
    target = str(args.get("id") or args.get("target") or "doc")
    # `name` stays: on `set` it is the rename prop, not a wire key.
    props = {k: v for k, v in args.items() if k not in ("id", "target", "kind")}
    if "props" in props and isinstance(props["props"], dict):
        props = dict(props.pop("props"))
    if target == "doc":
        return _set_doc(doc, props, assumed)
    if target.startswith("sk:") or target in doc.sketches:
        return _set_sketch(doc, target, props, assumed)
    if target.startswith(_ASSEMBLY_IDS):
        from partkiln.assembly.verbs import set_target as set_assembly

        return set_assembly(doc, target, props, assumed)
    if doc.parts or target.startswith(("part:", "feat:")):
        from partkiln.features import set_target

        return set_target(doc, target, props, assumed)
    ids = ["doc", *(f"sk:{n}" for n in sorted(doc.sketches))]
    raise CommandError(
        f"nothing to set on {target!r}. Settable ids: {', '.join(ids)}.", code="pk_ref_unknown"
    )


def _set_doc(doc: Document, props: dict[str, Any], assumed: dict[str, Any]) -> dict[str, Any]:
    from partkiln import units

    doc.assume_once(
        assumed,
        "doc_defaults",
        {
            "units": doc.units,
            "angle_unit": doc.angle_unit,
            "standard": doc.standard,
            "angle": doc.drawing_angle,
            "strict_units": doc.strict_units,
        },
    )
    if not props:
        raise CommandError(
            "set doc needs at least one of units, angle_unit, standard, angle, strict_units, name.",
            code="pk_needs",
        )
    changed: list[dict[str, Any]] = []
    unchanged = 0

    def note(key: str, old: Any, new: Any) -> None:
        nonlocal unchanged
        if old == new:
            unchanged += 1
        else:
            changed.append({"key": key, "old": old, "new": new})

    for key, raw in props.items():
        if key == "units":
            new = units.canonical_unit(str(raw), "length")
            note(key, doc.units, new)
            doc.units = new
            doc.params.default_unit = new
        elif key == "angle_unit":
            new = units.canonical_unit(str(raw), "angle")
            note(key, doc.angle_unit, new)
            doc.angle_unit = new
            doc.params.default_angle_unit = new
        elif key == "standard":
            new = str(raw).upper()
            if new not in ("ISO", "ANSI", "DIN"):
                raise CommandError(f"standard {raw!r} is not ISO, ANSI or DIN.", code="pk_needs")
            note(key, doc.standard, new)
            doc.standard = new
            if "angle" not in props:  # the projection angle follows the standard (D5)
                follows = "third" if new == "ANSI" else "first"
                note("angle", doc.drawing_angle, follows)
                doc.drawing_angle = follows
        elif key == "angle":
            new = str(raw).lower()
            if new not in ("first", "third"):
                raise CommandError(
                    f"angle {raw!r} is not a projection: first or third.", code="pk_needs"
                )
            note(key, doc.drawing_angle, new)
            doc.drawing_angle = new
        elif key == "strict_units":
            if not isinstance(raw, bool):
                raise CommandError("strict_units is true or false.", code="pk_needs")
            note(key, doc.strict_units, raw)
            doc.strict_units = raw
        elif key == "name":
            new = str(raw)
            note(key, doc.name, new)
            doc.name = new
        else:
            raise CommandError(
                f"doc has no setting {key!r}. Settings: units, angle_unit, standard, angle, "
                "strict_units, name.",
                code="pk_ref_unknown",
            )
    return {"id": "doc", "changed": changed, "unchanged": unchanged}


def _set_sketch(
    doc: Document, target: str, props: dict[str, Any], assumed: dict[str, Any]
) -> dict[str, Any]:
    sketch = doc.sketch(target)
    if not props:
        known = ", ".join(d.tag for d in sketch.dims) or "(none)"
        raise CommandError(
            f"set {target} needs {{dimension tag: value}}. Dimensions: {known}.", code="pk_needs"
        )
    changed: list[dict[str, Any]] = []
    deps: set[str] = set()
    for tag, raw in props.items():
        dim = sketch.dim(str(tag))
        driven = None
        if isinstance(raw, dict):
            driven = raw.get("driven")
            raw = raw.get("value", dim.value)
        parse = doc.angle if dim.kind == "angle" else doc.length
        value = parse(raw, assumed, deps)
        old, new = sketch.set_dim(dim.tag, value, expr=raw if isinstance(raw, str) else None)
        if driven is not None:
            dim.driven = bool(driven)
        changed.append({"tag": dim.tag, "old": round(old, 6), "new": round(new, 6)})
    sketch.param_deps |= deps
    _register_users(doc, sketch)
    report = _solve_or_refuse(sketch, f"set {target}")
    out = {"id": f"sk:{sketch.name}", "changed": changed, **report}
    if doc.parts:
        from partkiln.features import after_sketch_change

        regen = after_sketch_change(doc, [sketch.name], assumed)
        if regen:
            out["regen"] = regen
    return out


def _solve_or_refuse(sketch: Any, doing: str) -> dict[str, Any]:
    solution = sketch.solve()
    if solution.status == "conflict":
        named = "; ".join(solution.conflicts) or "(no single row can be dropped to fix it)"
        raise CommandError(
            f"{doing}: the sketch is over-constrained and does not solve "
            f"(max residual {solution.residual_max_mm:.3g} mm). In conflict: {named}. "
            "Drop or relax one of them, or make a dimension driven (driven: true).",
            code="pk_sketch_overconstrained",
        )
    return sketch.report()


def _register_users(doc: Document, sketch: Any) -> None:
    sid = f"sk:{sketch.name}"
    for name, users in doc.params.users.items():
        if name not in sketch.param_deps:
            users.discard(sid)
    for name in sketch.param_deps:
        doc.params.users.setdefault(name, set()).add(sid)


@register_verb("param_set")
def _v_param_set(doc: Document, args: dict[str, Any], assumed: dict[str, Any]) -> dict[str, Any]:
    assignments = _assignments(args)
    if not assignments:
        raise CommandError(
            "param_set needs {name: value} pairs, e.g. {W: '120mm', H: 'W/2 - 5mm'}. "
            "A parameter named kind, name or id must be given under 'params'.",
            code="pk_needs",
        )
    outcome = doc.params.set_many(assignments)
    changed_names = {c.name for c in outcome["changes"]}
    resolved: list[dict[str, Any]] = []
    for name, sketch in sorted(doc.sketches.items()):
        if not sketch.param_deps & changed_names:
            continue
        deps: set[str] = set()
        for dim in sketch.dims:
            if dim.expr is not None:
                parse = doc.angle if dim.kind == "angle" else doc.length
                sketch.set_dim(dim.tag, parse(dim.expr, assumed, deps), expr=dim.expr)
        sketch.param_deps = deps
        _register_users(doc, sketch)
        report = _solve_or_refuse(sketch, f"param_set on sk:{name}")
        resolved.append({"id": f"sk:{name}", "dof": report["dof"], "status": report["status"]})
    result: dict[str, Any] = {
        "changed": [c.as_dict() for c in outcome["changes"]],
        "unchanged": outcome["unchanged"],
    }
    if resolved:
        result["sketches"] = resolved
    if doc.parts:
        from partkiln.features import after_param_change

        regen = after_param_change(doc, changed_names, [r["id"][3:] for r in resolved], assumed)
        if regen:
            result["regen"] = regen
    return result


@register_verb("create")
def _v_create(doc: Document, args: dict[str, Any], assumed: dict[str, Any]) -> dict[str, Any]:
    kind = args.get("kind")
    handler = _KINDS.get(str(kind))
    if handler is None:
        # The later phases register their kinds on import; loaded on first
        # need so a document that never creates a part never pays for them.
        load_verb_modules()
        handler = _KINDS.get(str(kind))
    if handler is None:
        raise CommandError(
            f"unknown create kind {kind!r}. partkiln creates: {', '.join(sorted(_KINDS))}.",
            code="pk_bad_op",
        )
    return handler(doc, args, assumed)


@register_kind("sketch")
def _k_sketch(doc: Document, args: dict[str, Any], assumed: dict[str, Any]) -> dict[str, Any]:
    from partkiln.sketch import presets
    from partkiln.sketch.model import Arc, Circle, Line, Point, Sketch

    name = doc.new_name(args, "sketch", doc.sketches)
    plane = args.get("plane")
    if plane is None:
        raise CommandError(
            "create sketch needs plane: XY, XZ, YZ, plane:<name> or on:<face ref>.",
            code="pk_plane_missing",
        )
    plane = str(plane)
    # Declared before the origin so a `origin: ["W/2", 0, 0]` records its
    # parameter dependency like every other length in the sketch.
    deps: set[str] = set()
    origin = args.get("origin")
    if origin is not None:
        if not plane.startswith("on:"):
            raise CommandError(
                "origin applies to an on:<face> plane only (XY/XZ/YZ and datums have their "
                "own origin).",
                code="pk_needs",
            )
        if "@" in plane:
            raise CommandError("give the origin once: origin: or @ in the plane.", code="pk_needs")
        if origin == "centroid":
            plane = f"{plane}@centroid"
        elif isinstance(origin, list | tuple) and len(origin) == 3:
            # Every other length on the wire goes through the document's
            # parser, so this one does too: "10mm", "0.5in" and "W/2" are the
            # spellings Law 12 asks for, and a bare number is the document
            # unit - not a raw float() that dies on the very literal we teach.
            x, y, z = (doc.length(v, assumed, deps) for v in origin)
            plane = f"{plane}@{x:g},{y:g},{z:g}"
        else:
            raise CommandError(
                "origin is 'centroid' or [x, y, z] - numbers in the document unit, or "
                "literals like '10mm' / '0.5in'.",
                code="pk_needs",
            )
    elif plane.startswith("on:") and "@" not in plane:
        assumed["origin"] = "the world origin projected onto the face"
    sketch = Sketch(name, plane)

    def length(v: Any) -> float:
        return doc.length(v, assumed, deps)

    def angle(v: Any) -> float:
        return doc.angle(v, assumed, deps)

    profile = args.get("profile")
    specs = profile if isinstance(profile, list) else ([profile] if profile else [])
    for spec in specs:
        if not isinstance(spec, dict):
            raise CommandError(
                f"profile entries are objects like {{rect: [100, 60]}}; got {spec!r}.",
                code="pk_needs",
            )
        expansion = presets.expand(spec, length=length, angle=angle, existing=sketch.tags())
        for entity in expansion.entities:
            sketch.add(entity)
        for c_kind, refs, tag in expansion.constraints:
            sketch.constrain(c_kind, *refs, tag=tag)
        for d_kind, refs, value, tag, axis, expr in expansion.dims:
            sketch.dimension(d_kind, *refs, value=value, tag=tag, axis=axis, expr=expr)
        for key, value in expansion.assumed.items():
            assumed.setdefault(key, {})[expansion.tag] = value

    for raw in args.get("entities") or []:
        if not isinstance(raw, dict):
            raise CommandError(f"entity {raw!r} is not an object.", code="pk_needs")
        if "point" in raw:
            at = raw.get("at")
            if not isinstance(at, list | tuple) or len(at) != 2:
                raise CommandError(f"point {raw.get('point')!r} needs at: [x, y].", code="pk_needs")
            sketch.add(
                Point(
                    str(raw["point"]), length(at[0]), length(at[1]), bool(raw.get("fixed", False))
                )
            )
        elif "line" in raw:
            sketch.add(
                Line(
                    str(raw["line"]),
                    str(raw.get("a")),
                    str(raw.get("b")),
                    bool(raw.get("construction", False)),
                )
            )
        elif "arc" in raw:
            sketch.add(
                Arc(
                    str(raw["arc"]),
                    str(raw.get("center")),
                    str(raw.get("start")),
                    str(raw.get("end")),
                    bool(raw.get("ccw", True)),
                    bool(raw.get("construction", False)),
                )
            )
        elif "circle" in raw:
            if "r" in raw:
                r = length(raw["r"])
            elif "d" in raw:
                r = length(raw["d"]) / 2.0
            else:
                raise CommandError(f"circle {raw['circle']!r} needs r or d.", code="pk_needs")
            sketch.add(
                Circle(
                    str(raw["circle"]),
                    str(raw.get("center")),
                    r,
                    bool(raw.get("construction", False)),
                )
            )
        else:
            raise CommandError(
                f"entity {raw!r} names none of point, line, arc, circle.", code="pk_needs"
            )

    for raw in args.get("constraints") or []:
        if not isinstance(raw, dict) or "c" not in raw:
            raise CommandError(
                f"constraint {raw!r} needs c: <kind> and on | a, b [, about].", code="pk_needs"
            )
        sketch.constrain(str(raw["c"]), *_refs(raw), tag=raw.get("tag"))

    for raw in args.get("dims") or []:
        if not isinstance(raw, dict) or "d" not in raw or "value" not in raw:
            raise CommandError(
                f"dimension {raw!r} needs d: <kind>, on | a, b, and value.", code="pk_needs"
            )
        d_kind = str(raw["d"])
        parse = angle if d_kind == "angle" else length
        value = raw["value"]
        sketch.dimension(
            d_kind,
            *_refs(raw),
            value=parse(value),
            driven=bool(raw.get("driven", False)),
            axis=raw.get("axis"),
            tag=raw.get("tag"),
            expr=value if isinstance(value, str) else None,
        )

    if not sketch.entities:
        raise CommandError(
            "create sketch made nothing: give a profile ({rect: [w, h]}, {circle: d}, "
            "{slot: [len, w]}, {polygon: n, d}, {poly: [[x, y], ...]}) or entities.",
            code="pk_needs",
        )
    report = _solve_or_refuse(sketch, f"create sketch {name}")
    sketch.param_deps = deps
    doc.sketches[name] = sketch
    _register_users(doc, sketch)
    return {"id": f"sk:{name}", **report}


def _refs(raw: dict[str, Any]) -> list[str]:
    on = raw.get("on")
    if on is not None:
        return [str(x) for x in on] if isinstance(on, list | tuple) else [str(on)]
    refs = [str(raw[k]) for k in ("a", "b", "about") if k in raw]
    if not refs:
        raise CommandError(
            f"{raw!r} names no entity: use on: <tag> or a: <tag>, b: <tag>.", code="pk_needs"
        )
    return refs


@register_verb("delete")
def _v_delete(doc: Document, args: dict[str, Any], assumed: dict[str, Any]) -> dict[str, Any]:
    target = args.get("id")
    if not target:
        raise CommandError("delete needs id, e.g. sk:base.", code="pk_needs")
    target = str(target)
    cascade = bool(args.get("cascade"))
    if target.startswith(_ASSEMBLY_IDS):
        from partkiln.assembly.verbs import delete_target as delete_assembly

        return delete_assembly(doc, target, cascade, assumed)
    if target.startswith(("part:", "feat:")) or (
        doc.parts and target not in doc.sketches and not target.startswith("sk:")
    ):
        from partkiln.features import delete_target

        return delete_target(doc, target, cascade, assumed)
    dependents = doc.dependents_of(target)
    if dependents and not cascade:
        raise CommandError(
            f"{target} is used by {', '.join(dependents)}. Delete those first, or pass "
            "cascade: true to remove them with it.",
            code="pk_delete_blocked",
        )
    sketch = doc.sketch(target)
    removed: list[str] = []
    if dependents:
        from partkiln.features import delete_target

        for dep in dependents:
            if dep.startswith("feat:") and any(p.has_feature(dep[5:]) for p in doc.parts.values()):
                removed.extend(delete_target(doc, dep, True, assumed)["deleted"])
    del doc.sketches[sketch.name]
    for users in doc.params.users.values():
        users.discard(f"sk:{sketch.name}")
    out: dict[str, Any] = {"deleted": f"sk:{sketch.name}", "sketches": len(doc.sketches)}
    if removed:
        out["cascaded"] = removed
    return out
