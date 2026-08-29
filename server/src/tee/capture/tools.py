"""Capture lane virtual tools (A42 T2): ingest + reconstruct.

Surface LAW: everything here is virtual (search -> describe -> call);
nothing joins the always-loaded surface. Capture sets ingest through the
EXISTING extract store (content-addressed, EXIF preserved, originals
referenced in place) plus a set manifest under `.tee/capture/sets/`;
reconstructions ride the jobs pattern and are gated BEFORE submission —
disk, engine presence, image count — with refusals that name the fix.
The ODM drone lane refuses without a Docker runtime (the T0 batched owner
ask); the PhotogrammetrySession helper serves structure sets today.
"""

from __future__ import annotations

import contextlib
import hashlib
import json
import os
import platform
import shutil
import subprocess
import time
from pathlib import Path
from typing import Any

from tee.capture import dji
from tee.kernel.errors import TeeError
from tee.kernel.registry import VirtualTool

DETAILS = ("preview", "reduced", "medium", "full", "raw")
MIN_IMAGES = 10
DEFAULT_MIN_FREE_GB = 20.0


def _sets_dir(root: Path) -> Path:
    return root / ".tee" / "capture" / "sets"


def _out_dir(root: Path) -> Path:
    return root / ".tee" / "capture" / "out"


def _helper_path(root: Path, cfg: dict[str, Any]) -> Path:
    configured = cfg.get("helper")
    if configured:
        return Path(str(configured)).expanduser()
    for base in (root, root.parent):
        candidate = base / "helpers" / "photogrammetry" / "tee-photogrammetry"
        if candidate.is_file():
            return candidate
    return root / "helpers" / "photogrammetry" / "tee-photogrammetry"


def _gate_disk(root: Path, cfg: dict[str, Any]) -> None:
    floor_gb = float(cfg.get("min_free_gb", DEFAULT_MIN_FREE_GB))
    free_gb = shutil.disk_usage(root).free / 1e9
    if free_gb < floor_gb:
        raise TeeError(
            "capture_disk_low",
            f"Only {free_gb:.1f} GB free (floor {floor_gb:.0f} GB) - "
            "reconstructions are tens of GB.",
            fix="Free disk space or lower [capture] min_free_gb deliberately.",
        )


