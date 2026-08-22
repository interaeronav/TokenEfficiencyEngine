"""Phase 12: digest lane, Verse lint, adapter fakes, export validator,
coordinate normalization, license hygiene."""

from __future__ import annotations

import pytest
from fixtures_uefn import (
    CLEAN_SNIPPET,
    DIGEST_V41,
    DIGEST_V42,
    HALLUCINATED_SNIPPET,
)

from tee.app import TeeApp
from tee.kernel.adapter import FakeAdapter
from tee.kernel.errors import TeeError
from tee.uefn.adapter import FakeUefn, luf_to_xyz, xyz_to_luf
from tee.uefn.digest import all_classes, digest_diff, find_member, parse_digest
from tee.uefn.export import validate_export
from tee.uefn.lint import explain_error, lint
from tee.uefn.templates import instantiate

# -- digest parsing ---------------------------------------------------------


def test_digest_parses_fixture():
    digest = parse_digest(DIGEST_V42, version="v42")
    classes = all_classes(digest)
    assert "button_device" in classes
    assert classes["button_device"]["parents"] == ["creative_device"]
    member = classes["button_device"]["members"]["Enable"]
    assert member["kind"] == "function" and "transacts" in member["effects"]
    event = classes["button_device"]["members"]["InteractedWithEvent"]
    assert event["kind"] == "event"
    # inherited member resolution
    assert find_member(digest, "button_device", "OnBegin") is not None


def test_digest_diff_emits_drift_facts():
    """Acceptance: diff between fixture versions emits the drift facts."""
    old = parse_digest(DIGEST_V41, version="v41")
    new = parse_digest(DIGEST_V42, version="v42")
    diff = digest_diff(old, new)
    kinds = {(f["kind"], f.get("member")) for f in diff["drift"]}
    assert ("member_removed", "GetPassengers") in kinds
    assert ("member_added", "GetOccupants") in kinds
    assert ("member_added", "HoldToInteractEvent") in kinds
    effects = [f for f in diff["drift"] if f["kind"] == "effects_changed"]
    assert any(f["member"] == "Eject" for f in effects)  # transacts -> reads/writes
    assert diff["breaking"]  # removals + effect changes are breaking


# -- lint -------------------------------------------------------------------


def test_lint_clean_snippet_passes():
    digest = parse_digest(DIGEST_V42, version="v42")
    out = lint(CLEAN_SNIPPET, digest)
    assert out["findings"] == [], out
    assert "NOT a compile" in out["boundary"]


def test_lint_catches_seeded_hallucinations():
    """Acceptance: <varies>, a removed member, and an invented device
    method are rejected with exact fixes."""
    digest = parse_digest(DIGEST_V42, version="v42")
    out = lint(HALLUCINATED_SNIPPET, digest)
    by_symbol = {f["symbol"]: f for f in out["findings"]}
    varies = by_symbol.get("<varies>")
    assert varies and "v30.00" in varies["fix"]
    passengers = next(f for s, f in by_symbol.items() if "GetPassengers" in s)
    assert "GetOccupants" in passengers["fix"]
    explode = next(f for s, f in by_symbol.items() if "Explode" in s)
    assert (
        "not in the button_device digest entry" in explode["fix"]
        or "not on button_device" in explode["fix"]
    )
    magic = next((f for s, f in by_symbol.items() if "MagicEvent" in s), None)
    assert magic and "listenable" in magic["fix"]


def test_error_map_includes_stale_validation():
    out = explain_error("stale_validation")
    assert "PREVIOUS build" in out["fix"]
    unknown = explain_error("vErr:S99999")
    assert "uefn_lint" in unknown["fix"]


# -- templates --------------------------------------------------------------


def test_template_validates_against_digest():
    digest = parse_digest(DIGEST_V42, version="v42")
    out = instantiate("device_subscribe", digest, name="door_opener")
    assert "door_opener := class(creative_device)" in out["code"]
    assert out["digest_version"] == "v42"


def test_template_rejects_drifted_digest():
    # a digest missing button_device entirely
    tiny = parse_digest("Verse<public> := module:\n", version="tiny")
    with pytest.raises(TeeError) as err:
        instantiate("device_subscribe", tiny)
    assert err.value.code == "template_digest_mismatch"
    assert "button_device" in err.value.message


