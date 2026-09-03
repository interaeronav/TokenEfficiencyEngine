"""The pc_* virtual tools (A67).

Registered into the progressive-disclosure registry, so this lane adds ZERO
tools to the always-loaded surface. Every response is a digest: the hard
invariant, tested, is that no pc_* response carries an array longer than 64
elements or a string longer than 2 KB. Points never leave disk.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np

from tee.kernel.errors import TeeError
from tee.kernel.registry import VirtualTool
from tee.pointcloud import control, io, report, slice2d
from tee.pointcloud import level as level_mod
from tee.pointcloud.store import CloudStore, digest, spacing

UNITS = {"m": 1.0, "cm": 0.01, "mm": 0.001, "ft": 0.3048, "in": 0.0254}


def register_pointcloud_tools(app, project_root: Path | str) -> CloudStore:
    store = CloudStore(project_root)
    reg = app.registry

    def _points(args: dict[str, Any]) -> tuple[str, np.ndarray]:
        cloud_id = str(args["cloud_id"])
        return cloud_id, store.points(cloud_id)

    # -- open / inspect ----------------------------------------------------

    def pc_open(args: dict[str, Any]) -> dict[str, Any]:
        path = Path(str(args["path"])).expanduser()
        units = str(args.get("units") or "m")
        if units not in UNITS:
            raise TeeError(
                "pc_bad_units",
                f"'{units}' is not a unit this lane knows.",
                fix=f"One of: {', '.join(UNITS)}.",
            )
        raw = io.read(path)
        pts = raw["points"] * UNITS[units]
        up = str(args.get("up_axis") or "z").lower()
        if up == "y":  # the glTF/scanner convention: Y-up -> Z-up
            pts = pts[:, [0, 2, 1]] * np.array([1.0, -1.0, 1.0])
        elif up not in ("z", ""):
            raise TeeError(
                "pc_bad_up_axis", f"up_axis '{up}' is not y or z.", fix="Use 'y' or 'z'."
            )
        cloud_id = store.mint(
            pts,
            op="open",
            extra={"source": path.name, "format": raw.get("format"), "units": units},
            colors=raw.get("colors"),
            intensity=raw.get("intensity"),
        )
        out: dict[str, Any] = {"cloud_id": cloud_id, **digest(pts)}
        out["spacing_mm"] = round(spacing(pts) * 1000, 2)
        out["format"] = raw.get("format")
        out["file_mb"] = round(path.stat().st_size / 1e6, 2)
        out["has_colour"] = "colors" in raw
        out["has_intensity"] = "intensity" in raw
        for key in ("srs", "writer", "point_format", "las_version"):
            if raw.get(key):
                out[key] = raw[key]
        store.update_meta(
            cloud_id,
            source=path.name,
            srs=raw.get("srs"),
            writer=raw.get("writer"),
            has_colour=out["has_colour"],
            has_intensity=out["has_intensity"],
        )
        return out

    def pc_stat(args: dict[str, Any]) -> dict[str, Any]:
        _, pts = _points(args)
        what = str(args.get("what") or "extent")
        if what == "extent":
            return {"what": what, **digest(pts)}
        if what == "density":
            sp = spacing(pts)
            lo, hi = pts.min(axis=0), pts.max(axis=0)
            area = float((hi[0] - lo[0]) * (hi[1] - lo[1])) or 1.0
            return {
                "what": what,
                "median_spacing_mm": round(sp * 1000, 2),
                "points": len(pts),
                "points_per_m2_footprint": round(len(pts) / area, 1),
            }
        if what == "z_histogram":
            counts, edges = np.histogram(pts[:, 2], bins=32)
            peaks = np.argsort(counts)[::-1][:4]
            return {
                "what": what,
                "bins": 32,
                "z_min_m": round(float(edges[0]), 3),
                "z_max_m": round(float(edges[-1]), 3),
                "counts": [int(c) for c in counts],
                "peak_z_m": sorted(round(float((edges[p] + edges[p + 1]) / 2), 3) for p in peaks),
                "note": "peaks are floor/ceiling candidates; pass one as floor_hint_z",
            }
        if what == "plane_census":
            rng = np.random.default_rng(0)
            sub = pts[rng.choice(len(pts), min(40_000, len(pts)), replace=False)]
            horiz = vert = 0
            from scipy.spatial import cKDTree

            k = min(64, len(sub) - 1)
            _, idx = cKDTree(sub).query(sub, k=k, workers=-1)
            nb = sub[idx]
            nb = nb - nb.mean(axis=1, keepdims=True)
            evals, evecs = np.linalg.eigh(np.einsum("nij,nik->njk", nb, nb) / k)
            normals = evecs[:, :, 0]
            planar = (evals[:, 1] - evals[:, 0]) / np.maximum(evals[:, 2], 1e-12) > 0.5
            nz = np.abs(normals[:, 2])[planar]
            horiz = int((nz > 0.95).sum())
            vert = int((nz < 0.25).sum())
            total = int(planar.sum()) or 1
            return {
                "what": what,
                "sampled": len(sub),
                "planar_fraction": round(total / len(sub), 3),
                "horizontal_pct": round(horiz / total * 100, 1),
                "vertical_pct": round(vert / total * 100, 1),
                "other_pct": round((total - horiz - vert) / total * 100, 1),
            }
        raise TeeError(
            "pc_unknown_stat",
            f"'{what}' is not a statistic this tool reports.",
            fix="One of: extent, density, z_histogram, plane_census.",
        )

    # -- condition ---------------------------------------------------------

    def pc_level(args: dict[str, Any]) -> dict[str, Any]:
        parent, pts = _points(args)
        hint = args.get("floor_hint_z")
        result = level_mod.level(
            pts,
            floor_hint_z=None if hint is None else float(hint),
            align_walls=bool(args.get("align_walls", True)),
        )
        levelled = result.pop("points")
        cloud_id = store.mint(levelled, parent=parent, op="level", extra=dict(result))
        return {"cloud_id": cloud_id, "parent": parent, **result, **digest(levelled)}

    # -- control and scale -------------------------------------------------

    def pc_control_add(args: dict[str, Any]) -> dict[str, Any]:
        cloud_id, pts = _points(args)
        baseline = control.add_baseline(
            pts,
            str(args["name"]),
            list(args["p1"]),
            list(args["p2"]),
            float(args["true_mm"]),
            float(args.get("tol_mm") or 5.0),
        )
        meta = store.meta(cloud_id)
        controls = [c for c in (meta.get("controls") or []) if c["name"] != baseline["name"]]
        controls.append(baseline)
        store.update_meta(cloud_id, controls=controls)
        return {
            "cloud_id": cloud_id,
            "baseline": baseline["name"],
            "measured_mm": baseline["measured_mm"],
            "true_mm": baseline["true_mm"],
            "delta_mm": round(baseline["measured_mm"] - baseline["true_mm"], 2),
            "snapped": baseline["snapped_from"],
            "baselines_on_cloud": len(controls),
        }

    def pc_control_verify(args: dict[str, Any]) -> dict[str, Any]:
        cloud_id = str(args["cloud_id"])
        return {"cloud_id": cloud_id, **control.check(store.meta(cloud_id).get("controls") or [])}

    def pc_scale_apply(args: dict[str, Any]) -> dict[str, Any]:
        parent, pts = _points(args)
        if args.get("factor") is not None:
            factor = float(args["factor"])
            source = "explicit"
        else:
            solved = control.check(store.meta(parent).get("controls") or [])
            factor = float(solved["suggested_scale"])
            source = "controls"
        if not (0.5 <= factor <= 2.0):
            raise TeeError(
                "pc_implausible_scale",
                f"A factor of {factor:.4f} is a units error, not a calibration.",
                fix="Re-open the cloud with the right units= instead of scaling it.",
            )
        scaled = pts * factor
        cloud_id = store.mint(
            scaled, parent=parent, op="scale", extra={"factor": round(factor, 7), "from": source}
        )
        # A baseline is a MEASUREMENT OF THIS CLOUD, so it scales with the
        # cloud. Carrying the parent's numbers forward unchanged left
        # pc_report reading pre-correction deltas and calling a corrected
        # scan "SHAPE ONLY - do not scale off this drawing". Rigid ops
        # (pc_level) preserve distance and correctly carry them untouched.
        carried = store.meta(cloud_id).get("controls") or []
        if carried:
            store.update_meta(
                cloud_id,
                controls=[
                    {
                        **c,
                        "measured_mm": round(float(c["measured_mm"]) * factor, 2),
                        "p1": [round(v * factor, 4) for v in c["p1"]],
                        "p2": [round(v * factor, 4) for v in c["p2"]],
                        "rescaled_by": round(factor, 7),
                    }
                    for c in carried
                ],
            )
        return {
            "cloud_id": cloud_id,
            "parent": parent,
            "factor": round(factor, 7),
            "from": source,
            **digest(scaled),
        }

    # -- templates ---------------------------------------------------------

    def _emit(args: dict[str, Any], pts2d: np.ndarray, stem: str) -> dict[str, Any]:
        fit = str(args.get("fit") or "lines")
        formats = [str(f).lower() for f in (args.get("out") or ["dxf"])]
        unknown = [f for f in formats if f not in ("dxf", "svg")]
        if unknown:
            raise TeeError(
                "pc_unsupported_format",
                f"{', '.join(unknown)} is not a template format.",
                fix="Use dxf, svg, or both.",
            )
        if fit == "none":
            segments, ignored = [], len(pts2d)
        elif fit == "ortho":
            segments, ignored = slice2d.fit_ortho(pts2d)
        elif fit == "lines":
            segments, ignored = slice2d.fit_lines(pts2d, float(args.get("ortho_snap_deg") or 3.0))
        else:
            raise TeeError(
                "pc_unknown_fit",
                f"'{fit}' is not a fit mode.",
                fix="lines (any orientation), ortho (rectilinear building), or none.",
            )
        if fit != "none" and not segments:
            raise TeeError(
                "pc_no_segments",
                f"No line fitted the {len(pts2d)} points in this band.",
                fix="Widen thickness_m, or use fit='none' to inspect the raw band first.",
            )
        out_dir = store.out_dir()
        paths = {}
        if "dxf" in formats:
            paths["dxf"] = str(slice2d.write_dxf(segments, out_dir / f"{stem}.dxf"))
        if "svg" in formats:
            paths["svg"] = str(
                slice2d.write_svg(
                    segments, out_dir / f"{stem}.svg", scale=str(args.get("scale") or "1:50")
                )
            )
        med = [s["residual_median_mm"] for s in segments]
        return {
            "paths": paths,
            "segments": len(segments),
            "band_points": len(pts2d),
            "points_ignored": ignored,
            "residual_median_mm": {
                "min": min(med) if med else None,
                "median": round(float(np.median(med)), 1) if med else None,
                "max": max(med) if med else None,
            },
            "worst_segment_max_mm": max((s["residual_max_mm"] for s in segments), default=None),
            "lengths_m": [s["length_m"] for s in segments[:32]],
            "units": "DXF is metres, $INSUNITS=6",
            "note": (
                "high points_ignored means clutter in the band - crop and re-run"
                if ignored > len(pts2d) * 0.25
                else "trace over the emitted geometry; verify the scale bar first"
            ),
        }

    def pc_slice(args: dict[str, Any]) -> dict[str, Any]:
        cloud_id, pts = _points(args)
        z = float(args["z_m"])
        band = slice2d.band(pts, z, float(args.get("thickness_m") or 0.05))
        return {"cloud_id": cloud_id, "z_m": z, **_emit(args, band, f"{cloud_id}-plan-{z:.2f}")}

    def pc_section(args: dict[str, Any]) -> dict[str, Any]:
        cloud_id, pts = _points(args)
        band = slice2d.section_band(
            pts, list(args["p1_xy"]), list(args["p2_xy"]), float(args.get("thickness_m") or 0.05)
        )
        line_id = abs(hash((tuple(args["p1_xy"]), tuple(args["p2_xy"])))) % 10**6
        stem = f"{cloud_id}-section-{line_id}"
        return {"cloud_id": cloud_id, **_emit(args, band, stem)}

    # -- out ---------------------------------------------------------------

    def pc_export(args: dict[str, Any]) -> dict[str, Any]:
        cloud_id, pts = _points(args)
        fmt = str(args.get("format") or "ply").lower()
        colors = store.attr(cloud_id, "rgb")
        intensity = store.attr(cloud_id, "int")
        target = args.get("decimate_to")
        if target and int(target) < len(pts):
            step = len(pts) / int(target)
            idx = (np.arange(int(target)) * step).astype(int)
            pts, colors = pts[idx], (None if colors is None else colors[idx])
            intensity = None if intensity is None else intensity[idx]
        out = store.out_dir() / f"{cloud_id}.{fmt}"
        written = io.write(pts, out, fmt, colors=colors, intensity=intensity)
        return {"cloud_id": cloud_id, "format": fmt, "count": len(pts), **written}

    def pc_report(args: dict[str, Any]) -> dict[str, Any]:
        cloud_id = str(args["cloud_id"])
        meta = store.meta(cloud_id)
        return report.write_sheet(meta, store.out_dir() / f"{cloud_id}-qa.md")

    # -- registration ------------------------------------------------------

    cloud_arg = {"cloud_id": {"type": "string", "description": "From pc_open or any pc_* call."}}
    template_args = {
        **cloud_arg,
        "thickness_m": {"type": "number", "description": "Band depth, default 0.05."},
        "fit": {
            "type": "string",
            "enum": ["lines", "ortho", "none"],
            "description": "ortho = declare the building rectilinear; far more robust.",
        },
        "ortho_snap_deg": {"type": "number", "description": "Snap near-square lines, default 3."},
        "out": {"type": "array", "description": "Any of dxf, svg. Default ['dxf']."},
        "scale": {"type": "string", "description": "Paper scale for the SVG, e.g. '1:50'."},
    }

    specs: list[tuple[str, str, dict, Any, list[str], list[dict]]] = [
        (
            "pc_open",
            "Open a point cloud (ply/las/laz/e57/xyz) and return a digest - never points.\n"
            "Points live on disk under the returned cloud_id; every later call takes that id. "
            "Reports the writer, SRS and spacing it actually finds rather than assuming a "
            "scanner app.",
            {
                "type": "object",
                "properties": {
                    "path": {"type": "string"},
                    "units": {"type": "string", "enum": list(UNITS)},
                    "up_axis": {"type": "string", "enum": ["z", "y"]},
                },
                "required": ["path"],
            },
            pc_open,
            ["pointcloud", "scan", "lidar", "open", "ply", "las", "laz", "e57", "import"],
            [{"path": "~/scans/room.ply"}],
        ),
        (
            "pc_stat",
            "One topic of numbers about a cloud: extent, density, z_histogram or plane_census.\n"
            "z_histogram finds floor/ceiling candidates; plane_census says how much of the "
            "cloud is actually flat surface rather than clutter.",
            {
                "type": "object",
                "properties": {
                    **cloud_arg,
                    "what": {
                        "type": "string",
                        "enum": ["extent", "density", "z_histogram", "plane_census"],
                    },
                },
                "required": ["cloud_id"],
            },
            pc_stat,
            ["pointcloud", "scan", "stats", "histogram", "density", "planes"],
            [{"cloud_id": "pc_1a2b3c4d5e", "what": "z_histogram"}],
        ),
        (
            "pc_level",
            "Level a scan on its floor and square it to the dominant wall; mints a new cloud.\n"
            "RANSACs the LOWEST dominant horizontal plane (a ceiling has as many points as the "
            "floor), drops it to z=0, then removes the wall azimuth. Returns the 4x4, the "
            "residual tilt and the floor RMS - the numbers that say whether to trust it.",
            {
                "type": "object",
                "properties": {
                    **cloud_arg,
                    "floor_hint_z": {"type": "number", "description": "From pc_stat z_histogram."},
                    "align_walls": {"type": "boolean"},
                },
                "required": ["cloud_id"],
            },
            pc_level,
            ["pointcloud", "scan", "level", "align", "floor", "tilt", "orient", "square"],
            [{"cloud_id": "pc_1a2b3c4d5e"}],
        ),
        (
            "pc_control_add",
            "Record one tape/DISTO baseline against the cloud; picks snap to the local surface.\n"
            "This is what gives a drifting scan absolute scale. p1/p2 are approximate 3D picks "
            "in cloud units - aim by eye, the snap fixes it.",
            {
                "type": "object",
                "properties": {
                    **cloud_arg,
                    "name": {"type": "string"},
                    "p1": {"type": "array"},
                    "p2": {"type": "array"},
                    "true_mm": {"type": "number", "description": "What the tape read."},
                    "tol_mm": {"type": "number"},
                },
                "required": ["cloud_id", "name", "p1", "p2", "true_mm"],
            },
            pc_control_add,
            ["pointcloud", "scan", "cloud", "control", "scale", "tape", "disto", "baseline"],
            [
                {
                    "cloud_id": "pc_1a2b3c4d5e",
                    "name": "north wall",
                    "p1": [0.02, 1.5, 1.2],
                    "p2": [4.01, 1.5, 1.2],
                    "true_mm": 4000,
                }
            ],
        ),
        (
            # Named `verify`, not `check`: `check` is a common English verb and
            # a 3-point name match, so `pc_control_check` outranked ex_estimate
            # for the vague query "check the drawing" and cost the registry a
            # recall slot (test_search_budget). The lane does not get to claim
            # another lane's vocabulary just by being newer.
            "pc_control_verify",
            "Compare every recorded baseline against its tape reading; suggest one scale.\n"
            "If baselines disagree by more than their tolerance that is DRIFT, not scale, and "
            "no single factor fixes it - the answer says so instead of inventing one.",
            {"type": "object", "properties": cloud_arg, "required": ["cloud_id"]},
            pc_control_verify,
            ["pointcloud", "scan", "cloud", "control", "scale", "drift", "ppm", "baseline"],
            [{"cloud_id": "pc_1a2b3c4d5e"}],
        ),
        (
            "pc_scale_apply",
            "Apply a uniform scale (explicit, or the one pc_control_verify suggested).\n"
            "Mints a new cloud; a factor further than 2x from 1.0 refuses as a units error.",
            {
                "type": "object",
                "properties": {
                    **cloud_arg,
                    "factor": {"type": "number", "description": "Omit to use the controls."},
                },
                "required": ["cloud_id"],
            },
            pc_scale_apply,
            ["pointcloud", "scan", "scale", "apply", "correct", "calibrate"],
            [{"cloud_id": "pc_1a2b3c4d5e"}],
        ),
        (
            "pc_slice",
            "Horizontal section at z -> DXF/SVG line work to trace, at true scale.\n"
            "DXF is metres with $INSUNITS=6; the SVG carries a 1 m reference square. Level the "
            "cloud first or the section is a diagonal cut.",
            {
                "type": "object",
                "properties": {**template_args, "z_m": {"type": "number"}},
                "required": ["cloud_id", "z_m"],
            },
            pc_slice,
            ["pointcloud", "scan", "cloud", "slice", "floorplan", "plan", "dxf", "trace"],
            [{"cloud_id": "pc_1a2b3c4d5e", "z_m": 1.2, "out": ["dxf", "svg"]}],
        ),
        (
            "pc_section",
            "Vertical section on an arbitrary XY line -> DXF/SVG, same contract as pc_slice.\n"
            "This is what feeds internal elevations.",
            {
                "type": "object",
                "properties": {
                    **template_args,
                    "p1_xy": {"type": "array"},
                    "p2_xy": {"type": "array"},
                },
                "required": ["cloud_id", "p1_xy", "p2_xy"],
            },
            pc_section,
            ["pointcloud", "scan", "section", "elevation", "vertical", "dxf", "svg", "trace"],
            [{"cloud_id": "pc_1a2b3c4d5e", "p1_xy": [0, 0], "p2_xy": [4, 0]}],
        ),
        (
            "pc_export",
            "Write a cloud back out (ply/las/laz/e57), optionally decimated.\n"
            "PLY is always origin-shifted because its vertices are float32 - a georeferenced "
            "cloud would otherwise lose 250 mm. LAS uses a 0.1 mm scale.",
            {
                "type": "object",
                "properties": {
                    **cloud_arg,
                    "format": {"type": "string", "enum": list(io.WRITABLE)},
                    "decimate_to": {"type": "integer"},
                },
                "required": ["cloud_id"],
            },
            pc_export,
            ["pointcloud", "scan", "export", "write", "ply", "las", "laz", "e57", "decimate"],
            [{"cloud_id": "pc_1a2b3c4d5e", "format": "las"}],
        ),
        (
            "pc_report",
            "Write the one-page QA sheet for a cloud and return a six-line verdict.\n"
            "Says whether a drawing traced off this cloud can be trusted, and why. File this "
            "next to the DXF.",
            {"type": "object", "properties": cloud_arg, "required": ["cloud_id"]},
            pc_report,
            ["pointcloud", "scan", "cloud", "report", "qa", "trust", "provenance"],
            [{"cloud_id": "pc_1a2b3c4d5e"}],
        ),
    ]

    for name, description, schema, handler, tags, examples in specs:
        reg.register(
            VirtualTool(
                name=name,
                description=description,
                schema=schema,
                handler=handler,
                tags=tags,
                examples=examples,
            )
        )
    return store
