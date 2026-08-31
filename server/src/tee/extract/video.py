"""Video lane (7.4): keyframes, timestamp index, DJI telemetry - all local,
zero tokens. ffmpeg ships inside the imageio-ffmpeg wheel and is invoked via
subprocess only (GPL binary stays out of process; research 13).
"""

from __future__ import annotations

import math
import re
import subprocess
from pathlib import Path
from typing import Any

from tee.kernel.errors import TeeError

VIDEO_EXTRACTOR = ("video", "1")
SAMPLE_EVERY_S = 2.0
MAX_KEYFRAMES = 15
KEYFRAME_HAMMING = 8
_TIME_RE = re.compile(r"Duration:\s*(\d+):(\d+):(\d+(?:\.\d+)?)")


def ffmpeg_exe() -> str:
    import imageio_ffmpeg

    return imageio_ffmpeg.get_ffmpeg_exe()


def _run(args: list[str], timeout: float = 300.0) -> subprocess.CompletedProcess:
    return subprocess.run(args, capture_output=True, text=True, timeout=timeout)


def probe_duration_s(path: Path) -> float:
    proc = _run([ffmpeg_exe(), "-i", str(path)])
    match = _TIME_RE.search(proc.stderr)
    if not match:
        raise TeeError("bad_video", f"ffmpeg cannot read {path.name}.")
    hours, minutes, seconds = match.groups()
    return int(hours) * 3600 + int(minutes) * 60 + float(seconds)


def extract_video(path: Path, derived: Path) -> list[dict[str, Any]]:
    """Sample every N seconds -> sharpness + phash funnel -> <= MAX_KEYFRAMES
    keyframes with a timestamp index. The every-N sampler is the primary path
    for continuous walkthrough/drone footage (research 13)."""
    import cv2
    import imagehash

    from tee.kernel.imaging import open_image

    duration = probe_duration_s(path)
    facts: list[dict[str, Any]] = [
        {"kind": "video", "duration_s": round(duration, 2), "sampled_every_s": SAMPLE_EVERY_S}
    ]
    frames_dir = derived / "frames"
    frames_dir.mkdir(parents=True, exist_ok=True)
    proc = _run(
        [
            ffmpeg_exe(),
            "-hide_banner",
            "-loglevel",
            "error",
            "-i",
            str(path),
            "-vf",
            f"fps=1/{SAMPLE_EVERY_S}",
            "-q:v",
            "4",
            str(frames_dir / "f%04d.jpg"),
        ],
        timeout=900.0,
    )
    if proc.returncode != 0:
        raise TeeError("bad_video", f"frame sampling failed: {proc.stderr[-200:]}")

    candidates = []
    for index, frame_path in enumerate(sorted(frames_dir.glob("f*.jpg"))):
        pts = index * SAMPLE_EVERY_S
        gray = cv2.imread(str(frame_path), cv2.IMREAD_GRAYSCALE)
        if gray is None:
            continue
        sharpness = float(cv2.Laplacian(gray, cv2.CV_64F).var())
        with open_image(frame_path) as img:
            phash = imagehash.phash(img)
        candidates.append({"path": frame_path, "pts": pts, "sharpness": sharpness, "phash": phash})

    # dedupe: cluster consecutive frames by phash, keep the sharpest of each
    keyframes: list[dict[str, Any]] = []
    cluster: list[dict[str, Any]] = []

    def flush() -> None:
        if cluster:
            keyframes.append(max(cluster, key=lambda c: c["sharpness"]))
            cluster.clear()

    for candidate in candidates:
        if cluster and (candidate["phash"] - cluster[-1]["phash"]) > KEYFRAME_HAMMING:
            flush()
        cluster.append(candidate)
    flush()
    if len(keyframes) > MAX_KEYFRAMES:
        step = len(keyframes) / MAX_KEYFRAMES
        keyframes = [keyframes[int(i * step)] for i in range(MAX_KEYFRAMES)]

    keep_dir = derived / "keyframes"
    keep_dir.mkdir(exist_ok=True)
    for number, frame in enumerate(keyframes, 1):
        target = keep_dir / f"k{number:02d}.jpg"
        frame["path"].replace(target)
        facts.append(
            {
                "kind": "keyframe",
                "id": f"k{number:02d}",
                "pts_time": round(frame["pts"], 2),
                "sharpness": round(frame["sharpness"], 1),
                "phash": str(frame["phash"]),
                "thumb": str(target),
            }
        )
    for leftover in frames_dir.glob("f*.jpg"):
        leftover.unlink(missing_ok=True)
    return facts


