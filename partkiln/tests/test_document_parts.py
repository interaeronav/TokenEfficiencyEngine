"""P2c acceptance for the document's parts container: replay, fingerprints across
processes, the D3 snapshot cache and its replay fallback, lazy verb loading, and
what a diff carries (scalars, never coordinates)."""

from __future__ import annotations

import json
import math
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

import pytest

from partkiln.document import CommandError, Document

pytest.importorskip("OCP", reason="partkiln[brep] not installed")

pytestmark = pytest.mark.brep

SRC = Path(__file__).resolve().parents[1] / "src"


def F1() -> list[dict[str, Any]]:
    return [
        {"op": "create", "kind": "part", "name": "plate"},
        {
            "op": "create",
            "kind": "sketch",
            "name": "base",
            "props": {"plane": "XY", "profile": [{"rect": [100, 60], "tag": "r"}]},
        },
        {
            "op": "create",
            "kind": "extrude",
            "name": "plate",
            "props": {"sketch": "base", "distance": 10},
        },
        {
            "op": "create",
            "kind": "hole",
            "name": "hole1",
            "props": {"on": "plate.end", "at": [[50, 30]], "dia": 10},
        },
    ]


def F2() -> list[dict[str, Any]]:
    return [
        {"op": "param_set", "props": {"t": "6mm"}},
        {"op": "create", "kind": "part", "name": "bracket", "props": {"material": "steel_s275"}},
        {
            "op": "create",
            "kind": "sketch",
            "name": "base_sk",
            "props": {"plane": "XY", "profile": [{"rect": [80, 60], "tag": "r"}]},
        },
        {
            "op": "create",
            "kind": "extrude",
            "name": "base",
            "props": {"sketch": "base_sk", "distance": "t"},
        },
        {
            "op": "create",
            "kind": "sketch",
            "name": "up_sk",
            "props": {"plane": "XZ", "profile": [{"rect": [80, 40], "tag": "u"}]},
        },
        {
            "op": "create",
            "kind": "extrude",
            "name": "upright",
            "props": {"sketch": "up_sk", "distance": "t", "direction": "-"},
        },
        {
            "op": "create",
            "kind": "fillet",
            "name": "fillet1",
            "props": {"edges": "upright:edges(concave)", "r": 6},
        },
        {
            "op": "create",
            "kind": "hole",
            "name": "h",
            "props": {
                "on": "base.end",
                "at": [[20, 30], [60, 30], [20, 50], [60, 50]],
                "std": "M6 clearance normal",
            },
        },
    ]


def F3() -> list[dict[str, Any]]:
    return [
        {"op": "create", "kind": "part", "name": "shaft"},
        {
            "op": "create",
            "kind": "sketch",
            "name": "prof",
            "props": {
                "plane": "XY",
                "profile": [
                    {
                        "poly": [
                            [0, 0],
                            [0, 10],
                            [50, 10],
                            [50, 15],
                            [80, 15],
                            [80, 10],
                            [120, 10],
                            [120, 0],
                        ],
                        "tag": "p",
                    }
                ],
            },
        },
        {
            "op": "create",
            "kind": "revolve",
            "name": "shaft",
            "props": {"sketch": "prof", "axis": "X", "thread": "M20x2.5"},
        },
        {
            "op": "create",
            "kind": "plane",
            "name": "top",
            "props": {"offset": {"from": "XY", "distance": 15}},
        },
        {
            "op": "create",
            "kind": "sketch",
            "name": "key",
            "props": {
                "plane": "plane:top",
                "profile": [{"rect": [30, 6], "at": [50, -3], "tag": "k"}],
            },
        },
        {
            "op": "create",
            "kind": "extrude",
            "name": "keyway",
            "props": {"sketch": "key", "distance": 3.5, "direction": "-", "mode": "cut"},
        },
    ]


def F5() -> list[dict[str, Any]]:
    return [
        {"op": "create", "kind": "part", "name": "plate"},
        {
            "op": "create",
            "kind": "sketch",
            "name": "sk",
            "props": {"plane": "XY", "profile": [{"rect": [220, 220], "tag": "r"}]},
        },
        {
            "op": "create",
            "kind": "extrude",
            "name": "plate",
            "props": {"sketch": "sk", "distance": 12},
        },
        {
            "op": "create",
            "kind": "hole",
            "name": "h",
            "props": {"on": "plate.end", "at": [[20, 20]], "dia": 8},
        },
        {
            "op": "create",
            "kind": "pattern",
            "name": "p",
            "props": {"of": "h", "dx": 20, "nx": 10, "dy": 20, "ny": 10},
        },
    ]


