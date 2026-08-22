"""Verse digest parsing (12.1): `*.digest.verse` files are plain Verse
declarations - the authoritative, always-current API surface.

Digests are per-install and Epic-copyrighted: TEE parses them from
`%LOCALAPPDATA%/UnrealEditorFortnite/Saved/VerseProject/…` on the user's
machine and NEVER redistributes their text; the test fixture is
synthetic. The parser is a tolerant line-based scan (indentation scoping
+ declaration regexes), extracting exactly what the linter needs:
modules, classes (+ parents), members with effect specifiers, and
`listenable` events.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from tee.kernel.errors import TeeError

# name<access> := module:
_MODULE_RE = re.compile(r"^(?P<indent>\s*)(?P<name>\w+)\s*<\w+>\s*:=\s*module\s*:")
# name<access> := class<specifiers>(parent):   /  := class(parent):
_CLASS_RE = re.compile(
    r"^(?P<indent>\s*)(?P<name>\w+)\s*<\w+>\s*:=\s*(?:class|interface)"
    r"(?:<[^>]*>)?\s*(?:\((?P<parents>[^)]*)\))?\s*:"
)
# name<access> := enum:  /  := enum {A, B}
_ENUM_RE = re.compile(r"^(?P<indent>\s*)(?P<name>\w+)\s*<\w+>\s*:=\s*enum")
# Function members:  Name<access>(args)<effect1><effect2>:type = external {}
_FUNC_RE = re.compile(
    r"^(?P<indent>\s*)(?P<name>\w+)\s*(?:<\w+>)?\s*\((?P<args>[^)]*)\)"
    r"(?P<effects>(?:\s*<\w+>)*)\s*:\s*(?P<rtype>[\w\[\]\(\)\?\., ]+)"
)
# Event members:  Name<access>:listenable(payload) = external {}
_EVENT_RE = re.compile(
    r"^(?P<indent>\s*)(?P<name>\w+)\s*(?:<\w+>)?\s*:\s*listenable\((?P<payload>[^)]*)\)"
)
# Data members:  Name<access>:type = …
_DATA_RE = re.compile(
    r"^(?P<indent>\s*)(?P<name>\w+)\s*(?:<\w+>)?\s*:\s*(?P<dtype>[\w\[\]\?\.]+)\s*(?:=|$)"
)
_EFFECT_RE = re.compile(r"<(\w+)>")

KNOWN_EFFECTS = {
    # exclusive (post-v30.00) + additive; <varies> died in the v30.00
    # redesign and is the canonical stale-codegen hallucination
    "converges", "computes", "transacts",
    "reads", "writes", "allocates", "suspends", "decides",
    "public", "internal", "protected", "private", "native", "final",
    "abstract", "concrete", "unique", "persistable", "epic_internal",
    "override", "localizes",
}


def parse_digest(text: str, *, version: str = "unknown") -> dict[str, Any]:
    """Parse one digest into version-keyed API facts:
    {version, modules: {path: {classes: {name: {parents, members:
    {name: {kind, effects, args?, type?}}}}, functions, enums}}}"""
    modules: dict[str, Any] = {}
    module_stack: list[tuple[int, str]] = []
    class_stack: list[tuple[int, str]] = []

    def module_path() -> str:
        return "/".join(name for _, name in module_stack) or "(root)"

    def current_module() -> dict[str, Any]:
        return modules.setdefault(
            module_path(), {"classes": {}, "functions": {}, "enums": []}
        )

    for raw in text.splitlines():
        line = raw.rstrip()
        if not line.strip() or line.strip().startswith("#"):
            continue
        indent = len(line) - len(line.lstrip())
        while module_stack and indent <= module_stack[-1][0]:
            module_stack.pop()
        while class_stack and indent <= class_stack[-1][0]:
            class_stack.pop()

        match = _MODULE_RE.match(line)
        if match:
            module_stack.append((indent, match.group("name")))
            current_module()
            continue
        match = _CLASS_RE.match(line)
        if match:
            parents = [
                p.strip() for p in (match.group("parents") or "").split(",") if p.strip()
            ]
            current_module()["classes"][match.group("name")] = {
                "parents": parents,
                "members": {},
            }
            class_stack.append((indent, match.group("name")))
            continue
        match = _ENUM_RE.match(line)
        if match:
            current_module()["enums"].append(match.group("name"))
            continue
        match = _EVENT_RE.match(line)
        if match and class_stack:
            cls = current_module()["classes"][class_stack[-1][1]]
            cls["members"][match.group("name")] = {
                "kind": "event",
                "payload": match.group("payload").strip(),
            }
            continue
        match = _FUNC_RE.match(line)
        if match:
            effects = _EFFECT_RE.findall(match.group("effects") or "")
            member = {
                "kind": "function",
                "effects": effects,
                "args": match.group("args").strip(),
                "type": match.group("rtype").strip(),
            }
            if class_stack:
                current_module()["classes"][class_stack[-1][1]]["members"][
                    match.group("name")
                ] = member
            else:
                current_module()["functions"][match.group("name")] = member
            continue
        match = _DATA_RE.match(line)
        if match and class_stack and match.group("name") not in ("using",):
            cls = current_module()["classes"][class_stack[-1][1]]
            cls["members"].setdefault(
                match.group("name"),
                {"kind": "data", "type": match.group("dtype")},
            )

    return {"version": version, "modules": modules}


def load_digest(path: Path, *, version: str | None = None) -> dict[str, Any]:
    path = Path(path)
    if not path.exists():
        raise TeeError(
            "no_such_file",
            f"No digest at {path}.",
            fix="Digests live in the UEFN install "
            "(%LOCALAPPDATA%/UnrealEditorFortnite/Saved/VerseProject/…); "
            "they are per-install and never redistributed.",
        )
    return parse_digest(
        path.read_text(errors="replace"), version=version or path.stem
    )


# -- lookup helpers ---------------------------------------------------------


def all_classes(digest: dict[str, Any]) -> dict[str, dict[str, Any]]:
    out = {}
    for module in digest["modules"].values():
        out.update(module["classes"])
    return out


def find_member(
    digest: dict[str, Any], class_name: str, member: str
) -> dict[str, Any] | None:
    classes = all_classes(digest)
    seen = set()
    stack = [class_name]
    while stack:
        name = stack.pop()
        if name in seen:
            continue
        seen.add(name)
        cls = classes.get(name)
        if cls is None:
            continue
        if member in cls["members"]:
            return cls["members"][member]
        stack.extend(cls["parents"])
    return None


def digest_diff(old: dict[str, Any], new: dict[str, Any]) -> dict[str, Any]:
    """Drift facts between two digest versions - the firewall rows for
    the 23.20 / 30.00 / 42.00 class of breaks."""
    old_classes, new_classes = all_classes(old), all_classes(new)
    facts: list[dict[str, Any]] = []
    for name in sorted(set(old_classes) - set(new_classes)):
        facts.append({"kind": "class_removed", "class": name})
    for name in sorted(set(new_classes) - set(old_classes)):
        facts.append({"kind": "class_added", "class": name})
    for name in sorted(set(old_classes) & set(new_classes)):
        old_members = old_classes[name]["members"]
        new_members = new_classes[name]["members"]
        for member in sorted(set(old_members) - set(new_members)):
            facts.append({
                "kind": "member_removed", "class": name, "member": member,
            })
        for member in sorted(set(new_members) - set(old_members)):
            facts.append({
                "kind": "member_added", "class": name, "member": member,
            })
        for member in sorted(set(old_members) & set(new_members)):
            old_effects = old_members[member].get("effects")
            new_effects = new_members[member].get("effects")
            if old_effects != new_effects:
                facts.append({
                    "kind": "effects_changed", "class": name, "member": member,
                    "from": old_effects, "to": new_effects,
                })
    return {
        "from": old.get("version"),
        "to": new.get("version"),
        "drift": facts,
        "breaking": [
            f for f in facts
            if f["kind"] in ("class_removed", "member_removed", "effects_changed")
        ],
    }
