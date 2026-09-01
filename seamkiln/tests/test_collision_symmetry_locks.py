"""A55: collision direction, symmetry sync, and locks.

The three share a shape: each is a correctness problem that does not show up
in any other number. An inside-out panel drapes identically and renders
wrong; an unbalanced mesh drapes almost identically and is asymmetric for no
visible reason; an unlocked panel changes and nobody notices until later.
"""

from __future__ import annotations

import numpy as np
import pytest

from seamkiln.drape import collision
from seamkiln.drape.body import mannequin, sdf_from_mesh, solid_ball
from seamkiln.drape.garment import build_garment, top_arrangement
from seamkiln.drape.solve import DrapeSettings, drape
from seamkiln.locking import LockedError, Locks
from seamkiln.pattern import symmetry
from seamkiln.pattern.fabric import fabric
from seamkiln.pattern.fixtures import tee_block
from seamkiln.session import Command, CommandError, Session


@pytest.fixture(scope="module")
def body():
    return mannequin()


@pytest.fixture(scope="module")
def draped(body):
    field = sdf_from_mesh(body, voxel_mm=10.0)
    pattern = tee_block()
    garment = build_garment(pattern, top_arrangement(pattern, body), particle_distance=16.0)
    return (
        garment,
        drape(garment, field, fabric="cotton_poplin", settings=DrapeSettings(frames=200)),
        field,
    )


# -- collision ---------------------------------------------------------------


def test_render_normals_are_measured_against_the_collision_direction(draped) -> None:
    """An inside-out panel is lit from inside: it renders dark, its wash lands
    on the wrong face and its fur grows INTO the body - while the drape is
    unaffected, which is why nothing else reports it.

    This check earned its keep immediately: it caught the right sleeve everting
    during the solve, which nothing else in the suite noticed. The cause was a
    restitution bug in the collision pass, not the sleeve's placement.
    """
    garment, result, field = draped
    report = collision.alignment(garment, result.points, field)
    assert set(report["panels"]) == set(garment.panel_slices)
    assert report["panels"]["FRONT"]["mean_agreement"] > 0.8
    assert report["panels"]["BACK"]["mean_agreement"] > 0.8
    assert report["inside_out_panels"] == [], "a panel is facing the body"
    assert report["aligned"] is True


def test_an_inverted_panel_is_caught_and_flipped(draped) -> None:
    garment, result, field = draped
    clean = collision.alignment(garment, result.points, field)["inside_out_panels"]
    low, high = garment.panel_slices["FRONT"]
    rows = np.all((garment.triangles >= low) & (garment.triangles < high), axis=1)
    garment.triangles[rows] = garment.triangles[rows][:, [0, 2, 1]]

    broken = collision.alignment(garment, result.points, field)
    assert "FRONT" in broken["inside_out_panels"]

    garment, fix = collision.align_to_field(garment, result.points, field)
    assert "FRONT" in fix["flipped"]
    assert fix["after"] > fix["before"], "flipping did not improve the agreement"
    assert not set(clean) - set(fix["flipped"]), "a clean panel was flipped"


def test_contact_material_combines_friction_the_way_people_expect() -> None:
    """Bullet multiplies friction, so two 0.5 surfaces read as 0.25 and
    surprise everyone once (research doc 34 records TEE hitting exactly
    that). The geometric mean keeps 0.5 and 0.5 at 0.5."""
    same = collision.ContactMaterial.between(fabric("cotton_poplin"), subject_friction=0.35)
    assert same.friction == pytest.approx(0.35, abs=0.01)
    assert 0.0 <= same.restitution < 0.2, "cloth is not a bouncing ball"


def test_contacts_counts_what_is_touching_and_what_is_inside(draped) -> None:
    garment, result, field = draped
    report = collision.contacts(garment, result.points, field)
    assert report["particles"] == len(result.points)
    assert report["touching"] > 0
    assert report["inside"] < report["particles"] * 0.05


def test_a_ball_far_away_touches_nothing() -> None:
    field = sdf_from_mesh(solid_ball(0.1, (0.0, 5.0, 0.0)), voxel_mm=10.0)
    pattern = tee_block()
    body = mannequin()
    garment = build_garment(pattern, top_arrangement(pattern, body), particle_distance=20.0)
    report = collision.contacts(garment, garment.points, field)
    assert report["inside"] == 0
    assert report["clear_mm"] > 1000.0


# -- symmetry ----------------------------------------------------------------


def test_the_tee_block_is_symmetric() -> None:
    for panel_id in ("FRONT", "BACK", "SLEEVE_L"):
        found = symmetry.detect_axis(tee_block().panel(panel_id))
        assert found.symmetric, f"{panel_id} is not symmetric"
        assert found.axis_x == pytest.approx(0.0, abs=1.0)


