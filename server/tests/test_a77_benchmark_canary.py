"""A77 P3: the numbers RESULTS.md quotes fail when they stop being true.

Not all 85 figures — a canary that fires on noise gets silenced, and then it
guards nothing. These are the invariants a change would break *silently*: the
always-loaded surface, the corpus a saving is computed over, and each lane's
headline cost. Every band below is stated, with the reason it is that wide.

The recorded lesson this answers: *"a number quoted in prose needs a test — the
surface figure went stale for four commits because only the tool COUNT had a
canary."* The count had one. The token figure did not. Now both do.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
RESULTS = REPO / "benchmarks" / "RESULTS.md"
sys.path.insert(0, str(REPO / "benchmarks"))


def _quoted(pattern: str) -> int:
    """A number RESULTS.md actually prints, so the test reads the prose."""
    m = re.search(pattern, RESULTS.read_text())
    assert m, f"RESULTS.md no longer contains {pattern!r} — update the row and this test together"
    return int(m.group(1).replace(",", ""))


@pytest.fixture(scope="module")
def surface():
    from run_benchmarks import run_surface_scenario

    row = run_surface_scenario()
    if row is None:  # pragma: no cover - only without the MCP client
        pytest.skip("surface scenario unavailable")
    return row


def test_the_always_loaded_surface_figure_is_still_true(surface):
    """+-2%. Tight on purpose: the one recorded regression moved it +96 tokens
    (A68 gave `adapter=` a description on eight tools), and a band wide enough
    to absorb that would not have caught it."""
    claimed = _quoted(r"TEE always-loaded \(wire\) \| 17 \| \*\*([\d,]+)\*\*")
    actual = surface["wire_tokens"]
    assert abs(actual - claimed) / claimed < 0.02, (
        f"RESULTS.md says {claimed:,} wire tokens; measured {actual:,}. "
        f"Re-run run_surface_scenario and correct the row."
    )


def test_the_saving_is_computed_over_the_corpus_that_ships(surface):
    """Exact, not banded: a tool count is an integer and any change to it is a
    fact, not noise. This is the assertion whose absence let the harness fall
    twelve lanes behind."""
    tools = _quoted(r"the \*\*([\d,]+)\*\* tools they contribute live")
    assert surface["n_virtual_tools"] == tools, (
        f"RESULTS.md says {tools} virtual tools; a served TEE now has "
        f"{surface['n_virtual_tools']}. A lane was added or removed and the row "
        f"was not re-measured."
    )


def test_the_headline_saving_still_holds(surface):
    """+-1 percentage point. A ratio over 30,000 tokens does not wobble."""
    m = re.search(r"behind the meta-tools, a \*\*([\d.]+)%\*\* saving", RESULTS.read_text())
    assert m, "the surface row no longer states a saving"
    assert abs(surface["saving"] - float(m.group(1))) < 1.0, (
        f"RESULTS.md claims {m.group(1)}%; measured {surface['saving']:.1f}%"
    )


@pytest.mark.parametrize(
    "scenario,pattern,band",
    [
        (
            "run_flightdyn_scenario",
            r"`fd_probe` to `fd_fly`, digests only\) \| \*\*([\d,]+)\*\*",
            0.10,
        ),
        (
            "run_engines_scenario",
            r"`eng_scan` \d+ \+ `eng_reconcile` \d+\) \| \*\*([\d,]+)\*\*",
            0.10,
        ),
    ],
)
def test_a_lanes_headline_cost_is_still_true(scenario, pattern, band):
    """+-10%. Wider than the surface figure because a digest carries free text —
    a verdict line rephrased moves it a few tokens and that is not a regression.
    A lane doubling its reply is."""
    import run_benchmarks

    row = getattr(run_benchmarks, scenario)()
    if row is None:
        pytest.skip(f"{scenario} held: its engine is not installed here")
    claimed = _quoted(pattern)
    actual = row["tee_tokens"]
    assert abs(actual - claimed) / claimed < band, (
        f"RESULTS.md says {claimed} tokens; measured {actual} "
        f"({100 * (actual - claimed) / claimed:+.0f}%). Re-run the scenario and "
        f"correct the row — or write up why it moved."
    )


def test_every_scenario_the_harness_defines_is_reachable_from_main():
    """A scenario nobody calls is a row nobody re-runs — how the flightdyn and
    engines rows came to be hand-measured prose in the first place."""
    src = (REPO / "benchmarks" / "run_benchmarks.py").read_text()
    defined = set(re.findall(r"^def (run_[a-z_]+_scenario)\(", src, re.M))
    main = src[src.index("def main()") :]
    called = set(re.findall(r"(run_[a-z_]+_scenario)", main))
    orphans = sorted(defined - called)
    assert not orphans, f"defined but never run by main(): {orphans}"
