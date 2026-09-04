"""Every verb in `VERBS`, in one script, replayed to one fingerprint (A65 P3.2).

The A53 replay test proved the law on five verbs. Eleven campaigns then added
twenty-four more, each tested on its own and none of them under the replay
law - so this is the script that uses all of them, in an order a garment can
actually take (pattern edits before the garment exists, live gestures after
a drape), with every seed fixed and every file written under `tmp_path`.
"""

from __future__ import annotations

import numpy as np
import pytest

from seamkiln.session import VERBS, Command, Session

pytest.importorskip("numba", reason="the walk and the live gestures use the numba tier")


def every_verb(tmp_path) -> Session:
    s = Session()

    def do(op: str, args: dict) -> dict:
        return s.apply(Command(op, args))

    # -- draft: the pattern verbs, before any garment exists. A pattern is
    # loaded from a file first and the block then replaces it, so the load
    # is exercised and replayed without leaving a seamless tee behind.
    from seamkiln.pattern.dxf import write_dxf
    from seamkiln.pattern.fixtures import tee_block

    write_dxf(tee_block(), tmp_path / "loaded.dxf", flavour="astm")
    do("load", {"path": str(tmp_path / "loaded.dxf")})
    do("block", {"block": "jacket-zip"})
    do("panel", {"id": "POCKET", "outline": [[0, 0], [120, 0], [120, 140], [0, 140]]})
    do("seam", {"id": "pocket-top", "a": "POCKET#2", "b": "FRONT_L#0"})
    do("delete", {"id": "POCKET"})  # takes pocket-top with it
    do("cut", {"panel": "BACK", "op": "pleat", "at_x": 0.0, "depth_mm": 20.0})
    do("grade", {"target": {"chest": 1040.0}, "strict": False})
    do("allowance", {"mm": 10.0})
    do("lock", {"scope": "fabric", "reason": "chosen"})
    do("unlock", {"scope": "fabric"})

    # -- the garment
    do("body", {"kind": "mannequin"})
    do("arrange", {"particle_distance_mm": 20.0})
    do("drape", {"fabric": "cotton_poplin", "frames": 40})
    do("fit", {"allow_unconverged": True})
    do("export", {"format": "dxf", "out": str(tmp_path / "pattern.dxf")})
    do("techpack", {"out": str(tmp_path / "techpack.pdf"), "allow_unconverged": True})

    # -- hardware
    do("zip", {"opening": "centre-front", "material": "metal", "frames": 20})
    do("unzip", {"opening": "centre-front", "to": 0.5, "frames": 20})
    do(
        "button",
        {
            "id": "storm-flap",
            "panel": "FRONT_R",
            "x": 14.0,
            "y": 350.0,
            "hole_panel": "FRONT_L",
            "hole_x": -14.0,
            "hole_y": 350.0,
            "frames": 20,
        },
    )
    do("unfasten", {"id": "storm-flap", "frames": 20})

    # -- the A54 follow-ups on the draped garment
    do("rip", {"seam": "side-left", "fraction": 0.3})
    top = s.drape.points[int(np.argmax(s.drape.points[:, 1]))]
    do(
        "pinch",
        {
            "grabs": [
                {
                    "at": [float(v) for v in top],
                    "radius_mm": 40.0,
                    "to": [float(top[0]), float(top[1]) + 0.02, float(top[2])],
                }
            ],
            "mirror": False,
            "frames": 20,
        },
    )
    do("lace", {"left_panel": "FRONT_L", "right_panel": "FRONT_R", "eyelets": 4, "frames": 20})
    do("finish", {"kind": "wash", "level": "medium"})
    do(
        "animate",
        {"keys": [{"time_s": 0.0, "weight": 0.5}, {"time_s": 0.5, "weight": 0.6}], "fps": 4},
    )
    do("walk", {"gait": "walk", "cycles": 0.25, "fps": 4, "samples_per_cycle": 4})

    # -- live gestures, then the handoff
    hem = s.garment.points[int(np.argmin(s.garment.points[:, 1]))]
    do(
        "pull",
        {
            "x": float(hem[0]),
            "y": float(hem[1]),
            "z": float(hem[2]),
            "to_x": float(hem[0]),
            "to_y": float(hem[1]) - 0.03,
            "to_z": float(hem[2]),
            "radius_mm": 40.0,
            "steps": 3,
            "settle": 5,
        },
    )
    do(
        "fold",
        {
            "x": float(hem[0]),
            "y": float(hem[1]) + 0.05,
            "z": float(hem[2]),
            "depth_mm": 30.0,
            "settle": 5,
        },
    )
    do("ease", {"seam": "side-right", "mm": 5.0})
    do("handoff", {"out": str(tmp_path / "handoff"), "target": "blender"})
    return s


def test_every_verb_replays_to_the_same_fingerprint(tmp_path) -> None:
    session = every_verb(tmp_path)
    used = {c.op for c in session.history}
    assert used == set(VERBS), f"verbs never exercised: {sorted(set(VERBS) - used)}"

    replayed = Session.replay(session.script())
    assert replayed.fingerprint() == session.fingerprint()
    assert [c.op for c in replayed.history] == [c.op for c in session.history]
