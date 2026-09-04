"""The pieces all three example pipelines share.

Small on purpose (the `seamkiln/examples/_common.py` precedent): an argument
parser, the on-disk layout, the script hand-off between stages, and the one
manifest writer that stamps a probe run as a probe. Anything with an opinion
of its own belongs in the example that holds the opinion.
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from typing import Any

from partkiln.client import LocalKernel
from partkiln.document import Document

# The words a probe manifest carries, verbatim, in every example. A draft run
# is a different answer, not a rougher one; nothing measured under it is
# evidence of anything but that the pipeline ran end to end.
PROBE_NOTE = (
    "PROBE RUN: this proves only that the pipeline runs, and nothing else. It ran at "
    "reduced fidelity - coarse tessellation, and the slow read-backs skipped wherever "
    "this pipeline has them (the STEP round trip, the PDF sheet) - so no number in "
    "this manifest is evidence of the part. Never rely on a coarse preview."
)
# Tessellation deflection: the delivered value, and the deliberately coarse one.
FULL_TOL_MM = 0.05
PROBE_TOL_MM = 0.5


def parser(prog: str, doc: str, stages: tuple[str, ...], out: str) -> argparse.ArgumentParser:
    """One sub-parser per stage plus `all`, each with `--out` and `--probe`."""
    top = argparse.ArgumentParser(prog=prog, description=doc)
    sub = top.add_subparsers(dest="stage", required=True)
    for stage in (*stages, "all"):
        help_text = "every stage in order" if stage == "all" else f"run the {stage} stage"
        p = sub.add_parser(stage, help=help_text)
        p.add_argument("--out", default=out, help=f"working directory (default {out})")
        p.add_argument(
            "--probe",
            action="store_true",
            help="a short, coarse run that proves the pipeline runs; not evidence",
        )
    return top


def layout(out: str | Path) -> dict[str, Path]:
    root = Path(out)
    return {
        "root": root,
        "script": root / "script.json",
        "manifest": root / "manifest.json",
        "drawing": root / "drawing",
        "export": root / "export",
    }


# -- the hand-off between stages is the script, never the solid -----------------


def save(kernel: LocalKernel, paths: dict[str, Path]) -> Path:
    """Write the document's script. This IS the checkpoint (Law 16)."""
    paths["root"].mkdir(parents=True, exist_ok=True)
    paths["script"].write_text(json.dumps(kernel.document.script(), indent=1))
    return paths["script"]


def load(paths: dict[str, Path], stage: str) -> LocalKernel:
    """Replay `script.json` into a fresh kernel, or say which stage to run first."""
    if not paths["script"].exists():
        raise SystemExit(
            f"{stage}: no {paths['script']} - run `model` first "
            f"(python -m {paths['root'].name} model --out {paths['root']})"
        )
    script = json.loads(paths["script"].read_text())
    return LocalKernel(Document.replay(script))


# -- manifests ------------------------------------------------------------------


def write_manifest(paths: dict[str, Path], payload: dict[str, Any], *, probe: bool) -> Path:
    """Merge `payload` into the manifest and stamp it if this was a probe."""
    paths["root"].mkdir(parents=True, exist_ok=True)
    data = read_manifest(paths)
    data.update(payload)
    data["probe"] = bool(probe or data.get("probe"))
    if data["probe"]:
        data["note"] = PROBE_NOTE
    else:
        data.pop("note", None)
    paths["manifest"].write_text(json.dumps(data, indent=1))
    return paths["manifest"]


def read_manifest(paths: dict[str, Path]) -> dict[str, Any]:
    if not paths["manifest"].exists():
        return {}
    return json.loads(paths["manifest"].read_text())


def probe_flag(args: argparse.Namespace, paths: dict[str, Path]) -> bool:
    """A later stage inherits the probe flag the model stage recorded."""
    return bool(getattr(args, "probe", False) or read_manifest(paths).get("probe"))


def tol_mm(probe: bool) -> float:
    return PROBE_TOL_MM if probe else FULL_TOL_MM


# -- printing -------------------------------------------------------------------


def banner(title: str, *, probe: bool) -> None:
    print(f"\n== {title}{'  [PROBE - not evidence]' if probe else ''}")


def files(rows: dict[str, Any]) -> list[dict[str, Any]]:
    """`{format: path-or-row}` -> sorted `[{format, path, bytes}]`, printed and stored."""
    out = []
    for fmt, row in sorted(rows.items()):
        path = Path(row["path"] if isinstance(row, dict) else row)
        out.append({"format": fmt, "path": str(path), "bytes": path.stat().st_size})
    for row in out:
        print(f"  {row['format']:>4}  {row['bytes']:>9,} B  {row['path']}")
    return out


class Stopwatch:
    def __init__(self) -> None:
        self.started = time.perf_counter()

    @property
    def s(self) -> float:
        return time.perf_counter() - self.started


def run_all(args: argparse.Namespace, stages: tuple) -> int:
    for stage in stages:
        code = stage(args)
        if code:
            return code
    return 0
