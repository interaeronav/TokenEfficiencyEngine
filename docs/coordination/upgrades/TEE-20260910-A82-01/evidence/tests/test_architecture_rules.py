"""Synthetic rule fixtures exercise decisions; no number here is legislation."""

from __future__ import annotations

import copy
import json

import pytest
from tee.architecture.model import ArchitectureError
from tee.architecture.rules import assess, coverage, validate_pack


def pack(**changes):
    result = {
        "schema": "tee-architecture-rulepack/1",
        "id": "synthetic-fixture",
        "version": "1",
        "kind": "synthetic",
        "edition": "TEST ONLY 2026",
        "authority": "Owned test fixture - not an authority",
        "jurisdiction": {"country": "ZA", "region": None, "municipality": None},
        "effective_from": "2026-01-01",
        "effective_until": "2026-12-31",
        "rules": [
            {
                "id": "opening-fixture",
                "clause": "synthetic-1",
                "fact": "entities.*.width",
                "entity_kind": "opening",
                "where": {"fill": "door"},
                "op": "gte",
                "value": 800,
                "unit": "mm",
            }
        ],
    }
    result.update(changes)
    return result


def document(width=800):
    return {
        "schema": "tee-architecture/1",
        "units": "mm",
        "revision": 2,
        "project": {
            "name": "Test house",
            "jurisdiction": {
                "country": "ZA",
                "region": "Fixture-region",
                "municipality": "Fixture-city",
            },
            "facts": {},
        },
        "entities": {
            "door": {"kind": "opening", "fill": "door", "width": width},
            "window": {"kind": "opening", "fill": "window", "width": 500},
        },
    }


def run(doc=None, packs=None, when="2026-09-11"):
    return assess(doc or document(), [pack()] if packs is None else packs, when)


@pytest.mark.parametrize(("width", "status"), [(799.999, "fail"), (800, "pass"), (801, "pass")])
def test_positive_negative_exact_boundary_are_explicitly_synthetic(width, status):
    result = run(document(width))
    assert len(result["checks"]) == 1
    assert result["checks"][0]["status"] == status
    assert result["checks"][0]["reason"] == "synthetic_fixture_only"
    assert result["coverage"]["status"] == "not_verified"
    assert result["status"] != "compliant"
    assert result["legal_approval"] is False
    assert result["ids_validation"] == result["schema_validation"] == "not_assessed"


def test_missing_country_never_selects_a_default():
    doc = document()
    doc["project"]["jurisdiction"] = {}
    result = run(doc)
    assert result["checks"][0]["status"] == "not_verified"
    assert "jurisdiction_missing" in result["checks"][0]["reason"]
    assert result["coverage"]["missing_location"] == ["country", "region", "municipality"]


def test_country_and_region_filters_do_not_turn_into_worldwide_coverage():
    rules = [pack(jurisdiction={"country": "QA", "region": None, "municipality": None})]
    result = run(packs=rules)
    assert result["checks"][0]["status"] == "not_applicable"
    assert result["coverage"]["worldwide_framework"] is True
    assert result["coverage"]["worldwide_verified_law_coverage"] is False
    assert coverage([], {"country": "JP"})["status"] == "not_verified"


@pytest.mark.parametrize("when", ["2025-12-31", "2027-01-01"])
def test_effective_edition_dates_are_enforced(when):
    assert run(when=when)["checks"][0]["status"] == "not_applicable"


def test_applicability_missing_excluded_and_matched():
    p = pack()
    p["rules"][0]["applicability"] = [
        {"fact": "project.facts.occupancy", "op": "in", "value": ["dwelling"]}
    ]
    doc = document()
    assert run(doc, [p])["checks"][0]["status"] == "not_verified"
    doc["project"]["facts"]["occupancy"] = "warehouse"
    assert run(doc, [p])["checks"][0]["status"] == "not_applicable"
    doc["project"]["facts"]["occupancy"] = "dwelling"
    assert run(doc, [p])["checks"][0]["status"] == "pass"


