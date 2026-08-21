"""Persistent cross-session project memory.

Fixes the catalogued friction point "users re-describe their scene every
session": a small on-disk state file per project, surfaced on demand through
tee_recall as a preamble capped at ~500 tokens.
"""

from __future__ import annotations

import contextlib
import json
import time
from pathlib import Path
from typing import Any

from tee.kernel.budget import estimate_tokens

_MAX_NOTES = 40
_PREAMBLE_TOKENS = 500


class ProjectMemory:
    def __init__(self, root: Path):
        self.path = Path(root) / ".tee" / "memory.json"
        self._data: dict[str, Any] = {"facts": {}, "notes": []}
        self._load()

    def _load(self) -> None:
        try:
            self._data = json.loads(self.path.read_text())
        except FileNotFoundError:
            pass
        except (json.JSONDecodeError, OSError):
            # Corrupt memory must never break the session; start fresh but
            # keep the corrupt file for inspection.
            backup = self.path.with_suffix(".corrupt.json")
            with contextlib.suppress(OSError):
                self.path.rename(backup)
        self._data.setdefault("facts", {})
        self._data.setdefault("notes", [])

    def _save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix(".tmp")
        tmp.write_text(json.dumps(self._data, indent=1))
        tmp.replace(self.path)

    # -- API ---------------------------------------------------------------

    def remember(self, key: str, value: Any) -> None:
        """Set one durable fact (dcc versions, naming conventions, paths...)."""
        self._data["facts"][key] = value
        self._save()

    def note(self, text: str) -> None:
        """Append one dated free-form note (done/todo log)."""
        notes: list[dict[str, str]] = self._data["notes"]
        notes.append({"at": time.strftime("%Y-%m-%d"), "text": text})
        if len(notes) > _MAX_NOTES:
            del notes[: len(notes) - _MAX_NOTES]
        self._save()

    def preamble(self, max_tokens: int = _PREAMBLE_TOKENS) -> dict[str, Any]:
        """Compact recap for session start; newest notes win under the cap."""
        facts = self._data["facts"]
        notes = list(self._data["notes"])
        payload = {"facts": facts, "notes": notes}
        while notes and estimate_tokens(payload) > max_tokens:
            notes.pop(0)
            payload = {"facts": facts, "notes": notes, "truncated": "older notes dropped"}
        return payload
