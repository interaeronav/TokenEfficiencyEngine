"""The case store: `<project>/.tee/windtunnel/cases/<case_id>/` with a
`case.json` sidecar that carries the provenance every answer quotes
(geometry hash, conditions, engine and version, dictionary hash, mesh hash,
runs and their results) - the `CloudStore` shape of the point-cloud lane.

The digest law lives here too: `digest()` walks any response and refuses to
let an array over 64 elements or a string over 2 KB through (a long list is
thinned to every k-th element and says so). The model never sees a cell.
"""

from __future__ import annotations

import hashlib
import json
import os
import threading
import time
from pathlib import Path
from typing import Any

from tee.kernel.errors import TeeError

MAX_ARRAY = 64
MAX_STRING = 2048


def digest(obj: Any, *, max_array: int = MAX_ARRAY, max_string: int = MAX_STRING) -> Any:
    """The response-size law, applied recursively."""
    if isinstance(obj, dict):
        return {
            str(k): digest(v, max_array=max_array, max_string=max_string) for k, v in obj.items()
        }
    if isinstance(obj, (list, tuple)):
        items = list(obj)
        if len(items) > max_array:
            step = -(-len(items) // max_array)
            items = items[::step][:max_array]
            items = [digest(v, max_array=max_array, max_string=max_string) for v in items]
            return {"thinned": True, "every": step, "n_total": len(obj), "items": items}
        return [digest(v, max_array=max_array, max_string=max_string) for v in items]
    if isinstance(obj, str) and len(obj) > max_string:
        return obj[: max_string - 16] + f"... [{len(obj)} chars]"
    if isinstance(obj, float):
        if obj != obj or obj in (float("inf"), float("-inf")):
            return None
        return obj
    return obj


def file_hash(path: Path, limit: int = 0) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        while True:
            chunk = fh.read(1 << 20)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()[:16]


def text_hash(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()[:16]


class CaseStore:
    """`case.json` per case. A solver's worker thread and the tool calls
    that poll it both rewrite the record, so every read-modify-write holds
    one lock; the file itself is replaced atomically."""

    def __init__(self, project_root: Path | str) -> None:
        self.root = Path(project_root).resolve() / ".tee" / "windtunnel"
        self.cases_dir = self.root / "cases"
        self.cases_dir.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()

    # -- ids -----------------------------------------------------------------
    def mint(self, kind: str, meta: dict[str, Any]) -> str:
        seed = (
            f"{time.time_ns()}:{os.getpid()}:{kind}:{json.dumps(meta, sort_keys=True, default=str)}"
        )
        case_id = "wt_" + hashlib.sha1(seed.encode()).hexdigest()[:10]
        d = self.case_dir(case_id)
        d.mkdir(parents=True, exist_ok=False)
        (d / "runs").mkdir()
        (d / "geometry").mkdir()
        record = {
            "case_id": case_id,
            "kind": kind,
            "created_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "state": "created",
            "runs": [],
            **meta,
        }
        self.save(case_id, record)
        return case_id

    def case_dir(self, case_id: str) -> Path:
        if not case_id.startswith("wt_") or "/" in case_id or ".." in case_id:
            raise TeeError(
                "wt_unknown_case",
                f"'{case_id}' is not a case id.",
                fix="Ids look like wt_1a2b3c4d5e; wt_case action=list shows them.",
            )
        return self.cases_dir / case_id

    def load(self, case_id: str) -> dict[str, Any]:
        path = self.case_dir(case_id) / "case.json"
        if not path.is_file():
            known = (
                ", ".join(sorted(p.name for p in self.cases_dir.iterdir() if p.is_dir())[:8])
                or "none"
            )
            raise TeeError("wt_unknown_case", f"No case '{case_id}'.", fix=f"Known cases: {known}.")
        return json.loads(path.read_text())

    def save(self, case_id: str, record: dict[str, Any]) -> None:
        path = self.case_dir(case_id) / "case.json"
        tmp = path.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(record, indent=1, default=str))
        os.replace(tmp, path)

    def update(self, case_id: str, **fields: Any) -> dict[str, Any]:
        with self._lock:
            rec = self.load(case_id)
            rec.update(fields)
            self.save(case_id, rec)
            return rec

    def list(self) -> list[dict[str, Any]]:
        out = []
        for p in sorted(self.cases_dir.iterdir()):
            if (p / "case.json").is_file():
                try:
                    rec = json.loads((p / "case.json").read_text())
                except ValueError:
                    continue
                out.append(
                    {
                        "case_id": rec.get("case_id", p.name),
                        "kind": rec.get("kind"),
                        "engine": rec.get("engine"),
                        "state": rec.get("state"),
                        "runs": len(rec.get("runs", [])),
                        "created_at": rec.get("created_at"),
                    }
                )
        return out

    # -- runs ----------------------------------------------------------------
    def new_run_id(self, case_id: str) -> str:
        rec = self.load(case_id)
        n = len(rec.get("runs", [])) + 1
        return f"run_{n:03d}"

    def run_dir(self, case_id: str, run_id: str) -> Path:
        if "/" in run_id or ".." in run_id:
            raise TeeError(
                "wt_unknown_run", f"'{run_id}' is not a run id.", fix="Run ids look like run_001."
            )
        return self.case_dir(case_id) / "runs" / run_id

    def add_run(self, case_id: str, run: dict[str, Any]) -> None:
        """Add or merge a run record (an existing run keeps the fields the
        new record does not name: the job id survives a state change)."""
        with self._lock:
            rec = self.load(case_id)
            runs = list(rec.get("runs", []))
            for i, r in enumerate(runs):
                if r.get("run_id") == run.get("run_id"):
                    runs[i] = {**r, **run}
                    break
            else:
                runs.append(dict(run))
            rec["runs"] = runs
            rec["state"] = run.get("state", rec.get("state"))
            self.save(case_id, rec)

    def find_run(self, case_id: str, run_id: str | None) -> dict[str, Any]:
        rec = self.load(case_id)
        runs = rec.get("runs", [])
        if not runs:
            raise TeeError("wt_no_results", f"Case {case_id} has no runs yet.", fix="wt_run first.")
        if run_id is None:
            return runs[-1]
        for r in runs:
            if r.get("run_id") == run_id:
                return r
        raise TeeError(
            "wt_unknown_run",
            f"No run '{run_id}' in case {case_id}.",
            fix=f"Runs: {', '.join(r['run_id'] for r in runs)}.",
        )

    def resolve(self, ref: str) -> tuple[str, str | None]:
        """`wt_xxxx` -> (case, latest); `wt_xxxx/run_002` -> (case, run)."""
        if "/" in ref:
            case_id, run_id = ref.split("/", 1)
            return case_id, run_id
        return ref, None
