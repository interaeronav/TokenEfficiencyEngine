"""P3 acceptance for interference, contact, clearance and the BOM on F6.

Pinned numbers (A66 P0a): d11 pin in the d10 hole interferes by 329.867 mm3
about (20, 20, 10); two 20 mm cubes at x = 0 and x = 19 share 400.000 mm3 at
(19.5, 10, 10); the d10 pin in the d10 hole is an exact fit - 0 mm3 with
contact - and the d9.9 pin clears by 0.050 mm; steel (7850 kg/m3) makes the
block 238.869 g and a pin 24.662 g, 337.517 g for the block and four pins.
"""

from __future__ import annotations

import time

import pytest

pytest.importorskip("OCP", reason="partkiln[brep] not installed")

from partkiln.assembly import (
    Assembly,
    Component,
    FrameRef,
    Mate,
    Pose,
    Ref,
    bom,
    clearance,
    interference,
    placed,
    report,
    solve,
)
from partkiln.assembly.interference import CONTACT_MM, FUZZY_MM, bodies_of
from partkiln.brep import fixtures, shapes
from partkiln.document import CommandError

pytestmark = pytest.mark.brep

BLOCK_MM3 = 30429.204
PIN_MM3 = 3141.593


@pytest.fixture(scope="module")
def f6():
    block, pin = fixtures.build_F6()
    return block, pin


# --------------------------------------------------------------------------- interference


def test_d11_pin_interferes_by_329_867(f6) -> None:
    block, _ = f6
    pin11 = shapes.cylinder(5.5, 40.0, (20.0, 20.0, -10.0))
    rows = interference([("block", block), ("pin", pin11)])
    assert rows == [
        {"a": "block", "b": "pin", "mm3": 329.867, "centroid": [20.0, 20.0, 10.0], "contact": False}
    ]


def test_two_cubes_at_x0_and_x19_share_400() -> None:
    a = shapes.box(20, 20, 20)
    b = shapes.box(20, 20, 20)
    rows = interference([("a", a, Pose()), ("b", b, Pose((19.0, 0.0, 0.0)))])
    assert rows == [
        {"a": "a", "b": "b", "mm3": 400.0, "centroid": [19.5, 10.0, 10.0], "contact": False}
    ]


def test_exact_fit_is_zero_interference_with_contact(f6) -> None:
    """The fuzzy policy, measured: OCCT 7.9.3's Common is EMPTY for the d10-in-d10
    fit with the fuzzy value at 0, so no sliver ever has to be filtered; the
    contact reading is the distance under 1e-6 mm."""
    block, pin = f6
    rows = interference([("block", block), ("pin", pin)])
    assert rows == [{"a": "block", "b": "pin", "mm3": 0.0, "centroid": None, "contact": True}]
    assert FUZZY_MM == 0.0 and CONTACT_MM == 1e-6
    assert interference([("block", block), ("pin", pin)], contact=False) == []


def test_d9_9_pin_clears_by_0_050(f6) -> None:
    block, _ = f6
    pin99 = shapes.cylinder(4.95, 40.0, (20.0, 20.0, -10.0))
    c = clearance(block, pin99)
    assert c["mm"] == 0.05 and c["contact"] is False
    assert len(c["points"]) == 2
    # the closest points are 0.05 apart, on the wall and on the pin
    p, q = c["points"]
    assert abs(((p[0] - q[0]) ** 2 + (p[1] - q[1]) ** 2 + (p[2] - q[2]) ** 2) ** 0.5 - 0.05) < 1e-3
    assert interference([("block", block), ("pin", pin99)]) == []


def test_bbox_prefilter_skips_far_pairs(f6) -> None:
    block, pin = f6
    far = placed(pin, Pose((500.0, 0.0, 0.0)))
    t0 = time.perf_counter()
    rows = interference([("block", block), ("far", far)])
    ms = (time.perf_counter() - t0) * 1000
    assert rows == []
    assert ms < 5.0, f"a skipped pair should cost nothing, took {ms:.1f} ms"


