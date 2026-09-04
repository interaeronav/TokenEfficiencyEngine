"""The partkiln adapter (A66 P4): mechanical CAD through the existing 17 tools.

The claim under test is the same one seamkiln made and this campaign inherits:
a whole product - sketches, features, parts, assemblies, drawings, exports -
arrives, and the always-loaded tool list does not move, because a part is a
scene and the `Adapter` protocol already knows how to drive one.

Everything here runs on `FakeKernel` (arithmetic, no OCP, no subprocess), so
the contract is proved on any machine. `test_partkiln_live.py` runs the same
shapes against the real kernel where one is installed.
"""

from __future__ import annotations

import tempfile
from typing import Any

import pytest
from fixtures_partkiln import FakeKernel

from tee.adapters.partkiln import PartkilnAdapter
from tee.app import TeeApp
from tee.kernel.adapter import Adapter
from tee.kernel.contract import AdapterContract
from tee.kernel.errors import TeeError

PK_TOOLS = (
    "pk_probe",
    "pk_verbs",
    "pk_lint",
    "pk_query",
    "pk_measure",
    "pk_check",
    "pk_standards",
    "pk_materials",
    "pk_bom",
    "pk_drawing",
    "pk_export",
    "pk_flat",
    "pk_import",
    "pk_script",
)

# W1, trimmed to what the fake models: the ops the benchmark and the live
# test both send, so a change in translation breaks here first.
W1 = [
    {"op": "param_set", "props": {"W": "120mm", "H": "80mm", "T": "10mm"}},
    {"op": "create", "kind": "part", "name": "bracket", "props": {"material": "steel_s275"}},
    {
        "op": "create",
        "kind": "sketch",
        "name": "base",
        "props": {"plane": "XY", "profile": [{"rect": ["W", "H"], "tag": "outer"}]},
    },
    {
        "op": "create",
        "kind": "extrude",
        "name": "plate",
        "props": {"sketch": "base", "distance": "T"},
    },
    {
        "op": "create",
        "kind": "hole",
        "name": "h",
        "props": {
            "on": "plate.end",
            "at": [[-50, -25], [50, -25], [-50, 25], [50, 25]],
            "std": "M6 clearance normal",
        },
    },
    {
        "op": "create",
        "kind": "fillet",
        "name": "f1",
        "props": {"edges": "plate:edges(dir=Z)", "r": "5mm"},
    },
]


@pytest.fixture
def app(tmp_path):
    return TeeApp(
        {"partkiln": PartkilnAdapter(tmp_path, kernel=FakeKernel())}, project_root=tmp_path
    )


@pytest.fixture
def adapter(app):
    return app.adapters["partkiln"]


class TestPartkilnAdapterContract(AdapterContract):
    """The packaged kernel contract, on a kernel made of arithmetic.

    A fresh temp dir per adapter because `snapshot()` writes a real
    checkpoint file - the contract's round trip must exercise the file path,
    not a mock of it."""

    def make_adapter(self) -> Any:
        return PartkilnAdapter(
            tempfile.mkdtemp(prefix="tee-partkiln-contract-"), kernel=FakeKernel()
        )


# -- the adapter itself --------------------------------------------------------


def test_it_is_an_adapter(adapter) -> None:
    assert isinstance(adapter, Adapter)
    assert adapter.probe() is True
    info = adapter.info()
    assert info.id == "partkiln"
    assert info.to_payload()["mode"] == "injected"


def test_a_bracket_becomes_entities_with_stable_ids(adapter) -> None:
    diff = adapter.execute(W1)
    assert diff.created == ["part:bracket", "sk:base", "feat:plate", "feat:h", "feat:f1"]
    # The body is CREATED here, so it never doubles as "modified" - but its
    # regenerated numbers still reach the diff, which is what a caller reads.
    assert "part:bracket" not in diff.modified
    assert diff.details["part:bracket"]["volume_mm3"] == pytest.approx(94_416.920, abs=1e-3)

    ids = {e.id for e in adapter.list_entities()}
    assert {"doc", "part:bracket", "sk:base", "feat:plate", "feat:h", "feat:f1"} <= ids
    assert adapter.list_entities() == adapter.list_entities()  # stable across calls


