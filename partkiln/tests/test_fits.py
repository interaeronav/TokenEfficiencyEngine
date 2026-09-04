"""ISO 286 limits and fits: what partkiln DERIVES, and what it refuses by name.

This lane exists because no permissively-licensed reproduction of the ISO 286
tolerance tables was found and copying one is not an option (A66 gap 6, and
the licence gate in `test_licences.py`). A formula may be implemented with a
citation, so `partkiln/data/iso286.json` carries the formula parameters from
ISO 286-1 clauses 2.1.1/2.1.2 - read in the publicly downloadable ISO/R
286:1962 preview at
https://cdn.standards.iteh.ai/samples/4201/65932c6743c94be8b27f0aa0c67376f0/ISO-R-286-1962.pdf
- and partkiln does the arithmetic.

The published values asserted below are SPOT CHECKS, not a table: they were
consulted on 2026-09-04 at engineersedge.com/international_tol.htm (which
cites ISO 286-1:2010(E)) and cross-checked at
unitcheatsheet.com/cheatsheets/iso-tolerance-grades.html (which cites ISO
286-1:2010 Table 1); the shaft rows were cross-checked at
cobanengineering.com/Tolerances/UpperAndLowerDeviationsShafts.asp. They are
here to prove the derivation lands on the standard's own numbers inside the
ranges partkiln serves - which is exactly the claim the refusals rest on.

The standard's rounding rules (clause 2.1.4) are NOT in the public text, so
outside those ranges the derivation is known to differ and every entry point
refuses `pk_not_served` naming the value the caller must supply. Those
refusals are the point of the file, not an edge case.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from partkiln import standards
from partkiln.data import provenance
from partkiln.document import CommandError

DATA = Path(__file__).resolve().parents[1] / "src" / "partkiln" / "data" / "iso286.json"


# -- the derivation lands on the published values ----------------------------------------


@pytest.mark.parametrize(
    ("size", "grade", "published_um"),
    [
        (4, 5, 5),
        (20, 5, 9),
        (40, 5, 11),
        (450, 5, 27),  # IT5: exact in all 13 steps
        (4, 6, 8),
        (20, 6, 13),
        (100, 6, 22),
        (200, 6, 29),  # IT6 (4 mm is ISO's own footnote)
        (4, 7, 12),
        (20, 7, 21),
        (40, 7, 25),
        (100, 7, 35),
        (200, 7, 46),
        (350, 7, 57),
        (4, 8, 18),
        (20, 8, 33),
        (100, 8, 54),
        (450, 8, 97),  # IT8: exact in all 13 steps
        (8, 9, 36),
        (20, 9, 52),
        (100, 9, 87),
        (20, 10, 84),
        (40, 10, 100),
        (200, 10, 185),
        (20, 11, 130),
        (20, 12, 210),
        (20, 13, 330),
        (8, 14, 360),
        (20, 15, 840),
        (20, 16, 1300),
    ],
)
def test_it_grade_equals_the_published_value(size: float, grade: int, published_um: int) -> None:
    """Agreement is ZERO micrometres everywhere partkiln agrees to serve."""
    row = standards.it_grade(size, grade)
    assert row["it_um"] == published_um, (
        f"IT{grade} at {size} mm: derived {row['it_um']} um, published {published_um} um"
    )
    assert row["basis"] == "derived"
    assert row["licence"] == "own" and row["source"].startswith("https://")


@pytest.mark.parametrize(
    ("size", "position", "grade", "upper_um", "lower_um"),
    [
        (20, "H", 7, 21, 0),  # basic hole, EI = 0 (ISO/R 286:1962 cl. 1.6.21)
        (20, "h", 6, 0, -13),  # basic shaft, es = 0 (cl. 1.6.20)
        (20, "g", 6, -7, -20),
        (50, "f", 7, -25, -50),
        (20, "k", 6, 15, 2),
        (25, "n", 6, 28, 15),
        (20, "F", 8, 53, 20),
        (20, "G", 7, 28, 7),
        (20, "js", 6, 6.5, -6.5),
    ],
)
def test_deviation_equals_the_published_pair(
    size: float, position: str, grade: int, upper_um: float, lower_um: float
) -> None:
    row = standards.deviation(size, position, grade)
    assert (row["upper_um"], row["lower_um"]) == (upper_um, lower_um)


def test_the_named_fits_match_the_published_limits() -> None:
    """H7/g6, H7/h6, H8/f7, H7/k6 and H7/n6 at 20-50 mm, to the micrometre."""
    g6 = standards.fit("20H7/g6")
    assert g6["kind"] == "clearance"
    assert (g6["min_clearance_um"], g6["max_clearance_um"]) == (7, 41)
    assert (g6["hole"]["min_mm"], g6["hole"]["max_mm"]) == (20.0, 20.021)
    assert (g6["shaft"]["min_mm"], g6["shaft"]["max_mm"]) == (19.98, 19.993)

    h6 = standards.fit("H7/h6", 20)
    assert h6["kind"] == "clearance"
    assert (h6["min_clearance_um"], h6["max_clearance_um"]) == (0, 34)

    f7 = standards.fit("50 H8/f7")
    assert (f7["min_clearance_um"], f7["max_clearance_um"]) == (25, 89)

    k6 = standards.fit("30H7/k6")
    assert k6["kind"] == "transition"
    assert (k6["min_clearance_um"], k6["max_clearance_um"]) == (-15, 19)

    n6 = standards.fit("25H7/n6")
    assert n6["kind"] == "transition"
    assert (n6["min_clearance_um"], n6["max_clearance_um"]) == (-28, 6)

    assert all(r["basis"] == "derived" for r in (g6, h6, f7, k6, n6))


# -- what it refuses, and by what name -----------------------------------------------------


def _code(exc: pytest.ExceptionInfo[CommandError]) -> str:
    return exc.value.code


def test_a_size_past_500_mm_refuses_by_name() -> None:
    with pytest.raises(CommandError) as exc:
        standards.fit("600H7/g6")
    assert _code(exc) == "pk_not_served"
    assert "500" in str(exc.value) and "it_um" in str(exc.value)


def test_a_size_in_a_step_the_derivation_does_not_reproduce_refuses() -> None:
    """8 mm H7 is the honest failure: 16i rounds to 14 um, ISO 286-1 prints 15."""
    with pytest.raises(CommandError) as exc:
        standards.fit("8H7/g6")
    message = str(exc.value)
    assert _code(exc) == "pk_not_served"
    assert "IT7" in message and "14 um" in message and "18-400 mm" in message
    assert "Supply it_um" in message


def test_a_tabulated_position_refuses_and_names_the_missing_value() -> None:
    with pytest.raises(CommandError) as exc:
        standards.fit("20H7/p6")
    message = str(exc.value)
    assert _code(exc) == "pk_not_served"
    assert "'p'" in message and "fd_um" in message
    assert "f, g, h, js, k, n" in message


@pytest.mark.parametrize("grade", [1, 2, 3, 4, 17, 18])
def test_the_grades_with_no_formula_refuse(grade: int) -> None:
    with pytest.raises(CommandError) as exc:
        standards.it_grade(20, grade)
    assert _code(exc) == "pk_not_served"
    assert "Supply it_um" in str(exc.value)


def test_k_outside_its_own_grade_range_refuses() -> None:
    with pytest.raises(CommandError) as exc:
        standards.deviation(20, "k", 8)
    assert _code(exc) == "pk_not_served"
    assert "IT4, IT5, IT6, IT7" in str(exc.value)


def test_an_unknown_letter_and_a_reversed_fit_refuse_with_the_fix() -> None:
    with pytest.raises(CommandError) as exc:
        standards.fit("20H7/q6")
    assert _code(exc) == "pk_not_served"
    with pytest.raises(CommandError) as exc:
        standards.fit("20h7/G6")
    assert _code(exc) == "pk_ref_unknown"
    assert "CAPITAL" in str(exc.value)
    with pytest.raises(CommandError) as exc:
        standards.fit("twenty H7/g6")
    assert _code(exc) == "pk_ref_unknown"


def test_a_fit_with_no_size_anywhere_refuses_pk_needs() -> None:
    with pytest.raises(CommandError) as exc:
        standards.fit("H7/g6")
    assert _code(exc) == "pk_needs"


# -- the caller's own licensed copy is the way past every refusal --------------------------


def test_supplied_values_unlock_a_refused_fit_and_say_so() -> None:
    """p6 at 20 mm with the ei the caller read from ISO 286-1: +22 um."""
    row = standards.fit("20H7/p6", supplied={"p6": {"fd_um": 22}})
    assert row["kind"] == "interference"
    assert (row["shaft"]["lower_um"], row["shaft"]["upper_um"]) == (22, 35)
    assert (row["shaft"]["min_mm"], row["shaft"]["max_mm"]) == (20.022, 20.035)
    assert row["basis"] == "supplied"


def test_supplied_it_unlocks_a_refused_size_step() -> None:
    row = standards.fit("8H7/g6", supplied={"H7": {"it_um": 15}, "g6": {"fd_um": -5, "it_um": 9}})
    assert (row["min_clearance_um"], row["max_clearance_um"]) == (5, 29)
    assert row["basis"] == "supplied"


def test_supported_fits_lists_the_ranges_and_the_refusals() -> None:
    listed = standards.supported_fits()
    assert listed["grades"]["IT7"] == "3-6 and 18-400 mm"
    assert listed["positions"]["g"] == "3-500 mm"
    assert set(listed["positions"]) == {"F", "G", "H", "JS", "f", "g", "h", "js", "k", "n"}
    assert listed["refused"] and listed["size_range_mm"] == [0, 500]


# -- the data file is formulae with a paper trail, never a table ---------------------------


def test_iso286_data_carries_its_provenance() -> None:
    entry = provenance("iso286.json")
    assert entry["licence"] == "own"
    assert entry["retrieved"] == "2026-09-04"
    assert "ISO-R-286-1962" in entry["source"]
    assert "ISO 286-1 clauses" in entry["authority"]


def test_the_data_file_stores_no_tolerance_table() -> None:
    """The licence half of the gap: coefficients, steps and intervals only.

    The ONE micrometre value in the file is the exception ISO's own footnote
    prints ('the value 7.5 is rounded off to 8 for grade 6 ... above 3 up to
    6 mm'), which is quoted with its clause. Anything else that looked like a
    tolerance value would mean a table had been copied in.
    """
    doc = json.loads(DATA.read_text(encoding="utf-8"))
    values = [k for k in _leaf_keys(doc) if k.endswith("_um")]
    assert values == ["value_um"], f"a value-shaped key appeared: {values}"
    assert doc["grade_exception"]["value_um"] == 8
    assert "7.5 is rounded off to 8" in doc["grade_exception"]["clause"]
    for grade, spans in doc["verified_exact_mm"]["it"].items():
        assert all(len(s) == 2 and 1 <= s[0] < s[1] <= 500 for s in spans), grade
    text = DATA.read_text(encoding="utf-8")
    assert not re.search(r"wikipedia|matweb|engineeringtoolbox|makeitfrom", text, re.IGNORECASE)


def _leaf_keys(node: object) -> list[str]:
    if isinstance(node, dict):
        out = []
        for key, value in node.items():
            out.append(key)
            out.extend(_leaf_keys(value))
        return out
    if isinstance(node, list):
        return [k for item in node for k in _leaf_keys(item)]
    return []


# -- a hole carries its class without moving a single face ---------------------------------


@pytest.mark.brep
def test_a_hole_records_its_fit_and_changes_no_geometry() -> None:
    """`fit: H7` is Law 18 cosmetic: the bore is cut at the basic size."""
    pytest.importorskip("OCP", reason="partkiln[brep] not installed")
    from test_document_parts import F1, build

    doc = build(F1()[:3])
    plain = build(F1()[:3])
    props = {"on": "plate.end", "at": [[50, 30]], "dia": 20}
    fitted = doc.apply(
        {"op": "create", "kind": "hole", "name": "bore", "props": {**props, "fit": "H7"}}
    )
    doc_plain = plain.apply({"op": "create", "kind": "hole", "name": "bore", "props": props})

    assert fitted["cosmetic"] == {"fit": "H7"}
    assert fitted["fit_min_mm"] == 20.0 and fitted["fit_max_mm"] == 20.021
    assert fitted["fit_it_um"] == 21 and fitted["fit_basis"] == "derived"
    assert any("basic size" in n for n in fitted["notes"])
    assert fitted["delta_mm3"] == doc_plain["delta_mm3"]
    assert doc.fingerprint() == plain.fingerprint(), "a cosmetic class moved the solid"


@pytest.mark.brep
def test_a_hole_refuses_a_fit_it_cannot_derive_and_a_shaft_class() -> None:
    pytest.importorskip("OCP", reason="partkiln[brep] not installed")
    from test_document_parts import F1, build

    doc = build(F1()[:3])
    with pytest.raises(CommandError) as exc:
        doc.apply(
            {
                "op": "create",
                "kind": "hole",
                "name": "bore",
                "props": {"on": "plate.end", "at": [[50, 30]], "dia": 20, "fit": "P7"},
            }
        )
    assert exc.value.code == "pk_not_served" and "fd_um" in str(exc.value)
    with pytest.raises(CommandError) as exc:
        doc.apply(
            {
                "op": "create",
                "kind": "hole",
                "name": "bore",
                "props": {"on": "plate.end", "at": [[50, 30]], "dia": 20, "fit": "h7"},
            }
        )
    assert exc.value.code == "pk_needs" and "SHAFT" in str(exc.value)
    with pytest.raises(CommandError) as exc:
        doc.apply(
            {
                "op": "create",
                "kind": "hole",
                "name": "bore",
                "props": {
                    "on": "plate.end",
                    "at": [[50, 30]],
                    "std": "M6 clearance",
                    "fit": "H7",
                },
            }
        )
    assert exc.value.code == "pk_spec_conflict"
