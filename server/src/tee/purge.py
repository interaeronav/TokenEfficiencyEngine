"""A52 — reclaiming what TEE left behind, and nothing else.

TEE writes a lot and reaps almost none of it: adapter workdirs from
`tempfile.mkdtemp` that outlive the process that made them, derived caches,
job directories, checkpoint scenes, staged bridge scripts. On this machine
`~/TEE/.tee` had reached 1.5 GB and orphaned `tee-*` temp directories were
scattered across `/tmp` and `/var/folders`.

**Three rules, and the first two are what make a delete tool safe to own.**

1. **It looks before it deletes, and it shows you first.** Every call is a
   DRY RUN unless `confirm: true`. The dry run names each candidate, its
   size and its age, so the decision is made on evidence rather than on
   trust in this module.
2. **It only removes what TEE made.** The scope is TEE's own state
   directory and its own `tee-*` temp directories. It will not touch the
   owner's projects, model caches, Docker, or anything it did not write -
   there is no path argument that lets a caller point it elsewhere, because
   a purge tool that can be aimed is a delete tool with a friendly name.
3. **Capability is not garbage.** The CAD sidecar is 1.4 GB and it IS the
   STEP-measuring capability (A46 P1b moved it out of the venv on purpose).
   Reclaiming it costs a ~150 s rebuild. It is therefore in its own
   category, never in the default sweep, and its entry says what removing
   it would cost.

What is NEVER removed, at any setting: `config.toml` and its backups,
`memory.json` (project memory), `extras-seen.json` (the upgrade-trap
record), pipeline pins, and anything under a project that is not TEE's own
`.tee` directory.
"""

from __future__ import annotations

import shutil
import time
from pathlib import Path
from typing import Any

from tee.kernel.errors import TeeError

# Never removed, whatever the caller asks for. These are records and
# decisions, not artefacts - losing them loses something a rebuild cannot
# restore.
PROTECTED = frozenset(
    {
        "config.toml",
        "memory.json",
        "extras-seen.json",
        "llm-profile.json",
        "pipeline.toml",
        "pipeline.pin",
        "server.pid",
    }
)

# category -> (relative paths under .tee, what it is, what losing it costs)
CATEGORIES: dict[str, tuple[tuple[str, ...], str, str]] = {
    "caches": (
        ("senses-cache.json", "embed-cache", "web", "kb-staging"),
        "derived answers and staged copies",
        "recomputed on next use - a repeated vision question pays the provider again",
    ),
    "workdirs": (
        (),  # handled specially: these live outside .tee
        "orphaned tee-* directories in the system temp dirs",
        "nothing - these belong to processes that have exited",
    ),
    "derived": (
        ("generated", "proxies", "exports", "capture", "boards"),
        "renders, proxies, exports and captures TEE produced",
        "re-render or re-export; the source scenes are untouched",
    ),
    "checkpoints": (
        ("shadow",),
        "checkpoint scenes and rollback state",
        "ROLLBACK HISTORY - you cannot undo past a purged checkpoint",
    ),
    "sidecars": (
        ("sidecars",),
        "the CAD sidecar venv - a CAPABILITY, not garbage",
        "cad_measure on STEP files stops working until rebuilt (~150 s, needs network)",
    ),
}

# Only these are swept when no category is named. `checkpoints` is excluded
# because losing rollback history is not a housekeeping decision, and
# `sidecars` because it is a capability.
DEFAULT_CATEGORIES = ("caches", "workdirs", "derived")


def _size(path: Path) -> int:
    if path.is_file():
        try:
            return path.stat().st_size
        except OSError:
            return 0
    total = 0
    for child in path.rglob("*"):
        try:
            if child.is_file():
                total += child.stat().st_size
        except OSError:
            continue
    return total


def _age_days(path: Path) -> float:
    try:
        return (time.time() - path.stat().st_mtime) / 86400.0
    except OSError:
        return 0.0


def _temp_workdirs() -> list[Path]:
    """`tee-*` directories left by `tempfile.mkdtemp` in adapters.

    Deliberately globbed rather than tracked: the processes that made them
    are gone, so there is no registry to consult - only the naming
    convention TEE itself uses.
    """
    import tempfile

    roots = {Path(tempfile.gettempdir()), Path("/tmp")}
    found: list[Path] = []
    for root in roots:
        if not root.is_dir():
            continue
        try:
            found.extend(p for p in root.glob("tee-*") if p.is_dir())
        except OSError:
            continue
    return sorted(set(found))


