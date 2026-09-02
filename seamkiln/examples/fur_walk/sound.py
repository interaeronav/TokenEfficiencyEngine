"""Footsteps, wind and the rustle of a heavy coat - all timed from the sim.

The footfalls are the minima of the pelvis height the simulation recorded
(the body's centre is lowest at double support, the instant a foot arrives);
the rustle is the cloth's own measured speed, which peaks when the coat
swings and dies when it hangs.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np

from examples._common import SR, Synth, master, read_manifest, write_wav


def soundtrack(sim_dir: str | Path, out_path: str | Path, *, log=print) -> Path:
    walk = Path(sim_dir)
    manifest = read_manifest(walk)
    fps, shots = manifest["fps"], manifest["shots"]
    synth = Synth(770077)
    duration = len(shots) / fps + 0.8
    n = int(duration * SR)
    track = np.zeros((n, 2))

    pelvis = np.asarray([s["pelvis_y"] for s in shots])
    zpos = np.asarray([s["offset"][2] for s in shots])
    start_z = float(zpos[0])
    span_z = max(float(zpos[-1] - zpos[0]), 1e-6)

    speed = np.zeros(len(shots))
    prev = None
    for k, s in enumerate(shots):
        pts = np.load(walk / "cloth" / f"{s['frame']:04d}.npy")
        if prev is not None:
            speed[k] = float(np.linalg.norm(pts - prev, axis=1).mean()) * fps
        prev = pts

    events = []
    for i in range(1, len(pelvis) - 1):
        if pelvis[i] <= pelvis[i - 1] and pelvis[i] < pelvis[i + 1]:
            close = np.clip((zpos[i] - start_z) / span_z, 0.0, 1.0)
            gain = 0.30 + 0.55 * close**1.6
            synth.place(
                track, i / fps, synth.footstep(1.0), gain, pan=0.35 * (1 if len(events) % 2 else -1)
            )
            events.append((round(i / fps, 2), "footfall", round(float(gain), 2)))

    bed = synth.band(synth.noise(n), 60.0, 900.0)
    track[:, 0] += bed * 0.020
    track[:, 1] += np.roll(bed, 1301) * 0.020

    rustle = synth.band(synth.noise(n), 1400.0, 9000.0)
    loud = np.interp(np.arange(n) / SR, np.arange(len(speed)) / fps, speed)
    loud = loud / max(float(speed.max()), 1e-9)
    near = np.interp(
        np.arange(n) / SR, np.arange(len(zpos)) / fps, np.clip((zpos - start_z) / span_z, 0.0, 1.0)
    )
    shaped = rustle * (loud**1.5) * (0.25 + 0.75 * near)
    track[:, 0] += shaped * 0.10
    track[:, 1] += shaped * 0.10

    out = write_wav(master(track, drive=1.25, ceiling=0.88), out_path, sample_rate=SR)
    log(f"wrote {out} - {duration:.2f}s, {len(events)} footfalls")
    log(f"  cloth speed: {speed.min():.3f}..{speed.max():.3f} m/s (mean per-particle)")
    return out
