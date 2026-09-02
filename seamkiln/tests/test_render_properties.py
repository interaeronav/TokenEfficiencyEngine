"""Render properties on the material card (A65 P3.3).

`roughness` and `texture` ride on `Fabric` so the library, a handoff manifest
and a tech pack can carry them - and every place they appear says they are
NOT physical. The solver never reads them; a glossier card is still the
measured cloth, which is why deriving one keeps the tier.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from seamkiln import materials
from seamkiln.pattern.fabric import Fabric, Tier, fabric
from seamkiln.session import Command, Session


def test_every_card_has_render_fields_labelled_non_physical() -> None:
    card = fabric("cotton_poplin")
    assert card.roughness == 0.5 and card.texture == ""
    render = card.describe()["render"]
    assert render["physical"] is False
    assert render["texture"] is None
    assert "never read by the solver" in render["note"]
    # and the physics is untouched by them
    assert "roughness" not in card.compliances()


def test_deriving_a_glossier_card_keeps_a_measured_tier() -> None:
    measured = Fabric(
        "lab_twill",
        240.0,
        0.55,
        1.1,
        1.0,
        1.0,
        60.0,
        48.0,
        tier=Tier.MEASURED,
        source="KES-F report 2026-08-12",
        roughness=0.7,
    )
    materials.add(measured, category="test", overwrite=True)
    glossy = materials.derive("lab_twill", "lab_twill_glossy", roughness=0.15, texture="twill.png")
    assert glossy.tier is Tier.MEASURED, "a render change is not a physical change"
    assert glossy.source == measured.source
    assert glossy.roughness == 0.15 and glossy.texture == "twill.png"
    heavier = materials.derive("lab_twill", "lab_twill_heavy", gsm=300.0)
    assert heavier.tier is Tier.PLAUSIBLE, "a physical change still drops the tier"


def test_roughness_is_bounded_like_a_renderer_would() -> None:
    with pytest.raises(materials.MaterialError, match="roughness"):
        materials.add(
            Fabric("mirror", 120.0, 0.3, 1.0, 1.0, 1.0, 38.0, 30.0, roughness=1.5),
            category="test",
            overwrite=True,
        )


def test_the_library_and_compare_carry_roughness() -> None:
    row = next(r for r in materials.library() if r["name"] == "cotton_poplin")
    assert row["roughness"] == 0.5 and row["texture"] is None
    side_by_side = materials.compare(["cotton_poplin", "denim_12oz"])
    assert side_by_side["rows"]["roughness"] == [0.5, 0.5]
    assert "not physical" in side_by_side["note"]


def test_a_material_file_round_trips_the_render_fields(tmp_path) -> None:
    materials.add(
        materials.derive("cotton_poplin", "poplin_satin", roughness=0.2, texture="satin.png"),
        category="test",
        overwrite=True,
    )
    path = tmp_path / "cards.json"
    materials.to_file(["poplin_satin"], path)
    written = json.loads(path.read_text())["cards"][0]
    assert written["roughness"] == 0.2 and written["texture"] == "satin.png"
    del materials._TABLE["poplin_satin"]
    assert materials.from_file(path, overwrite=True) == ["poplin_satin"]
    assert fabric("poplin_satin").texture == "satin.png"


def _garment(tmp_path) -> Session:
    session = Session()
    for command in (
        Command("block", {"block": "tee"}),
        Command("body", {"kind": "mannequin"}),
        Command("arrange", {"particle_distance_mm": 25.0}),
        Command("drape", {"fabric": "cotton_poplin", "frames": 30}),
    ):
        session.apply(command)
    return session


def test_the_handoff_manifest_carries_the_render_fields(tmp_path) -> None:
    pytest.importorskip("numba")
    session = _garment(tmp_path)
    out = session.apply(Command("handoff", {"out": str(tmp_path / "h"), "target": "blender"}))
    manifest = json.loads(Path(out["files"]["manifest"]).read_text())
    assert manifest["fabric"] == "cotton_poplin"
    assert manifest["fabric_render"]["physical"] is False
    assert manifest["fabric_render"]["roughness"] == 0.5


def test_the_tech_pack_labels_the_render_rows(tmp_path) -> None:
    pypdf = pytest.importorskip("pypdf")
    pytest.importorskip("fpdf")
    session = Session()
    session.apply(Command("block", {"block": "tee"}))
    out = tmp_path / "pack.pdf"
    session.apply(Command("techpack", {"out": str(out), "allow_unconverged": True}))
    text = "".join(page.extract_text() or "" for page in pypdf.PdfReader(str(out)).pages)
    assert "render roughness" in text
    assert "not physical" in text