def test_measured_fact_requires_provenance_units_and_finite_value():
    p = pack()
    p["rules"][0].update(fact="project.facts.clear_width")
    doc = document()
    for fact in [
        800,
        {"value": 800, "unit": "mm"},
        {"value": 0.8, "unit": "kg", "evidence": {"kind": "measurement", "source": "survey"}},
        {
            "value": float("nan"),
            "unit": "mm",
            "evidence": {"kind": "measurement", "source": "survey"},
        },
    ]:
        doc["project"]["facts"]["clear_width"] = fact
        assert run(doc, [p])["checks"][0]["status"] == "not_verified"
    doc["project"]["facts"]["clear_width"] = {
        "value": 0.8,
        "unit": "m",
        "evidence": {"kind": "measurement", "source": "owned-survey-sha256"},
    }
    assert run(doc, [p])["checks"][0]["measured"] == 800


def reviewed_fixture():
    # Supplied review metadata only: example.invalid cannot represent real law.
    return pack(
        kind="regulatory",
        source={
            "kind": "primary",
            "url": "https://example.invalid/fixture",
            "title": "Fictional review fixture",
            "sha256": "1" * 64,
            "accessed_on": "2026-01-02",
            "clauses": ["synthetic-1"],
        },
        review={"status": "reviewed", "reviewer": "Test fixture", "reviewed_on": "2026-01-02"},
        adoption={
            "instrument": "Fictional adoption fixture",
            "url": "https://example.invalid/adoption",
            "effective_on": "2026-01-01",
        },
    )


def test_regulatory_source_review_clause_adoption_are_mandatory():
    p = pack(kind="regulatory")
    result = run(packs=[p])
    assert result["checks"][0]["status"] == "not_verified"
    assert "primary_source_required" in result["checks"][0]["reason"]
    p = reviewed_fixture()
    assert validate_pack(p)["provenance_ready"] is True
    assert run(packs=[p])["checks"][0]["status"] == "pass"
    assert run(packs=[p])["status"] == "not_verified"
    p["source"]["clauses"] = []
    assert run(packs=[p])["checks"][0]["status"] == "not_verified"


def test_exact_parent_and_explicit_amendment_replace_only_named_rule():
    parent = pack(id="parent")
    amendment = pack(
        id="city-amendment",
        jurisdiction={"country": "ZA", "region": "Fixture-region", "municipality": "Fixture-city"},
        requires=[{"id": "parent", "version": "1", "sha256": validate_pack(parent)["sha256"]}],
    )
    amendment["rules"][0]["value"] = 900
    amendment["rules"][0]["overrides"] = [{"pack_id": "parent", "rule_id": "opening-fixture"}]
    checks = run(packs=[parent, amendment])["checks"]
    assert [check["status"] for check in checks] == ["not_applicable", "fail"]
    assert "explicit_parent" in checks[0]["reason"]
    assert run(packs=[amendment])["checks"][0]["status"] == "not_verified"
    parent["rules"][0]["value"] = 700
    checks = run(packs=[parent, amendment])["checks"]
    assert next(c for c in checks if c["pack_id"] == "city-amendment")["status"] == "not_verified"


def test_conflicting_threshold_interpretations_and_duplicate_editions_fail_closed():
    a, b = pack(id="a"), pack(id="b")
    b["rules"][0]["value"] = 900
    checks = run(packs=[a, b])["checks"]
    assert all(check["status"] == "not_verified" for check in checks)
    assert all(
        check["status"] == "not_verified" for check in run(packs=[a, copy.deepcopy(a)])["checks"]
    )


@pytest.mark.parametrize(
    "field,value",
    [
        ("op", "eval"),
        ("op", "__import__"),
        ("fact", "project.__class__"),
        ("value", float("inf")),
        ("value", True),
    ],
)
def test_no_arbitrary_code_or_nonfinite_thresholds(field, value):
    p = pack()
    p["rules"][0][field] = value
    with pytest.raises(ArchitectureError):
        validate_pack(p)


