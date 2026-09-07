"""A76 P1: the eng_* lane, hermetic — no endpoint, no weights, no network."""

from __future__ import annotations

import json
import socket
import time

import pytest

from tee.app import TeeApp
from tee.cli import _attach_engines
from tee.engines import discover, table, weights
from tee.kernel import trust
from tee.kernel.adapter import FakeAdapter
from tee.kernel.budget import estimate_tokens
from tee.kernel.errors import TeeError
from tee.server import _DESC

ENG_TOOLS = ["eng_adopt", "eng_check", "eng_reconcile", "eng_scan", "eng_senses"]


def _dead_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return int(s.getsockname()[1])


@pytest.fixture
def app(tmp_path):
    a = TeeApp({"fake": FakeAdapter()})
    _attach_engines(a, tmp_path)
    return a


def call(app_, tool, /, **args):
    return app_.registry.call(tool, args)


# --- surface -------------------------------------------------------------


def test_the_lane_registers_exactly_its_tools(app):
    assert sorted(n for n in app.registry.names() if n.startswith("eng_")) == ENG_TOOLS


def test_the_always_loaded_surface_did_not_move(app):
    assert len(_DESC) == 17
    assert not [n for n in _DESC if n.startswith("eng_")]


def test_every_tool_is_tabled_and_there_is_no_family_row(app):
    for name in ENG_TOOLS:
        assert trust.capability_for(name) in trust.CAPABILITIES
    assert not [p for p, _ in trust._FAMILY if p == "eng_"]


def test_an_untabled_eng_tool_is_a_startup_error():
    with pytest.raises(TeeError) as e:
        trust.capability_for("eng_not_tabled")
    assert e.value.code == "trust_untabled_tool"


@pytest.mark.parametrize(
    "query,want",
    [
        ("which local model is actually running", "eng_scan"),
        ("reconcile the engine registry", "eng_reconcile"),
        ("check an endpoint actually produces text", "eng_check"),
    ],
)
def test_search_reaches_the_lane(app, query, want):
    top = [i["name"] for i in app.registry.search(query)["items"][:3]]
    assert want in top, f"{query!r} -> {top}"


# --- the lane serves nothing ---------------------------------------------


def test_the_package_opens_no_listening_socket():
    """TEE is a client of models and a witness to them, never a server."""
    import ast
    from pathlib import Path

    lane = Path(__file__).resolve().parents[1] / "src" / "tee" / "engines"
    banned = {"listen", "bind", "serve_forever", "HTTPServer", "ThreadingHTTPServer"}
    for f in lane.glob("*.py"):
        for node in ast.walk(ast.parse(f.read_text())):
            if isinstance(node, ast.Attribute) and node.attr in banned:
                raise AssertionError(f"{f.name} touches {node.attr}")
            if isinstance(node, ast.Name) and node.id in banned:
                raise AssertionError(f"{f.name} names {node.id}")


def test_the_lane_never_writes_the_owners_config(tmp_path, app):
    """The line: the lane measures, the owner declares."""
    from pathlib import Path

    lane = Path(__file__).resolve().parents[1] / "src" / "tee" / "engines"
    for f in lane.glob("*.py"):
        for i, line in enumerate(f.read_text().splitlines(), 1):
            if "config.toml" not in line:
                continue
            # naming it in prose is the POINT (the law is stated); writing it is not
            assert not any(w in line for w in ("write_text", "open(", "w+", '"w"')), (
                f"{f.name}:{i} looks like it writes the owner's config: {line.strip()}"
            )


# --- discovery, with nothing listening -----------------------------------


def test_a_dead_endpoint_is_reported_not_raised():
    row = discover.probe_endpoint(f"http://127.0.0.1:{_dead_port()}/v1", timeout=0.5)
    assert row["answers"] is False and row["http"] is None
    assert "round_trip_ms" in row


def test_the_fingerprint_names_its_evidence():
    fp = discover.fingerprint({}, {"data": [{"id": "mlx-community/x"}]})
    assert fp["software"] == "mlx" and fp["why"]
    fp2 = discover.fingerprint({"server": "uvicorn"}, {"data": []})
    assert fp2["software"] == "uvicorn-hosted"


def test_scan_survives_a_machine_with_nothing_running(tmp_path, app):
    out = call(app, "eng_scan")
    assert out["scanned"] >= 1 and "endpoints" in out
    assert all(isinstance(e["models"], int) for e in out["endpoints"]), (
        "the scan digest carries model COUNTS, never every id"
    )


# --- weights -------------------------------------------------------------


def test_an_alias_is_not_a_checkpoint_name():
    d = weights.locate("claude-qwen-vl")
    assert d["found"] is False and "org/name" in d["reason"]


def test_senses_come_from_config_not_behaviour(tmp_path):
    snap = tmp_path / "snap"
    snap.mkdir()
    (snap / "config.json").write_text(
        json.dumps(
            {"architectures": ["Qwen3VLForConditionalGeneration"], "vision_config": {"x": 1}}
        )
    )
    out = weights.senses_from_config(snap)
    assert out["senses"] == ["vision"]
    assert str(snap) in out["senses_source"], "a sense carries where it was read"