def build(commands: list[dict[str, Any]], name: str = "doc") -> Document:
    doc = Document(name=name)
    for c in commands:
        doc.apply(c)
    return doc


# -- replay and determinism -------------------------------------------------------------


@pytest.mark.parametrize("script", [F1, F2, F3, F5])
def test_replay_of_every_verb_script_reproduces_the_fingerprint(script) -> None:
    doc = build(script())
    twin = Document.replay(json.loads(json.dumps(doc.script())))
    assert twin.fingerprint() == doc.fingerprint()
    assert twin.summary()["parts"][0]["volume_mm3"] == doc.summary()["parts"][0]["volume_mm3"]
    assert [f.id for f in twin.parts[next(iter(twin.parts))].features] == [
        f.id for f in doc.parts[next(iter(doc.parts))].features
    ]


def test_two_processes_agree_on_the_f2_fingerprint() -> None:
    doc = build(F2())
    code = (
        "import json, sys\n"
        "from partkiln.document import Document\n"
        "doc = Document.replay(json.loads(sys.stdin.read()))\n"
        "print(doc.fingerprint())\n"
    )
    out = subprocess.run(
        [sys.executable, "-c", code],
        input=json.dumps(doc.script()),
        capture_output=True,
        text=True,
        env={**os.environ, "PYTHONPATH": str(SRC)},
        check=True,
    )
    assert out.stdout.strip() == doc.fingerprint()


def test_replay_with_overrides_is_the_part_family() -> None:
    doc = build(F2())
    fat = Document.replay(doc.script(), overrides={"t": "8mm"})
    assert fat.parts["bracket"].summary()["volume_mm3"] == pytest.approx(58403.27, abs=5e-3)
    assert fat.fingerprint() != doc.fingerprint()


# -- lazy verbs and import hygiene ----------------------------------------------------------


def test_feature_verbs_load_lazily_and_import_partkiln_stays_ocp_free() -> None:
    code = (
        "import sys, partkiln, partkiln.document\n"
        "from partkiln.document import Document\n"
        "bad = lambda: sorted(m for m in sys.modules "
        "if m.split('.')[0] in ('OCP', 'tee', 'cadquery'))\n"
        "assert 'partkiln.features' not in sys.modules\n"
        "print(bad())\n"
        "d = Document(); d.apply({'op': 'create', 'kind': 'part', 'name': 'p'})\n"
        "assert 'partkiln.features' in sys.modules\n"
        "print(bad())\n"
    )
    out = subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True,
        text=True,
        env={"PYTHONPATH": str(SRC), "PATH": "/usr/bin:/bin"},
        check=True,
    )
    assert out.stdout.split("\n")[:2] == ["[]", "[]"], out.stdout


def test_unknown_kind_lists_the_feature_kinds() -> None:
    with pytest.raises(CommandError, match=r"extrude.*hole.*pattern") as excinfo:
        Document().apply({"op": "create", "kind": "spaceship"})
    assert excinfo.value.code == "pk_bad_op"


# -- the diff carries scalars only -----------------------------------------------------------


def _scan(value: Any, path: str = "") -> list[str]:
    """Paths of any list of >= 7 numbers or nested numeric lists (a coordinate dump)."""
    found: list[str] = []
    if isinstance(value, dict):
        for k, v in value.items():
            found.extend(_scan(v, f"{path}.{k}"))
    elif isinstance(value, list):
        if len(value) >= 7 and all(isinstance(x, int | float) for x in value):
            found.append(path)
        if value and all(
            isinstance(x, list) and all(isinstance(y, int | float) for y in x) for x in value
        ):
            found.append(path)
        for i, v in enumerate(value):
            found.extend(_scan(v, f"{path}[{i}]"))
    return found


