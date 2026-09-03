"""Synthetic scan fixtures for the pc_* lane (A67).

Deterministic, numpy-only, no scanner and no network: this is the gate that
runs in CI. The corruption is deliberate - a real scan arrives tilted, yawed,
translated and slightly off-scale, and recovering those four is the whole job.

The reference numbers in docs/research/69 came from `make_room(seed=7)`,
which produces exactly 279,352 points.
"""

from __future__ import annotations

import numpy as np


def make_room(
    L: float = 4.000,
    W: float = 3.000,
    H: float = 2.700,
    step: float = 0.015,
    noise: float = 0.012,
    tilt: tuple[float, float] = (2.3, 1.1),
    yaw: float = 37.0,
    scale: float = 1.004,
    offset: tuple[float, float, float] = (12.34, -5.67, 2.10),
    seed: int = 7,
) -> tuple[np.ndarray, dict]:
    """Interior-faces point cloud of a rectangular room, then corrupted.

    Returns (points Nx3, truth dict).
    """
    rng = np.random.default_rng(seed)

    def grid(a: float, b: float):
        return np.meshgrid(
            np.arange(0, a + step, step), np.arange(0, b + step, step), indexing="ij"
        )

    faces = []
    x, y = grid(L, W)
    faces += [
        np.c_[x.ravel(), y.ravel(), np.zeros(x.size)],
        np.c_[x.ravel(), y.ravel(), np.full(x.size, H)],
    ]
    x, z = grid(L, H)
    faces += [
        np.c_[x.ravel(), np.zeros(x.size), z.ravel()],
        np.c_[x.ravel(), np.full(x.size, W), z.ravel()],
    ]
    y, z = grid(W, H)
    faces += [
        np.c_[np.zeros(y.size), y.ravel(), z.ravel()],
        np.c_[np.full(y.size, L), y.ravel(), z.ravel()],
    ]
    total = sum(f.shape[0] for f in faces)
    pts = np.vstack(faces) + rng.normal(0, noise, (total, 3))

    rx, ry, rz = np.deg2rad([tilt[0], tilt[1], yaw])
    mx = np.array([[1, 0, 0], [0, np.cos(rx), -np.sin(rx)], [0, np.sin(rx), np.cos(rx)]])
    my = np.array([[np.cos(ry), 0, np.sin(ry)], [0, 1, 0], [-np.sin(ry), 0, np.cos(ry)]])
    mz = np.array([[np.cos(rz), -np.sin(rz), 0], [np.sin(rz), np.cos(rz), 0], [0, 0, 1]])
    pts = (pts * scale) @ (mz @ my @ mx).T + np.asarray(offset)

    truth = {
        "L": L,
        "W": W,
        "H": H,
        "noise": noise,
        "tilt": tilt,
        "yaw": yaw,
        "scale": scale,
        "scaled_L": L * scale,
        "scaled_W": W * scale,
        "correction": 1.0 / scale,
    }
    return pts, truth
