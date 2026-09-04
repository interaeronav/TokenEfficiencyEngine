"""The standards tables and material cards: every number has a row and a paper trail.

"Clearance hole for an M6 bolt" is the question a model answers from memory
wrongly (6.5? 6.4? 6.6?). These tests pin the answers to bd_warehouse's ISO
273 row (6.6 normal, 6.4 close, 7.0 loose) and pin that every answer carries
its authority, source URL and licence, so the number can be checked rather
than trusted. Row counts are pinned to what the manifest says was retrieved:
a table that silently grew or shrank is a different table.
"""

from __future__ import annotations

import pytest

from partkiln import data, materials, standards
from partkiln.document import CommandError

# Rows per shipped CSV, as the manifest notes record them on retrieval.
ROW_COUNTS = {
    "clearance_holes.csv": 90,
    "tap_holes.csv": 99,
    "drill_sizes.csv": 106,
    "iso4762.csv": 57,
    "iso4014_4017.csv": 29,
    "iso4032.csv": 31,
    "iso7089.csv": 33,
    "iso261_pitch.csv": 532,
}


# --- the loader ---------------------------------------------------------------------


def test_every_csv_has_the_retrieved_row_count() -> None:
    shipped = [f for f in data.shipped_files() if f.endswith(".csv")]
    assert sorted(shipped) == sorted(ROW_COUNTS)
    for name, expected in ROW_COUNTS.items():
        rows = data.load_table(name)
        assert len(rows) == expected, f"{name}: {len(rows)} rows, manifest says {expected}"
        assert all(rows[0]), f"{name}: an empty header cell after stripping"


def test_load_table_hands_out_copies() -> None:
    """A caller that edits a row must not poison the cached table (determinism)."""
    rows = data.load_table("clearance_holes.csv")
    rows[0]["Normal"] = 999.0
    assert data.load_table("clearance_holes.csv")[0]["Normal"] != 999.0


def test_blank_cells_stay_blank_not_zero() -> None:
    rows = data.load_table("iso4032.csv")
    m18 = next(r for r in rows if r["Size"] == "M1.8-0.35")
    assert m18["iso4032:m"] == ""  # ISO 4032 does not table M1.8
    assert m18["iso4035:m"] == 1.1


def test_data_error_is_a_command_error() -> None:
    assert issubclass(data.DataError, CommandError)
    with pytest.raises(CommandError) as excinfo:
        data.load_table("nope.csv")
    assert excinfo.value.code == "pk_not_served"
    assert "manifest.json" in str(excinfo.value)


# --- standards lookups ---------------------------------------------------------------


def test_clearance_hole_m6() -> None:
    row = standards.clearance_hole("M6")
    assert (row["dia_mm"], row["close_mm"], row["normal_mm"], row["loose_mm"]) == (
        6.6,
        6.4,
        6.6,
        7.0,
    )
    assert row["series"] == "normal"
    assert standards.clearance_hole("M6", "close")["dia_mm"] == 6.4
    assert standards.clearance_hole(6, "LOOSE")["dia_mm"] == 7.0
    assert row["authority"] == "ISO 273:1979"
    assert row["licence"] == "Apache-2.0"
    assert row["source"].startswith("https://raw.githubusercontent.com/gumyr/bd_warehouse/")


def test_clearance_refusals_name_the_fix() -> None:
    with pytest.raises(CommandError, match="close, normal, loose"):
        standards.clearance_hole("M6", "snug")
    with pytest.raises(CommandError) as excinfo:
        standards.clearance_hole("M6.5")
    assert "Nearest tabled: M6, M7, M5" in str(excinfo.value)
    assert excinfo.value.code == "pk_ref_unknown"


@pytest.mark.parametrize(
    ("text", "parsed"),
    [
        ("M6", (6.0, None)),
        ("m6", (6.0, None)),
        ("M6x1", (6.0, 1.0)),
        ("M6-1", (6.0, 1.0)),
        ("m6 X 1.0", (6.0, 1.0)),
        ("M6\u00d71", (6.0, 1.0)),  # a typed multiplication sign
        ("M1.6-0.35", (1.6, 0.35)),
        (6, (6.0, None)),
        (2.5, (2.5, None)),
    ],
)
def test_designations_parse_tolerantly(
    text: str | float, parsed: tuple[float, float | None]
) -> None:
    assert standards.parse_designation(text) == parsed