def test_details_carry_assumed_resolved_names_and_no_coordinate_lists() -> None:
    doc = Document(name="f1")
    results = [doc.apply(c) for c in F1()]
    hole = results[-1]
    assert hole["assumed"]["depth"] == "through"
    assert hole["resolved"] == {"plate.end": 1}
    assert hole["selected"] == {"plate.end": ["plate.end"]}
    assert hole["names"] == ["hole1.1.wall"]
    assert hole["frame"] == {
        "origin": [0.0, 0.0, 10.0],
        "normal": [0.0, 0.0, 1.0],
        "x": [1.0, 0.0, 0.0],
    }
    for r in results:
        assert _scan(r) == [], r
        json.dumps(r)
    summary = doc.summary()
    assert _scan(summary) == []
    part = summary["parts"][0]
    assert part["id"] == "part:plate" and part["faces"] == 7 and part["edges"] == 15
    assert part["volume_mm3"] == pytest.approx(59214.602, abs=5e-4)
    assert part["com_mm"] == [50.0, 30.0, 5.0]
    assert [row["id"] for row in part["tree"]] == ["feat:plate", "feat:hole1"]
    assert len(json.dumps(summary)) < 2500  # a 2-feature part is a few hundred tokens


# -- D3: snapshot and restore -------------------------------------------------------------


def test_snapshot_fast_path_restores_shapes_and_names_without_regen(tmp_path: Path) -> None:
    doc = build(F2())
    snap = doc.snapshot("cp1", tmp_path)
    assert snap["brep"] is True and snap["commands"] == 8
    assert set(snap) == {"label", "path", "commands", "fingerprint", "brep", "caches"}
    json_path = Path(snap["path"])
    assert json_path.name.startswith("cp1-") and json_path.parent == tmp_path
    assert (tmp_path / f"{json_path.stem}-bracket.brep").is_file()
    payload = json.loads(json_path.read_text())
    assert set(payload["parts"]["bracket"]["names"]) >= {
        "base.end",
        "upright.end",
        "fillet1.face[0]",
        "h.4.wall",
    }
    t = time.perf_counter()
    twin = Document.restore(snap)
    dt = time.perf_counter() - t
    assert twin.restored_via == "cache"
    assert twin.fingerprint() == doc.fingerprint()
    part = twin.parts["bracket"]
    assert part.cached is True
    assert [f.status for f in part.features] == ["cached"] * 4
    assert part.summary()["volume_mm3"] == pytest.approx(44916.967, abs=5e-4)
    assert part.inventory().face_index("base.end") is not None  # names resolve by fingerprint
    assert dt < 0.05, f"fast path took {dt * 1000:.1f} ms (budget 5 ms warm; 50 ms with slack)"
    # the first edit rebuilds from 0 and lands on the same numbers
    r = twin.apply({"op": "set", "id": "feat:h", "props": {"std": "M8 clearance normal"}})  # 9 mm
    assert part.cached is False and r["failed"] == []
    assert part.summary()["volume_mm3"] == pytest.approx(
        44916.967 - 4 * math.pi * (4.5**2 - 3.3**2) * 6, abs=5e-3
    )


def test_snapshot_fast_path_is_fast_when_warm(tmp_path: Path) -> None:
    doc = build(F1())
    snap = doc.snapshot("cp", tmp_path)
    Document.restore(snap)  # warm the readers
    best = min(_timed_restore(snap) for _ in range(3))
    assert best < 0.005, f"best of 3 restores {best * 1000:.2f} ms > 5 ms"


def _timed_restore(snap: dict[str, Any]) -> float:
    t = time.perf_counter()
    Document.restore(snap)
    return time.perf_counter() - t


