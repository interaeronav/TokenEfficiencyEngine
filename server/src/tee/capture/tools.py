"""Capture lane virtual tools (A42 T2): ingest + reconstruct.

Surface LAW: everything here is virtual (search -> describe -> call);
nothing joins the always-loaded surface. Capture sets ingest through the
EXISTING extract store (content-addressed, EXIF preserved, originals
referenced in place) plus a set manifest under `.tee/capture/sets/`;
reconstructions ride the jobs pattern and are gated BEFORE submission —
disk, engine presence, image count — with refusals that name the fix.
Structure sets ride the PhotogrammetrySession helper; drone sets run ODM
in Docker with rolling-shutter correction per the resolver's verdict
(both proven live 2026-08-29 — the 40-frame site probe ran 5.0 min).
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

from tee.capture import align, deviate, dji
from tee.kernel.errors import TeeError
from tee.kernel.registry import VirtualTool

DETAILS = ("preview", "reduced", "medium", "full", "raw")
MIN_IMAGES = 10
DEFAULT_MIN_FREE_GB = 20.0
ODM_IMAGE = "opendronemap/odm:latest"


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


def _resident_line(app) -> str:
    """What the machine currently holds - a reconstruction launch says so
    (the A41 guard seam's second direction)."""
    from tee.llm import profiles

    resolved = profiles.resolve(app.llm_cfg)
    return f"{resolved['profile']} resident ({resolved['model']})"


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

    def _run_odm(docker_cmd: str, inputs: list[Path], job_dir: Path, correction_on: bool):
        """Stage COPIES under the job dir — the Docker VM shares $HOME, not
        the system tmp, so originals are never assumed reachable — then run
        the ODM container and hand back the artifact paths."""
        images = job_dir / "code" / "images"
        images.mkdir(parents=True, exist_ok=True)
        for i, src in enumerate(inputs):
            shutil.copy2(src, images / f"{i:04d}{src.suffix.lower()}")
        cmd = [
            docker_cmd, "run", "--rm", "-v", f"{job_dir}:/datasets", ODM_IMAGE,
            "--project-path", "/datasets", "code",
            "--dsm", "--dtm",  # the lane exists for the site surfaces (research 56)
        ]  # fmt: skip
        if correction_on:
            cmd.append("--rolling-shutter")
        start = time.time()
        log_path = job_dir / "odm.log"
        with log_path.open("w") as log:
            code = subprocess.run(cmd, stdout=log, stderr=subprocess.STDOUT).returncode
        if code != 0:
            errors = [
                line.strip()
                for line in log_path.read_text(errors="replace").splitlines()
                if "ERROR" in line
            ]
            raise TeeError(
                "capture_reconstruct_failed",
                errors[-1][:300] if errors else f"odm exited {code}",
                fix="Follow the capture protocol's overlap/grid rules "
                f"(ODM says the same in its flying docs); full log: {log_path}",
            )
        project = job_dir / "code"
        candidates = {
            "orthophoto": project / "odm_orthophoto" / "odm_orthophoto.tif",
            "dsm": project / "odm_dem" / "dsm.tif",
            "dtm": project / "odm_dem" / "dtm.tif",
            "point_cloud": project / "odm_georeferencing" / "odm_georeferenced_model.laz",
            "textured_dir": project / "odm_texturing",
        }
        artifacts = {name: str(path) for name, path in candidates.items() if path.exists()}
        return {"seconds": round(time.time() - start, 1), "artifacts": artifacts}

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
        inputs_hash = hashlib.sha256("".join(sorted(manifest["files"])).encode()).hexdigest()[:12]
        first_set = manifest["resolver"]["sets"][0]
        if engine == "odm":
            docker_cmd = str(cfg.get("docker", "docker"))
            if shutil.which(docker_cmd) is None:
                raise TeeError(
                    "capture_no_docker",
                    "The drone lane runs ODM in Docker and no runtime is installed.",
                    fix="Install a Docker runtime (the T0 batched owner ask); "
                    "the odm arm64 image is 566 MB compressed.",
                )
            image_probe = subprocess.run(
                [docker_cmd, "image", "inspect", ODM_IMAGE], capture_output=True
            )
            if image_probe.returncode != 0:
                raise TeeError(
                    "capture_odm_image_missing",
                    f"The {ODM_IMAGE} image is not pulled.",
                    fix=f"docker pull {ODM_IMAGE} (566 MB compressed; arm64 verified 2026-08-29)",
                )
            job_dir = out_root / f"{manifest['set']}_odm.job"
            correction_on = first_set["correction"]["mode"] == "matched"
            provenance = {
                "engine": f"ODM/{ODM_IMAGE}",
                "inputs_hash": inputs_hash,
                "cameras": [s["camera_code"] for s in manifest["resolver"]["sets"]],
                "band": first_set["band"],
                "rolling_shutter": first_set["correction"],
            }

            ledger_key = f"{manifest['set']}@odm"
            app.machine.register_job(ledger_key, "reconstruct-odm")

            def odm_worker() -> dict[str, Any]:
                try:
                    run = _run_odm(docker_cmd, inputs, job_dir, correction_on)
                finally:
                    app.machine.release_job(ledger_key)
                return {
                    "artifacts": run["artifacts"],
                    "seconds": run["seconds"],
                    "provenance": provenance,
                }

            try:
                job_id = app.jobs.submit(
                    f"reconstruct {manifest['set']} @odm",
                    odm_worker,
                    qos="batch",
                    engine="reconstruct-odm",
                )
            except TeeError:
                app.machine.release_job(ledger_key)
                raise
            return {
                "job": job_id,
                "engine": "odm",
                "files": len(inputs),
                "resident": _resident_line(app),
                "note": "poll tee_job; 40-frame probe ran 5.0 min on the 8-CPU VM",
            }
        helper = _helper_path(root, cfg)
        if not helper.is_file():
            raise TeeError(
                "capture_helper_missing",
                f"PhotogrammetrySession helper not built at {helper}.",
                fix="Run `make` in helpers/photogrammetry (macOS SDK only).",
            )
        out_path = out_root / f"{manifest['set']}_{detail}.usdz"
        job_dir = out_root / f"{manifest['set']}_{detail}.job"
        provenance = {
            "engine": f"PhotogrammetrySession/macOS {platform.mac_ver()[0]}",
            "inputs_hash": inputs_hash,
            "cameras": [s["camera_code"] for s in manifest["resolver"]["sets"]],
            "band": first_set["band"],
            "detail": detail,
        }

        ledger_key = f"{manifest['set']}@photogrammetry"
        app.machine.register_job(ledger_key, "reconstruct-photogrammetry")

        def worker() -> dict[str, Any]:
            try:
                run = _run_helper(helper, inputs, out_path, detail, job_dir)
            finally:
                app.machine.release_job(ledger_key)
            return {
                "model": str(out_path),
                "seconds": run["seconds"],
                "provenance": provenance,
            }

        try:
            job_id = app.jobs.submit(
                f"reconstruct {manifest['set']} @{detail}",
                worker,
                qos="batch",
                engine="reconstruct-photogrammetry",
            )
        except TeeError:
            app.machine.release_job(ledger_key)
            raise
        return {
            "job": job_id,
            "detail": detail,
            "files": len(inputs),
            "resident": _resident_line(app),
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
            "quality level (preview..raw); drone sets run ODM in Docker with "
            "rolling-shutter correction per the resolver's verdict. Gated on "
            "disk, engine presence and image count before submission.",
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

    def capture_register(args: dict[str, Any]) -> dict[str, Any]:
        return align.register_icp(
            Path(str(args.get("source") or "")),
            Path(str(args.get("target") or "")),
            cfg=cfg,
            work_dir=_out_dir(root) / "align",
            max_rms_m=float(args["max_rms_m"]) if args.get("max_rms_m") else None,
            overlap_percent=int(args["overlap_percent"]) if args.get("overlap_percent") else None,
        )

    def capture_terrain(args: dict[str, Any]) -> dict[str, Any]:
        dem2 = args.get("dem2")
        return align.terrain_op(
            str(args.get("op") or ""),
            Path(str(args.get("dem") or "")),
            cfg=cfg,
            work_dir=_out_dir(root) / "terrain",
            dem2=Path(str(dem2)) if dem2 else None,
            interval_m=float(args.get("interval_m", 1.0)),
        )

    reg.register(
        VirtualTool(
            "capture_register",
            "ICP-register a capture cloud/mesh onto the design model "
            "(CloudCompare headless). The target frame is design truth on the "
            "locked site datum - the source transforms into it, never the "
            "reverse. Reports RMS + the transform; a registration above the "
            "RMS gate REFUSES with its numbers instead of confident nonsense.",
            {
                "type": "object",
                "properties": {
                    "source": {"type": "string"},
                    "target": {"type": "string"},
                    "max_rms_m": {"type": "number"},
                    "overlap_percent": {"type": "number"},
                },
                "required": ["source", "target"],
            },
            capture_register,
            tags=["capture", "register", "icp", "align", "cloudcompare", "datum", "as-built"],
        )
    )
    reg.register(
        VirtualTool(
            "capture_terrain",
            "One headless terrain product from a DEM via qgis_process: "
            "contours (vector, interval_m), hillshade, or dem_diff (A-B "
            "against dem2). Returns the product path; refusals name the "
            "missing binary or input.",
            {
                "type": "object",
                "properties": {
                    "op": {"type": "string"},
                    "dem": {"type": "string"},
                    "dem2": {"type": "string"},
                    "interval_m": {"type": "number"},
                },
                "required": ["op", "dem"],
            },
            capture_terrain,
            tags=["capture", "terrain", "dem", "dtm", "contours", "hillshade", "qgis", "diff"],
        )
    )

    def _phrase_via_router(lines: list[str]) -> list[str] | None:
        """The lane's first routed chore: phrasing under the extractive-
        numbers verifier. An escalation means the deterministic lines
        stand - the lane never waits on the router."""
        from tee.llm import chores, router

        routed = router.route(
            "phrase_deviation",
            lambda hop_cfg: chores.phrase_deviation(lines, refine="local", cfg=hop_cfg),
            cfg=app.llm_cfg,
            ledger=app.machine,
            input_pointer="deviation-facts",
        )
        return routed["result"]["lines"] if routed.get("ok") else None

    def capture_deviate(args: dict[str, Any]) -> dict[str, Any]:
        work = _out_dir(root) / "deviation"
        if args.get("detail"):
            reports = sorted(work.glob("report-*.json"))
            if not reports:
                raise TeeError(
                    "capture_no_report",
                    "No deviation report exists yet.",
                    fix="Run capture_deviate with source+target first.",
                )
            rows = json.loads(reports[-1].read_text())
            row = next((c for c in rows if c["id"] == str(args["detail"])), None)
            if row is None:
                known = ", ".join(c["id"] for c in rows[:12])
                raise TeeError(
                    "capture_unknown_deviation",
                    f"No deviation '{args['detail']}' in the last report.",
                    fix=f"Known ids: {known}.",
                )
            return row
        report = deviate.deviation_report(
            Path(str(args.get("source") or "")),
            Path(str(args.get("target") or "")),
            cfg=cfg,
            work_dir=work,
            band=str(args.get("band") or "meters-class absolute (consumer GNSS)"),
            elements=args.get("elements"),
            budget_tokens=int(args.get("max_tokens") or deviate.DEFAULT_BUDGET_TOKENS),
            phrase=None if args.get("phrase") == "off" else _phrase_via_router,
        )
        clusters = report.pop("_clusters")
        work.mkdir(parents=True, exist_ok=True)
        (work / f"report-{int(time.time())}.json").write_text(json.dumps(clusters, indent=1))
        return report

    reg.register(
        VirtualTool(
            "capture_deviate",
            "The as-built deviation report (CloudCompare C2M): budgeted facts "
            "with sign, extent, severity and the capture's honesty band; ends "
            "with the decision menu (accept-as-built / keep-design / "
            "flag-for-site) and NEVER applies anything. detail=<id> drills "
            "into one deviation from the last report. Fact lines may be "
            "phrased by the routed local engine under the numbers-verbatim "
            "verifier; phrase='off' keeps them deterministic.",
            {
                "type": "object",
                "properties": {
                    "source": {"type": "string"},
                    "target": {"type": "string"},
                    "band": {"type": "string"},
                    "elements": {"type": "array", "items": {"type": "object"}},
                    "max_tokens": {"type": "number"},
                    "phrase": {"type": "string"},
                    "detail": {"type": "string"},
                },
            },
            capture_deviate,
            tags=["capture", "deviation", "c2m", "as-built", "report", "severity", "menu"],
        )
    )
