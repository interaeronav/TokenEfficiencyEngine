import pytest
from fixtures_extract import HOUSE_D, HOUSE_W, make_dxf, make_pdf

from tee.extract.documents import classify_sheet, extract_dxf, extract_pdf, parse_dimension_text
from tee.extract.plan import wall_length


def facts_of_kind(facts, kind):
    return [f for f in facts if f["kind"] == kind]


def test_dimension_text_parsing():
    assert parse_dimension_text("4200") == 4.2
    assert parse_dimension_text("4200 mm") == 4.2
    assert parse_dimension_text("420 cm") == 4.2
    assert parse_dimension_text("4.2 m") == 4.2
    assert parse_dimension_text("12") is None  # ambiguous bare small number
    assert parse_dimension_text("hello") is None


def test_sheet_classifier_metadata_first():
    assert classify_sheet("A-101 plan.pdf", "")["class"] == "plan"
    assert classify_sheet("A-201.pdf", "")["class"] == "elevation"
    assert classify_sheet("sheet.pdf", "SOUTH ELEVATION 1:100")["class"] == "elevation"
    assert classify_sheet("x.pdf", "nothing useful")["class"] == "unknown"


def test_dxf_extraction_full(tmp_path):
    path = make_dxf(tmp_path / "plan.dxf")
    facts = extract_dxf(path, "dwg:test:model")

    units = facts_of_kind(facts, "units")[0]
    assert units["meters_per_unit"] == 0.001
    assert units["calibration_needed"] is False

    dims = facts_of_kind(facts, "dimension")
    values = sorted(round(d["value_m"], 2) for d in dims)
    assert HOUSE_W in values and HOUSE_D in values
    assert all(d["tier"] == "dimension_text" for d in dims)

    plan = facts_of_kind(facts, "plan")[0]["plan"]
    assert len(plan["walls"]) == 5  # 4 outer segments + 1 interior
    lengths = sorted(round(wall_length(w), 2) for w in plan["walls"])
    assert lengths.count(HOUSE_D) == 3  # two sides + interior
    assert lengths.count(HOUSE_W) == 2
    assert all(w["thickness"] == pytest.approx(0.2) for w in plan["walls"])

    rooms = {r["name"] for r in plan["rooms"]}
    assert rooms == {"Living Room", "Bedroom 1"}

    assert len(plan["openings"]) == 1
    assert plan["openings"][0]["kind"] == "door"


def test_unitless_dxf_triggers_calibration_question(tmp_path):
    path = make_dxf(tmp_path / "unitless.dxf", unitless=True)
    facts = extract_dxf(path, "dwg:u:model")
    units = facts_of_kind(facts, "units")[0]
    assert units["calibration_needed"] is True
    questions = facts_of_kind(facts, "question")
    assert questions and "INSUNITS" in questions[0]["question"]
    assert questions[0]["assumption"]["confidence"] == "assumed"


def test_vector_pdf_extraction(tmp_path):
    path = make_pdf(tmp_path / "A-101.pdf")
    facts = extract_pdf(path, "dwg:pdf")

    page = facts_of_kind(facts, "page")[0]
    assert page["vector"] is True

    sheet = facts_of_kind(facts, "sheet")[0]
    assert sheet["class"] == "plan"

    dims = facts_of_kind(facts, "dimension")
    values = sorted(round(d["value_m"], 1) for d in dims)
    assert 8.0 in values and 6.0 in values

    scale = facts_of_kind(facts, "scale")[0]
    assert scale["method"] == "dimension_fit"
    # 1 drawing mm = 0.1 m -> meters per PDF point = 0.1 / 2.8346
    assert scale["meters_per_point"] == pytest.approx(0.1 / 2.83464567, rel=0.02)

    plans = facts_of_kind(facts, "plan")
    assert plans, "wall reconstruction produced no plan"
    walls = plans[0]["plan"]["walls"]
    assert len(walls) >= 4
    lengths = sorted(round(wall_length(w), 1) for w in walls)
    assert any(abs(length - HOUSE_W) < 0.3 for length in lengths)
    assert any(abs(length - HOUSE_D) < 0.3 for length in lengths)
    assert all(0.05 <= w["thickness"] <= 0.5 for w in walls)
