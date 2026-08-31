"""The upgrade trap: optional extras vanish, and nothing says so.

Claude Desktop provisions a bundle with `uv sync`, which rebuilds the
extension venv strictly from `uv.lock` and discards anything installed on
top of it. The fleet extras ARE installed on top by design — A46 P1 cut the
base venv from 2.2 GB to 586 MB precisely by keeping them out — so **every
upgrade deletes them**. Measured three times running: 0.9.0 -> 0.10.0,
0.11.0, and 0.12.0, each dropping the venv from ~1.1 GB back to 34 MB.

Documenting it did not work. The failure is quiet and, worse, *misleading*:
`probe.need()` refuses with "uv pip install 'tee-engine[medimg]'", which
reads as **you never set this up** rather than **your upgrade removed it**.
A correct message is the whole fix, because the two situations need
different reactions from the reader.

So TEE remembers. When a group is satisfiable its name is written here;
when one that was previously satisfiable stops importing, the refusal says
so and dates it. TEE does not reinstall anything itself — that is a
side-effecting act the owner takes — it just stops lying about what
happened.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

STATE_FILE = "extras-seen.json"

# group -> one import that proves the group is really there. Deliberately a
# leaf import, not the distribution name: a group is present when its code
# can actually run, not when metadata says so.
WITNESS = {
    "solve": "highspy",
    "quant": "skfolio",
    "medimg": "pydicom",
    "extract": "ezdxf",
    "assets": "imagehash",
    "cad": "cadquery",
}

# `cad` moved to a sidecar in A46 P1b and is NOT expected in TEE's own venv,
# so its absence is normal and must never be reported as a loss.
NOT_IN_TEE_VENV = frozenset({"cad"})


def _path(state_dir: str | Path | None) -> Path | None:
    return Path(state_dir) / STATE_FILE if state_dir else None


def present() -> set[str]:
    """Groups whose witness imports right now."""
    from importlib.util import find_spec

    out = set()
    for group, module in WITNESS.items():
        if group in NOT_IN_TEE_VENV:
            continue
        try:
            if find_spec(module) is not None:
                out.add(group)
        except (ImportError, ValueError):
            pass
    return out


def _load(state_dir: str | Path | None) -> dict[str, Any]:
    p = _path(state_dir)
    if not p or not p.is_file():
        return {}
    try:
        data = json.loads(p.read_text())
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def remember(state_dir: str | Path | None, *, today: str) -> dict[str, Any]:
    """Record what is installed now. Never forgets a group on its own: a
    group that disappears stays in the record with its last-seen date,
    because that date is the evidence that it was once there."""
    p = _path(state_dir)
    if not p:
        return {}
    seen = dict(_load(state_dir))
    for group in present():
        seen[group] = today
    try:
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(seen, indent=1, sort_keys=True))
    except OSError:
        return seen  # a read-only state dir must not break a tool call
    return seen


def lost(state_dir: str | Path | None) -> dict[str, str]:
    """group -> the date it was last seen, for groups that were installed
    and are not any more."""
    here = present()
    return {g: when for g, when in _load(state_dir).items() if g not in here}


def loss_note(group: str, state_dir: str | Path | None) -> str | None:
    """The sentence that turns 'never installed' into 'an upgrade ate it'."""
    when = lost(state_dir).get(group)
    if not when:
        return None
    return (
        f"[{group}] was installed here on {when} and is missing now. "
        "Installing a new TEE bundle rebuilds the venv from its lock and "
        "drops anything added on top - this is that, not a setup you never did."
    )
