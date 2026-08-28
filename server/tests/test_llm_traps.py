"""The API-defer trap suite (A34 M2 acceptance; research 50 addendum).

Runs against a REAL local model (llm marker): seeded tracebacks whose
correct fix depends on an API fact the evidence omits must come back
confidence='needs_verification' - inventing an API blocks adoption
outright. Grounded controls keep always-deferring from passing.
"""

from __future__ import annotations

import pytest
from fixtures_llm import CONTROLS, TRAPS

from tee.kernel import local_llm
from tee.llm import chores

pytestmark = pytest.mark.llm


@pytest.fixture(scope="module")
def live() -> dict:
    if not local_llm.available():
        pytest.skip(f"no local model at {local_llm.DEFAULT_URL}")
    return {}


@pytest.mark.parametrize("case", TRAPS, ids=[t["name"] for t in TRAPS])
def test_traps_defer_instead_of_inventing(live: dict, case: dict) -> None:
    result = chores.triage(case["failure"], case["context"], refine="local")
    assert result is not None
    assert result["confidence"] == "needs_verification", (
        f"{case['name']}: the model answered '{result['fix']}' as grounded - "
        "an API fact not in the evidence was asserted from weights"
    )


@pytest.mark.parametrize("case", CONTROLS, ids=[c["name"] for c in CONTROLS])
def test_controls_stay_grounded(live: dict, case: dict) -> None:
    result = chores.triage(case["failure"], case["context"], refine="local")
    assert result is not None
    assert result["confidence"] == "grounded", (
        f"{case['name']}: the evidence contains the whole fix; deferring "
        "here means the chore adds nothing"
    )
