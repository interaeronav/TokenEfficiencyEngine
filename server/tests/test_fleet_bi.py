"""A45 P2d — headless BI (Cube).

Live-server tests skip cleanly without one. The compaction and coercion
are TEE's own code and are asserted directly, because they are the reason
this module exists rather than a passthrough.
"""

from __future__ import annotations

import json
import tempfile
import urllib.error
import urllib.parse
import urllib.request

import pytest

from tee.fleet import bi
from tee.kernel.errors import TeeError

CUBE = {"url": "http://127.0.0.1:4100"}


def _cube_up() -> bool:
    try:
        urllib.request.urlopen(f"{CUBE['url']}/readyz", timeout=2)
        return True
    except Exception:
        return False


needs_cube = pytest.mark.skipif(
    not _cube_up(),
    reason="no Cube on :4100 - docker run -d -p 4100:4000 -v <conf>:/cube/conf cubejs/cube:latest",
)


# -- TEE's own behaviour, no server needed ---------------------------------


def test_numbers_arrive_as_strings_from_cube_and_are_coerced():
    """Cube serialises measures as STRINGS. Passing '210' through as text
    makes every downstream comparison a string comparison."""
    assert bi._round("210") == 210
    assert isinstance(bi._round("210"), int)
    assert bi._round("181.5") == 181.5
    assert bi._round("179.98765") == 179.9877
    assert bi._round("completed") == "completed", "non-numeric strings pass through"
    assert bi._round(None) is None


def test_an_unreachable_cube_names_the_docker_line_and_the_mount_trap():
    with pytest.raises(TeeError) as e:
        bi.catalogue({"url": "http://127.0.0.1:1"})
    assert e.value.code == "bi_unreachable"
    assert "cubejs/cube" in e.value.fix
    assert "/private/tmp" in e.value.fix, "the mount trap cost an hour; say it"


def test_an_empty_query_is_refused_before_any_request():
    with pytest.raises(TeeError) as e:
        bi.query({"url": "http://127.0.0.1:1", "query": {}})
    assert e.value.code == "bi_bad_query"
    assert "bi_catalogue" in e.value.fix


def test_unknown_result_id_refuses():
    with pytest.raises(TeeError) as e:
        bi.detail("bi_nope")
    assert "No result" in e.value.message


def test_bi_is_open_tier_but_taints():
    """A BI read changes nothing, so it needs no grant - but the answer is
    data from a database the model did not read, so it may never go on to
    cause a side effect."""
    from tee.kernel import trust

    assert "read-bi" in trust.READ_TIER
    assert "read-bi" in trust.TAINT_SOURCES
    g = trust.Grants()
    assert trust.check("read-bi", caller="chore", grants=g).allowed
    # ...and a task holding BI output cannot then execute
    d = trust.check("exec-code", caller="chore", grants=g, taint=("read-bi:bi_query",))
    assert not d.allowed and d.enforced


# -- against a live Cube ----------------------------------------------------


@needs_cube
def test_the_catalogue_lists_names_only():
    c = bi.catalogue(dict(CUBE))
    assert c["ok"] is True
    assert c["n_cubes"] >= 1
    row = c["cubes"][0]
    assert set(row) == {"cube", "measures", "dimensions"}
    assert all(isinstance(m, str) for m in row["measures"])


@needs_cube
def test_a_query_returns_a_compact_table_far_smaller_than_cube_sends():
    q = {
        "measures": ["orders.total_amount", "orders.count"],
        "dimensions": ["orders.status"],
        "order": {"orders.total_amount": "desc"},
    }
    r = bi.query(dict(CUBE, query=q))
    assert r["ok"] is True
    assert r["cols"] == ["orders.status", "orders.total_amount", "orders.count"]
    assert r["n_rows"] == 3

    by_status = {row[0]: (row[1], row[2]) for row in r["rows"]}
    assert by_status["processing"] == (210, 1)
    assert by_status["completed"] == (181.5, 3)
    assert by_status["shipped"] == (179.99, 2)
    for _amount, count in by_status.values():
        assert isinstance(count, int), "counts must be numbers, not strings"

    # the whole point: the compact answer is a fraction of Cube's payload
    raw = urllib.request.urlopen(
        f"{CUBE['url']}/cubejs-api/v1/load?query={urllib.parse.quote(json.dumps(q))}",
        timeout=30,
    ).read()
    compact = len(json.dumps({k: v for k, v in r.items() if k != "wall_s"}))
    assert compact < len(raw) * 0.25, f"compact {compact} vs cube {len(raw)}"


@needs_cube
def test_a_bad_member_name_refuses_with_where_to_look():
    with pytest.raises(TeeError) as e:
        bi.query(dict(CUBE, query={"measures": ["orders.nonexistent"]}))
    assert e.value.code in ("bi_query_failed", "bi_http_error")
    assert e.value.fix


@needs_cube
def test_detail_pages_the_stored_result():
    r = bi.query(dict(CUBE, query={"measures": ["orders.count"], "dimensions": ["orders.status"]}))
    d = bi.detail(r["result_id"], offset=1, limit=1)
    assert d["returned"] == 1
    assert d["total"] == r["n_rows"]
    assert d["cols"] == r["cols"]


@needs_cube
def test_probe_reports_reachable_and_the_cubes():
    p = bi.probe(dict(CUBE))
    assert p["reachable"] is True
    assert "orders" in p["cubes"]
    assert "none" in p["dependencies"]


def test_probe_reports_unreachable_without_raising():
    p = bi.probe({"url": "http://127.0.0.1:1"})
    assert p["reachable"] is False
    assert "cubejs/cube" in p["fix"]


def test_registration():
    from tee.app import TeeApp

    app = TeeApp({}, project_root=tempfile.mkdtemp())
    for n in ("bi_catalogue", "bi_query", "bi_detail", "bi_probe"):
        assert app.registry._tools[n].capability == "read-bi"