# -- LUF <-> XYZ ------------------------------------------------------------


def test_luf_xyz_round_trip_property():
    """Acceptance: round-trip is exact over a coordinate grid."""
    values = [-512.0, -1.5, 0.0, 0.25, 100.0, 4096.0]
    for x in values:
        for y in values:
            for z in values:
                assert xyz_to_luf(luf_to_xyz([x, y, z])) == [x, y, z]
                assert luf_to_xyz(xyz_to_luf([x, y, z])) == [x, y, z]


def test_luf_xyz_axes_meaning():
    # forward in LUF becomes +X in UE; up stays up
    assert luf_to_xyz([0, 0, 1]) == [1, 0, 0]
    assert luf_to_xyz([0, 1, 0]) == [0, 0, 1]
    assert luf_to_xyz([1, 0, 0]) == [0, -1, 0]  # left = -right


# -- adapter fakes + capability probe ---------------------------------------


def test_capability_probe_degrades_cleanly():
    """Acceptance: no editor -> offline mode with remediation, no crash."""
    offline = FakeUefn(editor_present=False).probe().to_payload()
    assert offline["mode"] == "offline"
    assert "digest facts + lint" in offline["available_offline"]
    gated = FakeUefn(editor_present=True, beta_access=False).probe().to_payload()
    assert gated["mode"] == "gated"
    assert "Beta Access" in gated["fix"]
    live = FakeUefn().probe().to_payload()
    assert live["mode"] == "live" and "verse" in live["toolsets"]


def test_scene_graph_batch_normalizes_coordinates():
    uefn = FakeUefn()
    out = uefn.entity_batch(
        [
            {
                "op": "create_entity",
                "name": "Crate",
                "position_xyz": [512, 256, 128],
                "components": ["Transform", "mesh_component"],
            }
        ]
    )
    eid = out["created"][0]
    entities = uefn.entities()
    entity = next(e for e in entities if e["id"] == eid)
    assert entity["position_xyz"] == [512, 256, 128]  # LUF round-trip inside
    assert "mesh_component" in entity["components"]


def test_device_catalog_local_index():
    uefn = FakeUefn(editor_present=False)  # catalog works OFFLINE
    hits = uefn.device_catalog("trigger")
    assert hits and all("device" in h for h in hits)
    with pytest.raises(TeeError):
        uefn.place_device("button_device", [0, 0, 0])  # placement needs live


# -- export validator -------------------------------------------------------


def _good_asset():
    return {
        "name": "crate",
        "complexity": "medium",
        "dims_m": [0.8, 0.8, 0.8],  # S size class
        "lods": [{"tris": 650}, {"tris": 320}, {"tris": 160}],
        "textures": [
            {"name": "crate_D", "px": [1024, 1024]},
            {"name": "crate_SRM", "px": [1024, 1024]},
        ],
        "material_sections": 1,
        "collision_meshes": ["UCX_crate_00"],
        "applied_transforms": True,
    }


def test_export_conformant_asset_passes():
    out = validate_export(_good_asset())
    assert out["export_ready"] is True
    assert out["violations"] == []
    assert "export-ready" in out["summary"]


def test_export_flags_every_seeded_violation():
    """Acceptance: over-cap LOD0, missing LODs, NPOT texture, bad UCX
    name, unapplied scale - each with the exact fix."""
    bad = {
        "name": "kitbash",
        "complexity": "simple",
        "dims_m": [0.5, 0.5, 0.5],  # S: cap 400
        "lods": [{"tris": 5000}],
        "textures": [{"name": "diff", "px": [3000, 2048]}],
        "material_sections": 4,
        "collision_meshes": ["crate_collision"],
        "applied_transforms": False,
        "procedural_materials": True,
    }
    out = validate_export(bad)
    assert out["export_ready"] is False
    checks = {v["check"] for v in out["violations"]}
    assert {
        "lod0_tris",
        "lod_count",
        "power_of_two",
        "collision_prefix",
        "transforms",
        "procedural_materials",
    } <= checks
    lod0 = next(v for v in out["violations"] if v["check"] == "lod0_tris")
    assert lod0["cap"] == 400 and "decimate" in lod0["fix"]
    ucx = next(v for v in out["violations"] if v["check"] == "collision_prefix")
    assert "UCX_" in ucx["fix"]