def test_the_diff_carries_the_numbers_and_the_assumptions(adapter) -> None:
    """W1's expectations, from the plan: the plate is 120x80x10, the four M6
    clearance holes come from ISO 273 with their source named, and the fillet
    reports how many edges its selector actually caught."""
    diff = adapter.execute(W1)
    plate = diff.details["feat:plate"]
    assert plate["delta_mm3"] == pytest.approx(96_000.0)
    hole = diff.details["feat:h"]
    assert hole["assumed"]["depth"] == "through"
    assert "ISO 273" in hole["assumed"]["dia"] and "Apache-2.0" in hole["assumed"]["dia"]
    assert hole["delta_mm3"] == pytest.approx(-1368.478, abs=1e-3)
    assert diff.details["feat:f1"]["resolved"] == {"plate:edges(dir=Z)": 4}
    body = next(e for e in adapter.list_entities() if e.id == "part:bracket")
    assert body.summary["material"] == "steel_s275"
    assert body.summary["volume_mm3"] == pytest.approx(94_416.920, abs=1e-3)


def test_entities_carry_scalars_not_geometry(adapter) -> None:
    adapter.execute(W1)
    body = next(e for e in adapter.list_entities() if e.id == "part:bracket")
    assert set(body.summary) >= {"volume_mm3", "faces", "edges", "valid"}
    assert set(body.concise()) <= {"id", "name", "kind", "parent"}
    assert "raw" not in body.summary and "outline" not in body.summary
    assert len(repr(body.detailed())) < 400


def test_every_created_id_reaches_upserts(adapter) -> None:
    """The SceneCache goes blind otherwise (the A65 lesson): an entity the
    diff created but never upserted is invisible to tee_scene_summary until
    a full refresh."""
    diff = adapter.execute(W1)
    upserted = {e.id for e in diff.upserts}
    assert set(diff.created) <= upserted
    assert set(diff.modified) <= upserted
    assert all(e.kind and e.name for e in diff.upserts)


def test_a_failing_op_rolls_the_whole_batch_back(adapter) -> None:
    """Law 16 through two layers: the kernel restores its own state, and the
    adapter says so in the refusal rather than leaving the caller to guess."""
    adapter.execute(W1[:4])
    before = adapter.kernel.fingerprint()
    with pytest.raises(TeeError) as excinfo:
        adapter.execute(
            [
                {
                    "op": "create",
                    "kind": "extrude",
                    "name": "second",
                    "props": {"sketch": "base", "distance": "4mm"},
                },
                {
                    "op": "create",
                    "kind": "fillet",
                    "name": "nope",
                    "props": {"edges": "plate:edges(dir=Z)"},
                },  # r has no safe default
            ]
        )
    assert excinfo.value.code == "pk_needs"
    assert "rolled the batch back" in (excinfo.value.fix or "")
    assert adapter.kernel.fingerprint() == before
    assert all(e.id != "feat:second" for e in adapter.list_entities())


def test_export_and_check_run_as_methods_when_they_are_not_verbs(adapter, tmp_path) -> None:
    """The kernel's verb set is closed and asked for once; `export`/`check`
    that it does not register run after the apply, on the finished document."""
    out = tmp_path / "bracket.step"
    diff = adapter.execute([*W1, {"op": "export", "props": {"format": "step", "out": str(out)}}])
    assert out.is_file()
    assert diff.details["export:bracket.step"]["roundtrip"] == {"volume_ok": True}
    assert any("exported step" in note for note in diff.notes)
    assert [c[0] for c in adapter.kernel.calls if c[0] == "export"] == ["export"]


def test_a_parameter_edit_reports_its_blast_radius(adapter) -> None:
    """Law 14: an edit answers with changed/unchanged per downstream feature,
    not with the new world."""
    adapter.execute(W1)
    diff = adapter.execute([{"op": "param_set", "props": {"T": "12mm"}}])
    report = diff.details["part:bracket"]
    assert [row["feature"] for row in report["changed"]] == ["plate", "h", "f1"]
    assert report["failed"] == []
    assert report["volume_mm3"] == pytest.approx(113_300.304, abs=1e-3)
    assert diff.details["param:T"] == {"old": 10.0, "new": 12.0}


