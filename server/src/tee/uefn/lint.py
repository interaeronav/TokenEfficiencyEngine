"""Digest-grounded Verse linting (12.2): the honest offline check.

There is no public Verse compiler, so full type/effect checking outside
UEFN is not claimable - but the DOMINANT failure class (hallucinated or
stale API) is checkable cheaply: every member access, effect specifier,
and event subscription the model emits is verified against the loaded
digest. Known drift (the v30.00 effects redesign, renamed members) gets
targeted one-line fixes; everything else unknown is flagged with the
nearest matches.
"""

from __future__ import annotations

import re
from typing import Any

from tee.uefn.digest import KNOWN_EFFECTS, all_classes, find_member

# Known-drift map: the documented hallucination classes with their exact
# fixes (research 39; each entry names the version that broke it).
KNOWN_DRIFT = {
    "varies": (
        "<varies> was removed in the v30.00 effects redesign (Sept 2024) - "
        "use the granular effects: <transacts> (default) or "
        "<reads><writes><allocates>"
    ),
    "GetPassengers": ("fort_vehicle.GetPassengers() was deprecated in v42.00 - use GetOccupants()"),
    "no_rollback": (
        "<no_rollback> is deprecated head-of-development syntax - not valid in shipped UEFN"
    ),
}

# Compiler-error -> one-line-fix map (fail loud and cheap), including the
# documented stale-validation false-positive class.
ERROR_FIXES = {
    "vErr:S77": "unknown identifier - check the digest spelling (uefn_lint "
    "catches these before compile)",
    "vErr:S57": "effect specifier not allowed here - suspends and decides "
    "cannot combine; check the function's effect row in the digest",
    "stale_validation": "publish validation sometimes reports errors from a "
    "PREVIOUS build (documented false-positive class) - recompile once "
    "before trusting the list; if it persists, the error is real",
}

_MEMBER_ACCESS_RE = re.compile(r"\b([A-Z]\w*|\w+_device)\s*\.\s*(\w+)\s*\(")
_EFFECT_USE_RE = re.compile(r"<(\w+)>")
_SUBSCRIBE_RE = re.compile(r"\b(\w+)\s*\.\s*(\w+)\s*\.\s*Subscribe\s*\(")
_TYPE_ANNOTATION_RE = re.compile(r":\s*(\w+_device)\b")


