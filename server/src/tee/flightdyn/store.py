"""Where a generated aircraft lives. One directory per aircraft, on disk."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from tee.kernel.errors import TeeError

_SAFE = re.compile(r"^[A-Za-z0-9_-]{1,48}$")


class AircraftStore:
    def __init__(self, project_root: Path | str) -> None:
        self.root = Path(project_root) / ".tee" / "flightdyn"

    def path(self, aircraft_id: str) -> Path:
        if not _SAFE.match(aircraft_id or ""):
            raise TeeError(
                "fd_bad_id",
                f"{aircraft_id!r} is not a valid aircraft id.",
                fix="Use letters, digits, underscore or hyphen, up to 48 characters.",
            )
        return self.root / aircraft_id

    def require(self, aircraft_id: str) -> Path:
        p = self.path(aircraft_id)
        if not (p / "aircraft" / aircraft_id / f"{aircraft_id}.xml").exists():
            known = self.list_ids()
            raise TeeError(
                "fd_no_aircraft",
                f"No aircraft {aircraft_id!r}."
                + (f" Known: {', '.join(known[:8])}." if known else " None generated yet."),
                fix="Generate one with fd_aircraft, or name one of the ids above.",
            )
        return p

    def list_ids(self) -> list[str]:
        if not self.root.is_dir():
            return []
        return sorted(p.name for p in self.root.iterdir() if p.is_dir())

    def write_record(self, aircraft_id: str, record: dict[str, Any]) -> None:
        p = self.path(aircraft_id)
        p.mkdir(parents=True, exist_ok=True)
        (p / "aircraft.json").write_text(json.dumps(record, indent=2, sort_keys=True))

    def read_record(self, aircraft_id: str) -> dict[str, Any]:
        f = self.path(aircraft_id) / "aircraft.json"
        return json.loads(f.read_text()) if f.exists() else {}
