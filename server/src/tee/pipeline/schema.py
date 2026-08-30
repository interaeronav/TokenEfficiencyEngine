"""The pipeline lane's declaration schema (A43 P0), owned by the project.

SI-B15: TEE's virtual surface assumes a live scene — epoch stamps, diffs,
checkpoints — so a build pipeline (files in, scripts between, files out)
had nothing to hold onto. One op did work: `dem_diff`, because it was a
DECLARED HEADLESS OPERATION. Declaration, not scene state, is what makes
work drivable, so this generalizes the declaration and the gap closes for
every project at once.

A project declares its own steps in its own tracked `.tee/pipeline.toml`:

    [[step]]
    name    = "basemap"
    kind    = "produce"
    argv    = ["python", "builder/build_basemap.py", "--tile", "{tile}"]
    params  = { tile = { type = "string", pattern = "^[a-z0-9_]{1,32}$" } }
    inputs  = ["data/atl08/**", "builder/build_basemap.py"]
    outputs = ["out/basemap_{tile}.tif"]

The laws this module enforces, none of which bend:

* **argv arrays only.** Never a shell string, never `shell=True`. A
  declaration that hands over a string is refused, because that is the
  one mistake that turns a bounded capability into a shell.
* **`{param}` substitution is typed, constrained, and lands as exactly
  ONE argv element** — so a value full of spaces, quotes and semicolons
  is inert data, not syntax.
* **The bound is the point, not the ceremony.** Every param used in argv
  must be constrained by `enum` or `pattern`. An unconstrained
  `make {target}` is refused as a laundered allowlist: it looks declared
  while granting arbitrary execution.
* **TEE never writes this file.** The adopt flow emits a `.proposed`
  file for the owner to move; a write attempt to the real path is a bug
  with a fixture guarding it.
* **Trust on first use.** The approved file is hash-pinned per project;
  an unapproved or CHANGED declaration refuses to run and names the
  change — a cloned repo's pipeline.toml is attacker-authored by
  definition.
"""

from __future__ import annotations

import hashlib
import re
import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from tee.kernel.errors import TeeError

KINDS = ("produce", "query")
PARAM_TYPES = ("string", "integer", "number", "boolean")
_NAME = re.compile(r"^[a-z][a-z0-9_]{0,63}$")
_PLACEHOLDER = re.compile(r"\{([a-z][a-z0-9_]*)\}")
_ENV_NAME = re.compile(r"^[A-Z][A-Z0-9_]{0,63}$")
# A param value may never be a path escape or a null byte, whatever its
# pattern says - belt over braces (the kb_propose traversal guard, hoisted).
_ALWAYS_REJECT = ("\x00", "..")


@dataclass
class Step:
    name: str
    kind: str
    argv: list[str]
    params: dict[str, dict[str, Any]] = field(default_factory=dict)
    inputs: list[str] = field(default_factory=list)
    outputs: list[str] = field(default_factory=list)
    cost: dict[str, Any] = field(default_factory=dict)
    answer: dict[str, Any] = field(default_factory=dict)
    env: dict[str, str] = field(default_factory=dict)

    def placeholders(self) -> set[str]:
        found: set[str] = set()
        for element in [*self.argv, *self.env.values()]:
            found.update(_PLACEHOLDER.findall(element))
        return found

    def summary(self) -> dict[str, Any]:
        """One compact row - the lane answers, it does not dump."""
        row: dict[str, Any] = {"name": self.name, "kind": self.kind, "argv": self.argv}
        if self.params:
            row["params"] = sorted(self.params)
        if self.outputs:
            row["outputs"] = self.outputs
        if self.answer:
            row["answer"] = self.answer
        return row


@dataclass
class Pipeline:
    steps: dict[str, Step]
    path: Path
    digest: str
    approved: bool
    change: str | None = None

    def require(self, name: str) -> Step:
        step = self.steps.get(name)
        if step is None:
            known = ", ".join(sorted(self.steps)) or "(none declared)"
            raise TeeError(
                "pipeline_unknown_step",
                f"No step named '{name}' in {self.path.name}.",
                fix=f"Declared steps: {known}.",
            )
        return step


def _fail(code: str, message: str, fix: str) -> TeeError:
    return TeeError(code, message, fix=fix)


