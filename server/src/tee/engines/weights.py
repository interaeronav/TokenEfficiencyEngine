"""Resolve a model id to the weights on disk, by path arithmetic only.

`huggingface_hub` is banned here: the lane must answer with nothing installed,
and reading a cache does not need a client for the service that filled it.

A49's law governs the senses field: they come from the model's own
`config.json`, never from behaviour, because the owner's shim reroutes
image-bearing requests and through it every model appears to see. Where the
store keeps no identity - oMLX is content-addressed under `~/.omlx/cache/0..f`
- the answer is `unverified` with the reason, never a guess.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

GB = 1024.0**3


def cache_roots() -> list[Path]:
    """Where a HuggingFace cache may live, most specific first."""
    out: list[Path] = []
    for var in ("HF_HUB_CACHE", "HF_HOME", "TRANSFORMERS_CACHE"):
        v = os.environ.get(var)
        if v:
            p = Path(v)
            out.append(p if p.name == "hub" else p / "hub")
    out.append(Path.home() / ".cache" / "huggingface" / "hub")
    return [p for i, p in enumerate(out) if p not in out[:i]]


def _snapshot(root: Path, model_id: str) -> Path | None:
    """`org/name` -> `<root>/models--org--name/snapshots/<sha>`."""
    d = root / ("models--" + model_id.replace("/", "--"))
    snaps = d / "snapshots"
    if not snaps.is_dir():
        return None
    kids = [p for p in snaps.iterdir() if p.is_dir()]
    if not kids:
        return None
    return max(kids, key=lambda p: p.stat().st_mtime)


def locate(model_id: str) -> dict[str, Any]:
    """Where this model's files are, or why they cannot be found."""
    if not model_id or "/" not in model_id:
        return {
            "found": False,
            "reason": f"{model_id!r} is not an org/name id; a served alias is not a "
            "checkpoint name and cannot be resolved to files",
        }
    for root in cache_roots():
        snap = _snapshot(root, model_id)
        if snap is not None:
            return {"found": True, "path": str(snap), "cache_root": str(root)}
    return {"found": False, "reason": "no snapshot under any known cache root"}


def footprint_gb(path: str | Path) -> float | None:
    """Measured weight bytes, in GB. None when there is nothing to weigh."""
    p = Path(path)
    if not p.is_dir():
        return None
    total = 0
    for f in p.rglob("*"):
        if f.is_file() and f.suffix in {".safetensors", ".bin", ".gguf", ".npz"}:
            try:
                total += f.stat().st_size
            except OSError:  # pragma: no cover - a race with a download
                continue
    return round(total / GB, 3) if total else None


def senses_from_config(path: str | Path) -> dict[str, Any]:
    """What the weights say about themselves. A49's method, automated."""
    cfg_file = Path(path) / "config.json"
    if not cfg_file.is_file():
        return {"senses": None, "senses_source": "no config.json beside the weights"}
    try:
        cfg = json.loads(cfg_file.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        return {"senses": None, "senses_source": f"config.json unreadable: {exc}"}
    senses: list[str] = []
    if cfg.get("vision_config") or cfg.get("image_token_id") is not None:
        senses.append("vision")
    if cfg.get("audio_config") or cfg.get("audio_token_id") is not None:
        senses.append("audio")
    arch = cfg.get("architectures") or []
    return {
        "senses": senses,
        "architectures": arch if isinstance(arch, list) else [str(arch)],
        "senses_source": f"config.json at {cfg_file}",
    }


def describe(model_id: str) -> dict[str, Any]:
    """The whole on-disk story for one model id."""
    out: dict[str, Any] = {"model": model_id}
    where = locate(model_id)
    out |= where
    if not where.get("found"):
        out["senses"] = None
        out["senses_source"] = where.get("reason")
        return out
    out["footprint_gb"] = footprint_gb(where["path"])
    out |= senses_from_config(where["path"])
    return out