def test_solved_pose_places_the_pin_in_contact(f6) -> None:
    """Solver -> placed shape -> interference: the pin standing on the block
    (bottom on top) touches it along the rim: 0 mm3, contact True."""
    block, _ = f6
    pin = shapes.cylinder(5.0, 40.0)
    hole = FrameRef("axis", (20.0, 20.0, 20.0), (0.0, 0.0, 1.0), radius=5.0)
    top = FrameRef("plane", (20.0, 20.0, 20.0), (0.0, 0.0, 1.0))
    pin_axis = FrameRef("axis", (0.0, 0.0, 0.0), (0.0, 0.0, 1.0), radius=5.0)
    pin_bottom = FrameRef("plane", (0.0, 0.0, 0.0), (0.0, 0.0, -1.0))
    asm = Assembly(
        [
            Component("block", "block", block, grounded=True),
            Component("pin", "pin", pin, pose=Pose((3.0, -4.0, 7.0))),
        ]
    )
    asm.add_mate(Mate("insert1", "insert", Ref("block", hole), Ref("pin", pin_axis)))
    asm.add_mate(Mate("mate1", "mate", Ref("block", top), Ref("pin", pin_bottom)))
    r = solve(asm)
    asm.component("pin").pose = r.poses["pin"]
    rows = interference(bodies_of(asm))
    assert rows == [{"a": "block", "b": "pin", "mm3": 0.0, "centroid": None, "contact": True}]
    # push it 10 mm into the hole: the common is the hole volume it fills
    asm.component("pin").pose = Pose((20.0, 20.0, 10.0))
    rows = interference(bodies_of(asm))
    assert rows == [{"a": "block", "b": "pin", "mm3": 0.0, "centroid": None, "contact": True}]
    asm.component("pin").pose = Pose((20.0, 20.0, 10.0)).compose(
        Pose.from_axis_angle((1, 0, 0), 10.0)
    )
    rows = interference(bodies_of(asm))
    assert len(rows) == 1 and rows[0]["mm3"] > 0 and rows[0]["contact"] is False


def test_report_shape_matches_details_asm(f6) -> None:
    block, _ = f6
    pin99 = shapes.cylinder(4.95, 40.0, (20.0, 20.0, -10.0))
    pin11 = shapes.cylinder(5.5, 40.0, (20.0, 20.0, -10.0))
    far = shapes.cylinder(5.0, 40.0, (500.0, 0.0, 0.0))
    out = report([("block", block), ("pin", pin99), ("big", pin11), ("far", far)])
    assert out["interference"] == [
        {"a": "block", "b": "big", "mm3": 329.867, "centroid": [20.0, 20.0, 10.0]},
        {
            "a": "pin",
            "b": "big",
            "mm3": 3079.075,  # the d9.9 pin lies wholly inside the d11
            "centroid": [20.0, 20.0, 10.0],
        },
    ]
    assert out["contacts"] == []
    assert out["clearance_mm"] == {"block-pin": 0.05}
    assert out["contact_tol_mm"] == CONTACT_MM


def test_duplicate_body_name_refuses(f6) -> None:
    block, pin = f6
    with pytest.raises(CommandError) as e:
        interference([("block", block), ("block", pin)])
    assert e.value.code == "pk_ref_ambiguous"


# --------------------------------------------------------------------------- BOM


def four_pin_assembly(f6) -> Assembly:
    block, pin = f6
    comps = [Component("block", "block", block, grounded=True)]
    for i in range(4):
        comps.append(Component(f"pin{i + 1}", "pin", pin, pose=Pose((10.0 * i, 0.0, 0.0))))
    return Assembly(comps)


def test_bom_parts_view_block_and_four_pins(f6) -> None:
    block, pin = f6
    asm = four_pin_assembly(f6)
    parts = {
        "block": {"material": "steel", "volume_mm3": shapes.volume(block)},
        "pin": {
            "material": "steel",
            "volume_mm3": shapes.volume(pin),
            "standard_designation": "ISO 2338 10 m6 x 40",
        },
    }
    out = bom(asm, parts)
    assert [(r["part"], r["qty"]) for r in out["rows"]] == [("block", 1), ("pin", 4)]
    assert out["rows"][0]["mass_g"] == 238.869 and out["rows"][1]["mass_g"] == 24.662
    assert out["rows"][1]["total_g"] == 98.648
    assert out["rows"][1]["standard"] == "ISO 2338 10 m6 x 40"
    assert out["rows"][1]["components"] == ["pin1", "pin2", "pin3", "pin4"]
    assert out["total_g"] == 337.517 and out["count"] == 5
    assert all(r["kind"] == "part" for r in out["rows"])
    # a mass given directly is taken as-is (3 dp)
    direct = bom(
        asm, {"block": {"material": "steel", "mass_g": 238.8691}, "pin": {"mass_g": 24.6615}}
    )
    assert direct["total_g"] == 337.517


