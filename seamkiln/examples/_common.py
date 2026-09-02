"""Shared pieces of the example pipelines.

Where Blender is, how a PNG or a WAV is written without another dependency,
the argument parser every example shares, and the small synthesiser both
soundtracks are cut from. Deliberately small: the examples exist so the next
session can re-run the delivered shots in minutes, and a helper module with
opinions of its own would be a third thing to learn first.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import struct
import subprocess
import time
import wave
import zlib
from pathlib import Path
from typing import Any

import numpy as np

BLENDER_CANDIDATES = ("/Applications/Blender.app/Contents/MacOS/Blender",)
HERE = Path(__file__).resolve().parent


# -- Blender, found rather than assumed -----------------------------------------


def find_blender() -> str | None:
    """`$BLENDER`, then the PATH, then the standard Mac install. None if absent."""
    env = os.environ.get("BLENDER")
    if env and Path(env).exists():
        return env
    found = shutil.which("blender")
    if found:
        return found
    for candidate in BLENDER_CANDIDATES:
        if Path(candidate).exists():
            return candidate
    return None


def run_blender(
    script: Path, args: list[Any], *, blender: str | None = None, log: Path | None = None
) -> int:
    """Run a standalone Blender-side script headless, factory startup.

    `--factory-startup` is not optional: these pipelines must never touch
    whatever the owner has open, and a headless Blender that loads the user
    preferences can still load their add-ons.
    """
    exe = blender or find_blender()
    if exe is None:
        raise RuntimeError(
            "no Blender found: set BLENDER=/path/to/blender or pass --blender. "
            "Only `render` and `encode` need it; `sim` and `sound` run without."
        )
    cmd = [exe, "--background", "--factory-startup", "--python", str(script), "--"]
    cmd += [str(a) for a in args]
    if log is None:
        return subprocess.call(cmd)
    with log.open("ab") as handle:
        return subprocess.call(cmd, stdout=handle, stderr=subprocess.STDOUT)


# -- files ----------------------------------------------------------------------


def write_png(rgb: np.ndarray, path: str | Path) -> Path:
    """An 8-bit RGB PNG from a (h, w, 3) array. zlib and struct, no PIL."""
    rgb = np.ascontiguousarray(rgb, dtype=np.uint8)
    height, width, _ = rgb.shape
    raw = b"".join(b"\x00" + rgb[y].tobytes() for y in range(height))

    def chunk(tag: bytes, data: bytes) -> bytes:
        body = tag + data
        return (
            struct.pack(">I", len(data)) + body + struct.pack(">I", zlib.crc32(body) & 0xFFFFFFFF)
        )

    png = (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
        + chunk(b"IDAT", zlib.compress(raw, 9))
        + chunk(b"IEND", b"")
    )
    out = Path(path)
    out.write_bytes(png)
    return out


def write_wav(track: np.ndarray, path: str | Path, *, sample_rate: int) -> Path:
    """A 16-bit stereo WAV from an (n, 2) float array in -1..1."""
    data = (np.clip(track, -1.0, 1.0) * 32767).astype(np.int16)
    with wave.open(str(path), "wb") as handle:
        handle.setnchannels(2)
        handle.setsampwidth(2)
        handle.setframerate(sample_rate)
        handle.writeframes(data.tobytes())
    return Path(path)


def read_manifest(sim_dir: Path) -> dict[str, Any]:
    return json.loads((Path(sim_dir) / "manifest.json").read_text())


class Stopwatch:
    def __init__(self) -> None:
        self.started = time.perf_counter()

    @property
    def s(self) -> float:
        return time.perf_counter() - self.started


# -- the parser every example shares ------------------------------------------

STAGES = ("sim", "render", "sound", "encode", "all")


def parser(prog: str, doc: str, *, seconds: float, fps: int, out: str) -> argparse.ArgumentParser:
    top = argparse.ArgumentParser(prog=prog, description=doc)
    sub = top.add_subparsers(dest="stage", required=True)
    for stage in STAGES:
        p = sub.add_parser(stage, help=f"run the {stage} stage" if stage != "all" else "all four")
        p.add_argument("--out", default=out, help=f"working directory (default {out})")
        p.add_argument(
            "--probe",
            action="store_true",
            help="a short, coarse run that proves the pipeline runs; not evidence",
        )
        p.add_argument("--blender", default=None, help="Blender executable (else $BLENDER/PATH)")
        if stage in ("sim", "all"):
            p.add_argument("--fps", type=int, default=fps)
            p.add_argument("--seconds", type=float, default=seconds)
        if stage in ("render", "all"):
            p.add_argument("--first", type=int, default=0)
            p.add_argument("--last", type=int, default=-1)
            p.add_argument("--res", type=int, nargs=2, default=None, metavar=("W", "H"))
            p.add_argument("--samples", type=int, default=None)
        if stage in ("encode", "all"):
            p.add_argument("--to", default=None, help="the .mp4 to write")
    return top


def layout(out: str | Path) -> dict[str, Path]:
    root = Path(out)
    return {
        "root": root,
        "sim": root / "sim",
        "frames": root / "frames",
        "wav": root / "track.wav",
        "log": root / "blender.log",
    }


def render_settings(args: argparse.Namespace, *, res: tuple[int, int], samples: int) -> tuple:
    if getattr(args, "probe", False):
        return (args.res or (640, 360)), (args.samples or 8)
    return (args.res or res), (args.samples or samples)


def encode(
    frames: Path,
    to: Path,
    *,
    fps: int,
    audio: Path | None,
    res: tuple[int, int],
    blender: str | None = None,
    log: Path | None = None,
) -> int:
    script = HERE / "_encode_blender.py"
    args: list[Any] = [frames, to, fps, audio if audio and audio.exists() else "-", *res]
    code = run_blender(script, args, blender=blender, log=log)
    settle_output(to)
    return code


def settle_output(to: Path) -> Path:
    """Blender names a movie `<stem><first>-<last>.mp4` whatever it was asked
    for; the caller asked for `to`, so that is what it gets."""
    to = Path(to)
    if to.exists():
        return to
    made = sorted(to.parent.glob(f"{to.stem}*{to.suffix}"), key=lambda p: p.stat().st_mtime)
    if made:
        made[-1].rename(to)
    return to


# -- a small synthesiser ---------------------------------------------------------
#
# Everything the soundtracks need: filtered noise, a few envelopes, and the
# handful of sounds the shots contain. A one-pole filter as a Python loop is
# slow and honest; the tracks are seconds long and the whole stage takes a
# few seconds, so it is not worth a dependency.

SR = 48000


class Synth:
    def __init__(self, seed: int) -> None:
        self.rng = np.random.default_rng(seed)

    def noise(self, n: int) -> np.ndarray:
        return self.rng.standard_normal(n)

    def pink(self, n: int) -> np.ndarray:
        """1/f-ish noise: three one-pole stages summed, then normalised."""
        w = self.noise(n)
        y = np.zeros(n)
        s = np.zeros(3)
        coeffs = ((0.99765, 0.0990460), (0.96300, 0.0993057), (0.57000, 0.1848290))
        for i in range(n):
            for k, (p, g) in enumerate(coeffs):
                s[k] = p * s[k] + w[i] * g
            y[i] = s.sum() + w[i] * 0.1848
        return y / (np.abs(y).max() + 1e-9)

    @staticmethod
    def onepole(x: np.ndarray, cutoff: float, kind: str = "low") -> np.ndarray:
        a = np.exp(-2.0 * np.pi * cutoff / SR)
        out = np.zeros_like(x)
        z = 0.0
        for i in range(len(x)):
            z = (1 - a) * x[i] + a * z
            out[i] = z
        return out if kind == "low" else x - out

    def band(self, x: np.ndarray, lo: float, hi: float) -> np.ndarray:
        return self.onepole(self.onepole(x, hi, "low"), lo, "high")

    @staticmethod
    def env(n: int, attack: float, decay: float, hold: float = 0.0, power: float = 1.6):
        a = max(int(attack * SR), 1)
        h = int(hold * SR)
        d = max(int(decay * SR), 1)
        e = np.zeros(n)
        e[:a] = np.linspace(0.0, 1.0, a)
        e[a : a + h] = 1.0
        tail = min(d, max(n - a - h, 0))
        if tail:
            e[a + h : a + h + tail] = np.linspace(1.0, 0.0, tail) ** power
        return e

    @staticmethod
    def place(
        track: np.ndarray, start_s: float, clip: np.ndarray, gain: float = 1.0, pan: float = 0.0
    ):
        i = int(start_s * SR)
        if i >= len(track) or i < 0:
            return
        n = min(len(clip), len(track) - i)
        left, right = gain * (1.0 - max(pan, 0.0)), gain * (1.0 + min(pan, 0.0))
        track[i : i + n, 0] += clip[:n] * left
        track[i : i + n, 1] += clip[:n] * right

    # -- the sounds ----------------------------------------------------------

    def thump(self, strength: float = 1.0, length: float = 0.55) -> np.ndarray:
        """A body landing: a pitch-dropping thud with a slap of noise on top."""
        n = int(length * SR)
        t = np.arange(n) / SR
        f = 96.0 * np.exp(-t * 7.0) + 34.0
        body = np.sin(2 * np.pi * np.cumsum(f) / SR) * self.env(n, 0.004, length * 0.85, power=2.2)
        slap = self.band(self.noise(n), 220.0, 2600.0) * self.env(n, 0.002, 0.10, power=3.0) * 0.5
        return (body * 0.9 + slap) * strength

    def boing(self, strength: float = 1.0, length: float = 0.80) -> np.ndarray:
        """A mat throwing somebody back: a resonance that RISES as it releases."""
        n = int(length * SR)
        t = np.arange(n) / SR
        f = 62.0 + 120.0 * (1.0 - np.exp(-t * 5.5))
        tone = np.sin(2 * np.pi * np.cumsum(f) / SR)
        wobble = np.sin(2 * np.pi * 11.0 * t) * 0.35 + 1.0
        skin = self.band(self.noise(n), 150.0, 1800.0) * self.env(n, 0.003, 0.16, power=3.0) * 0.35
        return (
            tone * wobble * self.env(n, 0.012, length * 0.9, power=1.3) * 0.85 + skin
        ) * strength

    def whoosh(self, length: float = 0.7, strength: float = 1.0, centre: float = 900.0):
        n = int(length * SR)
        t = np.arange(n) / SR
        sweep = self.band(self.noise(n), centre * 0.35, centre * 2.6)
        shape = np.sin(np.pi * np.clip(t / length, 0, 1)) ** 1.4
        return sweep * shape * strength

    def splash(self, length: float = 1.6, strength: float = 1.0) -> np.ndarray:
        """Water: a burst, a spray tail, and the hollow of a body going in."""
        n = int(length * SR)
        t = np.arange(n) / SR
        burst = self.band(self.noise(n), 300.0, 7000.0) * self.env(n, 0.004, 0.35, power=2.4)
        spray = self.band(self.noise(n), 1800.0, 11000.0) * self.env(n, 0.02, 0.9, power=2.8) * 0.55
        gulp = np.sin(2 * np.pi * (150.0 * np.exp(-t * 4.0) + 60.0) * t)
        gulp *= self.env(n, 0.02, 0.6, power=2.0) * 0.5
        return (burst + spray + gulp) * strength

    def bubbles(self, length: float, strength: float = 1.0) -> np.ndarray:
        n = int(length * SR)
        rumble = self.onepole(self.noise(n), 190.0, "low") * 0.6
        out = rumble.copy()
        for _ in range(int(length * 9)):
            at = self.rng.uniform(0, max(length - 0.25, 0.01))
            m = int(0.16 * SR)
            tt = np.arange(m) / SR
            f = self.rng.uniform(380, 1500) * (1.0 + 2.4 * tt / 0.16)
            blip = np.sin(2 * np.pi * np.cumsum(f) / SR) * self.env(m, 0.002, 0.13, power=3.2)
            i = int(at * SR)
            out[i : i + m] += blip[: len(out) - i] * self.rng.uniform(0.12, 0.4)
        return out * strength

    def footstep(self, strength: float = 1.0, length: float = 0.34) -> np.ndarray:
        """Boot on hard ground: a short low thud with grit on top."""
        n = int(length * SR)
        t = np.arange(n) / SR
        f = 78.0 * np.exp(-t * 16.0) + 42.0
        body = np.sin(2 * np.pi * np.cumsum(f) / SR) * self.env(n, 0.003, length, power=3.0)
        grit = self.band(self.noise(n), 900.0, 6500.0) * self.env(n, 0.001, 0.055, power=4.0)
        return (body * 0.85 + grit * 0.30) * strength


def master(track: np.ndarray, drive: float = 1.35, ceiling: float = 0.90) -> np.ndarray:
    peak = float(np.abs(track).max())
    return np.tanh(track / max(peak, 1e-9) * drive) * ceiling