def validate_step(raw: Any, index: int) -> Step:
    """One declaration -> a Step, or a refusal naming the exact fix."""
    where = f"[[step]] #{index + 1}"
    if not isinstance(raw, dict):
        raise _fail(
            "pipeline_bad_step", f"{where} is not a table.", "Each step is a [[step]] table."
        )
    name = str(raw.get("name") or "")
    if not _NAME.match(name):
        raise _fail(
            "pipeline_bad_step",
            f"{where}: name '{name}' is not usable.",
            "Names are lower-case identifiers: [a-z][a-z0-9_]*.",
        )
    kind = str(raw.get("kind") or "")
    if kind not in KINDS:
        raise _fail(
            "pipeline_bad_step",
            f"step '{name}': kind '{kind}' is not a step kind.",
            'Use kind = "produce" (artifacts out) or "query" (an answer out).',
        )

    argv = raw.get("argv")
    if isinstance(argv, str):
        raise _fail(
            "pipeline_shell_string",
            f"step '{name}': argv is a string.",
            "argv is a LIST of arguments, never a shell string: "
            'argv = ["python", "build.py", "--tile", "{tile}"]. TEE never '
            "runs a shell, so a string could only be misread.",
        )
    if not isinstance(argv, list) or not argv or not all(isinstance(a, str) and a for a in argv):
        raise _fail(
            "pipeline_bad_step",
            f"step '{name}': argv must be a non-empty list of strings.",
            'argv = ["python", "builder/build.py"]',
        )

    env_raw = raw.get("env") or {}
    if not isinstance(env_raw, dict):
        raise _fail(
            "pipeline_bad_step",
            f"step '{name}': env must be a table of NAME = \"value\".",
            'env = { PROJ_NETWORK = "ON" }',
        )
    env: dict[str, str] = {}
    for key, value in env_raw.items():
        if not _ENV_NAME.match(str(key)):
            raise _fail(
                "pipeline_bad_step",
                f"step '{name}': '{key}' is not an environment variable name.",
                "Names are A-Z, digits and underscore: PROJ_NETWORK.",
            )
        if not isinstance(value, str):
            raise _fail(
                "pipeline_bad_step",
                f"step '{name}': env {key} must be a string.",
                f'{key} = "1" - quote numbers; the environment holds text.',
            )
        env[str(key)] = value

    params_raw = raw.get("params") or {}
    if not isinstance(params_raw, dict):
        raise _fail(
            "pipeline_bad_step",
            f"step '{name}': params must be a table.",
            "params = { tile = {...} }",
        )
    params: dict[str, dict[str, Any]] = {}
    for key, spec in params_raw.items():
        if not isinstance(spec, dict):
            raise _fail(
                "pipeline_bad_step",
                f"step '{name}': param '{key}' must be a table.",
                'tile = { type = "string", pattern = "^[a-z0-9_]+$" }',
            )
        ptype = str(spec.get("type") or "")
        if ptype not in PARAM_TYPES:
            raise _fail(
                "pipeline_bad_step",
                f"step '{name}': param '{key}' has no usable type.",
                f"type is one of: {', '.join(PARAM_TYPES)}.",
            )
        params[str(key)] = dict(spec)

    step = Step(
        name=name,
        kind=kind,
        argv=[str(a) for a in argv],
        params=params,
        inputs=[str(i) for i in raw.get("inputs") or []],
        outputs=[str(o) for o in raw.get("outputs") or []],
        cost=dict(raw.get("cost") or {}),
        answer=dict(raw.get("answer") or {}),
        env=env,
    )

    used = step.placeholders()
    missing = sorted(used - set(params))
    if missing:
        raise _fail(
            "pipeline_bad_step",
            f"step '{name}': argv uses {{{missing[0]}}} with no declared param.",
            f'Declare it: params = {{ {missing[0]} = {{ type = "string", '
            'pattern = "^[a-z0-9_]+$" }} }}',
        )
    # THE BOUND IS THE POINT. A param that can be anything makes the step an
    # arbitrary-execution grant wearing a declaration's clothes.
    for key in sorted(used):
        spec = params[key]
        if not spec.get("enum") and not spec.get("pattern") and spec.get("type") == "string":
            raise _fail(
                "pipeline_unbounded_param",
                f"step '{name}': param '{key}' is a free string, so this step "
                "is an arbitrary-execution grant wearing a declaration's clothes.",
                f'Constrain it: {key} = {{ type = "string", enum = [...] }} or '
                f'{{ type = "string", pattern = "^[a-z0-9_]+$" }}.',
            )
    if step.kind == "produce" and not step.outputs:
        raise _fail(
            "pipeline_bad_step",
            f"step '{name}': a produce step declares what it produces.",
            'outputs = ["out/basemap.tif"] - the artifact diff is the answer.',
        )
    return step


def substitute_env(step: Step, values: dict[str, Any]) -> dict[str, str]:
    """The declared environment, with the SAME constraint law as argv.

    An env var is an input to the process like any other, so a free string
    here would reopen exactly the hole the argv rule closes - only less
    visibly, because nobody reads the environment when they read a command.
    """
    return {key: _render(step, value, values) for key, value in step.env.items()}


