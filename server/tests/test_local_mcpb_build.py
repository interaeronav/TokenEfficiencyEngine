"""The LOCAL bundle shape: bundled source, borrowed dependency environment.

Two .mcpb shapes exist and only one of them is safe for this machine.

`make mcpb` ships `pyproject.toml` + `uv.lock`, and Claude Desktop provisions a
venv from them with `uv sync` - which rebuilds from the lock and deletes every
pip-installed extra. That is the documented wipe the target prints a reminder
about.

`make mcpb-local` ships neither. `launch.py` puts the bundle's own `src` first
and runs it on an interpreter that already has the dependencies. Measured
2026-09-10 on the A78 0.30.1 bundle of this shape: all nine fleet extras intact
after the install, because nothing was ever provisioned.

These tests pin the properties that make that true, and one bug that was made
while writing the builder.
"""

from __future__ import annotations

import json
import sys
import tomllib
import zipfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "packaging"))

import build_local_mcpb  # noqa: E402


@pytest.fixture(scope="module")
def built(tmp_path_factory):
    tmp = tmp_path_factory.mktemp("local-mcpb")
    out = build_local_mcpb.build(
        python=ROOT / "server" / ".venv" / "bin" / "python",
        out_dir=tmp / "dist",
        build_dir=tmp / "build",
    )
    with zipfile.ZipFile(out) as z:
        return {"path": out, "names": set(z.namelist()), "zip": out}


def _manifest(built):
    with zipfile.ZipFile(built["zip"]) as z:
        return json.loads(z.read("manifest.json"))


def test_it_ships_no_environment_to_provision(built):
    """The whole point. Any of these three turns Desktop's install back into a
    `uv sync`, which is what deletes the fleet extras."""
    for forbidden in ("pyproject.toml", "uv.lock"):
        assert forbidden not in built["names"], (
            f"the local bundle ships {forbidden}; Desktop will provision a venv "
            "from it and wipe the extras this shape exists to preserve"
        )
    assert not any(n.startswith(".venv/") for n in built["names"])


def test_the_manifest_names_the_venv_not_the_base_interpreter():
    """A venv's `bin/python` is a SYMLINK to the base interpreter. Resolving it
    points the bundle at an interpreter whose site-packages has none of the
    dependencies - so the bundle would import nothing it borrowed. The builder
    made exactly this mistake on its first run (it emitted
    `~/.local/share/uv/python/cpython-3.11.15-.../bin/python3.11`), which is
    why the path is made absolute without `resolve()`."""
    venv_python = ROOT / "server" / ".venv" / "bin" / "python"
    assert venv_python.is_symlink(), "premise gone: this venv python is not a symlink"
    assert build_local_mcpb.Path(build_local_mcpb.os.path.abspath(venv_python)) == venv_python
    assert venv_python.resolve() != venv_python, "resolve() would leave the venv"


def test_the_bundle_carries_its_own_version_metadata(built):
    """`launch.py` inserts the bundle's `src` at sys.path[0], so THIS metadata
    is what `tee --version` reports - not the borrowed venv's own tee-engine.
    Generated from pyproject so the two cannot disagree."""
    version = tomllib.loads((ROOT / "server" / "pyproject.toml").read_text())["project"]["version"]
    dist = f"src/tee_engine-{version}.dist-info/METADATA"
    assert dist in built["names"], sorted(n for n in built["names"] if "dist-info" in n)
    with zipfile.ZipFile(built["zip"]) as z:
        assert f"Version: {version}" in z.read(dist).decode()
    assert _manifest(built)["version"] == version


def test_it_is_the_python_shape_and_declares_its_platform(built):
    server = _manifest(built)["server"]
    assert server["type"] == "python" and server["entry_point"] == "launch.py"
    assert server["mcp_config"]["args"][0] == "${__dirname}/launch.py"
    assert server["mcp_config"]["env"]["PYTHONDONTWRITEBYTECODE"] == "1"
    # it hardcodes an absolute interpreter, so it is not portable
    assert _manifest(built)["compatibility"]["platforms"] == [sys.platform]


def test_the_serve_flags_come_from_the_tracked_manifest(built):
    """Derived, not restated: the lanes this shape serves must be the lanes the
    tracked manifest serves, or the two bundles would drift apart."""
    tracked = json.loads((ROOT / "packaging" / "mcpb_manifest.json").read_text())
    want = [a for a in tracked["server"]["mcp_config"]["args"]]
    want = want[want.index("serve") :]
    assert _manifest(built)["server"]["mcp_config"]["args"][1:] == want


def test_it_refuses_an_interpreter_that_is_not_there(tmp_path):
    with pytest.raises(SystemExit, match="no interpreter"):
        build_local_mcpb.build(
            python=tmp_path / "nope" / "python",
            out_dir=tmp_path / "dist",
            build_dir=tmp_path / "build",
        )
