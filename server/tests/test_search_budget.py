"""A50 — the search reply costs what it must and no more.

`tee_search_tools` is the most frequent call TEE makes on its own behalf:
every virtual-tool reach starts with one. Its default returned 10 items at
~370 tokens when 5 finds everything 10 finds, measured over 19 realistic
queries against a 42-tool registry.

RE-BASELINED 2026-09-04 (A66). The corpus grew from 67 tools to 81 when the
partkiln lane registered its 14 `pk_*` tools, and a bigger corpus is a
different measurement, not a broken one. Re-run over the CASES below, on the
registry as it now is:

    limit 3   28/29      limit 5   29/29
    limit 8   29/29      limit 10  29/29

Five still finds everything ten finds, and three still does not, so the
default stands on its own evidence rather than on 2025's. What moved: A50's
rank-4 witness was "check the drawing" -> `ex_estimate`, which scored 2.0
(the word "drawing" in its description) and survived at exactly rank 5.
`pk_check` and `pk_drawing` now score 4.0 on that query by NAME - 3.0 for the
name hit plus 1.0 for the ubiquitous "the" - and `ex_estimate` fell to rank 7.
No tag or description edit can undo that without lying about the tools: a
name hit cannot be tagged away, `pk_drawing` does write drawings and
`pk_check` does check. So the query was reassigned to its honest owner and
"size from an image" -> `ex_estimate` (rank 4) took over as the witness that
three is not enough. The five direct `pk_*` cases were added for the same
reason the `pc_*` block was: a lane that grows the corpus must be findable in
it, or it has made every other search worse for nothing.

RE-MEASURED 2026-09-04 (A67 second pass) at 85 tools, after `pc_crop`,
`pc_clean`, `pc_ortho` and `pc_merge` landed and four cases were added for
them. The table is unmoved - 3 still misses exactly one, 5 still finds all 33
- so four more tools cost the search nothing. That is the result worth having:
the case for progressive disclosure is that the corpus can grow without the
reach getting worse, and this is the file that would catch it if it did.

RE-BASELINED 2026-09-05 (A68) on the registry a Desktop server ACTUALLY
serves: the manifest's three lanes with bl_*/hb_* attached and every kernel
lane cmd_serve attaches - 173 tools, not the 85 this fixture used to hold.
The first measurement on it found the old table false: "size from an image"
ranked `ex_estimate` SIXTH, behind `bl_build_from_plan` (3.0 for the word
"from" in its name), `pdf_compose`, `sk_body`, `board_compose` and
`cad_scad_build`, because the tool never said "image" or "size" about
itself. Tagging it with both - its own vocabulary, nobody else's - put it
first. Five cases were added (three for the garment lane, which had none,
and two for the routing this campaign is about), and the table re-run over
38 cases:

    limit 3   35/38      limit 5   38/38
    limit 8   38/38      limit 10  38/38

Three now misses three (watermark -> pdf_edit at 4, check the drawing ->
pk_drawing at 5, best allocation -> quant_optimize at 4), five still finds
everything, so the default stands on the corpus it is actually used on.
"""

from __future__ import annotations

import json
import tempfile

import pytest

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
    ("crop the clutter out of a scan", "pc_crop"),
    ("remove outliers from a point cloud", "pc_clean"),
    ("rectified facade image to trace", "pc_ortho"),
    ("combine two scans into one cloud", "pc_merge"),
    # A66: the pk_* lane, 14 tools, is the corpus growth this file was
    # re-baselined against - so it is measured here rather than assumed
    ("dimensioned drawing sheet", "pk_drawing"),
    ("check a part against a spec", "pk_check"),
    ("unfold sheet metal to a flat pattern", "pk_flat"),
    ("bill of materials for the assembly", "pk_bom"),
    ("export a solid to step", "pk_export"),
    # deliberately vague - these are why the default is 5 and not 3
    ("make a document", "pdf_compose"),
    ("look at this", "sense_describe"),
    ("what does the scene look like", "sense_viewport"),
    # A66: this query used to want ex_estimate and now wants the partkiln
    # lane, which owns both of its content words by name. See the module
    # docstring: the reassignment is the finding, not a workaround.
    ("check the drawing", "pk_drawing"),
    # A66: the replacement rank-4 witness. ex_estimate is what a caller
    # wants here and it sits behind three tools that merely mention a size
    # or an image, so a default of 3 would lose it.
    ("size from an image", "ex_estimate"),
    ("find the best allocation", "quant_optimize"),
    # A68: the garment lane had no case at all, and the registry this file
    # measures is now the one a Desktop server serves (bl_*/hb_* attached,
    # every kernel lane), so the lanes a model routes between are all here
    ("tech pack for a garment", "sk_techpack"),
    ("hand the garment to blender", "sk_handoff"),
    ("plot the pattern at full size", "sk_plot"),
    ("import a glb into the scene", "as_import"),
    ("what ops does the mechanical cad lane take", "pk_verbs"),
]


