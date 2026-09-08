"""The join nothing has ever made: ENGINES x profiles x scan x measured file.

Each row gets ONE verdict and one line saying what to do about it. The digest
never probes - it reads a cached scan and says how old it is.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from tee.kernel.machine import ENGINES

MEASURED_FILE = "engines.json"
STALE_DAYS = 30.0

#: Ordered: the first that applies wins, so a paid engine is never reported as
#: merely unreachable and a wrong row is never reported as merely stale.
VERDICTS = (
    "paid",
    "declared-not-served",
    "served-not-reachable",
    "named-wrong",
    "endpoint-down",
    "wrong",
    "stale",
    "unmeasured",
    "live",
)


def measured_path(state_dir: str | Path | None) -> Path | None:
    return Path(state_dir) / MEASURED_FILE if state_dir else None


def load_measured(state_dir: str | Path | None) -> dict[str, Any]:
    p = measured_path(state_dir)
    if p is None or not p.is_file():
        return {}
    try:
        rows = json.loads(p.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}
    return rows if isinstance(rows, dict) else {}


def save_measured(state_dir: str | Path | None, rows: dict[str, Any]) -> Path | None:
    p = measured_path(state_dir)
    if p is None:
        return None
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(".tmp")
    tmp.write_text(json.dumps(rows, indent=2, sort_keys=True), encoding="utf-8")
    tmp.replace(p)
    return p


def _verdict(
    engine: str,
    spec: dict[str, Any],
    declared_profiles: dict[str, Any],
    served: dict[str, list[str]],
    endpoint_up: dict[str, bool],
    resolved_url: str | None,
    resolved_model: str | None,
    measured: dict[str, Any],
    now: float,
    stale_days: float,
    fallback_model: str | None = None,
) -> tuple[str, str]:
    """(verdict, the one line that says what to do)."""
    profile = spec.get("profile")
    if profile and bool((declared_profiles.get(profile) or {}).get("paid")):
        return "paid", "never a router target; not measured"
    # ENGINES carries model=None on every row: the id lives in the profile
    # spec (BUILTIN_PROFILES / [llm.profiles.*]), falling back to [llm] model.
    # That absence is why nothing has ever reconciled this table - there was
    # no machine-readable id to join on.
    declared_here = profile in declared_profiles
    pspec = declared_profiles.get(profile) or {}
    # ENGINES carries model=None on every row: the id lives in the profile spec
    # (BUILTIN_PROFILES / [llm.profiles.*]). That absence is why nothing has
    # ever reconciled this table - there was no machine-readable id to join on.
    # A profile this machine has NOT declared has no model at all: inheriting
    # the ACTIVE profile's id would report every unknown engine as serving
    # whatever is currently pinned, which is the sin this lane exists to stop.
    model = spec.get("model") or pspec.get("model")
    if model is None and declared_here:
        model = fallback_model  # a declared profile with no model key inherits [llm]

    served_ids = set(served)
    model_served = bool(model and model in served_ids)

    if not declared_here:
        if model_served:
            return (
                "served-not-reachable",
                f"served but unreachable: add [llm.profiles.{profile}]",
            )
        return (
            "declared-not-served",
            f"no profile declares {profile!r}: no model id, so nothing routes "
            f"here. Declare it or drop the row",
        )

    if resolved_url and endpoint_up.get(resolved_url) is False:
        return "endpoint-down", f"{resolved_url} silent"
    if resolved_model and served_ids and resolved_model not in served_ids:
        return (
            "named-wrong",
            f"endpoint answers but does not serve {resolved_model!r}",
        )

    row = measured.get(engine) or {}
    if row:
        if row.get("model") and model and row["model"] != model:
            return "wrong", f"measured {row['model']!r}, registry says {model!r}: re-audition"
        age_days = (now - float(row.get("measured_at") or 0)) / 86400.0
        if age_days > stale_days:
            return "stale", f"measured {age_days:.0f}d ago: re-audition"
        return "live", "measured and current"
    return "unmeasured", "reachable, never measured: eng_audition"


def reconcile(
    *,
    declared_profiles: dict[str, Any],
    scan: dict[str, Any],
    measured: dict[str, Any],
    resolved: dict[str, Any] | None = None,
    stale_days: float = STALE_DAYS,
    now: float | None = None,
) -> dict[str, Any]:
    """One verdict per ENGINES row, plus what the join could not explain."""
    now = time.time() if now is None else now
    served = scan.get("served_models") or {}
    endpoint_up = {r["url"]: bool(r.get("answers")) for r in scan.get("endpoints") or []}
    resolved = resolved or {}

    rows: list[dict[str, Any]] = []
    for engine, spec in ENGINES.items():
        if not spec.get("profile"):
            continue  # jobs and non-model rows are not engines in this sense
        r_url = resolved.get("url") if spec.get("profile") == resolved.get("profile") else None
        r_model = resolved.get("model") if spec.get("profile") == resolved.get("profile") else None
        verdict, fix = _verdict(
            engine,
            spec,
            declared_profiles,
            served,
            endpoint_up,
            r_url,
            r_model,
            measured,
            now,
            stale_days,
            fallback_model=resolved.get("model"),
        )
        pspec = declared_profiles.get(spec.get("profile")) or {}
        row = {
            "engine": engine,
            "model": (
                spec.get("model")
                or pspec.get("model")
                or (resolved.get("model") if spec.get("profile") in declared_profiles else None)
            ),
            "verdict": verdict,
        }
        if verdict != "live":  # a healthy row needs no remedy, and the digest pays per word
            row["fix"] = fix
        m = measured.get(engine) or {}
        declared_gb = spec.get("footprint_gb")
        if (
            m.get("footprint_gb") is not None
            and declared_gb is not None
            and abs(float(m["footprint_gb"]) - float(declared_gb)) > 0.5
        ):
            row["footprint_disagrees"] = {
                "declared_gb": declared_gb,
                "measured_gb": m["footprint_gb"],
            }
        rows.append(row)

    served_unclaimed = sorted(
        m
        for m in served
        if not any(s.get("model") == m for s in ENGINES.values()) and not m.endswith("*")
    )
    counts: dict[str, int] = {}
    for r in rows:
        counts[r["verdict"]] = counts.get(r["verdict"], 0) + 1
    return {
        "rows": rows,
        "verdicts": counts,
        "measured_rows": len(measured),
        "endpoints": {"scanned": scan.get("scanned", 0), "answering": scan.get("answering", 0)},
        "scan_age_s": round(now - float(scan.get("scanned_at") or now), 1),
        "served_but_unregistered": served_unclaimed[:32],
    }