def test_restore_replays_when_a_brep_is_missing_or_the_fingerprint_mismatches(
    tmp_path: Path,
) -> None:
    doc = build(F1())
    snap = doc.snapshot("cp2", tmp_path)
    (tmp_path / f"{Path(snap['path']).stem}-plate.brep").unlink()
    twin = Document.restore(snap)
    assert twin.restored_via == "replay"
    assert twin.fingerprint() == doc.fingerprint()
    assert twin.parts["plate"].cached is False
    # a tampered fingerprint: the replay wins, and the mismatch is reported
    snap3 = doc.snapshot("cp3", tmp_path)
    payload = json.loads(Path(snap3["path"]).read_text())
    payload["fingerprint"] = "0000000000000000"
    Path(snap3["path"]).write_text(json.dumps(payload))
    with pytest.raises(CommandError, match="edited or written by another") as excinfo:
        Document.restore(snap3)
    assert excinfo.value.code == "pk_checkpoint_mismatch"
    with pytest.raises(CommandError, match="tee_purge") as excinfo:
        Document.restore({"path": str(tmp_path / "nope.json")})
    assert excinfo.value.code == "pk_checkpoint_missing"
    with pytest.raises(CommandError) as excinfo:
        Document.restore({})
    assert excinfo.value.code == "pk_needs"


# -- Law 16 and the dependents hook ------------------------------------------------------


def test_a_refused_feature_never_advances_state() -> None:
    doc = build(F1())
    before = doc.fingerprint()
    with pytest.raises(CommandError):
        doc.apply(
            {
                "op": "create",
                "kind": "fillet",
                "name": "f",
                "props": {"edges": "plate:edges(dir=Z)", "r": 40},
            }
        )
    assert doc.fingerprint() == before
    assert [f.id for f in doc.parts["plate"].features] == ["plate", "hole1"]
    assert len(doc.history) == 4


def test_dependents_and_delete_through_the_document() -> None:
    doc = build(F1())
    assert doc.dependents_of("sk:base") == ["feat:plate"]
    assert doc.dependents_of("feat:plate") == ["feat:hole1"]
    with pytest.raises(CommandError, match="feat:plate") as excinfo:
        doc.apply({"op": "delete", "id": "sk:base"})
    assert excinfo.value.code == "pk_delete_blocked"
    r = doc.apply({"op": "delete", "id": "feat:hole1"})
    assert r["deleted"] == ["feat:hole1"] and r["volume_mm3"] == 60000.0
    r = doc.apply({"op": "delete", "id": "sk:base", "props": {"cascade": True}})
    assert r["cascaded"] == ["feat:plate"]
    assert doc.parts["plate"].features == [] and doc.parts["plate"].shape is None


def test_multiple_parts_need_naming_and_summary_lists_both() -> None:
    doc = Document()
    doc.apply({"op": "create", "kind": "part", "name": "a"})
    doc.apply({"op": "create", "kind": "part", "name": "b", "props": {"material": "steel"}})
    doc.apply(
        {
            "op": "create",
            "kind": "sketch",
            "name": "s",
            "props": {"plane": "XY", "profile": {"rect": [10, 10]}},
        }
    )
    with pytest.raises(CommandError, match="part: <name>") as excinfo:
        doc.apply({"op": "create", "kind": "extrude", "props": {"sketch": "s", "distance": 5}})
    assert excinfo.value.code == "pk_part_ambiguous"
    doc.apply(
        {"op": "create", "kind": "extrude", "props": {"sketch": "s", "distance": 5, "part": "b"}}
    )
    rows = doc.summary()["parts"]
    assert [r["id"] for r in rows] == ["part:a", "part:b"]
    assert rows[1]["mass_g"] == pytest.approx(500 * 7850 * 1e-6, abs=1e-3)
    assert rows[0]["volume_mm3"] == 0.0


def test_discarding_a_checkpoint_removes_its_brep_caches(tmp_path: Path) -> None:
    """DEFECT 8: `snapshot()` wrote `<stem>-<part>.brep` siblings and reported
    only a BOOL, so `LocalKernel.discard()` - which unlinks `path` and whatever
    `files`/`breps` the payload names - left every cache on disk forever.

    D3: the script is the checkpoint and the B-rep is a cache; a cache the
    owner cannot name is a leak.
    """
    from partkiln.client import LocalKernel

    doc = build(F2())
    snap = doc.snapshot("cp_discard", tmp_path)
    assert snap["brep"] is True
    assert snap["caches"] == [f"{Path(snap['path']).stem}-bracket.brep"]
    assert sorted(p.name for p in tmp_path.iterdir()) == sorted(
        [Path(snap["path"]).name, *snap["caches"]]
    )
    kernel = LocalKernel()
    kernel.discard(snap)
    assert list(tmp_path.iterdir()) == []
    kernel.discard(snap)  # discarding twice is not an error