def test_export_texture_hard_max():
    asset = _good_asset()
    asset["textures"] = [{"name": "huge", "px": [8192, 8192]}]
    out = validate_export(asset)
    assert any(v["check"] == "texture_max" for v in out["violations"])


# -- tools end-to-end -------------------------------------------------------


@pytest.fixture()
def app(tmp_path):
    from tee.uefn.tools import register_uefn_tools

    application = TeeApp({"fake": FakeAdapter()}, project_root=tmp_path)
    register_uefn_tools(application, tmp_path, uefn=FakeUefn())
    return application


def test_uefn_tools_end_to_end(tmp_path, app):
    assert app.registry.call("uefn_status", {})["mode"] == "live"
    loaded = app.registry.call("uefn_digest_load", {"text": DIGEST_V42, "version": "v42"})
    assert loaded["classes"] >= 4
    app.registry.call("uefn_digest_load", {"text": DIGEST_V41, "version": "v41"})
    diff = app.registry.call("uefn_digest_diff", {"from": "v41", "to": "v42"})
    assert diff["breaking"]
    lint_out = app.registry.call("uefn_lint", {"code": HALLUCINATED_SNIPPET, "version": "v42"})
    assert lint_out["findings"]
    template = app.registry.call(
        "uefn_template", {"template": "device_subscribe", "version": "v42"}
    )
    assert "creative_device" in template["code"]
    batch = app.registry.call(
        "uefn_entity_batch",
        {"ops": [{"op": "create_entity", "name": "Crate", "position_xyz": [100, 0, 50]}]},
    )
    assert batch["created"]
    coords = app.registry.call("uefn_coords", {"luf": [1, 2, 3]})
    assert coords["xyz"] == [3, -1, 2]
    preflight = app.registry.call("export_preflight", {"asset": _good_asset()})
    assert preflight["export_ready"]


def test_uefn_lint_without_digest_names_fix(tmp_path):
    from tee.uefn.tools import register_uefn_tools

    application = TeeApp({"fake": FakeAdapter()}, project_root=tmp_path)
    register_uefn_tools(application, tmp_path)  # offline default
    with pytest.raises(TeeError) as err:
        application.registry.call("uefn_lint", {"code": "x"})
    assert err.value.code == "no_digest"
    assert "never bundled" in (err.value.fix or "")


def test_pack_channels(tmp_path, app):
    from PIL import Image

    rough = tmp_path / "rough.png"
    Image.new("L", (64, 64), 180).save(rough)
    out = app.registry.call("uefn_pack_channels", {"roughness": str(rough), "size": 256})
    assert out["channels"] == {"R": "specular", "G": "metallic", "B": "roughness"}
    with Image.open(out["path"]) as img:
        assert img.size == (256, 256)
        r, g, b = img.getpixel((10, 10))
        assert (r, g, b) == (128, 0, 180)


# -- license hygiene (acceptance) -------------------------------------------


def test_no_agpl_and_no_epic_digest_text_in_repo():
    """Acceptance: license lint - no AGPL-derived code, no Epic digest
    text. The fixtures declare themselves synthetic."""
    from pathlib import Path

    root = Path(__file__).resolve().parents[2]
    suspects = []
    for path in (root / "server" / "src").rglob("*.py"):
        text = path.read_text(errors="ignore")
        if "AGPL" in text and "reference-only" not in text and "never" not in text:
            suspects.append(str(path))
        # Epic digest text would carry these signature paths verbatim
        if "/Fortnite.com/Devices}" in text.replace(" ", "") and "digest" in path.name:
            suspects.append(f"{path} (digest-like content)")
    assert suspects == [], suspects
    # the test fixtures are explicitly synthetic
    fixture = Path(__file__).parent / "fixtures_uefn.py"
    assert "synthetic" in fixture.read_text()


@pytest.mark.network
def test_uefn_analytics_live(tmp_path, app, network):
    """Public Fortnite Data API, unauthenticated (skips offline)."""
    out = app.registry.call("uefn_analytics", {"island": "6560-2820-9190", "interval": "day"})
    assert out["island"] == "6560-2820-9190"
    # either aggregated metrics or the sparse-data note - both valid
    assert len(out) > 2 or "note" in out