def test_bad_designation_refuses() -> None:
    with pytest.raises(CommandError, match=r"M6x0\.75"):
        standards.parse_designation("bolt")
    assert standards.size_key(6.0) == "M6"
    assert standards.size_key(1.6) == "M1.6"


def test_pitch_coarse_and_fine() -> None:
    coarse = standards.pitch("M6")
    assert (coarse["pitch_mm"], coarse["series"], coarse["designation"]) == (1.0, "coarse", "M6")
    assert coarse["licence"] == "BSD-3-Clause"  # threadlib
    fine = standards.pitch("M6x0.75")
    assert (fine["pitch_mm"], fine["series"]) == (0.75, "fine")
    with pytest.raises(CommandError, match="Tabled pitches"):
        standards.pitch("M6x0.9")
    with pytest.raises(CommandError, match=r"M0\.25x<pitch>"):
        standards.pitch("M0.25")  # never listed bare by threadlib: unlabelled, so no guess
    with pytest.raises(CommandError, match="Nearest tabled"):
        standards.pitch("M6.3")


def test_tap_drill_resolves_a_bare_size_through_iso_261() -> None:
    row = standards.tap_drill("M6")
    assert (row["size"], row["pitch_mm"], row["drill_mm"], row["soft_mm"], row["hard_mm"]) == (
        "M6x1",
        1.0,
        5.0,
        5.0,
        5.4,
    )
    assert standards.tap_drill("M6x0.75")["drill_mm"] == 5.25
    with pytest.raises(CommandError, match="Tabled for this nominal"):
        standards.tap_drill("M6x0.5")


def test_fasteners_by_standard() -> None:
    shcs = standards.fastener("ISO 4762", "M6")
    assert (shcs["dk"], shcs["k"], shcs["s"], shcs["t"]) == (10.22, 6.0, 5.0, 3.0)
    assert (shcs["short"], shcs["long"], shcs["pitch_mm"], shcs["units"]) == (8.0, 60.0, 1.0, "mm")
    assert shcs["licence"] == "Apache-2.0"
    hex_bolt = standards.fastener("iso4014", "M10")  # spacing and case are the model's
    assert (hex_bolt["standard"], hex_bolt["k"], hex_bolt["s"]) == ("ISO 4014", 6.4, 16.0)
    nut = standards.fastener("ISO 4032", "M6")
    assert (nut["m"], nut["s"]) == (5.2, 10.0)
    washer = standards.fastener("ISO 7089", "M6")
    assert (washer["d1"], washer["d2"], washer["h"], washer["pitch_mm"]) == (6.4, 12.0, 1.8, None)


def test_fastener_refusals() -> None:
    with pytest.raises(CommandError) as excinfo:
        standards.fastener("ISO 4033", "M1.6")  # style 2 nuts start at M5
    assert "does not table M1.6" in str(excinfo.value)
    assert "Nearest tabled: M5" in str(excinfo.value)
    with pytest.raises(CommandError) as excinfo:
        standards.fastener("DIN 912", "M6")
    message = str(excinfo.value)
    assert "Supported:" in message
    for name in standards.supported_standards():
        assert name in message
    assert standards.supported_standards() == sorted(standards.supported_standards())


def test_drill_sizes_in_both_units() -> None:
    seven = standards.drill_size("#7")
    assert (seven["dia_in"], seven["dia_mm"]) == (0.201, 5.105)
    assert standards.drill_size("a")["dia_mm"] == 5.944
    with pytest.raises(CommandError, match="A-Z"):
        standards.drill_size("#99")


# --- material cards -----------------------------------------------------------------------


def test_every_card_validates_and_carries_an_honesty_tier() -> None:
    cards = materials.cards()
    assert [c["name"] for c in cards] == materials.names() == sorted(materials.names())
    for card in cards:
        assert "density" in card["properties"], card["name"]
        for prop, leaf in card["properties"].items():
            assert leaf["honesty"] in materials.HONESTY_TIERS, (card["name"], prop)
            assert leaf["source"] and leaf["unit"], (card["name"], prop)
            if leaf["honesty"] == "typical_range":
                low, high = leaf["range"]
                assert low <= leaf["value"] <= high, (card["name"], prop)


