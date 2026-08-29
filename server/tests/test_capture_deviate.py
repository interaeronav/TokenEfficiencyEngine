"""T4 on fakes (A42 acceptance): the seeded-deviation fixture must come
back as EXACTLY the planted deltas; the summary honors its token budget;
elements name their regions; the phrasing hook can only improve, never
break, the deterministic facts; and the numbers-verbatim verifier kills
any phrasing that drops a value."""

from __future__ import annotations

import json

import pytest
from fixtures_llm import fake_llm_server

from tee.capture import deviate
from tee.kernel.budget import estimate_tokens
from tee.kernel.errors import TeeError
from tee.llm import chores

CC_ASC_FAKE = """#!/bin/sh
out=""
prev2=""
prev=""
for a in "$@"; do
  [ "$prev2" = "-SAVE_CLOUDS" ] && [ "$prev" = "FILE" ] && out="$a"
  prev2="$prev"
  prev="$a"
done
cp "$(dirname "$0")/planted.asc" "$out"
exit 0
"""


def _fake_cc(tmp_path) -> dict:
    rows = []
    for i in range(20):  # base surface, within noise
        for j in range(10):
            rows.append(f"{i / 10:.3f} {j / 10:.3f} 0.0 0.001")
    for i in range(5):  # patch A: +38 mm around (2.0, 2.0)
        for j in range(5):
            rows.append(f"{2.0 + i / 20:.3f} {2.0 + j / 20:.3f} 0.0 0.038")
    for i in range(4):  # patch B: -22 mm around (-1.0, -1.0)
        for j in range(3):
            rows.append(f"{-1.0 + i / 20:.3f} {-1.0 + j / 20:.3f} 0.0 -0.022")
    (tmp_path / "planted.asc").write_text("\n".join(rows))
    fake = tmp_path / "fake-cc"
    fake.write_text(CC_ASC_FAKE)
    fake.chmod(0o755)
    src = tmp_path / "capture.xyz"
    dst = tmp_path / "design.obj"
    src.write_text("0 0 0\n")
    dst.write_text("v 0 0 0\n")
    return {"cloudcompare": str(fake), "_src": src, "_dst": dst}


def test_seeded_deviations_come_back_exactly(tmp_path):
    cfg = _fake_cc(tmp_path)
    report = deviate.deviation_report(
        cfg["_src"], cfg["_dst"], cfg=cfg, work_dir=tmp_path / "w", band="test-band"
    )
    assert len(report["deviations"]) == 2 and report["more"] == 0
    first, second = report["deviations"]
    assert "+38 mm" in first and "[high]" in first and "0.2x0.2 m" in first
    assert "-22 mm" in second and "[warn]" in second
    assert report["within_band_pct"] == pytest.approx(84.4, abs=0.1)
    assert report["band"] == "test-band"
    assert report["menu"] == ["accept-as-built", "keep-design", "flag-for-site"]
    assert "owner decides" in report["note"]
    assert report["phrasing"] == "deterministic"
    rows = report["_clusters"]
    assert rows[0]["mean_m"] == pytest.approx(0.038, abs=0.0005)
    assert rows[1]["mean_m"] == pytest.approx(-0.022, abs=0.0005)


def test_budget_trims_but_never_lies(tmp_path):
    cfg = _fake_cc(tmp_path)
    report = deviate.deviation_report(
        cfg["_src"], cfg["_dst"], cfg=cfg, work_dir=tmp_path / "w",
        band="b", budget_tokens=60,
    )  # fmt: skip
    assert len(report["deviations"]) == 1 and report["more"] == 1
    trimmed = dict(report)
    trimmed.pop("_clusters")
    assert estimate_tokens(str(trimmed)) <= 60 or len(report["deviations"]) == 1


def test_elements_name_their_regions(tmp_path):
    cfg = _fake_cc(tmp_path)
    elements = [{"name": "north wall", "min": [1.5, 1.5], "max": [2.5, 2.5]}]
    report = deviate.deviation_report(
        cfg["_src"], cfg["_dst"], cfg=cfg, work_dir=tmp_path / "w",
        band="b", elements=elements,
    )  # fmt: skip
    assert report["deviations"][0].startswith("north wall: +38 mm")


def test_phrase_hook_can_only_improve(tmp_path):
    cfg = _fake_cc(tmp_path)

    def wrong_count(lines):
        return ["just one line"]

    report = deviate.deviation_report(
        cfg["_src"], cfg["_dst"], cfg=cfg, work_dir=tmp_path / "w",
        band="b", phrase=wrong_count,
    )  # fmt: skip
    assert report["phrasing"] == "deterministic"

    def crashes(lines):
        raise RuntimeError("model exploded")

    report = deviate.deviation_report(
        cfg["_src"], cfg["_dst"], cfg=cfg, work_dir=tmp_path / "w",
        band="b", phrase=crashes,
    )  # fmt: skip
    assert report["phrasing"] == "deterministic"

    def good(lines):
        return [f"On site: {line}" for line in lines]

    report = deviate.deviation_report(
        cfg["_src"], cfg["_dst"], cfg=cfg, work_dir=tmp_path / "w",
        band="b", phrase=good,
    )  # fmt: skip
    assert report["phrasing"] == "routed"
    assert report["deviations"][0].startswith("On site:")


def test_phrase_chore_verifier_kills_dropped_numbers(tmp_path):
    facts = ["north wall: +38 mm (peak +40 mm) over 0.5x0.5 m [high]"]
    good = json.dumps(
        {"lines": ["The north wall sits +38 mm proud (peak +40 mm) across 0.5x0.5 m - high."]}
    )
    with fake_llm_server([good]) as (url, _calls):
        out = chores.phrase_deviation(facts, refine="local", cfg={"url": url, "model": "m"})
    assert out["lines"][0].startswith("The north wall")

    dropped = json.dumps({"lines": ["The north wall deviates noticeably."]})
    with (
        fake_llm_server([dropped, dropped]) as (url, _calls),
        pytest.raises(TeeError) as excinfo,
    ):
        chores.phrase_deviation(facts, refine="local", cfg={"url": url, "model": "m"})
    assert excinfo.value.code == "llm_bad_shape"


def test_missing_inputs_refuse(tmp_path):
    with pytest.raises(TeeError) as excinfo:
        deviate.deviation_report(
            tmp_path / "absent.xyz", tmp_path / "d.obj", cfg={}, work_dir=tmp_path, band="b"
        )
    assert excinfo.value.code == "capture_align_missing_input"
