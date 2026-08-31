"""The ONE machine-load ledger + the registry-form engine facts (A42 R1
seams 1+3): schema-complete rows, job registration both directions, and
may_swap refusing with the honest line while a registered job holds the
machine."""

from __future__ import annotations

import pytest

from tee.kernel.errors import TeeError
from tee.kernel.machine import ENGINES, QOS, RESERVE_GB, MachineLedger


def test_registry_rows_carry_the_k_layer_schema():
    assert QOS == ("interactive", "standard", "batch", "maintenance")
    for name, spec in ENGINES.items():
        assert spec["kind"] in ("llm", "job", "client", "sense"), name
        assert spec["capability"], name
        assert spec["footprint_gb"] >= 0, name
        assert spec["qos_default"] in QOS, name
        assert spec["cost"], name
    # llm rows bind to their switch profiles
    assert ENGINES["q14b+a2"]["profile"] == "q14b"
    assert ENGINES["q27b-bare"]["profile"] == "q27b"
    # A47: sense rows are a distinct kind - they convert media rather than
    # reason, so they carry `senses` and an `evicts` list. Every llm row
    # declares its senses too, because "this model is blind" is a fact the
    # router needs stated, not inferred from an absent key.
    for name, spec in ENGINES.items():
        if spec["kind"] == "sense":
            assert spec["senses"], name
            assert isinstance(spec["evicts"], list), name
        if spec["kind"] == "llm":
            # A49 P0: a chore engine's senses are whatever its own config
            # says - q27b-bare really does see. What the schema requires is
            # that the claim EXISTS and cites where it was read from, not
            # that it is empty.
            assert isinstance(spec["senses"], list), name
            assert spec.get("senses_source"), f"{name} declares senses with no source"


def test_register_release_and_footprint():
    ledger = MachineLedger(total_gb=128)
    row = ledger.register_job("set1@odm", "reconstruct-odm")
    assert row["qos"] == "batch" and row["footprint_gb"] == 16.0
    assert ledger.jobs_footprint_gb() == 16.0
    ledger.register_job("set2@photogrammetry", "reconstruct-photogrammetry")
    assert len(ledger.active_jobs()) == 2
    ledger.release_job("set1@odm")
    ledger.release_job("set2@photogrammetry")
    ledger.release_job("never-registered")  # releasing the unknown is a no-op
    assert ledger.active_jobs() == []


def test_unknown_job_engine_refuses_with_the_known_list():
    ledger = MachineLedger(total_gb=128)
    with pytest.raises(TeeError) as excinfo:
        ledger.register_job("x", "q14b+a2")  # an llm row is not a job engine
    assert excinfo.value.code == "machine_unknown_engine"
    assert "reconstruct-odm" in excinfo.value.fix


def test_swap_refused_while_a_registered_job_holds_the_machine():
    ledger = MachineLedger(total_gb=128)
    ledger.register_job("okongo@odm", "reconstruct-odm")
    capable, reason = ledger.may_swap("q27b-bare")
    assert capable is False
    assert "okongo@odm" in reason and "batch" in reason and "deferred" in reason
    ledger.release_job("okongo@odm")
    capable, reason = ledger.may_swap("q27b-bare")
    assert capable is True and "capable" in reason


def test_swap_refused_when_the_footprint_does_not_fit():
    ledger = MachineLedger(total_gb=32)
    capable, reason = ledger.may_swap("q27b-bare")  # 55 GB into 32-16
    assert capable is False
    assert "55 GB" in reason and f"{RESERVE_GB:.0f}" in reason
    capable, _ = ledger.may_swap("q14b+a2")  # 9 GB fits
    assert capable is True


def test_unknown_swap_target_is_named():
    capable, reason = MachineLedger(total_gb=128).may_swap("gpt-x")
    assert capable is False and "not in the registry" in reason