def _render(step: Step, element: str, values: dict[str, Any]) -> str:
    names = _PLACEHOLDER.findall(element)
    if not names:
        return element
    rendered = element
    for key in names:
        spec = step.params[key]
        if key not in values:
            if spec.get("required", True):
                raise _fail(
                    "pipeline_missing_param",
                    f"step '{step.name}': parameter '{key}' is required.",
                    f'Pass params = {{"{key}": ...}}.',
                )
            rendered = rendered.replace(f"{{{key}}}", str(spec.get("default", "")))
            continue
        rendered = rendered.replace(f"{{{key}}}", _check_value(step, key, spec, values[key]))
    return rendered


def substitute(step: Step, values: dict[str, Any]) -> list[str]:
    """Build the real argv. Every value is validated against its declared
    constraint and lands as exactly ONE element, whatever it contains."""
    resolved: list[str] = []
    for element in step.argv:
        # ONE element whatever it renders to: spaces and quotes are data
        resolved.append(_render(step, element, values))
    return resolved


def _check_value(step: Step, key: str, spec: dict[str, Any], value: Any) -> str:
    ptype = spec.get("type")
    if ptype == "integer" and not isinstance(value, int):
        raise _fail(
            "pipeline_bad_param",
            f"step '{step.name}': '{key}' must be an integer.",
            "Pass a number.",
        )
    if ptype == "boolean" and not isinstance(value, bool):
        raise _fail(
            "pipeline_bad_param",
            f"step '{step.name}': '{key}' must be true or false.",
            "Pass a boolean.",
        )
    text = str(value)
    for banned in _ALWAYS_REJECT:
        if banned in text:
            raise _fail(
                "pipeline_bad_param",
                f"step '{step.name}': '{key}' contains {banned!r}, which is never "
                "allowed in a parameter.",
                "Parameters name things; they do not traverse paths.",
            )
    enum = spec.get("enum")
    if enum and text not in [str(e) for e in enum]:
        raise _fail(
            "pipeline_bad_param",
            f"step '{step.name}': '{key}' must be one of {enum}.",
            f"Got {text!r}.",
        )
    pattern = spec.get("pattern")
    if pattern and not re.match(str(pattern), text):
        raise _fail(
            "pipeline_bad_param",
            f"step '{step.name}': '{key}' does not match {pattern}.",
            f"Got {text!r} - the declaration constrains this value deliberately.",
        )
    return text


def digest_of(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()[:16]


def pin_path(project_root: Path) -> Path:
    """TEE's own record of the declaration it was shown. Kept in TEE's
    state, never in the project's file - TEE does not write that."""
    return Path(project_root) / ".tee" / "pipeline.pin"


def load(project_root: Path | str) -> Pipeline:
    """Read a project's declarations. Trust on first use: the file is
    hash-pinned, and a CHANGED file is unapproved until the owner says so."""
    root = Path(project_root)
    path = root / ".tee" / "pipeline.toml"
    if not path.is_file():
        raise _fail(
            "pipeline_absent",
            f"No pipeline declared for this project ({path} is absent).",
            "Declare steps in .tee/pipeline.toml, or run pipeline_init to draft "
            "a candidate you review before adopting.",
        )
    try:
        data = tomllib.loads(path.read_text())
    except (tomllib.TOMLDecodeError, OSError) as exc:
        raise _fail(
            "pipeline_unreadable", f"{path.name} could not be read: {exc}", "Fix the TOML syntax."
        ) from exc
    raw_steps = data.get("step") or []
    if not isinstance(raw_steps, list):
        raise _fail(
            "pipeline_bad_file",
            f"{path.name}: [[step]] must be an array of tables.",
            "Use [[step]].",
        )
    steps: dict[str, Step] = {}
    for index, raw in enumerate(raw_steps):
        step = validate_step(raw, index)
        if step.name in steps:
            raise _fail(
                "pipeline_bad_file",
                f"{path.name}: step '{step.name}' is declared twice.",
                "Step names are unique within a project.",
            )
        steps[step.name] = step

    digest = digest_of(path)
    pin = pin_path(root)
    approved = False
    change: str | None = None
    if pin.is_file():
        pinned = pin.read_text().strip()
        approved = pinned == digest
        if not approved:
            change = f"declaration changed since it was approved ({pinned[:8]} -> {digest[:8]})"
    else:
        change = "never approved on this machine"
    return Pipeline(steps=steps, path=path, digest=digest, approved=approved, change=change)