def test_structural_steel_is_the_standard_value() -> None:
    steel = materials.card("steel")
    assert steel["name"] == "steel_s275"
    density = steel["properties"]["density"]
    assert (density["value"], density["unit"], density["honesty"]) == (
        7850,
        "kg/m3",
        "standard_value",
    )
    assert "EN 1993-1-1" in density["source"]
    assert steel["properties"]["E"]["value"] == 210000
    assert steel["properties"]["yield"]["value"] == 275
    assert materials.card("100cr6")["properties"]["density"]["honesty"] == "datasheet"
    assert materials.card("100cr6")["properties"]["density"]["value"] == 7810
    assert materials.resolve("304") == "stainless_1_4301"
    assert materials.resolve("6061") == "aluminium_6061"


def test_mass_g_is_rounded_before_the_wire() -> None:
    assert materials.mass_g("steel", 91158.6) == 715.595  # the W1 bracket
    assert materials.mass_g("s275", 44916.967) == 352.598  # F2
    assert materials.mass_g("6061", 1_000_000) == 2700.0  # a litre of aluminium
    with pytest.raises(CommandError, match="never negative"):
        materials.mass_g("steel", -1.0)


def test_unknown_material_lists_the_cards() -> None:
    with pytest.raises(CommandError) as excinfo:
        materials.resolve("unobtainium")
    message = str(excinfo.value)
    assert excinfo.value.code == "pk_ref_unknown"
    for name in materials.names():
        assert name in message


def test_describe_is_one_line_per_value() -> None:
    described = materials.describe("dc01")
    assert described["values"]["density"] == 7850
    assert described["honesty"]["yield"] == "typical_range"
    assert described["ranges"]["yield"] == [140, 280]
    assert any(line.startswith("yield = 210 N/mm2 (typical_range") for line in described["notes"])
    assert len(described["notes"]) == len(described["values"]) + 1  # + the card's own note


def test_a_card_without_a_source_is_refused(monkeypatch: pytest.MonkeyPatch) -> None:
    broken = {
        "cards": {
            "x": {"properties": {"density": {"value": 1, "unit": "kg/m3", "honesty": "derived"}}}
        }
    }
    monkeypatch.setattr(materials, "load_json", lambda name: broken)
    materials._cards.cache_clear()
    try:
        with pytest.raises(data.DataError, match="lacks 'source'"):
            materials.names()
    finally:
        materials._cards.cache_clear()


def test_asme_b18_3_is_reachable_by_the_sizes_its_rows_use() -> None:
    """`supported_standards()` advertised ASME B18.3 but no input could reach a row.

    Its columns are filled only on the imperial rows (`#10-24`, `1/4-20`,
    `1-8`), which the metric designation parser cannot spell - so every
    lookup refused. The data supports the standard; the parser did not.
    """
    assert "ASME B18.3" in standards.supported_standards()
    gauge = standards.fastener("ASME B18.3", "#10-24")
    assert (gauge["size"], gauge["units"], gauge["tpi"]) == ("#10-24", "in", 24)
    assert (gauge["dk"], gauge["k"], gauge["t"]) == (0.312, 0.19, 0.09)
    assert gauge["pitch_mm"] is None
    fractional = standards.fastener("asme b18.3", "1/4-20")
    assert (fractional["size"], fractional["dk"], fractional["k"]) == ("1/4-20", 0.375, 0.25)
    assert standards.fastener("ASME B18.3", "1-8")["size"] == "1-8"
    assert standards.fastener("ASME B18.3", "1/2 - 13")["size"] == "1/2-13"


def test_a_standard_that_does_not_table_a_size_names_the_ones_it_does() -> None:
    """The refusal used to end 'Nearest tabled: .' - no candidate at all."""
    with pytest.raises(CommandError) as excinfo:
        standards.fastener("ASME B18.3", "M6")
    message = str(excinfo.value)
    assert excinfo.value.code == "pk_ref_unknown"
    assert "#10-24" in message and "1/4-20" in message
    with pytest.raises(CommandError) as excinfo:
        standards.fastener("ASME B18.3", "#99-13")
    assert "#10-24" in str(excinfo.value)
    with pytest.raises(CommandError) as excinfo:
        standards.fastener("ISO 4762", "#10-24")  # a metric standard, an imperial size
    assert "M6" in str(excinfo.value)