def test_pack_hash_protects_threshold_identity_and_assess_does_not_mutate():
    p = pack()
    p["sha256"] = validate_pack(p)["sha256"]
    before = json.dumps(p, sort_keys=True)
    doc = document()
    saved = copy.deepcopy(doc)
    run(doc, [p])
    assert json.dumps(p, sort_keys=True) == before and doc == saved
    p["rules"][0]["value"] = 1
    with pytest.raises(ArchitectureError, match="sha256"):
        validate_pack(p)


def test_bounds_reject_excessive_rules_and_work():
    p = pack()
    p["rules"] *= 257
    with pytest.raises(ArchitectureError, match="256"):
        validate_pack(p)
    with pytest.raises(ArchitectureError, match="64"):
        run(packs=[pack()] * 65)


def test_no_matching_entities_is_unknown_not_vacuous_pass():
    doc = document()
    doc["entities"] = {}
    assert run(doc)["checks"][0]["status"] == "not_verified"


def test_unsupported_pack_reports_not_verified_during_assessment():
    invalid = pack()
    invalid["rules"][0]["op"] = "python"
    result = run(packs=[invalid])
    assert result["status"] == "not_verified"
    assert result["checks"][0]["reason"] == "invalid_or_unsupported_rule_pack"
    assert result["coverage"]["packs"][0]["status"] == "not_verified"


def test_authority_is_selected_by_explicit_applicability_not_ignored_location_key():
    p = pack()
    p["jurisdiction"]["authority"] = "Fixture authority"
    assert run(packs=[p])["checks"][0]["status"] == "not_verified"
    del p["jurisdiction"]["authority"]
    p["rules"][0]["applicability"] = [
        {"fact": "project.facts.authority", "op": "eq", "value": "Fixture authority"}
    ]
    assert run(packs=[p])["checks"][0]["status"] == "not_verified"


@pytest.mark.parametrize("value", [[], {}, None, True, 1])
@pytest.mark.parametrize(
    "field",
    [
        "kind",
        "rule.op",
        "rule.unit",
        "source.url",
        "source.title",
        "review.reviewer",
        "adoption.instrument",
        "adoption.url",
    ],
)
def test_malformed_pack_field_types_are_unknown_not_runtime_crashes(field, value):
    p = reviewed_fixture()
    if field.startswith("rule."):
        p["rules"][0][field.split(".")[1]] = value
    elif "." in field:
        section, key = field.split(".")
        p[section][key] = value
    else:
        p[field] = value
    assert run(packs=[p])["status"] == "not_verified"
    assert run(packs=[p])["checks"][0]["status"] == "not_verified"


@pytest.mark.parametrize(
    ("value", "uncertainty", "expected"),
    [
        (0.8, 0.005, "not_verified"),
        (0.81, 0.005, "pass"),
        (0.79, 0.005, "fail"),
        (0.8, 0, "pass"),
        (0.8, -1, "not_verified"),
        (0.8, "unknown", "not_verified"),
    ],
)
def test_declared_measurement_uncertainty_is_converted_and_checked(value, uncertainty, expected):
    p = pack()
    p["rules"][0]["fact"] = "project.facts.clear_width"
    doc = document()
    doc["project"]["facts"]["clear_width"] = {
        "value": value,
        "unit": "m",
        "uncertainty": uncertainty,
        "evidence": {"kind": "measurement", "source": "owned survey fixture"},
    }
    assert run(doc, [p])["checks"][0]["status"] == expected


def test_uncertain_equality_never_passes_on_center_value_alone():
    p = pack()
    p["rules"][0].update(fact="project.facts.clear_width", op="eq")
    doc = document()
    doc["project"]["facts"]["clear_width"] = {
        "value": 800,
        "unit": "mm",
        "uncertainty": 1,
        "evidence": {"kind": "measurement", "source": "owned survey fixture"},
    }
    assert run(doc, [p])["checks"][0]["status"] == "not_verified"
