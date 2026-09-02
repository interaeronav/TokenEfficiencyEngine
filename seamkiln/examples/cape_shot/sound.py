"""The soundtrack, cut from the simulation's own record.

Nothing here is tapped in by ear. Landings are the frames the hero stops
being airborne (a fact the sim recorded, not inferred from the motion - the
crouch moved the origin up and down while standing still and every wobble
read as a fresh landing), the bounce is the frame the mat is most
compressed, the whooshes scale with the measured speed, the splash is the
frame the fabric card changed, and the wind bed follows the same wind the
cape was pushed with.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np

from examples._common import SR, Synth, master, read_manifest, write_wav


def soundtrack(sim_dir: str | Path, out_path: str | Path, *, log=print) -> Path:
    manifest = read_manifest(Path(sim_dir))
    fps, shots = manifest["fps"], manifest["shots"]
    synth = Synth(20260901)
    duration = len(shots) / fps + 1.2
    n = int(duration * SR)
    track = np.zeros((n, 2))

    y = np.asarray([s["offset"][1] for s in shots])
    x = np.asarray([s["offset"][0] for s in shots])
    wind = np.asarray([s["wind_ms"] for s in shots])
    squash = np.asarray([s.get("mat_squash", 0.0) for s in shots])
    wet = np.asarray([bool(s["wet"]) for s in shots])
    ground = np.asarray([bool(s.get("grounded", False)) for s in shots])

    # the wind bed
    bed = synth.band(synth.pink(n), 110.0, 3200.0)
    speed = np.interp(np.arange(n) / SR, np.arange(len(wind)) / fps, wind)
    bed *= (speed / max(wind.max(), 1e-6)) ** 1.5
    gust = 1.0 + 0.35 * np.sin(2 * np.pi * 0.23 * np.arange(n) / SR)
    track[:, 0] += bed * gust * 0.085
    track[:, 1] += bed * np.roll(gust, 977) * 0.085

    events = []
    dy = np.diff(y, prepend=y[0])
    for i in range(1, len(ground)):
        if ground[i] and not ground[i - 1] and not wet[i]:
            speed_in = abs(dy[i - 1]) * fps
            synth.place(track, i / fps, synth.thump(min(max(speed_in, 1.0) / 4.0, 1.3)), 0.58)
            events.append((round(i / fps, 2), "landing", round(speed_in, 2)))

    if squash.max() > 0.05:
        peak = int(np.argmax(squash))
        contact = int(np.argmax(squash > 0.02))
        synth.place(track, contact / fps, synth.thump(1.15, 0.45), 0.62)
        synth.place(track, peak / fps, synth.boing(1.0), 0.72)
        events.append((round(contact / fps, 2), "mat contact", round(float(squash[peak]), 2)))
        events.append((round(peak / fps, 2), "mat release", 1.0))

    step = np.hypot(np.diff(x, prepend=x[0]), dy) * fps
    airborne = ~ground & (step > 2.2)
    i = 0
    while i < len(airborne):
        if airborne[i]:
            j = i
            while j < len(airborne) and airborne[j]:
                j += 1
            span = (j - i) / fps
            if span > 0.25:
                fast = float(step[i:j].max())
                synth.place(
                    track,
                    i / fps,
                    synth.whoosh(span * 0.95, min(fast / 7.0, 1.0), centre=520 + 90 * fast),
                    0.30,
                )
                events.append((round(i / fps, 2), "whoosh", round(fast, 2)))
            i = j
        else:
            i += 1

    if wet.any():
        entry = int(np.argmax(wet))
        synth.place(track, entry / fps, synth.splash(1.7, 1.0), 0.85)
        synth.place(
            track, (entry + 6) / fps, synth.bubbles(len(shots) / fps - entry / fps + 0.6), 0.30
        )
        events.append((round(entry / fps, 2), "water entry", 1.0))

    out = write_wav(master(track), out_path, sample_rate=SR)
    log(f"wrote {out} - {duration:.2f}s")
    for t, what, how in sorted(events):
        log(f"  {t:5.2f}s  {what:14s} {how}")
    return out
