"""The two delivered shots run from the repo (A65 P3.1).

Only the `sim` stage runs here, as a `--probe`: short, coarse, no Blender.
A probe's one claim is that the pipeline runs end to end and writes what the
render stage reads - its manifest says so in words, because nothing measured
on a coarse preview is evidence of anything else.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pytest

EXAMPLES_ROOT = Path(__file__).resolve().parents[1]  # seamkiln/, which holds examples/
if str(EXAMPLES_ROOT) not in sys.path:
    sys.path.insert(0, str(EXAMPLES_ROOT))

pytest.importorskip("numba", reason="the examples run the numba solver tier")


def test_the_cape_shot_probe_runs_and_gets_wet(tmp_path) -> None:
    from examples.cape_shot import sim

    manifest = sim.simulate(tmp_path / "sim", probe=True, log=lambda *_: None)
    assert manifest["probe"] is True and "not evidence" in manifest["note"]
    shots = manifest["shots"]
    assert len(shots) == manifest["frames"] == round(sim.DURATION * sim.PROBE["fps"])
    # the timeline's beats are in the record the sound stage cuts from
    assert any(s["grounded"] for s in shots) and any(not s["grounded"] for s in shots)
    assert max(s["mat_squash"] for s in shots) > 0.5, "the mat never compressed"
    wet_frames = [s for s in shots if s["wet"]]
    assert wet_frames and wet_frames[-1]["fabric"].endswith("_wet"), "the wet card never came in"
    assert shots[-1]["body_wet"] > 0.3, "the hero went in the pool and stayed dry"
    assert shots[-1]["cape_wet"] > 0.0, "the cape never touched the water"
    # what the render stage reads
    last = shots[-1]["frame"]
    pts = np.load(tmp_path / "sim" / "cape" / f"{last:04d}.npy")
    tri = np.load(tmp_path / "sim" / "cape_topology.npy")
    assert pts.shape[1] == 3 and tri.max() < len(pts)
    assert (tmp_path / "sim" / "body" / f"{last:04d}.ply").stat().st_size > 1000
    assert json.loads((tmp_path / "sim" / "manifest.json").read_text())["example"] == "cape_shot"


def test_the_cape_shot_soundtrack_is_cut_from_the_record(tmp_path) -> None:
    from examples.cape_shot import sim, sound

    sim.simulate(tmp_path / "sim", probe=True, seconds=sim.DURATION, log=lambda *_: None)
    lines: list[str] = []
    wav = sound.soundtrack(tmp_path / "sim", tmp_path / "track.wav", log=lines.append)
    assert wav.stat().st_size > 48000 * 2 * 2 * 8, "shorter than the shot"
    said = "\n".join(lines)
    for event in ("landing", "mat contact", "mat release", "water entry"):
        assert event in said, f"no {event!r} event: the soundtrack is not reading the sim"


def test_the_fur_walk_probe_runs_and_stays_worn(tmp_path) -> None:
    from examples.fur_walk import sim

    manifest = sim.simulate(tmp_path / "sim", probe=True, seconds=1.0, log=lambda *_: None)
    assert manifest["probe"] is True
    assert manifest["zip"]["material"] == "metal"
    assert "dressed" in manifest
    shots = manifest["shots"]
    assert len(shots) == round(1.0 * sim.PROBE["fps"])
    assert all(s["strands"] > 0 for s in shots)
    # the body travels at the gait's own speed
    travelled = shots[-1]["offset"][2] - shots[0]["offset"][2]
    expected = sim.GAITS["walk"].speed_ms * (shots[-1]["t"] - shots[0]["t"])
    assert abs(travelled - expected) < 1e-3  # offsets are recorded to 4 dp
    last = shots[-1]["frame"]
    strands = np.load(tmp_path / "sim" / "fur" / f"{last:04d}.npy")
    assert strands.shape[1:] == (3, 3)
    assert (tmp_path / "sim" / "cloth" / f"{last:04d}.npy").exists()


def test_the_flag_is_the_flag(tmp_path) -> None:
    from examples.cape_shot import flag

    img = flag.namibia(300)
    assert img.shape == (200, 300, 3)
    # blue upper hoist, green lower fly, gold sun in the blue
    assert tuple(img[10, 10]) == flag.BLUE
    assert tuple(img[190, 290]) == flag.GREEN
    assert tuple(img[int(0.28 * 200), int(0.25 * 300)]) == flag.GOLD
    assert (img == np.array(flag.RED)).all(axis=2).sum() > 0.05 * img.shape[0] * img.shape[1]
    out = flag.write(tmp_path / "flag.png", 120)
    assert out.read_bytes()[:8] == b"\x89PNG\r\n\x1a\n"


def test_the_dispatchers_parse_every_stage() -> None:
    from examples import _common

    parser = _common.parser("x", "doc", seconds=1.0, fps=24, out="o")
    for stage in _common.STAGES:
        args = parser.parse_args([stage, "--probe"])
        assert args.stage == stage and args.probe and args.out == "o"
    assert parser.parse_args(["render", "--res", "640", "360"]).res == [640, 360]
