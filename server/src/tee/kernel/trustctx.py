"""L2/L3: ambient caller class + taint, propagated by ONE mechanism.

Research 64's FP-1, verified against this code: chore call sites take raw
content, not a descriptor, and jobs run on DAEMON THREADS which do not
inherit context. So a taint label set during a live turn never reached the
model on exactly the async paths that matter. The fix is one ContextVar
pair with two install points — not N call-site edits:

    server.py:_tool   -> mints `live-turn` (the ONLY place it is minted)
    jobs.submit       -> snapshots the context; the worker re-installs it

Two rules make this safe rather than merely present:

* **`live-turn` is minted at the MCP boundary and never accepted from
  below.** A call arriving there IS a human turn; nothing deeper can
  claim one.
* **The hop DOWNGRADES the caller.** A job submitted during a live turn
  runs later, unattended, so the worker re-installs the *taint* verbatim
  but the caller becomes `job`. Propagating `live-turn` into a daemon
  thread would let a live turn mint standing authority for unattended
  work — the untaint path requires the human to be present, not to have
  been present once.

Absent context reads as `content-derived` with unknown taint: the default
is already the safe class (fail closed), which is what makes a forgotten
call site harmless instead of silently privileged.
"""

from __future__ import annotations

import contextvars

CALLER: contextvars.ContextVar[str] = contextvars.ContextVar(
    "tee_caller", default="content-derived"
)
# Ids (never payloads) of the untrusted content this task carries.
TAINT: contextvars.ContextVar[tuple[str, ...]] = contextvars.ContextVar("tee_taint", default=())


def caller() -> str:
    return CALLER.get()


def taint() -> tuple[str, ...]:
    return TAINT.get()


def is_live_turn() -> bool:
    return CALLER.get() == "live-turn"


def enter_live_turn():
    """Mint the live-turn class. Called ONLY by the MCP entry wrapper."""
    return CALLER.set("live-turn")


def reset(token) -> None:
    if token is not None:
        CALLER.reset(token)


def add_taint(*ids: str) -> None:
    """Mark this task as carrying untrusted content, by id.

    Called where untrusted content is minted (web extracts, backend
    results, KB reads, unapproved declarations). Ids only - taint is a
    property of an id, never of a string, which is exactly what makes it
    affordable in a system that already passes ids and not payloads."""
    if not ids:
        return
    current = set(TAINT.get())
    current.update(str(i) for i in ids if i)
    TAINT.set(tuple(sorted(current)))


def derive(new_id: str, parents: tuple[str, ...] | list[str]) -> str:
    """The ONLY sanctioned way to mint an id from other ids (FP-5).

    Unions parent taint by construction, so a summary of tainted inputs
    cannot come back clean through forgetfulness. An id built directly,
    without derivation, is treated as tainted by `taint_of` below - the
    safe path is the only path."""
    parent_ids = tuple(str(p) for p in parents if p)
    tainted = set(TAINT.get())
    if any(p in tainted for p in parent_ids):
        add_taint(new_id)
    _DERIVED[new_id] = parent_ids
    return new_id


# Derivation ledger: an id absent here has no known lineage (orphan), and
# an orphan reads back TAINTED. The audit sweep in tee_trust lists them.
_DERIVED: dict[str, tuple[str, ...]] = {}


def taint_of(entity_id: str) -> bool:
    """Is this id untrusted? Orphans (no derivation, no explicit clean
    mark) read back tainted - laundering by omission is the failure this
    prevents."""
    if entity_id in TAINT.get():
        return True
    return entity_id not in _DERIVED and entity_id not in _CLEAN


_CLEAN: set[str] = set()


def mark_clean(entity_id: str) -> None:
    """Record an id as first-party (owner-authored, TEE-generated). Only
    ever called from code paths that KNOW the provenance."""
    _CLEAN.add(str(entity_id))


def snapshot() -> tuple[str, tuple[str, ...]]:
    return CALLER.get(), TAINT.get()


def install(caller_class: str, taint_ids: tuple[str, ...]) -> None:
    """Install a snapshot inside a worker thread (jobs' daemon hop)."""
    CALLER.set(caller_class)
    TAINT.set(tuple(taint_ids))


def clear_for_tests() -> None:
    _DERIVED.clear()
    _CLEAN.clear()
    TAINT.set(())