def register_capture_tools(app, project_root: Path | str, extract_store=None) -> None:
    root = Path(project_root)
    reg = app.registry
    cfg = dict(getattr(app.config, "capture", {}) or {})

    def _store():
        if extract_store is None:
            raise TeeError(
                "extract_missing",
                "Capture ingest rides the extract store, which is not active.",
                fix="Install the server with the 'extract' extra.",
            )
        return extract_store

    def _manifest(set_id: str) -> dict[str, Any]:
        path = _sets_dir(root) / f"{set_id}.json"
        if not path.is_file():
            known = sorted(p.stem for p in _sets_dir(root).glob("*.json"))
            raise TeeError(
                "capture_unknown_set",
                f"No capture set '{set_id}'.",
                fix=f"capture_ingest first; known sets: {known or 'none'}",
            )
        return json.loads(path.read_text())

    def capture_ingest(args: dict[str, Any]) -> dict[str, Any]:
        paths = [Path(p) for p in args.get("paths") or []]
        resolved = dji.resolve_set(paths)  # refuses empty/missing loudly
        store = _store()
        hashes = [store.register_source(p)["hash"] for p in paths]
        set_id = hashlib.sha256("".join(sorted(hashes)).encode()).hexdigest()[:12]
        manifest = {
            "set": set_id,
            "label": str(args.get("label") or ""),
            "files": hashes,
            "resolver": resolved,
            "created": time.strftime("%Y-%m-%d %H:%M:%S"),
        }
        _sets_dir(root).mkdir(parents=True, exist_ok=True)
        (_sets_dir(root) / f"{set_id}.json").write_text(json.dumps(manifest, indent=1))
        return {
            "set": set_id,
            "files": len(hashes),
            "cameras": resolved["sets"],
            "split_by_camera": resolved["split_by_camera"],
        }

    def _engine_for(manifest: dict[str, Any], requested: str) -> str:
        if requested != "auto":
            return requested
        drone = any(
            s["camera_code"] in dji.MODEL_TABLE or s["priors"].get("relative_altitude_m")
            for s in manifest["resolver"]["sets"]
        )
        return "odm" if drone else "photogrammetry"

    def _input_paths(manifest: dict[str, Any]) -> list[Path]:
        store = _store()
        paths = []
        for media_hash in manifest["files"]:
            meta = json.loads((store.source_dir(media_hash) / "meta.json").read_text())
            existing = next((Path(p) for p in meta["paths"] if Path(p).is_file()), None)
            if existing is None:
                raise TeeError(
                    "capture_originals_moved",
                    f"No original on disk for {media_hash[:8]} (known paths: {meta['paths']}).",
                    fix="Restore the originals or re-ingest the set.",
                )
            paths.append(existing)
        return paths

    def _run_helper(helper: Path, inputs: list[Path], out_path: Path, detail: str, job_dir: Path):
        link_dir = job_dir / "input"
        link_dir.mkdir(parents=True, exist_ok=True)
        for i, src in enumerate(inputs):
            target = link_dir / f"{i:04d}{src.suffix.lower()}"
            try:
                os.symlink(src, target)
            except OSError:
                shutil.copy2(src, target)
        events: list[dict[str, Any]] = []
        with subprocess.Popen(
            [str(helper), str(link_dir), str(out_path), "--detail", detail],
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
        ) as proc:
            for line in proc.stdout or []:
                line = line.strip()
                if line.startswith("{"):
                    with contextlib.suppress(json.JSONDecodeError):
                        events.append(json.loads(line))
            code = proc.wait()
        (job_dir / "events.json").write_text(json.dumps(events, indent=1))
        error = next((e for e in events if e.get("event") == "error"), None)
        if code != 0 or error:
            message = (error or {}).get("message", f"helper exited {code}")
            fix = (error or {}).get("fix", "See the capture protocol's coverage rules.")
            raise TeeError("capture_reconstruct_failed", message, fix=fix)
        done = next((e for e in events if e.get("event") == "done"), {})
        return {"seconds": round(float(done.get("seconds", 0.0)), 1)}

    def capture_reconstruct(args: dict[str, Any]) -> dict[str, Any]:
        manifest = _manifest(str(args.get("set") or ""))
        detail = str(args.get("detail") or "preview")
        if detail not in DETAILS:
            raise TeeError(
                "capture_bad_detail",
                f"Unknown detail '{detail}'.",
                fix=f"One of: {', '.join(DETAILS)} (the measured ladder).",
            )
        engine = _engine_for(manifest, str(args.get("engine") or "auto"))
        _gate_disk(root, cfg)
        if engine == "odm":
            if shutil.which("docker") is None:
                raise TeeError(
                    "capture_no_docker",
                    "The drone lane runs ODM in Docker and no runtime is installed.",
                    fix="Install a Docker runtime (the T0 batched owner ask); "
                    "the odm arm64 image is 566 MB compressed.",
                )
            raise TeeError(
                "capture_odm_pending",
                "Docker is present but the ODM lane lands with its live probe (T2/T6).",
                fix="Use engine='photogrammetry' for structure sets meanwhile.",
            )
        helper = _helper_path(root, cfg)
        if not helper.is_file():
            raise TeeError(
                "capture_helper_missing",
                f"PhotogrammetrySession helper not built at {helper}.",
                fix="Run `make` in helpers/photogrammetry (macOS SDK only).",
            )
        inputs = _input_paths(manifest)
        if len(inputs) < MIN_IMAGES:
            raise TeeError(
                "capture_too_few_images",
                f"{len(inputs)} images; reconstruction wants >= {MIN_IMAGES} "
                "sharp overlapping photos of one subject.",
                fix="Recapture per the protocol (70-80% overlap, 3+ views per point).",
            )
        out_root = _out_dir(root)
        out_root.mkdir(parents=True, exist_ok=True)
        out_path = out_root / f"{manifest['set']}_{detail}.usdz"
        job_dir = out_root / f"{manifest['set']}_{detail}.job"
        inputs_hash = hashlib.sha256("".join(sorted(manifest["files"])).encode()).hexdigest()[:12]
        provenance = {
            "engine": f"PhotogrammetrySession/macOS {platform.mac_ver()[0]}",
            "inputs_hash": inputs_hash,
            "cameras": [s["camera_code"] for s in manifest["resolver"]["sets"]],
            "band": manifest["resolver"]["sets"][0]["band"],
            "detail": detail,
        }

        def worker() -> dict[str, Any]:
            run = _run_helper(helper, inputs, out_path, detail, job_dir)
            return {
                "model": str(out_path),
                "seconds": run["seconds"],
                "provenance": provenance,
            }

        job_id = app.jobs.submit(f"reconstruct {manifest['set']} @{detail}", worker)
        return {
            "job": job_id,
            "detail": detail,
            "files": len(inputs),
            "note": "poll tee_job; preview measured ~16 s on the 36-view fixture",
        }

    reg.register(
        VirtualTool(
            "capture_ingest",
            "Ingest a capture set (photos) into the extract store with a set "
            "manifest; the DJI-spectrum resolver answers camera, shutter, "
            "correction mode, honesty band and priors per set from the files' "
            "own metadata.",
            {
                "type": "object",
                "properties": {
                    "paths": {"type": "array", "items": {"type": "string"}},
                    "label": {"type": "string"},
                },
                "required": ["paths"],
            },
            capture_ingest,
            tags=["capture", "ingest", "drone", "dji", "photos", "site", "as-built"],
        )
    )
    reg.register(
        VirtualTool(
            "capture_reconstruct",
            "Reconstruct an ingested capture set as an async job (poll tee_job): "
            "structure sets ride the PhotogrammetrySession helper at a chosen "
            "quality level (preview..raw); drone sets target ODM and refuse "
            "loudly until its runtime lands. Gated on disk, engine presence "
            "and image count before submission.",
            {
                "type": "object",
                "properties": {
                    "set": {"type": "string"},
                    "detail": {"type": "string"},
                    "engine": {"type": "string"},
                },
                "required": ["set"],
            },
            capture_reconstruct,
            tags=["capture", "reconstruct", "photogrammetry", "odm", "job", "3d", "mesh"],
        )
    )