def test_bom_structured_view_lists_every_instance(f6) -> None:
    asm = four_pin_assembly(f6)
    parts = {"block": {"mass_g": BLOCK_MM3 * 7.85e-3}, "pin": {"mass_g": PIN_MM3 * 7.85e-3}}
    out = bom(asm, parts, view="structured")
    assert [r["components"] for r in out["rows"]] == [
        ["block"],
        ["pin1"],
        ["pin2"],
        ["pin3"],
        ["pin4"],
    ]
    assert [r["item"] for r in out["rows"]] == [1, 2, 3, 4, 5]
    assert out["total_g"] == 337.517


def test_bom_virtual_component_and_refusals(f6) -> None:
    asm = four_pin_assembly(f6)
    asm.add_component(Component("label", "object", virtual=True))
    parts = {"block": {"mass_g": 238.869}, "pin": {"mass_g": 24.662}}
    out = bom(asm, parts)
    assert out["rows"][2] == {
        "item": 3,
        "kind": "virtual",
        "part": "object",
        "qty": 1,
        "material": "none",
        "mass_g": 0.0,
        "total_g": 0.0,
        "standard": "",
        "components": ["label"],
    }
    assert out["total_g"] == 337.517
    with pytest.raises(CommandError) as e:
        bom(asm, {"block": {"mass_g": 1.0}})
    assert e.value.code == "pk_ref_unknown" and "'pin'" in str(e.value) and "block" in str(e.value)
    with pytest.raises(CommandError) as e:
        bom(asm, parts, view="tree")
    assert e.value.code == "pk_bad_op" and "parts, structured" in str(e.value)
    with pytest.raises(CommandError) as e:
        _ = asm.component("label").shape
    assert e.value.code == "pk_ref_empty"


def test_bom_row_with_no_material_is_none_and_the_total_says_partial(f6) -> None:
    """A mass that cannot be computed is `None`, never `0.000` (audited defect).

    A card with neither `mass_g` nor a `material` used to print `0.000 g` and
    add nothing to `total_g`: the bill understated the assembly by a whole
    part while looking precise to 3 dp. Now the row says `None`, the part is
    named in `missing_mass`, and `partial` marks the total as a lower bound.
    """
    block, pin = f6
    asm = Assembly(
        [
            Component("block", "block", block, grounded=True),
            Component("pin1", "pin", pin),
        ]
    )
    priced = {"material": "steel", "volume_mm3": shapes.volume(block)}
    out = bom(asm, {"block": priced, "pin": {"volume_mm3": shapes.volume(pin)}})
    rows = {r["part"]: r for r in out["rows"]}
    assert rows["block"]["mass_g"] == 238.869 and rows["block"]["total_g"] == 238.869
    assert rows["pin"]["mass_g"] is None and rows["pin"]["total_g"] is None
    assert rows["pin"]["material"] == "none"
    assert out["total_g"] == 238.869  # the block alone, and it says so
    assert out["partial"] is True and out["missing_mass"] == ["pin"]

    whole = bom(
        asm,
        {"block": priced, "pin": {"material": "steel", "volume_mm3": shapes.volume(pin)}},
    )
    assert whole["total_g"] == 263.531
    assert whole["partial"] is False and whole["missing_mass"] == []

    # structured view: every instance of the unpriced part is named once
    asm.add_component(Component("pin2", "pin", pin, pose=Pose((10.0, 0.0, 0.0))))
    each = bom(asm, {"block": priced, "pin": {}}, view="structured")
    assert [r["mass_g"] for r in each["rows"]] == [238.869, None, None]
    assert each["partial"] is True and each["missing_mass"] == ["pin"]
