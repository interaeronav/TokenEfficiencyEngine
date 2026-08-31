"""A47 P0/P0.5 — the machine declares what it can perceive, and where it
is rooted.

Two silences fixed. TEE knew nothing about its own senses, so a host that
lacked one could not learn whether TEE could lend it one. And `serve
--project` defaults to the launching client's cwd, so a terminal host that
omits it boots away from the owner's grants, keeps the read tiers, loses
every mutation tier, and is told none of that.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

from tee.app import TeeApp
from tee.kernel.machine import ENGINES


def test_the_blind_engines_are_declared_blind():
    """Not an absence of data - a stated fact. dsflash cannot see, and now
    something in TEE knows it."""
    for name in ("dsflash", "q27b-bare", "q14b+a2"):
        assert ENGINES[name]["senses"] == []


def test_the_providers_carry_measured_costs():
    for name in ("qvl", "whisper"):
        row = ENGINES[name]
        assert row["kind"] == "sense"
        assert row["senses"], f"{name} provides no sense"
        assert "measured" in row["cost"], f"{name} carries an unmeasured cost"


def test_the_eviction_is_declared_because_it_is_invisible_otherwise():
    """The shim knows an 84 GB host and a 17 GB eye cannot share 128 GB and
    silently evicts one. That cost appeared in no ledger and no answer."""
    qvl = ENGINES["qvl"]
    assert qvl["evicts"] == ["dsflash"]
    assert qvl["cost"]["swap_s"] == 10.0
    assert ENGINES["whisper"]["evicts"] == []  # small enough to coexist


def test_sense_providers_never_enter_the_chore_ladder():
    """They convert media; they do not reason. A router that picked one for
    a chore would be routing to the wrong kind of thing entirely."""
    from tee.llm.router import LADDER

    for name in LADDER:
        assert ENGINES[name]["kind"] == "llm"
    assert "qvl" not in LADDER and "whisper" not in LADDER


def test_no_two_engines_still_claim_one_profile():
    """The A46 P3a lesson, re-run now that rows were added."""
    from collections import Counter

    counts = Counter(e["profile"] for e in ENGINES.values() if "profile" in e)
    assert [p for p, n in counts.items() if n > 1] == []


# -- P0.5: rootedness -------------------------------------------------------


def test_a_grantless_root_says_so_and_names_the_fix():
    rooted = TeeApp({}, project_root=Path(tempfile.mkdtemp())).status()["rooted_at"]
    assert rooted["grants_file"] == "none found"
    assert rooted["granted"] == []
    assert "exec-code" in rooted["denied_tiers"]
    assert "--project" in rooted["fix"]
    assert "reads and project memory work" in rooted["why"]


def test_reporting_rootedness_never_grants_anything():
    """A45's law. Naming the door is not opening it."""
    app = TeeApp({}, project_root=Path(tempfile.mkdtemp()))
    app.status()
    assert sorted(app.registry.grants.granted) == []


def test_doctor_warns_a_first_contact_host(tmp_path):
    from tee.doctor import check_rooted

    c = check_rooted(tmp_path)
    assert c.status == "warn"
    assert "no grants" in c.detail and c.fix


def test_doctor_states_the_machines_senses():
    from tee.doctor import check_senses

    c = check_senses()
    assert "vision" in c.detail and "audio" in c.detail
    # measured numbers, not adjectives
    assert "GB" in c.detail and "s measured" in c.detail