def _candidates(state: Path, categories: tuple[str, ...], older_than_days: float):
    out: list[dict[str, Any]] = []
    for name in categories:
        paths, what, cost = CATEGORIES[name]
        targets: list[Path] = []
        if name == "workdirs":
            targets = _temp_workdirs()
        else:
            for rel in paths:
                target = state / rel
                if target.exists():
                    targets.append(target)
        for target in targets:
            if target.name in PROTECTED:
                continue
            age = _age_days(target)
            if age < older_than_days:
                continue
            out.append(
                {
                    "category": name,
                    "path": str(target),
                    "bytes": _size(target),
                    "age_days": round(age, 1),
                    "what": what,
                    "losing_it_costs": cost,
                }
            )
    return out


def purge(spec: dict[str, Any], *, project_root: str | Path) -> dict[str, Any]:
    """Report what could be reclaimed; remove it only when told to."""
    state = Path(project_root).expanduser() / ".tee"
    asked = spec.get("categories") or list(DEFAULT_CATEGORIES)
    if isinstance(asked, str):
        asked = [asked]
    unknown = [c for c in asked if c not in CATEGORIES]
    if unknown:
        raise TeeError(
            "purge_unknown_category",
            f"Not a category: {', '.join(unknown)}.",
            fix=f"Use any of: {', '.join(CATEGORIES)}. Default sweep is "
            f"{', '.join(DEFAULT_CATEGORIES)} - `checkpoints` and `sidecars` "
            "are excluded from it on purpose and must be named.",
        )
    older = max(0.0, float(spec.get("older_than_days") or 0.0))
    confirm = bool(spec.get("confirm"))

    found = _candidates(state, tuple(asked), older)
    total = sum(item["bytes"] for item in found)

    if not confirm:
        return {
            "ok": True,
            "dry_run": True,
            "categories": asked,
            "candidates": len(found),
            "would_reclaim_bytes": total,
            "would_reclaim_mb": round(total / 1_048_576, 1),
            "items": sorted(found, key=lambda i: -i["bytes"])[:40],
            "protected": sorted(PROTECTED),
            "note": "Nothing was deleted. This is what a purge WOULD remove. "
            "Pass confirm: true to do it, after reading the list.",
        }

    removed, failed = [], []
    for item in found:
        target = Path(item["path"])
        if target.name in PROTECTED:  # belt and braces
            continue
        try:
            if target.is_dir():
                shutil.rmtree(target)
            else:
                target.unlink()
            removed.append(item)
        except OSError as exc:
            failed.append({**item, "error": str(exc)[:120]})
    reclaimed = sum(item["bytes"] for item in removed)
    return {
        "ok": not failed,
        "dry_run": False,
        "removed": len(removed),
        "reclaimed_bytes": reclaimed,
        "reclaimed_mb": round(reclaimed / 1_048_576, 1),
        "failed": failed,
        "categories": asked,
        "note": "Removed only TEE's own artefacts. Project files, model "
        "caches and Docker were not touched.",
    }


def register_purge_tools(app, project_root: str | Path) -> None:
    from tee.kernel.registry import VirtualTool

    root = Path(project_root)

    def tee_purge(args: dict[str, Any]) -> dict[str, Any]:
        return purge(args, project_root=root)

    app.registry.register(
        VirtualTool(
            name="tee_purge",
            description=(
                "Reclaim disk TEE itself used: derived renders and exports, "
                "caches, and orphaned adapter workdirs. ALWAYS a dry run "
                "first - it reports what it would remove, with sizes and "
                "ages, and deletes nothing until you pass confirm: true. "
                "It only ever touches TEE's own state directory and its own "
                "tee-* temp dirs; it cannot be pointed at anything else. "
                "Project memory, config and the upgrade record are never "
                "removed. `checkpoints` (rollback history) and `sidecars` "
                "(a working capability) are excluded from the default sweep "
                "and must be asked for by name."
            ),
            schema={
                "type": "object",
                "properties": {
                    "categories": {
                        "type": "array",
                        "items": {"type": "string", "enum": sorted(CATEGORIES)},
                        "description": "Default: caches, workdirs, derived.",
                    },
                    "older_than_days": {
                        "type": "number",
                        "description": "Only consider items older than this.",
                    },
                    "confirm": {
                        "type": "boolean",
                        "description": "Without this it is a dry run and deletes nothing.",
                    },
                },
            },
            handler=tee_purge,
            tags=[
                "purge",
                "clean",
                "cleanup",
                "disk",
                "space",
                "reclaim",
                "delete",
                "tidy",
                "housekeeping",
                "cache",
                "temp",
            ],
            examples=[{}, {"categories": ["derived"], "older_than_days": 7, "confirm": True}],
        )
    )
