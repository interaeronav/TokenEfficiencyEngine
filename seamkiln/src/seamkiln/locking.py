"""Locks: stop a change nobody meant to make.

A garment session is a long sequence of commands, and most of the damage a
long sequence does is accidental - a grade that also moved a panel you had
finished, a body swap that silently reset the room, a drape that overwrote a
fabric someone spent an afternoon choosing. A lock is the cheap answer: say
what is finished, and a command that would change it refuses instead.

Locks are on the SESSION, not on the objects, for one reason: a lock has to
survive being replayed. Because it is set by a command like everything else,
a script that locked the front panel at step 4 still locks it at step 4 when
it is replayed, and the drape that follows is the same drape.

What can be locked:
  panel:<id>   that panel's geometry - outline, marks, internals
  panels       every panel
  body         the subject: which body, its size, where it stands
  environment  the room - gravity, wind, temperature
  fabric       the material choice
  all          everything above
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

SCOPES = ("panels", "body", "environment", "fabric", "all")


class LockedError(RuntimeError):
    """A change refused because the thing it would change is locked."""


@dataclass(slots=True)
class Locks:
    held: set[str] = field(default_factory=set)
    reasons: dict[str, str] = field(default_factory=dict)

    def add(self, scope: str, reason: str = "") -> Locks:
        scope = str(scope).strip()
        if not (scope in SCOPES or scope.startswith("panel:")):
            raise ValueError(
                f"cannot lock {scope!r}. Lockable: {', '.join(SCOPES)}, or "
                "'panel:<id>' for one piece."
            )
        self.held.add(scope)
        if reason:
            self.reasons[scope] = reason
        return self

    def remove(self, scope: str) -> Locks:
        self.held.discard(scope)
        self.reasons.pop(scope, None)
        return self

    def clear(self) -> Locks:
        self.held.clear()
        self.reasons.clear()
        return self

    def covering(self, scope: str) -> str | None:
        """Which held lock covers this scope, if any. `all` covers everything,
        `panels` covers every individual panel."""
        if "all" in self.held:
            return "all"
        if scope in self.held:
            return scope
        if scope.startswith("panel:") and "panels" in self.held:
            return "panels"
        return None

    def check(self, scope: str, doing: str) -> None:
        """Refuse a change to a locked scope, naming how to allow it."""
        holder = self.covering(scope)
        if holder is None:
            return
        why = self.reasons.get(holder)
        raise LockedError(
            f"{doing} would change {scope}, which is locked"
            + (f" ({why})" if why else "")
            + f". Unlock it first: {{'op': 'unlock', 'args': {{'scope': '{holder}'}}}}."
        )

    def as_dict(self) -> dict[str, Any]:
        return {
            "locked": sorted(self.held),
            "reasons": dict(self.reasons),
            "lockable": [*SCOPES, "panel:<id>"],
        }
