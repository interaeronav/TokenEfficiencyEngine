"""The session verbs reach the rig: `body kind=custom` keeps a skeleton and `walk` bends it.

`test_rig_walk.py` proves the FACTORY articulates. This proves the two
session verbs actually reach it, which is a different thing and was missing
until 2026-09-04: every non-figure body went to `rigid_factory`, so the whole
rig lane existed and nothing could get to it.
"""

from __future__ import annotations

import numpy as np
import pytest

from seamkiln.avatar import gait, rigged_factory, rigid_factory
from seamkiln.rig.character import build_character
from seamkiln.rig.skin import load_rigged_avatar
from seamkiln.session import Command, Session

STATURE = 1.75


@pytest.fixture(scope="module")
def hero(tmp_path_factory) -> str:
    path = tmp_path_factory.mktemp("rig") / "hero.glb"
    build_character(STATURE).to_glb(path)
    return str(path)


def test_a_glb_with_a_skin_arrives_articulated(hero: str) -> None:
    session = Session()
    out = session.apply(Command("body", {"kind": "custom", "path": hero}))
    assert out["articulated"] is True
    assert session.rig is not None
    # all nine of seamkiln's joints found, by NAME, in a Mixamo-style rig
    assert len(out["avatar"]["rig"]["mapped"]) == 9
    # ... and the session still holds a plain mesh for the SDF and the measurer
    assert session.body.vertices.shape[1] == 3


def test_reshaping_the_mesh_drops_the_skeleton_and_says_so(hero: str) -> None:
    """`adjust` reshapes the mesh; the bind pose no longer fits it.

    Skinning against a stale bind pose tears a limb, so the rig is dropped
    rather than used - and the answer says which, because a body that quietly
    stopped articulating is the failure this whole lane exists to remove.
    """
    session = Session()
    out = session.apply(Command("body", {"kind": "custom", "path": hero, "girth_scale": 1.2}))
    assert out["articulated"] is False
    assert session.rig is None
    assert "skeleton no longer fits" in out["note"]


def test_a_new_body_never_inherits_the_last_ones_skeleton(hero: str) -> None:
    session = Session()
    session.apply(Command("body", {"kind": "custom", "path": hero}))
    assert session.rig is not None
    out = session.apply(Command("body", {"kind": "mannequin"}))
    assert session.rig is None and out["articulated"] is False


def test_the_walk_bends_the_body_instead_of_sliding_it(hero: str) -> None:
    """The one measurement rigid motion cannot fake.

    A rigid body can travel, rise and turn, but it cannot change the DISTANCE
    between two of its own vertices. Measured over one walk cycle: the feet's
    fore-aft spread swings about half a metre when the rig drives it and is
    constant to the last bit when it does not.
    """
    rig = load_rigged_avatar(hero)
    track = gait("walk", cycles=1.0, samples_per_cycle=12)

    def foot_spread(factory) -> np.ndarray:
        out = []
        for pose in track.poses:
            mesh, _ = factory(pose.as_values())
            v = np.asarray(mesh.vertices)
            feet = v[v[:, 1] < v[:, 1].min() + 0.12]
            out.append(float(feet[:, 2].max() - feet[:, 2].min()))
        return np.array(out)

    articulated = foot_spread(rigged_factory(rig))
    rigid = foot_spread(rigid_factory(rig.mesh()))

    assert np.ptp(articulated) > 0.30, articulated
    assert np.ptp(rigid) == 0.0, rigid


def test_the_pelvis_rise_is_earned_not_scripted(hero: str) -> None:
    """Articulated, the body is put on the ground each frame and the pelvis
    rises because the stance leg straightens. Rigid, the rise is the gait's
    own scripted number. Both are legitimate; they must not be confused."""
    rig = load_rigged_avatar(hero)
    track = gait("walk", cycles=1.0, samples_per_cycle=12)
    art = np.array([rigged_factory(rig)(p.as_values())[1][1] for p in track.poses])
    scripted = np.array([p.rise_m for p in track.poses])

    assert np.ptp(art) > 0.01  # it really does bob
    # and it is NOT the scripted track echoed back
    assert not np.allclose(art - art.mean(), scripted - scripted.mean(), atol=1e-6)