def fetch_frame(path: Path, pts_time: float, out: Path) -> Path:
    """Frame-accurate re-fetch by timestamp (input seeking; never -c copy)."""
    proc = _run(
        [
            ffmpeg_exe(),
            "-hide_banner",
            "-loglevel",
            "error",
            "-ss",
            f"{max(0.0, pts_time):.3f}",
            "-i",
            str(path),
            "-frames:v",
            "1",
            "-q:v",
            "3",
            "-y",
            str(out),
        ]
    )
    if proc.returncode != 0 or not out.exists():
        raise TeeError(
            "frame_fetch_failed",
            f"No frame at t={pts_time:.2f}s: {proc.stderr[-160:]}",
            fix="Check the timestamp against the video duration in ex_facts.",
        )
    return out


# -- DJI SRT telemetry -------------------------------------------------------

_SRT_LAT = re.compile(r"\[latitude:\s*(-?\d+(?:\.\d+)?)\]")
_SRT_LON = re.compile(r"\[longitude:\s*(-?\d+(?:\.\d+)?)\]")
_SRT_REL = re.compile(r"\[rel_alt:\s*(-?\d+(?:\.\d+)?)")
_SRT_ABS = re.compile(r"abs_alt:\s*(-?\d+(?:\.\d+)?)\]")
_SRT_LEGACY = re.compile(r"GPS\s*\((-?\d+\.\d+),\s*(-?\d+\.\d+)")
_SRT_TS = re.compile(r"(\d+):(\d+):(\d+)[,.](\d+)\s*-->")


def parse_dji_srt(text: str) -> list[dict[str, Any]]:
    """DJI SRT telemetry -> flight-path facts, downsampled to turning points.
    Handles bracketed [latitude:]/[longitude:] and legacy GPS(...) layouts;
    the vertical channel is a lower evidence tier (research 18)."""
    samples: list[dict[str, Any]] = []
    for block in re.split(r"\n\s*\n", text):
        ts = _SRT_TS.search(block)
        lat = _SRT_LAT.search(block)
        lon = _SRT_LON.search(block)
        if lat and lon:
            latitude, longitude = float(lat.group(1)), float(lon.group(1))
        else:
            legacy = _SRT_LEGACY.search(block)
            if not legacy:
                continue
            longitude, latitude = float(legacy.group(1)), float(legacy.group(2))
        t = 0.0
        if ts:
            h, m, s, ms = (int(g) for g in ts.groups())
            t = h * 3600 + m * 60 + s + ms / 1000.0
        sample = {"t": t, "lat": latitude, "lon": longitude}
        rel = _SRT_REL.search(block)
        abs_alt = _SRT_ABS.search(block)
        if rel:
            sample["rel_alt"] = float(rel.group(1))
        if abs_alt:
            sample["abs_alt"] = float(abs_alt.group(1))
        samples.append(sample)
    if not samples:
        return []
    path = _turning_points(samples)
    return [
        {
            "kind": "flight_path",
            "tier": "gps_prior",
            "samples": len(samples),
            "path": path,
            "note": "vertical channel is a separate, lower evidence tier",
        }
    ]


def _turning_points(samples: list[dict[str, Any]], angle_deg: float = 10.0) -> list[dict[str, Any]]:
    if len(samples) <= 2:
        return samples
    kept = [samples[0]]
    for previous, current, following in zip(samples, samples[1:], samples[2:], strict=False):
        v1 = (current["lat"] - previous["lat"], current["lon"] - previous["lon"])
        v2 = (following["lat"] - current["lat"], following["lon"] - current["lon"])
        n1, n2 = math.hypot(*v1), math.hypot(*v2)
        if n1 == 0 or n2 == 0:
            continue
        cos = max(-1.0, min(1.0, (v1[0] * v2[0] + v1[1] * v2[1]) / (n1 * n2)))
        if math.degrees(math.acos(cos)) > angle_deg:
            kept.append(current)
    kept.append(samples[-1])
    return kept