def lint(code: str, digest: dict[str, Any]) -> dict[str, Any]:
    """Findings with one-line fixes; empty findings = the symbol layer is
    digest-clean (NOT a compile - the honest boundary is stated)."""
    findings: list[dict[str, Any]] = []
    classes = all_classes(digest)

    # 1. effect specifiers
    for match in _EFFECT_USE_RE.finditer(code):
        effect = match.group(1)
        if effect in KNOWN_DRIFT:
            findings.append(
                {
                    "kind": "known_drift",
                    "symbol": f"<{effect}>",
                    "fix": KNOWN_DRIFT[effect],
                }
            )
        elif effect.lower() not in KNOWN_EFFECTS and effect not in classes:
            findings.append(
                {
                    "kind": "unknown_effect",
                    "symbol": f"<{effect}>",
                    "fix": f"'{effect}' is not a known effect/specifier; known: "
                    "converges, computes, transacts, reads, writes, allocates, "
                    "suspends, decides",
                }
            )

    # 2. typed device/class member calls
    for match in _MEMBER_ACCESS_RE.finditer(code):
        owner, member = match.group(1), match.group(2)
        if member in KNOWN_DRIFT:
            findings.append(
                {
                    "kind": "known_drift",
                    "symbol": f"{owner}.{member}",
                    "fix": KNOWN_DRIFT[member],
                }
            )
            continue
        if owner in classes and find_member(digest, owner, member) is None:
            nearest = _nearest(member, classes[owner]["members"])
            findings.append(
                {
                    "kind": "unknown_member",
                    "symbol": f"{owner}.{member}",
                    "fix": f"'{member}' is not in the {owner} digest entry"
                    + (f"; nearest: {', '.join(nearest)}" if nearest else ""),
                }
            )

    # 3. variables typed as devices: resolve their member calls too
    var_types: dict[str, str] = {}
    for match in _TYPE_ANNOTATION_RE.finditer(code):
        # crude but effective: `Name : type_device` bindings
        prefix = code[: match.start()].rsplit("\n", 1)[-1]
        var = prefix.strip().split()[-1] if prefix.strip() else ""
        if var.isidentifier():
            var_types[var] = match.group(1)
    for match in re.finditer(r"\b(\w+)\s*\.\s*(\w+)\s*\(", code):
        owner_var, member = match.group(1), match.group(2)
        cls = var_types.get(owner_var)
        if cls and cls in classes and member != "Subscribe":
            if member in KNOWN_DRIFT:
                findings.append(
                    {
                        "kind": "known_drift",
                        "symbol": f"{owner_var}.{member}",
                        "fix": KNOWN_DRIFT[member],
                    }
                )
            elif find_member(digest, cls, member) is None:
                nearest = _nearest(member, classes[cls]["members"])
                findings.append(
                    {
                        "kind": "unknown_member",
                        "symbol": f"{owner_var}.{member} ({cls})",
                        "fix": f"'{member}' is not on {cls} in the digest"
                        + (f"; nearest: {', '.join(nearest)}" if nearest else ""),
                    }
                )

    # 4. event subscriptions must target listenable members
    for match in _SUBSCRIBE_RE.finditer(code):
        owner_var, event = match.group(1), match.group(2)
        cls = var_types.get(owner_var)
        if cls and cls in classes:
            member = find_member(digest, cls, event)
            if member is None or member.get("kind") != "event":
                findings.append(
                    {
                        "kind": "not_listenable",
                        "symbol": f"{owner_var}.{event}.Subscribe",
                        "fix": f"'{event}' is not a listenable event on {cls}; "
                        f"events: {_events_of(digest, cls)}",
                    }
                )

    deduped = []
    seen = set()
    for finding in findings:
        key = (finding["kind"], finding["symbol"])
        if key not in seen:
            seen.add(key)
            deduped.append(finding)
    return {
        "findings": deduped,
        "digest_version": digest.get("version"),
        "boundary": (
            "symbol/signature lint against the digest - catches stale/"
            "hallucinated API; it is NOT a compile (type/effect checking "
            "needs the UEFN editor via Epic's MCP Verse toolset)"
        ),
    }


def _nearest(name: str, members: dict[str, Any], limit: int = 3) -> list[str]:
    lower = name.lower()
    scored = []
    for candidate in members:
        cl = candidate.lower()
        score = 0
        if lower in cl or cl in lower:
            score += 2
        score += len(set(lower) & set(cl)) / max(len(set(lower) | set(cl)), 1)
        scored.append((score, candidate))
    scored.sort(key=lambda pair: -pair[0])
    return [c for s, c in scored[:limit] if s > 0.5]


def _events_of(digest: dict[str, Any], class_name: str) -> str:
    classes = all_classes(digest)
    events = []
    stack, seen = [class_name], set()
    while stack:
        cls_name = stack.pop()
        if cls_name in seen:
            continue
        seen.add(cls_name)
        cls = classes.get(cls_name)
        if cls:
            events += [m for m, v in cls["members"].items() if v.get("kind") == "event"]
            stack.extend(cls["parents"])
    return ", ".join(sorted(events)) or "(none)"


def explain_error(error_code: str) -> dict[str, str]:
    fix = ERROR_FIXES.get(error_code)
    if fix is None:
        return {
            "error": error_code,
            "fix": "not in the mapped set - read the compiler message; if it "
            "names a symbol, run uefn_lint on the file first",
        }
    return {"error": error_code, "fix": fix}
