"""Worldwide, source-labelled, declarative architectural rule assessments.

This module does not fetch legislation, execute pack code, learn thresholds or
assert complete regulatory coverage. A review record is supplied provenance,
not an independently authenticated legal opinion. All evaluations are bounded.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
from datetime import date
from typing import Any
from urllib.parse import urlparse

SCHEMA = "tee-architecture-rulepack/1"
MAX_PACKS = 64
MAX_RULES = 256
MAX_CHECKS = 4096
MAX_PACK_BYTES = 1024 * 1024
LEVELS = ("country", "region", "municipality")
OPS = {"gt", "gte", "lt", "lte", "eq"}
DIMENSIONS = {
    "width",
    "height",
    "thickness",
    "depth",
    "sill",
    "offset",
    "elevation",
    "base_height",
    "panel_thickness",
    "back_thickness",
    "plinth_height",
    "edge_band_mm",
}
_ID = re.compile(r"^[A-Za-z0-9_-]{1,96}$")
_PATH = re.compile(
    r"^(project\.facts\.[A-Za-z0-9_-]+(?:\.[A-Za-z0-9_-]+){0,5}|entities\.(?:\*|[A-Za-z0-9_-]+)\.[A-Za-z0-9_-]+)$"
)


def _error(message: str) -> Exception:
    from .model import ArchitectureError

    return ArchitectureError(message)


def _canonical(pack: dict[str, Any]) -> bytes:
    try:
        data = json.dumps(
            {k: v for k, v in pack.items() if k != "sha256"},
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode()
    except (TypeError, ValueError, RecursionError):
        raise _error("Rule pack must contain bounded finite JSON values.") from None
    if len(data) > MAX_PACK_BYTES:
        raise _error(f"Rule pack exceeds {MAX_PACK_BYTES} bytes.")
    return data


def _text(value: Any, name: str, *, maximum: int = 1024) -> str:
    if not isinstance(value, str) or not value.strip() or len(value) > maximum:
        raise _error(f"Rule pack {name} must be a nonempty string up to {maximum} characters.")
    return value


def _id(value: Any, name: str) -> str:
    if not isinstance(value, str) or not _ID.fullmatch(value):
        raise _error(f"Rule pack {name} must use 1-96 letters, digits, underscore or hyphen.")
    return value


def _date(value: Any, name: str) -> date:
    try:
        if not isinstance(value, str) or len(value) != 10:
            raise ValueError
        return date.fromisoformat(value)
    except ValueError:
        raise _error(f"{name} must use YYYY-MM-DD.") from None


def _numeric(value: Any) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and abs(value) <= 1e15
        and math.isfinite(value)
    )


def _jurisdiction(value: Any, *, require_country: bool = False) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise _error("Jurisdiction must declare country, region and municipality explicitly.")
    if set(value) - set(LEVELS):
        raise _error(
            "Jurisdiction supports country, region and municipality; "
            "use applicability for authority."
        )
    result = {level: value.get(level) for level in LEVELS}
    if result["country"] is None and require_country:
        raise _error("Rule pack needs an explicit two-letter country code.")
    if result["country"] is not None and not re.fullmatch(r"[A-Z]{2}", str(result["country"])):
        raise _error("Country must be an uppercase two-letter code; no default country is assumed.")
    for level in ("region", "municipality"):
        if result[level] is not None:
            _text(result[level], level, maximum=160)
    if result["municipality"] is not None and result["region"] is None:
        raise _error("Municipality selection requires its region to avoid ambiguous names.")
    return result


def _source_ready(pack: dict[str, Any], rules: list[dict[str, Any]]) -> list[str]:
    if pack["kind"] == "synthetic":
        return ["synthetic_fixture_not_law"]
    missing = []

    def named(value: Any, maximum: int = 1024) -> bool:
        return isinstance(value, str) and bool(value.strip()) and len(value) <= maximum

    def primary_url(value: Any) -> bool:
        if not named(value, 4096):
            return False
        try:
            parsed = urlparse(value)
            return parsed.scheme == "https" and bool(parsed.hostname)
        except ValueError:
            return False

    source = pack.get("source", {})
    if not isinstance(source, dict):
        return ["reviewed_primary_source_missing"]
    if source.get("kind") != "primary":
        missing.append("primary_source_required")
    if not primary_url(source.get("url")):
        missing.append("primary_source_url_missing")
    if not isinstance(source.get("sha256"), str) or not re.fullmatch(
        r"[0-9a-f]{64}", source["sha256"]
    ):
        missing.append("source_document_hash_missing")
    if not named(source.get("title")):
        missing.append("source_title_missing")
    clauses = source.get("clauses", [])
    if not isinstance(clauses, list) or any(rule["clause"] not in clauses for rule in rules):
        missing.append("source_clauses_missing")
    review = pack.get("review", {})
    if (
        not isinstance(review, dict)
        or review.get("status") != "reviewed"
        or not named(review.get("reviewer"), 256)
    ):
        missing.append("reviewed_interpretation_missing")
    for obj, key, reason in (
        (source, "accessed_on", "source_access_date_missing"),
        (review, "reviewed_on", "review_date_missing"),
    ):
        try:
            _date(obj.get(key), key)
        except (ValueError, AttributeError):
            missing.append(reason)
    adoption = pack.get("adoption", {})
    if (
        not isinstance(adoption, dict)
        or not named(adoption.get("instrument"))
        or not primary_url(adoption.get("url"))
    ):
        missing.append("adoption_instrument_missing")
    else:
        try:
            _date(adoption.get("effective_on"), "adoption.effective_on")
        except ValueError:
            missing.append("adoption_effective_date_missing")
    return missing


def _validate_pack(pack: dict[str, Any]) -> dict[str, Any]:
    """Validate a supplied pack without fetching or authenticating its sources."""
    if not isinstance(pack, dict):
        raise _error("Rule pack must be a JSON object.")
    digest = hashlib.sha256(_canonical(pack)).hexdigest()
    if pack.get("schema") != SCHEMA or pack.get("kind") not in {"synthetic", "regulatory"}:
        raise _error(f"Rule pack needs schema {SCHEMA} and kind synthetic or regulatory.")
    _id(pack.get("id"), "id")
    _text(pack.get("version"), "version", maximum=96)
    _text(pack.get("edition"), "edition", maximum=160)
    _text(pack.get("authority"), "authority", maximum=256)
    _jurisdiction(pack.get("jurisdiction"), require_country=True)
    start = _date(pack.get("effective_from"), "effective_from")
    until = pack.get("effective_until")
    if until is not None and _date(until, "effective_until") < start:
        raise _error("effective_until cannot precede effective_from.")
    if pack.get("sha256") is not None and pack["sha256"] != digest:
        raise _error("Rule pack sha256 differs from canonical contents; review the changed pack.")
    rules = pack.get("rules")
    if not isinstance(rules, list) or not 1 <= len(rules) <= MAX_RULES:
        raise _error(f"Rule pack requires 1-{MAX_RULES} declarative rules.")
    ids = set()
    for rule in rules:
        if not isinstance(rule, dict):
            raise _error("Every rule must be an object.")
        rid = _id(rule.get("id"), "rule.id")
        if rid in ids:
            raise _error("Rule IDs must be unique within a pack.")
        ids.add(rid)
        _text(rule.get("clause"), "rule.clause", maximum=256)
        fact = rule.get("fact")
        if not isinstance(fact, str) or not _PATH.fullmatch(fact):
            raise _error("Rule fact must be project.facts.<path> or entities.<id|*>.<dimension>.")
        if rule.get("op") not in OPS or not _numeric(rule.get("value")):
            raise _error("Rules support finite numeric gt/gte/lt/lte/eq comparisons only.")
        if rule.get("unit") not in {"mm", "m", "m2", "mm2", "degrees", "count", "ratio"}:
            raise _error("Rule unit must be mm, m, mm2, m2, degrees, count or ratio.")
        if fact.startswith("entities.") and fact.rsplit(".", 1)[1] not in DIMENSIONS:
            raise _error("Entity facts support explicit millimetre dimensions only.")
        if "entity_kind" in rule:
            _id(rule["entity_kind"], "rule.entity_kind")
        where = rule.get("where", {})
        if (
            not isinstance(where, dict)
            or len(where) > 8
            or any(
                not isinstance(k, str)
                or not _ID.fullmatch(k)
                or not isinstance(v, (str, bool, int, float))
                or (isinstance(v, float) and not math.isfinite(v))
                for k, v in where.items()
            )
        ):
            raise _error("Rule where must contain up to eight literal field filters.")
        applicability = rule.get("applicability", [])
        if not isinstance(applicability, list) or len(applicability) > 16:
            raise _error("Rule applicability supports up to sixteen literal conditions.")
        for condition in applicability:
            if (
                not isinstance(condition, dict)
                or not isinstance(condition.get("fact"), str)
                or not re.fullmatch(
                    r"project\.facts\.[A-Za-z0-9_-]+(?:\.[A-Za-z0-9_-]+){0,5}", condition["fact"]
                )
            ):
                raise _error("Applicability facts must use bounded project.facts paths.")
            if condition.get("op") not in {"eq", "in"}:
                raise _error("Applicability supports only literal eq or in conditions.")
            values = condition.get("value")
            values = values if condition["op"] == "in" else [values]
            if (
                not isinstance(values, list)
                or not 1 <= len(values) <= 32
                or any(
                    not isinstance(v, (str, bool, int, float))
                    or (isinstance(v, float) and not math.isfinite(v))
                    for v in values
                )
            ):
                raise _error("Applicability values must be bounded finite scalar literals.")
        overrides = rule.get("overrides", [])
        if not isinstance(overrides, list) or len(overrides) > 32:
            raise _error("Rule overrides must be a bounded list of pack_id/rule_id references.")
        for reference in overrides:
            if not isinstance(reference, dict):
                raise _error("Rule override requires pack_id and rule_id.")
            _id(reference.get("pack_id"), "override.pack_id")
            _id(reference.get("rule_id"), "override.rule_id")
    requires = pack.get("requires", [])
    if not isinstance(requires, list) or len(requires) > 32:
        raise _error("Pack requires must be a bounded list of exact parent identities.")
    for dependency in requires:
        if not isinstance(dependency, dict):
            raise _error("Pack dependency requires id, version and sha256.")
        _id(dependency.get("id"), "requires.id")
        _text(dependency.get("version"), "requires.version", maximum=96)
        if not isinstance(dependency.get("sha256"), str) or not re.fullmatch(
            r"[0-9a-f]{64}", dependency["sha256"]
        ):
            raise _error("Pack dependency requires an exact canonical sha256.")
    missing = _source_ready(pack, rules)
    return {
        "ok": True,
        "id": pack["id"],
        "version": pack["version"],
        "sha256": digest,
        "kind": pack["kind"],
        "rules": len(rules),
        "provenance_ready": not missing,
        "unverified_reasons": missing,
        "source_authentication": "not_performed",
    }


def validate_pack(pack: dict[str, Any]) -> dict[str, Any]:
    """Validate JSON types as well as supported semantics; refuse malformed packs."""
    from .model import ArchitectureError

    try:
        return _validate_pack(pack)
    except ArchitectureError:
        raise
    except (TypeError, KeyError, AttributeError, OverflowError, RecursionError):
        raise _error("Rule pack contains invalid field types; check its declared schema.") from None


def _match(pack_location: dict[str, Any], project_location: dict[str, Any]) -> str:
    missing = False
    for level in LEVELS:
        expected = pack_location.get(level)
        actual = project_location.get(level)
        if expected is None:
            continue
        if actual is None:
            missing = True
        elif actual != expected:
            return "not_applicable"
    return "not_verified" if missing else "applicable"


def _packs(packs: Any) -> list[dict[str, Any]]:
    if not isinstance(packs, list) or len(packs) > MAX_PACKS:
        raise _error(f"Assess at most {MAX_PACKS} rule packs per call.")
    from .model import ArchitectureError

    validations = []
    for pack in packs:
        try:
            validations.append(validate_pack(pack))
        except ArchitectureError as exc:
            validations.append(
                {
                    "ok": False,
                    "reason": "invalid_or_unsupported_rule_pack",
                    "detail": str(exc)[:256],
                }
            )
    return validations


def coverage(packs: list[dict[str, Any]], jurisdiction: dict[str, Any]) -> dict[str, Any]:
    """Report declared subset coverage; no catalog here establishes all law."""
    validations = _packs(packs)
    location = _jurisdiction(jurisdiction)
    matching = []
    for pack, validation in zip(packs, validations, strict=True):
        if not validation["ok"]:
            matching.append({"status": "not_verified", **validation})
            continue
        match = _match(pack["jurisdiction"], location)
        if match != "not_applicable":
            matching.append(
                {
                    "id": pack["id"],
                    "version": pack["version"],
                    "kind": pack["kind"],
                    "jurisdiction_status": match,
                    "jurisdiction": pack["jurisdiction"],
                    "provenance_ready": validation["provenance_ready"],
                    "rules": validation["rules"],
                }
            )
    return {
        "status": "not_verified",
        "jurisdiction": location,
        "packs": matching,
        "missing_location": [level for level in LEVELS if not location.get(level)],
        "reason": "complete_applicable_legislation_inventory_not_established",
        "worldwide_framework": True,
        "worldwide_verified_law_coverage": False,
        "legal_approval": False,
    }


_MISSING = object()


def _get(document: dict[str, Any], path: str) -> Any:
    value: Any = document
    for key in path.split("."):
        if not isinstance(value, dict) or key not in value:
            return _MISSING
        value = value[key]
    return value


def _applicability(document: dict[str, Any], rule: dict[str, Any]) -> str:
    unknown = False
    for condition in rule.get("applicability", []):
        value = _get(document, condition["fact"])
        if isinstance(value, dict):
            value = value.get("value", _MISSING)
        if (
            value is _MISSING
            or value is None
            or not isinstance(value, (str, bool, int, float))
            or (
                isinstance(value, (int, float))
                and not isinstance(value, bool)
                and not _numeric(value)
            )
        ):
            unknown = True
            continue
        allowed = condition["value"] if condition["op"] == "in" else [condition["value"]]
        if value not in allowed:
            return "not_applicable"
    return "not_verified" if unknown else "applicable"


def _facts(document: dict[str, Any], rule: dict[str, Any]) -> list[tuple[str, Any]]:
    path = rule["fact"]
    if path.startswith("project.facts."):
        return [(path, _get(document, path))]
    _, target, field = path.split(".")
    entities = document.get("entities", {})
    if not isinstance(entities, dict) or len(entities) > 10_000:
        raise _error("Rules require an entity map containing at most 10000 entities.")
    if target != "*":
        entity = entities.get(target, {})
        selected = [(target, entity)] if isinstance(entity, dict) else []
    else:
        selected = [
            (key, entity) for key, entity in sorted(entities.items()) if isinstance(entity, dict)
        ]
    result = []
    for key, entity in selected:
        if rule.get("entity_kind") and entity.get("kind") != rule["entity_kind"]:
            continue
        if any(
            entity.get(name, _MISSING) != expected
            for name, expected in rule.get("where", {}).items()
        ):
            continue
        value = entity.get(field, _MISSING)
        result.append(
            (
                f"entities.{key}.{field}",
                {
                    "value": value,
                    "unit": "mm",
                    "evidence": {
                        "kind": "authored_dimension",
                        "revision": document.get("revision"),
                    },
                },
            )
        )
    return result


def _measure(fact: Any, unit: str) -> tuple[float | None, str]:
    if not isinstance(fact, dict) or not _numeric(fact.get("value")):
        return None, "measured_fact_missing"
    evidence = fact.get("evidence")
    if (
        not isinstance(evidence, dict)
        or not isinstance(evidence.get("kind"), str)
        or evidence.get("kind")
        not in {
            "measurement",
            "model",
            "authored_dimension",
        }
    ):
        return None, "measurement_provenance_missing"
    if evidence["kind"] != "authored_dimension" and not evidence.get("source"):
        return None, "measurement_source_missing"
    actual_unit = fact.get("unit")
    if not isinstance(actual_unit, str):
        return None, "measurement_unit_mismatch"
    conversions = {("mm", "m"): 0.001, ("m", "mm"): 1000.0, ("mm2", "m2"): 1e-6, ("m2", "mm2"): 1e6}
    factor = 1 if actual_unit == unit else conversions.get((actual_unit, unit))
    if factor is None:
        return None, "measurement_unit_mismatch"
    result = float(fact["value"]) * factor
    if not math.isfinite(result):
        return None, "measurement_not_finite"
    return result, "measured"


def _compare(value: float, op: str, threshold: float) -> bool:
    if op == "gt":
        return value > threshold
    if op == "gte":
        return value >= threshold
    if op == "lt":
        return value < threshold
    if op == "lte":
        return value <= threshold
    return value == threshold


def _decision(fact: Any, value: float, unit: str, op: str, threshold: float) -> tuple[str, str]:
    """A supplied error interval must not be silently reduced to its centre."""
    if any(str(key).startswith("uncertainty") and key != "uncertainty" for key in fact):
        return "not_verified", "unsupported_uncertainty_field"
    uncertainty = fact.get("uncertainty", 0)
    if not _numeric(uncertainty) or uncertainty < 0:
        return "not_verified", "measurement_uncertainty_invalid"
    error_fact = {**fact, "value": uncertainty}
    error, reason = _measure(error_fact, unit)
    if error is None:
        return "not_verified", reason
    if error == 0:
        return ("pass" if _compare(value, op, threshold) else "fail"), "exact_supplied_value"
    low, high = value - error, value + error
    if op == "eq":
        if low <= threshold <= high:
            return "not_verified", "measurement_uncertainty_crosses_threshold"
        return "fail", "measurement_interval_outside_threshold"
    decisions = [_compare(bound, op, threshold) for bound in (low, high)]
    if decisions[0] != decisions[1]:
        return "not_verified", "measurement_uncertainty_crosses_threshold"
    return ("pass" if decisions[0] else "fail"), "measurement_interval_checked"


def assess(
    document_dict: dict[str, Any],
    packs: list[dict[str, Any]],
    assessment_date: str | None = None,
) -> dict[str, Any]:
    """Evaluate a supplied rule subset, preserving unknowns and source identity."""
    if not isinstance(document_dict, dict) or document_dict.get("units") != "mm":
        raise _error("Assess a millimetre architectural document.")
    today = (
        _date(assessment_date, "assessment_date") if assessment_date is not None else date.today()
    )
    initial_validations = _packs(packs)
    location = _jurisdiction(document_dict.get("project", {}).get("jurisdiction", {}))
    cov = coverage(packs, location)
    checks = [
        {"status": "not_verified", **validation}
        for validation in initial_validations
        if not validation["ok"]
    ]
    packs = [
        pack
        for pack, validation in zip(packs, initial_validations, strict=True)
        if validation["ok"]
    ]
    validations = [validation for validation in initial_validations if validation["ok"]]
    by_id: dict[str, list[int]] = {}
    for index, pack in enumerate(packs):
        by_id.setdefault(pack["id"], []).append(index)
    pack_reasons: dict[int, list[str]] = {}
    for index, pack in enumerate(packs):
        reasons = []
        if len(by_id[pack["id"]]) > 1:
            reasons.append("conflicting_pack_identity")
        for dependency in pack.get("requires", []):
            indices = by_id.get(dependency["id"], [])
            if len(indices) != 1:
                reasons.append("parent_pack_missing_or_ambiguous")
                continue
            parent = indices[0]
            if (
                packs[parent]["version"] != dependency["version"]
                or validations[parent]["sha256"] != dependency["sha256"]
            ):
                reasons.append("parent_pack_identity_mismatch")
            if _match(packs[parent]["jurisdiction"], location) != "applicable" or (
                today < _date(packs[parent]["effective_from"], "effective_from")
                or (
                    packs[parent].get("effective_until") is not None
                    and today > _date(packs[parent]["effective_until"], "effective_until")
                )
            ):
                reasons.append("parent_pack_not_applicable")
            if pack["kind"] == "regulatory" and not validations[parent]["provenance_ready"]:
                reasons.append("parent_pack_not_verified")
        pack_reasons[index] = reasons

    # Memoisation bounds a dense dependency graph; a recursion stack rejects cycles.
    dependency_results: dict[int, bool] = {}

    def depends(index: int, stack: tuple[int, ...] = ()) -> bool:
        if index in stack:
            return False
        if index in dependency_results:
            return dependency_results[index]
        for dependency in packs[index].get("requires", []):
            indices = by_id.get(dependency["id"], [])
            if (
                len(indices) != 1
                or pack_reasons[indices[0]]
                or not depends(indices[0], (*stack, index))
            ):
                dependency_results[index] = False
                return False
        dependency_results[index] = True
        return True

    for index in range(len(packs)):
        if not depends(index):
            pack_reasons[index].append("dependency_chain_not_verified")
    active: list[tuple[int, dict[str, Any], dict[str, Any]]] = []
    for index, pack in enumerate(packs):
        location_status = _match(pack["jurisdiction"], location)
        date_active = today >= _date(pack["effective_from"], "effective_from") and (
            pack.get("effective_until") is None
            or today <= _date(pack["effective_until"], "effective_until")
        )
        for rule in pack["rules"]:
            base = {
                "pack_id": pack["id"],
                "pack_version": pack["version"],
                "pack_sha256": validations[index]["sha256"],
                "rule_id": rule["id"],
                "clause": rule["clause"],
                "kind": pack["kind"],
                "fact": rule["fact"],
                "unit": rule["unit"],
                "op": rule["op"],
                "threshold": rule["value"],
            }
            if location_status == "not_applicable" or not date_active:
                checks.append(
                    {
                        **base,
                        "status": "not_applicable",
                        "reason": "jurisdiction_or_date_outside_scope",
                    }
                )
                continue
            application = _applicability(document_dict, rule)
            if application == "not_applicable":
                checks.append(
                    {
                        **base,
                        "status": "not_applicable",
                        "reason": "declared_applicability_excluded",
                    }
                )
                continue
            reasons = list(pack_reasons[index])
            if location_status != "applicable":
                reasons.append("jurisdiction_missing")
            if application == "not_verified":
                reasons.append("applicability_fact_missing")
            if pack["kind"] == "regulatory":
                reasons.extend(validations[index]["unverified_reasons"])
                adoption = pack.get("adoption", {})
                if isinstance(adoption, dict) and adoption.get("effective_on"):
                    try:
                        if today < _date(adoption["effective_on"], "adoption.effective_on"):
                            reasons.append("adoption_not_yet_effective")
                    except ValueError:
                        reasons.append("adoption_date_invalid")
            if reasons:
                checks.append(
                    {**base, "status": "not_verified", "reason": ",".join(sorted(set(reasons)))}
                )
            else:
                active.append((index, rule, base))
    overridden: set[tuple[int, str]] = set()
    bad_overrides: set[tuple[int, str]] = set()
    for index, rule, _ in active:
        dependencies = {dep["id"] for dep in packs[index].get("requires", [])}
        for override in rule.get("overrides", []):
            matches = [
                (parent, old)
                for parent, old, _ in active
                if packs[parent]["id"] == override["pack_id"] and old["id"] == override["rule_id"]
            ]
            if len(matches) != 1 or override["pack_id"] not in dependencies:
                bad_overrides.add((index, rule["id"]))
            else:
                parent, old = matches[0]
                if (old["fact"], old.get("entity_kind"), old.get("where", {})) != (
                    rule["fact"],
                    rule.get("entity_kind"),
                    rule.get("where", {}),
                ):
                    bad_overrides.add((index, rule["id"]))
                else:
                    overridden.add((parent, old["id"]))
    groups: dict[str, list[tuple[int, dict[str, Any]]]] = {}
    for index, rule, _ in active:
        if (index, rule["id"]) in overridden:
            continue
        key = json.dumps(
            [
                rule["fact"],
                rule.get("entity_kind"),
                rule.get("where", {}),
                rule.get("applicability", []),
            ],
            sort_keys=True,
        )
        groups.setdefault(key, []).append((index, rule))
    conflicts = set()
    for group in groups.values():
        # Fail closed on competing threshold interpretations; an exact reviewed
        # parent override is required to silently replace an earlier rule.
        if len({(rule["op"], rule["value"], rule["unit"]) for _, rule in group}) > 1:
            conflicts.update((index, rule["id"]) for index, rule in group)
    for index, rule, base in active:
        key = (index, rule["id"])
        if key in overridden:
            checks.append(
                {**base, "status": "not_applicable", "reason": "explicit_parent_rule_override"}
            )
        elif key in bad_overrides or key in conflicts:
            checks.append(
                {**base, "status": "not_verified", "reason": "amendment_or_threshold_conflict"}
            )
        else:
            facts = _facts(document_dict, rule)
            if not facts:
                checks.append(
                    {**base, "status": "not_verified", "reason": "no_matching_measured_entities"}
                )
            for path, fact in facts:
                value, reason = _measure(fact, rule["unit"])
                if value is None:
                    checks.append(
                        {**base, "fact": path, "status": "not_verified", "reason": reason}
                    )
                else:
                    status, decision_reason = _decision(
                        fact, value, rule["unit"], rule["op"], rule["value"]
                    )
                    checks.append(
                        {
                            **base,
                            "fact": path,
                            "measured": value,
                            "status": status,
                            "reason": decision_reason
                            if status == "not_verified"
                            else (
                                "synthetic_fixture_only"
                                if packs[index]["kind"] == "synthetic"
                                else "reviewed_rule_subset"
                            ),
                            "measurement_basis": decision_reason,
                        }
                    )
                if len(checks) > MAX_CHECKS:
                    raise _error(
                        f"Assessment exceeds {MAX_CHECKS} checks; assess smaller rule subsets."
                    )
    if len(checks) > MAX_CHECKS:
        raise _error(f"Assessment exceeds {MAX_CHECKS} checks; assess smaller rule subsets.")
    counts = {
        status: sum(check["status"] == status for check in checks)
        for status in ("pass", "fail", "not_applicable", "not_verified")
    }
    return {
        "status": "fail" if counts["fail"] else "not_verified",
        "assessment_date": today.isoformat(),
        "document_revision": document_dict.get("revision"),
        "checks": checks,
        "counts": counts,
        "coverage": cov,
        "schema_validation": "not_assessed",
        "ids_validation": "not_assessed",
        "geometry_validation": "not_assessed",
        "legal_approval": False,
        "threshold_policy": "versioned_source_interpretations_learning_cannot_modify",
        "source_authentication": "supplied_review_records_not_independently_authenticated",
    }