def test_syncing_makes_a_panel_symmetric_to_the_last_decimal() -> None:
    from seamkiln.pattern.geometry import Vertex

    panel = tee_block().panel("FRONT")
    nudged = list(panel.outline)
    nudged[3] = Vertex(nudged[3].x + 9.0, nudged[3].y, nudged[3].kind)
    from seamkiln.pattern.model import Panel

    lopsided = Panel(id="L", outline=nudged)
    assert not symmetry.detect_axis(lopsided).symmetric

    fixed = symmetry.sync(lopsided, keep="right")
    assert symmetry.detect_axis(fixed).symmetric
    assert symmetry.detect_axis(fixed).deviation_mm == pytest.approx(0.0, abs=1e-9)


def test_mirroring_the_mesh_is_faster_and_exactly_balanced() -> None:
    """Meshing a symmetric piece whole does the same work twice and gets two
    DIFFERENT answers: the lattice does not land the same way on both halves,
    so one piece ends up with different topology left and right."""
    from seamkiln.drape.triangulate import triangulate_panel

    panel = symmetry.sync(tee_block().panel("FRONT"))
    whole = triangulate_panel(panel, particle_distance=10.0)
    mirrored, info = symmetry.triangulate_symmetric(panel, particle_distance=10.0)

    points = mirrored.points
    reflected = points.copy()
    reflected[:, 0] = 2.0 * info["axis_x_mm"] - reflected[:, 0]
    worst = max(np.linalg.norm(points - row, axis=1).min() for row in reflected)
    assert worst == pytest.approx(0.0, abs=1e-9), "the mirrored mesh is not balanced"

    assert mirrored.triangles.shape[0] > 0
    assert abs(mirrored.n_points - whole.n_points) < whole.n_points * 0.15
    # the area still adds up: mirroring must not lose or double the piece
    p = mirrored.points
    a, b, c = p[mirrored.triangles[:, 0]], p[mirrored.triangles[:, 1]], p[mirrored.triangles[:, 2]]
    area = (
        0.5
        * np.abs(
            (b[:, 0] - a[:, 0]) * (c[:, 1] - a[:, 1]) - (c[:, 0] - a[:, 0]) * (b[:, 1] - a[:, 1])
        ).sum()
    )
    assert area == pytest.approx(panel.area_mm2, rel=0.02)


def test_an_asymmetric_panel_refuses_the_mirrored_mesher() -> None:
    from seamkiln.pattern.geometry import Vertex
    from seamkiln.pattern.model import Panel

    wedge = Panel(id="W", outline=[Vertex(0, 0), Vertex(300, 0), Vertex(40, 200)])
    with pytest.raises(symmetry.SymmetryError, match="not symmetric"):
        symmetry.triangulate_symmetric(wedge, particle_distance=15.0)


# -- locks -------------------------------------------------------------------


def test_a_lock_refuses_the_change_and_names_the_way_out() -> None:
    locks = Locks().add("panel:FRONT", "signed off")
    with pytest.raises(LockedError, match="'op': 'unlock'"):
        locks.check("panel:FRONT", "a pleat")
    locks.check("panel:BACK", "a pleat")  # not locked: no exception


def test_all_covers_everything_and_panels_covers_each_piece() -> None:
    assert Locks().add("all").covering("body") == "all"
    assert Locks().add("panels").covering("panel:FRONT") == "panels"
    assert Locks().add("panel:FRONT").covering("panel:BACK") is None
    with pytest.raises(ValueError, match="Lockable"):
        Locks().add("colour")


def test_a_locked_panel_stops_the_collective_operations_too() -> None:
    """Locking one piece has to stop a grade that would move it. Checking only
    the collective scope let exactly that through."""
    session = Session()
    session.apply(Command("block", {"block": "tee"}))
    session.apply(Command("lock", {"scope": "panel:FRONT", "reason": "signed off"}))

    for verb, args in (
        ("cut", {"panel": "FRONT", "op": "pleat", "at_x": 0.0, "depth_mm": 20.0}),
        ("grade", {"target": {"chest": 1050.0}}),
        ("allowance", {"mm": 10.0}),
    ):
        with pytest.raises(CommandError, match="locked"):
            session.apply(Command(verb, args))

    # precise, not blunt: an allowance aimed only at BACK is fine
    assert session.apply(Command("allowance", {"mm": 10.0, "panels": ["BACK"]}))


def test_locks_survive_a_replay() -> None:
    """A lock is set by a command like everything else, so a script that
    locked a panel at step 4 still locks it at step 4 when replayed."""
    session = Session()
    session.apply(Command("block", {"block": "tee"}))
    session.apply(Command("lock", {"scopes": ["fabric"], "reason": "chosen"}))
    replayed = Session.replay(session.script())
    assert replayed.lock_state.held == {"fabric"}
    assert replayed.fingerprint() == session.fingerprint()


def test_unlocking_lets_the_change_through() -> None:
    session = Session()
    session.apply(Command("block", {"block": "tee"}))
    session.apply(Command("lock", {"scope": "panels"}))
    with pytest.raises(CommandError, match="locked"):
        session.apply(Command("allowance", {"mm": 10.0}))
    session.apply(Command("unlock", {"scope": "panels"}))
    assert session.apply(Command("allowance", {"mm": 10.0}))