def test_checkpoint_and_rollback_round_trip(adapter) -> None:
    adapter.execute(W1)
    kept = adapter.kernel.fingerprint()
    payload = adapter.snapshot("bracket")
    assert payload["brep"] is False and payload["commands"] == len(W1)

    adapter.execute([{"op": "delete", "id": "feat:f1"}])
    assert all(e.id != "feat:f1" for e in adapter.list_entities())

    adapter.restore(payload)
    assert adapter.kernel.fingerprint() == kept
    assert any(e.id == "feat:f1" for e in adapter.list_entities())

    adapter.discard_snapshot(payload)
    assert not __import__("pathlib").Path(payload["path"]).exists()


def test_capture_refuses_and_names_the_three_text_routes(adapter) -> None:
    with pytest.raises(TeeError) as excinfo:
        adapter.capture("front", 200_000)
    assert excinfo.value.code == "pk_capture_text_first"
    for route in ("pk_drawing", "pk_measure", "tee_entity_detail"):
        assert route in excinfo.value.fix


def test_every_refusal_names_the_fix(adapter) -> None:
    for batch, needle in (
        ([{"op": "frobnicate"}], "partkiln accepts"),
        ([{"op": "create"}], "pk_verbs"),
        ([{"op": "delete"}], "cascade"),
        ([{"op": "param_set", "props": {}}], "param_set"),
        (
            [
                {
                    "op": "create",
                    "kind": "extrude",
                    "name": "x",
                    "props": {"sketch": "nope", "distance": "1mm"},
                }
            ],
            "create the sketch first",
        ),
    ):
        with pytest.raises(TeeError) as excinfo:
            adapter.execute(batch)
        assert excinfo.value.code and needle in excinfo.value.fix, excinfo.value.fix


def test_a_bad_unit_is_named_with_the_ones_that_work(adapter) -> None:
    with pytest.raises(TeeError) as excinfo:
        adapter.execute(
            [
                {
                    "op": "create",
                    "kind": "sketch",
                    "name": "s",
                    "props": {"profile": {"rect": ["12 mils", 10]}},
                }
            ]
        )
    assert excinfo.value.code == "pk_unit_unknown"
    assert "inch" in excinfo.value.fix and "mm" in excinfo.value.fix


# -- the surface promise -------------------------------------------------------


def test_the_surface_does_not_move(app) -> None:
    """A66's architectural claim, as an assertion: fourteen new tools, zero
    new always-loaded ones."""
    from tee.server import _DESC

    assert len(_DESC) == 17, "the always-loaded surface moved"
    assert not any(name.startswith("pk_") for name in _DESC)
    assert set(PK_TOOLS) <= set(app.registry.names())


def test_all_fourteen_are_tabled_in_the_trust_kernel(app) -> None:
    """An untabled tool raises at STARTUP, so building the app at all is most
    of this assertion; the tiers are pinned because a writer inheriting the
    open read tier is exactly the A45 failure this table exists to prevent."""
    from tee.kernel import trust

    tiers = {name: trust.capability_for(name) for name in PK_TOOLS}
    assert tiers == {
        "pk_probe": "read-compute",
        "pk_verbs": "read-scene",
        "pk_lint": "read-compute",
        "pk_query": "read-scene",
        "pk_measure": "read-compute",
        "pk_check": "read-compute",
        "pk_standards": "read-compute",
        "pk_materials": "read-compute",
        "pk_bom": "read-scene",
        "pk_drawing": "write-artifacts",
        "pk_export": "write-artifacts",
        "pk_flat": "write-artifacts",
        "pk_import": "write-scene",
        "pk_script": "write-scene",
    }
    assert not any(prefix.startswith("pk_") for prefix, _ in trust._FAMILY)


def test_the_tool_descriptions_pay_their_way(app) -> None:
    """The search row price is the first line; the registry caps it at 150,
    and a first line that needed capping was written wrong."""
    for name in PK_TOOLS:
        tool = app.registry._tools[name]
        first = tool.description.splitlines()[0]
        assert len(first) <= 150, f"{name}: {len(first)} chars"
        assert tool.one_line == first
        assert tool.examples, f"{name} has no example"
        assert "partkiln" in tool.tags


