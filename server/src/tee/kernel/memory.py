"""Persistent cross-session project memory.

Fixes the catalogued friction point "users re-describe their scene every
session": a small on-disk state file per project, surfaced on demand through
tee_recall as a preamble capped at ~500 tokens.

A43 L3: **taint crosses this boundary.** Everywhere else in TEE taint is a
property of an id held in memory; here it must ride the stored bytes,
because otherwise persistence launders it - a web-derived summary written
in one session reads back "clean" in the next, and a default-clean caller
acts on attacker-shaped content (research 63 #1, confirmed by the qmax
adversarial pass 2026-08-30). So each fact carries a label bound to its
key AND a content hash, and a label that is missing, unreadable, or does
not match the stored value reads back TAINTED - fail closed at the one
place the id-based scheme has to become bytes.
"""

from __future__ import annotations

import contextlib
import hashlib
import json
import time
from pathlib import Path
from typing import Any

from tee.kernel import trustctx
from tee.kernel.budget import estimate_tokens

_MAX_NOTES = 40
_PREAMBLE_TOKENS = 500
_FACT_VALUE_LIMIT = 500
_FACT_KEY_LIMIT = 80


def _content_hash(value: Any) -> str:
    """Bind a taint label to the exact bytes it described."""
    return hashlib.sha256(json.dumps(value, sort_keys=True, default=str).encode()).hexdigest()[:16]


class ProjectMemory:
    def __init__(self, root: Path):
        self.path = Path(root) / ".tee" / "memory.json"
        self._data: dict[str, Any] = {"facts": {}, "notes": [], "taint": {}}
        self._load()

    def _load(self) -> None:
        try:
            loaded = json.loads(self.path.read_text())
        except FileNotFoundError:
            return
        except (json.JSONDecodeError, OSError):
            loaded = None
        # Corrupt or wrong-shaped memory must never break the session: start
        # fresh but keep the bad file for inspection.
        if (
            isinstance(loaded, dict)
            and isinstance(loaded.get("facts", {}), dict)
            and isinstance(loaded.get("notes", []), list)
        ):
            self._data = loaded
            self._data.setdefault("facts", {})
            self._data.setdefault("notes", [])
        else:
            backup = self.path.with_suffix(".corrupt.json")
            with contextlib.suppress(OSError):
                self.path.rename(backup)

    def _save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix(".tmp")
        tmp.write_text(json.dumps(self._data, indent=1))
        tmp.replace(self.path)

    # -- API ---------------------------------------------------------------

    def remember(self, key: str, value: Any) -> None:
        """Set one durable fact (dcc versions, naming conventions, paths...).
        Values are bounded - memory is a recap, not a data store.

        The writing task's taint is recorded WITH the value: a fact written
        while carrying untrusted content stays untrusted forever, and no
        later reader can be fooled by its clean-looking prose."""
        if isinstance(value, str) and len(value) > _FACT_VALUE_LIMIT:
            value = value[:_FACT_VALUE_LIMIT] + "…"
        stored_key = str(key)[:_FACT_KEY_LIMIT]
        self._data["facts"][stored_key] = value
        self._data.setdefault("taint", {})[stored_key] = {
            "hash": _content_hash(value),
            "tainted": bool(trustctx.taint()),
            "by": list(trustctx.taint())[:3],
        }
        self._save()

    def note(self, text: str) -> None:
        """Append one dated free-form note (done/todo log)."""
        notes: list[dict[str, str]] = self._data["notes"]
        notes.append({"at": time.strftime("%Y-%m-%d"), "text": text})
        if len(notes) > _MAX_NOTES:
            del notes[: len(notes) - _MAX_NOTES]
        self._save()

    def taint_of(self, key: str) -> bool:
        """Is this stored fact untrusted? Missing or mismatched label =>
        TAINTED (the fail-closed side of the persistence boundary)."""
        label = dict(self._data.get("taint") or {}).get(key)
        if not isinstance(label, dict):
            return True
        if label.get("hash") != _content_hash(self._data["facts"].get(key)):
            return True  # value changed under its label: trust nothing
        return bool(label.get("tainted"))

    def rehydrate_taint(self, keys: list[str] | None = None) -> list[str]:
        """Re-install stored taint into the reading task. Called on every
        read path, so a session that reads a tainted memory inherits it."""
        marked: list[str] = []
        for key in keys if keys is not None else list(self._data["facts"]):
            if self.taint_of(key):
                marked.append(f"memory:{key}")
        if marked:
            trustctx.add_taint(*marked)
        return marked

    def preamble(self, max_tokens: int = _PREAMBLE_TOKENS) -> dict[str, Any]:
        """Compact recap for session start; the cap always holds - newest
        notes win, then newest facts."""
        self.rehydrate_taint()
        facts = dict(self._data["facts"])
        notes = list(self._data["notes"])
        payload: dict[str, Any] = {"facts": facts, "notes": notes}
        truncated = False
        while notes and estimate_tokens(payload) > max_tokens:
            notes.pop(0)
            truncated = True
        fact_keys = list(facts)
        while fact_keys and estimate_tokens(payload) > max_tokens:
            facts.pop(fact_keys.pop(0))  # oldest facts go first
            truncated = True
        if truncated:
            payload["truncated"] = "older notes/facts dropped to fit the recap budget"
        return payload
