"""A46 P2b — no tool call may block on a first import.

A cold `med_` or `cad_` call used to pay 60-140 s and time out, because
importing MONAI dragged torch (505 MB) and importing CadQuery dragged vtk,
casadi and llvmlite (1.1 GB). P1 removed the first and moved the second to
a sidecar; this is the guard that keeps them out.

The test is deliberately NOT a stopwatch. A timing assertion on a shared
machine is a flake generator, and the thing actually worth pinning is not
"was it fast today" but "did a heavyweight get back into the interpreter
that serves every tool call" - which is exactly measurable.
"""

from __future__ import annotations

import subprocess
import sys

# Each of these is a dependency TEE was carrying but never used for the
# work it was doing, with what it cost in the extension venv.
HEAVY = {
    "torch": "505 MB, pulled by monai, to take min/max/mean of an array",
    "vtkmodules": "592 MB, pulled by cadquery-ocp: a renderer TEE never renders with",
    "casadi": "159 MB, cadquery's assembly solver; TEE never assembles",
    "llvmlite": "129 MB, a JIT via numba that TEE never triggers",
    "numba": "the JIT's front end; pandas needs it only for its `performance` extra",
    "OCP": "225 MB BREP kernel - legitimate, but it belongs in the sidecar",
    "monai": "the reader dispatcher P1a replaced with direct dispatch",
}

# The fleet modules that a tool call imports.
FLEET = ("tee.fleet.med", "tee.fleet.cad", "tee.fleet.solve", "tee.fleet.quant")


def _imported_after(modules: tuple[str, ...]) -> set[str]:
    """Import in a FRESH interpreter and report which heavyweights landed in
    sys.modules. A subprocess because the pytest process has already imported
    half the world."""
    code = (
        "import sys\n"
        f"for m in {list(modules)!r}:\n"
        "    __import__(m)\n"
        f"print(','.join(sorted(h for h in {sorted(HEAVY)!r} if h in sys.modules)))\n"
    )
    out = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, timeout=180)
    assert out.returncode == 0, out.stderr[-800:]
    return {x for x in out.stdout.strip().split(",") if x}


def test_importing_the_fleet_pulls_in_no_heavyweight():
    landed = _imported_after(FLEET)
    assert landed == set(), "\n".join(
        f"{name} is back in TEE's interpreter - {HEAVY[name]}" for name in sorted(landed)
    )


def test_running_a_real_med_measurement_pulls_in_no_torch(tmp_path):
    """Stronger than the module-load check above: the fleet imports lazily
    (which is why that check returns in 0.03 s), so a heavyweight would only
    appear once a tool actually RAN. This drives the real entry point on a
    real array and looks again."""
    import numpy as np

    vol = tmp_path / "v.npy"
    np.save(vol, np.arange(27, dtype=np.float32).reshape(3, 3, 3))
    code = (
        "import sys\n"
        "from tee.fleet import med\n"
        f"r = med.volume_stats({{'path': {str(vol)!r}}})\n"
        "assert r['max'] == 26.0, r\n"
        f"print(','.join(sorted(h for h in {sorted(HEAVY)!r} if h in sys.modules)))\n"
    )
    out = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, timeout=180)
    assert out.returncode == 0, out.stderr[-800:]
    landed = {x for x in out.stdout.strip().split(",") if x}
    assert landed == set(), f"a real med call imported {sorted(landed)}"


def test_the_cad_measurement_capability_still_exists():
    """The weight moved; it was not deleted. P1b's rule was that no
    capability may be lost to save space, so assert the entry point is
    still there and still knows where its sidecar lives."""
    from tee.fleet import cad

    assert hasattr(cad, "measure")
    assert cad.SIDECAR_PY.name == "python"
    assert "sidecars" in str(cad.SIDECAR_PY)


def test_medical_reading_survived_monai_removal():
    from tee.fleet import med

    assert hasattr(med, "_read_volume")
    assert med.PHI_TAGS, "the PHI withholding list went missing with MONAI"