@pytest.fixture(scope="module")
def registry():
    """The registry a Desktop server actually serves (A68): the manifest's
    three lanes with Blender's own bl_*/hb_* tools attached, and every
    kernel lane cmd_serve attaches. Until A68 this fixture held 85 tools and
    said 33/33 at the shipped limit; the 173-tool registry it now holds is
    what the number has to be true of."""
    from importlib import import_module

    from tee import cli
    from tee.adapters.partkiln import PartkilnAdapter

    fake_kernel = import_module("fixtures_partkiln").FakeKernel
    root = tempfile.mkdtemp()
    lanes = [
        cli._blender_lane("127.0.0.1", 1),  # registers bl_*/hb_*; never contacts a bridge
        cli.Lane("partkiln", PartkilnAdapter(root, kernel=fake_kernel())),
        cli._seamkiln_lane(root),
    ]
    app = cli.build_app(lanes, root, allow_code_exec=False)
    store = cli._attach_extract(app, root, with_handoff=True)
    cli._attach_assets(app, root, store)
    cli._attach_capture(app, root, store)
    cli._attach_pointcloud(app, root)
    cli._attach_pipeline(app, root)
    cli._attach_design(app, root)
    cli._attach_senses(app, root)
    cli._attach_pdf(app, root)
    cli._attach_purge(app, root)
    cli._attach_physical(app, root)
    cli._attach_uefn(app, root)
    cli._attach_kb(app, root)
    cli._attach_llm(app, root)
    cli._attach_web(app, root)
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
    smallest defensible-looking number.

    A66: the witness was "size from an image" -> ex_estimate at rank 4.
    A68: on the Desktop registry that query ranks first once the tool says
    "image" about itself; three other queries land at rank 4-5 (watermark,
    check the drawing, best allocation). Recall over CASES is 35/38 at
    limit 3 and 38/38 at 5, 8 and 10."""
    beyond_three = [
        query
        for query, want in CASES
        if want not in [i["name"] for i in registry.search(query, limit=3)["items"]]
    ]
    assert beyond_three, "if nothing needs rank 4+, revisit the default"


def test_the_rebaselined_recall_table_holds(registry):
    """The docstring's table, executed. A50 recorded its numbers in prose and
    the prose went stale the moment the corpus grew; measured here, a future
    lane that costs recall at 5 - or that makes 3 sufficient again, which
    would mean the default is now too big - fails instead of drifting."""
    recall = {
        limit: sum(
            1
            for query, want in CASES
            if want in [i["name"] for i in registry.search(query, limit=limit)["items"]]
        )
        for limit in (3, 5, 8, 10)
    }
    assert recall == {3: len(CASES) - 3, 5: len(CASES), 8: len(CASES), 10: len(CASES)}
    assert len(CASES) == 38  # 2026-09-05, the 173-tool Desktop registry (85 before A68)


def test_the_reply_stays_small(registry):
    """~229 tokens against ~370 at the old default of 10."""
    reply = registry.search("write a pdf report")
    assert len(reply["items"]) <= 5
    assert len(json.dumps(reply)) // 4 < 280


def test_a_truncated_search_says_how_much_it_hid(registry):
    """A caller must be able to tell 'that is everything' from 'that is the
    top five'. Without it, an empty tail is indistinguishable from a hidden
    one."""
    # "image" matches more tools than the default returns; "portfolio"
    # matches only three, so it has nothing to hide - which is the other
    # half of the contract and the reason this test names both.
    #
    # A66: the narrow half used to be "pdf". It now matches six tools
    # (pdf_compose, pdf_edit, pk_drawing, sk_plot, sk_techpack, ex_ingest),
    # because pk_drawing genuinely writes PDF sheets and says so. Six is
    # the honest count, so the query - not the tool description - is what
    # had to change.
    reply = registry.search("image")
    assert reply.get("more", 0) >= 1
    assert len(reply["items"]) == 5
    narrow = registry.search("portfolio")
    assert len(narrow["items"]) == 3
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
