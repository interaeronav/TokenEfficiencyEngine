"""A50 — the search reply costs what it must and no more.

`tee_search_tools` is the most frequent call TEE makes on its own behalf:
every virtual-tool reach starts with one. Its default returned 10 items at
~370 tokens when 5 finds everything 10 finds, measured over 19 realistic
queries against a 42-tool registry.
"""

from __future__ import annotations

import json
import tempfile

import pytest

from tee.app import TeeApp
from tee.extract.tools import register_extract_tools
from tee.kernel.adapter import FakeAdapter
from tee.pdf import register_pdf_tools
from tee.pointcloud.tools import register_pointcloud_tools
from tee.senses import register_sense_tools

CASES = [
    ("write a pdf report", "pdf_compose"),
    ("add a watermark to a document", "pdf_edit"),
    ("describe what is in an image", "sense_describe"),
    ("transcribe audio speech", "sense_transcribe"),
    ("see the blender viewport", "sense_viewport"),
    ("aim a camera at an object", "sense_camera"),
    ("estimate a length from a photo", "ex_estimate"),
    ("optimise a portfolio", "quant_optimize"),
    ("solve a scheduling problem", "solve_program"),
    ("backtest a trading rule", "trade_backtest"),
    ("measure a step file", "cad_measure"),
    ("dicom study", "med_find_studies"),
    ("ingest site photos", "ex_ingest"),
    ("query a semantic layer", "bi_query"),
    # A67: the pc_* lane must stay findable without displacing the rest
    ("open a lidar scan", "pc_open"),
    ("level a point cloud on its floor", "pc_level"),
    ("floor plan from a scan", "pc_slice"),
    ("check a scan against a tape measurement", "pc_control_verify"),
    # deliberately vague - these are why the default is 5 and not 3
    ("make a document", "pdf_compose"),
    ("look at this", "sense_describe"),
    ("what does the scene look like", "sense_viewport"),
    ("check the drawing", "ex_estimate"),
    ("find the best allocation", "quant_optimize"),
]


@pytest.fixture(scope="module")
def registry():
    root = tempfile.mkdtemp()
    app = TeeApp({"blender": FakeAdapter()}, project_root=root)
    register_extract_tools(app, root)
    register_sense_tools(app, root)
    register_pdf_tools(app, root)
    register_pointcloud_tools(app, root)
    return app.registry


def test_the_default_finds_everything_a_wider_search_would(registry):
    """The measurement the default rests on. If a future change costs recall
    at 5, this fails before anyone ships it."""
    missed = []
    for query, want in CASES:
        names = [i["name"] for i in registry.search(query)["items"]]
        if want not in names:
            wide = [i["name"] for i in registry.search(query, limit=50)["items"]]
            missed.append((query, want, wide.index(want) + 1 if want in wide else None))
    assert missed == [], f"the default lost these: {missed}"


def test_three_would_not_have_been_enough(registry):
    """Recorded so the number is not 'tidied' downward later: at least one
    real query lands at rank 4, which is why 5 is the floor rather than the
    smallest defensible-looking number."""
    beyond_three = [
        query
        for query, want in CASES
        if want not in [i["name"] for i in registry.search(query, limit=3)["items"]]
    ]
    assert beyond_three, "if nothing needs rank 4+, revisit the default"


def test_the_reply_stays_small(registry):
    """~229 tokens against ~370 at the old default of 10."""
    reply = registry.search("write a pdf report")
    assert len(reply["items"]) <= 5
    assert len(json.dumps(reply)) // 4 < 280


def test_a_truncated_search_says_how_much_it_hid(registry):
    """A caller must be able to tell 'that is everything' from 'that is the
    top five'. Without it, an empty tail is indistinguishable from a hidden
    one."""
    # "image" matches more tools than the default returns; "pdf" matches
    # only three, so it has nothing to hide - which is the other half of
    # the contract and the reason this test names both.
    reply = registry.search("image")
    assert reply.get("more", 0) >= 1
    assert len(reply["items"]) == 5
    narrow = registry.search("pdf")
    assert "more" not in narrow, "nothing was suppressed, so nothing should be claimed"
    exact = registry.search("qwertyuiopasdf")
    assert "more" not in exact and exact["items"] == []


def test_a_weak_match_still_says_so(registry):
    reply = registry.search("qwertyuiopasdf")
    assert "no strong match" in reply.get("note", "")


def test_the_default_a_model_sees_matches_the_measured_one():
    """The registry default and the MCP signature are two different
    defaults. The first version of this change moved only the registry's,
    which left every real caller - a model calling tee_search_tools with no
    limit - still paying for ten results. Whichever one a caller reaches
    first is the one that must carry the measurement."""
    import inspect

    from tee import server
    from tee.kernel.registry import ToolRegistry

    assert inspect.signature(ToolRegistry.search).parameters["limit"].default == 5
    source = inspect.getsource(server)
    assert "def tee_search_tools(query: str, limit: int = 5)" in source
