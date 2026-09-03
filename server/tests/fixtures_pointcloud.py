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


def make_two_rooms(
    step: float = 0.02,
    noise: float = 0.012,
    clutter: int = 4_000,
    seed: int = 11,
) -> tuple[np.ndarray, dict]:
    """Two rooms either side of a thick partition, with furniture in the way.

    The single-rectangle fixture cannot catch the failures that matter on a
    real scan, because it has no wall thickness, no second room, no doorway
    and no clutter. Measured on the Okongo test scan, an unguarded RANSAC
    fitter ran 4 m diagonals through a bed and returned 133 m of "wall"
    inside a 5 x 5 m room. This fixture reproduces that shape.

    Layout (metres), walls 2.6 m high:
        x = 0.00  west wall          y = 0.00  south wall
        x = 2.40  partition, west face
        x = 2.66  partition, east face   (260 mm thick)
        x = 6.00  east wall          y = 4.00  north wall
    The partition carries a 0.9 m doorway between y = 1.5 and y = 2.4.
    """
    rng = np.random.default_rng(seed)

    def plane_x(x, y0, y1, z0=0.0, z1=2.6):
        yy, zz = np.meshgrid(np.arange(y0, y1, step), np.arange(z0, z1, step), indexing="ij")
        return np.c_[np.full(yy.size, x), yy.ravel(), zz.ravel()]

    def plane_y(y, x0, x1, z0=0.0, z1=2.6):
        xx, zz = np.meshgrid(np.arange(x0, x1, step), np.arange(z0, z1, step), indexing="ij")
        return np.c_[xx.ravel(), np.full(xx.size, y), zz.ravel()]

    faces = [
        plane_x(0.00, 0.0, 4.0),
        plane_x(6.00, 0.0, 4.0),
        plane_y(0.00, 0.0, 6.0),
        plane_y(4.00, 0.0, 6.0),
        # the partition, both faces, interrupted by a doorway
        plane_x(2.40, 0.0, 1.5),
        plane_x(2.40, 2.4, 4.0),
        plane_x(2.66, 0.0, 1.5),
        plane_x(2.66, 2.4, 4.0),
    ]
    xx, yy = np.meshgrid(np.arange(0, 6.0, step), np.arange(0, 4.0, step), indexing="ij")
    faces.append(np.c_[xx.ravel(), yy.ravel(), np.zeros(xx.size)])
    points = np.vstack(faces)
    points = points + rng.normal(0, noise, points.shape)

    # furniture: scattered blobs in the middle of the big room, the exact
    # thing a RANSAC line will try to join up into a wall
    blobs = []
    for cx, cy in ((4.2, 1.1), (3.4, 3.0), (5.0, 2.6)):
        blobs.append(rng.normal([cx, cy, 0.6], [0.35, 0.30, 0.45], (clutter // 3, 3)))
    points = np.vstack([points, *blobs])

    truth = {
        "west": 0.00,
        "east": 6.00,
        "south": 0.00,
        "north": 4.00,
        "partition_west": 2.40,
        "partition_east": 2.66,
        "partition_thickness": 0.26,
        "door_from": 1.5,
        "door_to": 2.4,
        "height": 2.6,
    }
    return points, truth
