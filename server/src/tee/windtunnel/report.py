"""What leaves the store: results as JSON, polars as CSV, a Markdown summary,
the `.foam` stub ParaView's reader wants, a `pipeline.toml` fragment for
projects that keep a freshness graph, a VTU conversion through meshio (the
optional extra), and a PDF through TEE's own pdf lane.

Every artefact repeats the provenance the answer carried: engine, version,
mesh hash, verdict, uncertainty label. Nothing here reads a field.
"""

from __future__ import annotations

import csv
import json
import time
from pathlib import Path
from typing import Any

from tee.kernel.errors import TeeError

FORMATS = ("json", "csv", "foam", "md", "pdf", "vtu", "pipeline")


def export(
    app: Any, fmt: str, case: dict[str, Any], run: dict[str, Any], out_dir: Path
) -> dict[str, Any]:
    if fmt not in FORMATS:
        raise TeeError(
            "wt_bad_format",
            f"'{fmt}' is not an export format.",
            fix=f"One of: {', '.join(FORMATS)}.",
        )
    out_dir.mkdir(parents=True, exist_ok=True)
    stem = f"{case['case_id']}_{run.get('run_id', 'case')}"
    if fmt == "json":
        path = out_dir / f"{stem}.json"
        path.write_text(json.dumps({"case": _case_facts(case), "run": run}, indent=1, default=str))
    elif fmt == "csv":
        path = out_dir / f"{stem}.csv"
        rows = run.get("polar") or ([run["result"]] if run.get("result") else [])
        if not rows:
            raise TeeError(
                "wt_no_results", "Nothing to tabulate yet.", fix="wt_result or wt_sweep first."
            )
        keys = ["aoa_deg", "mach", "cl", "cd", "cm", "l_over_d", "state"]
        with open(path, "w", newline="") as fh:
            w = csv.writer(fh)
            w.writerow(keys)
            for r in rows:
                w.writerow([r.get(k, "") for k in keys])
    elif fmt == "foam":
        case_dir = Path(case["engine_dir"])
        path = case_dir / "case.foam"
        path.write_text("")
    elif fmt == "md":
        path = out_dir / f"{stem}.md"
        path.write_text(markdown(case, run))
    elif fmt == "pipeline":
        path = out_dir / f"{stem}.pipeline.toml"
        path.write_text(pipeline_fragment(case, run))
    elif fmt == "vtu":
        path = _export_vtu(case, run, out_dir / f"{stem}.vtu")
    else:  # pdf
        path = _export_pdf(app, case, run, out_dir / f"{stem}.pdf")
    return {"path": str(path), "bytes": path.stat().st_size, "format": fmt}


def _case_facts(case: dict[str, Any]) -> dict[str, Any]:
    keep = (
        "case_id",
        "kind",
        "engine",
        "fidelity",
        "conditions",
        "refs",
        "geometry",
        "mesh",
        "created_at",
    )
    return {k: case[k] for k in keep if k in case}


def markdown(case: dict[str, Any], run: dict[str, Any]) -> str:
    res = run.get("result") or {}
    lines = [
        f"# Wind-tunnel case {case['case_id']} / {run.get('run_id', '')}",
        "",
        f"- engine: {case.get('engine')} {run.get('engine_version', '')} "
        f"({case.get('fidelity', {}).get('chosen', '')})",
        f"- conditions: {json.dumps(case.get('conditions', {}), default=str)}",
        f"- mesh: {json.dumps(case.get('mesh', {}), default=str)}",
        f"- run: state {run.get('state')} wall {run.get('wall_s')} s",
        "",
    ]
    if res:
        lines += [
            "| cl | cd | cm | L/D | verdict |",
            "|---|---|---|---|---|",
            f"| {res.get('cl')} | {res.get('cd')} | {res.get('cm')} | {res.get('l_over_d')} | "
            f"{res.get('verdict', {}).get('state')} |",
            "",
            f"Uncertainty: **{res.get('uncertainty', {}).get('trust')}** - "
            f"{res.get('uncertainty', {}).get('label')}",
            "",
            f"Cite: {res.get('uncertainty', {}).get('cite')}",
        ]
    if run.get("polar"):
        lines += ["", "| alpha | cl | cd | cm |", "|---|---|---|---|"]
        for r in run["polar"]:
            lines.append(f"| {r.get('aoa_deg')} | {r.get('cl')} | {r.get('cd')} | {r.get('cm')} |")
    lines.append("")
    lines.append(f"generated-by: tee.windtunnel {time.strftime('%Y-%m-%d')}")
    return "\n".join(lines) + "\n"


def pipeline_fragment(case: dict[str, Any], run: dict[str, Any]) -> str:
    argv = run.get("argv") or []
    argv_txt = ", ".join(json.dumps(a) for a in argv)
    return (
        f"# generated-by: tee.windtunnel - a pipeline.toml fragment for case {case['case_id']}\n"
        "[[step]]\n"
        f'name = "wt_{case["case_id"]}_{run.get("run_id", "run")}"\n'
        'kind = "produce"\n'
        f"argv = [{argv_txt}]\n"
        f'inputs = ["{case.get("engine_dir", "")}"]\n'
        f'outputs = ["{run.get("run_dir", "")}"]\n'
        f"cost = {{ wall_s = [{max(1, int(run.get('wall_s') or 60))}, "
        f"{max(2, int((run.get('wall_s') or 60) * 3))}] }}\n"
    )


def _export_vtu(case: dict[str, Any], run: dict[str, Any], path: Path) -> Path:
    try:
        import meshio
    except ImportError as exc:
        raise TeeError(
            "wt_extra_missing",
            "VTU export converts the mesh through meshio, which is not installed.",
            fix="uv pip install 'tee-engine[windtunnel]'",
        ) from exc
    src = run.get("volume_file") or case.get("mesh", {}).get("su2_file")
    if not src or not Path(src).exists():
        raise TeeError(
            "wt_no_results",
            "No volume file to convert (SU2 flow.vtu or a .su2 mesh).",
            fix="Run the case first.",
        )
    m = meshio.read(src)
    meshio.write(str(path), m)
    return path


def _export_pdf(app: Any, case: dict[str, Any], run: dict[str, Any], path: Path) -> Path:
    """Through the registered pdf_compose so the pdf extra's own refusal and
    the trust table apply; this lane never imports fpdf."""
    body = markdown(case, run)
    try:
        app.registry.call(
            "pdf_compose",
            {
                "path": str(path),
                "title": f"Wind tunnel {case['case_id']}",
                "sections": [{"heading": "Result", "text": body}],
            },
        )
    except TeeError:
        raise
    except Exception as exc:  # pragma: no cover - the pdf lane's own failure shape
        raise TeeError(
            "wt_export_failed",
            f"pdf_compose failed: {str(exc)[:200]}",
            fix="Check the pdf lane: uv pip install 'tee-engine[pdf]'.",
        ) from exc
    if not path.exists():
        raise TeeError(
            "wt_export_failed",
            "pdf_compose returned without writing the file.",
            fix="Check the pdf lane's own answer.",
        )
    return path