def test_mechanical_queries_land_the_right_tool_top_three(app) -> None:
    """D9's ranking pins. Progressive disclosure only works if the search
    finds the tool - an unreachable capability is an absent one (A65)."""
    for query, want in (
        ("extrude a sketch", "pk_verbs"),
        ("add a fillet", "pk_verbs"),
        ("mate two parts", "pk_verbs"),
        ("drawing with dimensions", "pk_drawing"),
        ("export STEP", "pk_export"),
        ("hand off part to blender", "pk_export"),
        ("bill of materials", "pk_bom"),
        ("sheet metal flat pattern", "pk_flat"),
        ("clearance hole for M6 bolt", "pk_standards"),
        ("assembly interference check", "pk_measure"),
    ):
        names = [item["name"] for item in app.registry.search(query, limit=3)["items"]]
        assert want in names, f"{query!r} found {names}"


# -- the tools --------------------------------------------------------------------


def test_the_long_tail_answers_through_the_adapter(app, tmp_path) -> None:
    adapter = app.adapters["partkiln"]
    adapter.execute(W1)

    health = app.registry.call("pk_probe", {})
    assert health["mode"] == "injected" and health["units"].startswith("mm")
    assert "OCCT-exception-1.0" in health["licence"]["occt"]
    assert "py-slvs" in health["licence"]["never_in_process"]

    assert app.registry.call("pk_verbs", {})["verbs"] == ["create", "delete", "param_set", "set"]
    assert app.registry.call("pk_query", {"selector": "plate:edges(dir=Z)"})["count"] == 4
    mass = app.registry.call("pk_measure", {"what": "mass", "of": "part:bracket"})
    assert mass["mass_g"] == pytest.approx(741.2, abs=0.5)
    assert app.registry.call("pk_standards", {"size": "M6"})["dia_mm"] == 6.6
    assert app.registry.call("pk_materials", {"name": "steel_s275"})["density_kg_m3"] == 7850.0
    assert app.registry.call("pk_bom", {"parts_only": True})["parts"] == 1
    sheet = app.registry.call("pk_drawing", {"of": "part:bracket", "out": str(tmp_path / "s.svg")})
    assert (tmp_path / "s.svg").is_file() and sheet["projected_agree"] is True
    assert app.registry.call("pk_script", {})["commands"]


def test_pk_lint_never_applies_anything(app) -> None:
    """The pre-flight's whole value is that it is free: a spy on the kernel's
    `apply` proves the lint path never reaches it."""
    adapter = app.adapters["partkiln"]
    before = len(adapter.kernel.applied)
    report = app.registry.call(
        "pk_lint",
        {
            "batch": [
                {"op": "knit"},
                {"op": "create", "kind": "extrude", "props": {"distance": "12 mils"}},
            ]
        },
    )
    assert len(adapter.kernel.applied) == before, "lint applied a command"
    assert report["ok"] is False
    codes = {p["code"] for p in report["problems"]}
    assert codes == {"pk_bad_op", "pk_unit_unknown"}
    with pytest.raises(TeeError, match="must be array"):
        app.registry.call("pk_lint", {"batch": "create a plate"})
    with pytest.raises(TeeError, match="pk_lint needs batch"):
        app.registry.call("pk_lint", {})


def test_a_tool_without_an_adapter_says_which_one_is_missing(tmp_path) -> None:
    """Two different absences, two different answers: a server with no
    partkiln adapter is not the same problem as a machine with no kernel, and
    a caller can only fix the one they are actually in."""
    from tee.kernel.adapter import FakeAdapter

    app = TeeApp({"fake": FakeAdapter()}, project_root=tmp_path)
    with pytest.raises(TeeError) as excinfo:
        app.registry.call("pk_verbs", {})
    assert excinfo.value.code in ("pk_not_served", "pk_kernel_absent")
    if excinfo.value.code == "pk_not_served":
        assert "--adapter partkiln" in excinfo.value.fix
    else:
        assert "sidecars/partkiln" in excinfo.value.fix