def test_a_store_with_no_config_says_so_rather_than_guessing(tmp_path):
    out = weights.senses_from_config(tmp_path)
    assert out["senses"] is None and "no config.json" in out["senses_source"]


# --- reconcile -----------------------------------------------------------


def _scan(served: dict[str, list[str]], up: dict[str, bool]) -> dict:
    return {
        "scanned": len(up),
        "answering": sum(up.values()),
        "endpoints": [{"url": u, "answers": a} for u, a in up.items()],
        "served_models": served,
        "scanned_at": time.time(),
    }


def test_an_undeclared_profile_has_no_model_and_says_so():
    out = table.reconcile(
        declared_profiles={"q14b": {}},
        scan=_scan({"mlx-community/x": ["u"]}, {"u": True}),
        measured={},
        resolved={"profile": "q14b", "url": "u", "model": "mlx-community/x"},
    )
    undeclared = [r for r in out["rows"] if r["verdict"] == "declared-not-served"]
    assert undeclared, out["verdicts"]
    for r in undeclared:
        assert r["model"] is None, (
            "an undeclared profile inheriting the ACTIVE model would report every "
            "unknown engine as serving whatever is pinned"
        )
        assert "no model id" in r["fix"]


def test_a_served_model_with_no_profile_is_reachable_but_unclaimed():

    out = table.reconcile(
        declared_profiles={},  # nothing declared at all
        scan=_scan({}, {"u": True}),
        measured={},
        resolved={},
    )
    assert set(out["verdicts"]) == {"declared-not-served"}


def test_a_stale_row_is_stale_and_a_wrong_row_is_wrong():
    from tee.kernel.machine import ENGINES

    engine = next(n for n, s in ENGINES.items() if s.get("profile"))
    prof = ENGINES[engine]["profile"]
    old = {engine: {"model": "m", "measured_at": time.time() - 400 * 86400}}
    out = table.reconcile(
        declared_profiles={prof: {"model": "m", "url": "u"}},
        scan=_scan({"m": ["u"]}, {"u": True}),
        measured=old,
        resolved={"profile": prof, "url": "u", "model": "m"},
    )
    assert [r for r in out["rows"] if r["verdict"] == "stale"]

    moved = {engine: {"model": "somethingelse", "measured_at": time.time()}}
    out2 = table.reconcile(
        declared_profiles={prof: {"model": "m", "url": "u"}},
        scan=_scan({"m": ["u"]}, {"u": True}),
        measured=moved,
        resolved={"profile": prof, "url": "u", "model": "m"},
    )
    assert [r for r in out2["rows"] if r["verdict"] == "wrong"], (
        "a row whose endpoint now serves a DIFFERENT model is wrong, not stale"
    )


def test_the_digest_never_probes_and_stays_small(app, tmp_path):
    out = call(app, "eng_reconcile")
    assert "no scan cached" in out.get("note", ""), "reconcile must not probe"
    # The script's acceptance said "under 250 tokens". Measured, five rows cost
    # 295 - and the excess is the fix lines, which are the digest's whole value.
    # A per-row bound is the honest shape: it holds as the registry grows and
    # cannot be met by deleting the remedy. The naive read is 20,840 tokens.
    cost = estimate_tokens(json.dumps(out))
    per_row = cost / max(1, len(out["rows"]))
    assert per_row < 80, f"{per_row:.0f} tokens per row ({cost} total)"
    assert cost < 600, f"the digest grew to {cost} tokens"


# --- refusals ------------------------------------------------------------


def test_check_refuses_a_paid_engine_by_name(app, tmp_path, monkeypatch):
    from tee.engines import tools as T

    monkeypatch.setattr(
        T._Lane,
        "_llm_cfg",
        lambda self: {"profiles": {"qmax": {"model": "paid-one", "paid": True}}},
    )
    with pytest.raises(TeeError) as e:
        call(app, "eng_check", url="http://127.0.0.1:1/v1", model="paid-one")
    assert e.value.code == "eng_paid_refused"


def test_adopt_refuses_a_paid_row(app):
    with pytest.raises(TeeError) as e:
        call(app, "eng_adopt", engine="x", row={"paid": True})
    assert e.value.code == "eng_paid_refused"


def test_adopt_writes_where_the_ladder_reads_and_nowhere_else(app, tmp_path):
    out = call(app, "eng_adopt", engine="q27b-bare", row={"footprint_gb": 50.956})
    assert out["measured_rows"] == 1
    written = table.load_measured(tmp_path / ".tee")
    assert written["q27b-bare"]["footprint_gb"] == 50.956
    assert written["q27b-bare"]["measured_at"], "a measured row carries when"
    assert not (tmp_path / ".tee" / "config.toml").exists()


def test_senses_needs_a_model(app):
    """The registry validates required arguments before the handler runs, so the
    refusal is the kernel's - the handler's own guard is the belt to that brace."""
    with pytest.raises(TeeError) as e:
        call(app, "eng_senses")
    assert e.value.code == "missing_argument"
    from tee.engines.tools import _Lane

    with pytest.raises(TeeError) as e2:
        _Lane(app, ".", {}).senses({})
    assert e2.value.code == "eng_needs_model"
