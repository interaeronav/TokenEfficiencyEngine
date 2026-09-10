"""Build the LOCAL .mcpb: bundled source, borrowed dependency environment.

Two shapes exist and they are not interchangeable.

`make mcpb` builds the PORTABLE shape: it ships `pyproject.toml` + `uv.lock`,
and Claude Desktop provisions a venv from them with `uv sync`. That rebuilds
strictly from the lock and drops anything installed on top - so it deletes the
fleet extras on every install, which is why that target prints a restore
reminder. Measured repeatedly: the venv falls from ~1.1 GB to 34 MB.

`make mcpb-local` builds THIS shape, first shipped by the A78 0.30.1 bundle:
no venv, no lock, no pyproject. `launch.py` puts the bundle's own `src` first
and runs it on an interpreter that already has the dependencies - this
checkout's server venv. Verified 2026-09-10: installing a bundle of this shape
left all nine fleet extras intact, because nothing was ever provisioned.

The trade is real and is stated in the bundle's own README: the extension then
depends on THIS checkout at THIS path. Move it, rename it, delete its venv or
`uv sync` it, and the extension breaks or silently loses lanes. That is why the
manifest this writes declares its platform and names the interpreter.

Everything that can be derived is derived. The version, the tool list and the
descriptions come from `packaging/mcpb_manifest.json` and `server/pyproject.toml`,
and only the `server` block and `compatibility.platforms` are overridden - so
this cannot become a second place the version lives. That failure already
happened once: the installed 0.30.1 bundle declared a version no tracked file
did, because its manifest had been edited out of tree.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tomllib
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SERVER = ROOT / "server"

#: Copied in verbatim: (source, destination inside the bundle).
EXTRAS: tuple[tuple[Path, str], ...] = (
    (ROOT / "packaging" / "icon.png", "icon.png"),
    (SERVER / "LICENSE", "LICENSE"),
    (ROOT / "docs" / "small-model-workflows.md", "docs/small-model-workflows.md"),
    (ROOT / "skills" / "tee-usage" / "SKILL.md", "skills/tee-usage/SKILL.md"),
)

README = """# TEE local Desktop bundle — {version}

Open the `.mcpb` in Claude Desktop and review the update to the existing Token
Efficiency Engine extension. Keep your existing project-folder setting.

**This package is built for one machine.** It contains TEE's source but no
Python environment: it runs on

    {python}

and borrows the dependencies already installed there. That is deliberate — the
portable bundle provisions its own venv with `uv sync`, which deletes every
pip-installed extra, and this shape does not, so the fleet lanes survive an
update.

The cost is a hard dependency on that path. If the repository is moved,
renamed or deleted, or its venv is rebuilt with `uv sync`, this extension
stops working or quietly loses lanes. Rebuild with `make mcpb-local` after any
such change.

Nothing here downloads models or synchronises dependencies. Local model
servers and DCC bridges are used only when their tools are called.

The always-loaded surface is unchanged at 17 tools; everything else stays
behind progressive discovery. See `docs/small-model-workflows.md` and
`skills/tee-usage/SKILL.md`.

Built from {commit}.
"""

METADATA = """Metadata-Version: 2.1
Name: {name}
Version: {version}
Summary: {summary}
Requires-Python: {requires_python}

Local Desktop bundle built by packaging/build_local_mcpb.py. Source-only:
dependencies come from the interpreter named in the manifest.
"""


def _commit() -> str:
    """The build's provenance, and honest when the tree is dirty."""
    try:
        rev = subprocess.run(
            ["git", "-C", str(ROOT), "rev-parse", "--short", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
        dirty = subprocess.run(
            ["git", "-C", str(ROOT), "status", "--porcelain"],
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
        return f"{rev}{' (dirty tree)' if dirty else ''}"
    except (OSError, subprocess.CalledProcessError):
        return "an unknown revision"


def build(python: Path, out_dir: Path, build_dir: Path) -> Path:
    project = tomllib.loads((SERVER / "pyproject.toml").read_text())["project"]
    name, version = project["name"], project["version"]
    manifest = json.loads((ROOT / "packaging" / "mcpb_manifest.json").read_text())

    if manifest["version"] != version:
        raise SystemExit(
            f"packaging/mcpb_manifest.json says {manifest['version']} and "
            f"server/pyproject.toml says {version}. Bump both (test_server_lint "
            "asserts they agree) before building."
        )
    if not python.exists():
        raise SystemExit(f"no interpreter at {python} - build the server venv first.")

    # keep every derived field; replace only what this shape changes
    args = list(manifest["server"]["mcp_config"]["args"])
    args = args[args.index("serve") :]  # drop the uv preamble, keep serve + flags
    manifest["server"] = {
        "type": "python",
        "entry_point": "launch.py",
        "mcp_config": {
            "command": str(python),
            "args": ["${__dirname}/launch.py", *args],
            "env": {"PYTHONDONTWRITEBYTECODE": "1"},
        },
    }
    # it names an absolute interpreter, so it is not portable across platforms
    manifest.setdefault("compatibility", {})["platforms"] = [sys.platform]

    stage = build_dir / "mcpb-local"
    shutil.rmtree(stage, ignore_errors=True)
    (stage / "src").mkdir(parents=True)

    shutil.copytree(SERVER / "src" / "tee", stage / "src" / "tee")
    shutil.copy2(ROOT / "packaging" / "launch.py", stage / "launch.py")
    (stage / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")

    # The bundle's own distribution metadata. `launch.py` inserts this dir at
    # sys.path[0], so importlib.metadata finds THIS before the borrowed venv's
    # own tee-engine - which is how `tee --version` reports the bundle rather
    # than the checkout. Generated from pyproject so it cannot disagree.
    dist = stage / "src" / f"{name.replace('-', '_')}-{version}.dist-info"
    dist.mkdir()
    (dist / "METADATA").write_text(
        METADATA.format(
            name=name,
            version=version,
            summary=project.get("description", "Token Efficiency Engine"),
            requires_python=project.get("requires-python", ">=3.11"),
        )
    )

    for src, dest in EXTRAS:
        if not src.exists():
            raise SystemExit(f"missing bundle input: {src}")
        target = stage / dest
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, target)
    (stage / "README.md").write_text(
        README.format(version=version, python=python, commit=_commit())
    )

    for pycache in stage.rglob("__pycache__"):
        shutil.rmtree(pycache, ignore_errors=True)
    for pyc in stage.rglob("*.pyc"):
        pyc.unlink()

    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / f"{name}-{version}-local.mcpb"
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        for path in sorted(stage.rglob("*")):
            if path.is_file():
                z.write(path, path.relative_to(stage))
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument(
        "--python",
        type=Path,
        default=SERVER / ".venv" / "bin" / "python",
        help="interpreter the extension runs on (default: this checkout's server venv)",
    )
    ap.add_argument("--out-dir", type=Path, default=SERVER / "dist")
    ap.add_argument("--build-dir", type=Path, default=SERVER / "build")
    a = ap.parse_args()
    # absolute, but NOT resolve(): a venv's `bin/python` is a symlink to the
    # base interpreter, and resolving it points the bundle at an interpreter
    # whose site-packages has none of the dependencies - the venv is exactly
    # what we are trying to borrow. doctor.py carries the same warning about
    # its `tee` candidate.
    python = Path(os.path.abspath(a.python))
    out = build(python, a.out_dir, a.build_dir)
    print(f"built {out}")
    print(f"  runs on   {python}")
    print("  no venv is provisioned, so the fleet extras survive an install -")
    print("  and the extension depends on that interpreter continuing to exist.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
