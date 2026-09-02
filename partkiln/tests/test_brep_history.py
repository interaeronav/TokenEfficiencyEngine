"""P2a acceptance for partkiln.brep.history: the hand-built BRepTools_History."""

from __future__ import annotations

import pytest

pytest.importorskip("OCP", reason="partkiln[brep] not installed")

from partkiln.brep import fixtures, history, query, shapes

pytestmark = pytest.mark.brep


def _all_z(shape):
    return [e for e in query.edges(shape) if e.direction and abs(e.direction[2]) > 0.999]


def test_fillet_r2_history_matches_the_measured_fact() -> None:
    f1 = fixtures.build_F1()
    faces = query.faces(f1)
    edges = _all_z(f1)  # 4 corners + the seam
    res = shapes.fillet(f1, [e.shape for e in edges], 2.0)
    hm = history.record(res.algo, res.inputs)
    generated = [len(hm.generated(e.shape)) for e in edges]
    assert sorted(generated) == [0, 1, 1, 1, 1]
    assert generated[[e.is_seam for e in edges].index(True)] == 0  # the seam generates nothing
    modified = {
        f.surface_type: len(hm.modified(f.shape)) for f in faces if f.surface_type == "cylinder"
    }
    assert modified == {"cylinder": 0}  # the wall is untouched
    assert [len(hm.modified(f.shape)) for f in faces if f.surface_type == "plane"] == [1] * 6
    assert shapes.counts(f1)["faces"] == 7 and shapes.counts(res.shape)["faces"] == 11
    corner = next(e for e in edges if not e.is_seam)
    assert hm.is_removed(corner.shape)  # consumed by its fillet face
    assert query.faces(hm.generated(corner.shape)[0])[0].surface_type == "cylinder"


def test_boolean_history_is_merged_not_rebuilt() -> None:
    base = shapes.box(100, 60, 10)
    hole = shapes.cylinder(5, 12, (50, 30, -1))
    res = shapes.cut(base, [hole])
    hm = history.from_algo(res.history)
    base_faces = query.faces(base)
    split = [f for f in base_faces if len(hm.modified(f.shape)) == 1]
    assert sorted(round(f.normal[2]) for f in split) == [-1, 1]  # top and bottom were pierced
    assert all(not hm.is_removed(f.shape) for f in base_faces)
    hole_faces = query.faces(hole)
    assert [hm.is_removed(f.shape) for f in hole_faces if f.surface_type == "plane"] == [True, True]
    wall = next(f for f in hole_faces if f.surface_type == "cylinder")
    assert len(hm.modified(wall.shape)) == 1 and not hm.is_removed(wall.shape)


def test_follow_across_a_chain_of_maps() -> None:
    base = shapes.box(100, 60, 10)
    top = next(f for f in query.faces(base) if f.normal[2] > 0.99)
    cut = shapes.cut(base, [shapes.cylinder(5, 12, (50, 30, -1))])
    m1 = history.from_algo(cut.history)
    corners = [e for e in _all_z(cut.shape) if not e.is_seam]
    fil = shapes.fillet(cut.shape, [e.shape for e in corners], 2.0)
    m2 = history.record(fil.algo, fil.inputs)
    (final,) = history.follow(top.shape, [m1, m2])
    assert query.faces(final)[0].area == pytest.approx(
        5921.460 - 4 * (4 - 3.141592653589793), abs=5e-3
    )
    # an untouched sub-shape passes through, a consumed one leads to its child
    side = next(f for f in query.faces(base) if abs(f.normal[0]) > 0.99)
    assert len(history.follow(side.shape, [m1])) == 1
    assert history.follow(side.shape, [m1])[0].IsSame(side.shape)
    assert query.faces(history.follow(corners[0].shape, [m2])[0])[0].surface_type == "cylinder"
    # merge() chains a later map onto an earlier one
    chained = history.from_algo(cut.history).merge(m2)
    assert len(chained.modified(top.shape)) == 1 and chained.modified(top.shape)[0].IsSame(final)


def test_prism_and_transform_record_generated_and_modified() -> None:
    face = shapes.make_face_from_points([(0, 0, 0), (100, 0, 0), (100, 60, 0), (0, 60, 0)])
    res = shapes.prism(face, (0, 0, 10))
    hm = history.record(res.algo, res.inputs)
    edges = query.edges(face)
    assert all(len(hm.generated(e.shape)) == 1 for e in edges)  # each edge sweeps one side face
    assert all(query.faces(hm.generated(e.shape)[0])[0].surface_type == "plane" for e in edges)
    moved = shapes.transform(res.shape, translation=(5, 0, 0))
    hm2 = history.record(moved.algo, moved.inputs)
    for f in query.faces(res.shape):
        images = hm2.modified(f.shape)
        assert len(images) == 1 and not hm2.is_removed(f.shape)
        assert query.faces(images[0])[0].centroid[0] == pytest.approx(f.centroid[0] + 5, abs=1e-9)


def test_unsupported_types_are_silent_not_errors() -> None:
    hm = history.HistoryMap()
    b = shapes.box(1, 1, 1)
    assert hm.generated(b) == [] and hm.modified(b) == [] and not hm.is_removed(b)
    assert hm.successors(b) == [b]
