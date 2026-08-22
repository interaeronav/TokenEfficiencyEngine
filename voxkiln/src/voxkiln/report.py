"""The compact machine report (decision A28): stats + repairs + budget
verdict + provenance, one message, never a render. Budget violations come
back with the exact fix - TEE's fail-loud-and-cheap rule as an API
contract."""

from __future__ import annotations

import hashlib
from typing import Any

import voxkiln

BUDGET_KEYS = ("max_tris", "require_watertight", "target_size_m", "max_texture")


def provenance(
    *,
    input_image_sha256: str,
    seed: int,
    params: dict[str, Any],
    model_repo: str = voxkiln.MODEL_REPO,
    model_revision: str | None = None,
) -> dict[str, Any]:
    return {
        "generator": "voxkiln",
        "generator_version": voxkiln.__version__,
        "upstream_commit": voxkiln.UPSTREAM_COMMIT,
        "model_repo": model_repo,
        "model_revision": model_revision or "unpinned",
        "input_image_sha256": input_image_sha256,
        "seed": seed,
        "params": params,
        "ai_generated": True,
    }


def mesh_content_hash(vertices, faces) -> str:
    """Stable content hash for determinism checks (research 48)."""
    import numpy as np

    h = hashlib.sha256()
    h.update(np.ascontiguousarray(np.round(np.asarray(vertices, dtype=np.float64), 6)).tobytes())
    h.update(np.ascontiguousarray(np.asarray(faces, dtype=np.int64)).tobytes())
    return h.hexdigest()[:16]


def validate_budget(budget: dict[str, Any] | None) -> None:
    """Reject unknown budget keys at SUBMIT time - a typo'd budget must
    fail loud before any GPU work, not silently pass everything."""
    if not budget:
        return
    unknown = set(budget) - set(BUDGET_KEYS)
    if unknown:
        raise ValueError(f"unknown budget keys {sorted(unknown)}; known: {BUDGET_KEYS}")


def verdict(stats: dict[str, Any], budget: dict[str, Any] | None) -> dict[str, Any]:
    """Accept/reject against the caller's budget, each violation with the
    exact fix."""
    if not budget:
        return {"accepted": True, "violations": []}
    validate_budget(budget)
    violations: list[dict[str, Any]] = []
    max_tris = budget.get("max_tris")
    if max_tris is not None and stats["tris"] > max_tris:
        violations.append(
            {
                "rule": "max_tris",
                "got": stats["tris"],
                "limit": max_tris,
                "fix": f"retry with target_faces={max_tris}",
            }
        )
    if budget.get("require_watertight") and not stats["watertight"]:
        violations.append(
            {
                "rule": "require_watertight",
                "got": False,
                "limit": True,
                "fix": "retry with repair_level='rebuild' (voxel rebuild closes the surface)",
            }
        )
    target_size = budget.get("target_size_m")
    if target_size is not None:
        largest = max(stats["bbox"]) if stats.get("bbox") else 0.0
        if largest <= 0 or not (0.5 * target_size <= largest <= 2.0 * target_size):
            violations.append(
                {
                    "rule": "target_size_m",
                    "got": round(largest, 4),
                    "limit": target_size,
                    "fix": f"scale by {target_size / largest:.4g} on import"
                    if largest > 0
                    else "generation produced an empty bbox - regenerate",
                }
            )
    max_texture = budget.get("max_texture")
    if max_texture is not None and stats.get("texture_size", 0) > max_texture:
        violations.append(
            {
                "rule": "max_texture",
                "got": stats["texture_size"],
                "limit": max_texture,
                "fix": f"retry with texture_size={max_texture}",
            }
        )
    return {"accepted": not violations, "violations": violations}


def build_report(
    *,
    asset_id: str,
    files: dict[str, str],
    stats: dict[str, Any],
    repairs: list[dict[str, Any]],
    budget: dict[str, Any] | None,
    prov: dict[str, Any],
    timings: dict[str, float] | None = None,
    notices: list[str] | None = None,
) -> dict[str, Any]:
    report = {
        "asset_id": asset_id,
        "files": files,
        "stats": stats,
        "repairs": repairs,
        "verdict": verdict(stats, budget),
        "provenance": prov,
    }
    if timings:
        report["timings_s"] = {k: round(v, 2) for k, v in timings.items()}
    if notices:
        report["notices"] = notices
    return report
