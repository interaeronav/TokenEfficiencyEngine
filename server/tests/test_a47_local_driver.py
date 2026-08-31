"""A47 P3 — an extraction channel that works for a host that cannot look.

Decision A9 made the default channel in-band: ex_prepare hands the host
file paths because "it reads media with its own tools". True while the host
was always Claude. The owner drove TEE from opencode with a local DeepSeek,
and both shipped drivers failed him - in-band because he IS the blind
model, ApiDriver because it wants a cloud key, which defeats running
locally. LocalVlmDriver existed the whole time, was ADVERTISED by
ex_prepare, and could not be invoked by anything.
"""

from __future__ import annotations

import os
import shutil
import time
from pathlib import Path

import pytest

from tee.app import TeeApp
from tee.extract import vlm
from tee.extract.tools import register_extract_tools
from tee.kernel import local_vlm
from tee.kernel.errors import TeeError

CARD = Path(
    "/private/tmp/claude-501/-Users-john-TokenEfficiencyEngine/54493178-b179-4f16-8309-d9a53217aa2f/scratchpad/probe.png"
)
needs_vision = pytest.mark.skipif(
    not local_vlm.available(timeout=1.0) or not CARD.is_file(),
    reason="local vision provider not reachable",
)


def _ingested(tmp_path):
    src = tmp_path / "media"
    src.mkdir()
    shutil.copy(CARD, src / "card.png")
    app = TeeApp({}, project_root=tmp_path)
    register_extract_tools(app, tmp_path)
    app.registry.call("ex_ingest", {"path": str(src)})
    deadline = time.monotonic() + 60
    while [j for j in app.jobs.list() if j["state"] in ("queued", "running")]:
        assert time.monotonic() < deadline, "ingest never finished"
        time.sleep(0.3)
    return app


def test_the_driver_report_says_how_not_merely_whether(tmp_path):
    """It used to advertise local_vlm_driver "available (free, on-machine)"
    with no way to invoke it. A sign on a door with no door behind it."""
    app = _ingested(tmp_path)
    drivers = app.registry.call("ex_prepare", {"source": "card"})["drivers"]
    assert set(drivers) == {"in_band", "local", "api"}
    for name, d in drivers.items():
        assert d["how"], f"{name} does not say how to invoke it"
    assert 'driver": "local"' in drivers["local"]["how"]


@needs_vision
def test_a_blind_host_extracts_without_ever_opening_the_file(tmp_path, monkeypatch):
    """The acceptance the campaign exists for, with no cloud key present."""
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    app = _ingested(tmp_path)
    started = app.registry.call("ex_prepare", {"source": "card", "driver": "local"})
    assert "job" in started

    deadline = time.monotonic() + 180
    while True:
        st = app.jobs.status(started["job"])
        if st["state"] not in ("queued", "running"):
            break
        assert time.monotonic() < deadline, "local extraction never finished"
        time.sleep(0.5)
    assert st["state"] == "done", st
    result = st["result"]
    assert result["facts_stored"] >= 1
    assert result["off_machine_calls"] == 0
    assert "not by you" in result["note"]

    # facts land in the SAME store shape the in-band path writes
    facts = app.registry.call("ex_facts", {"source": "card"})["facts"]
    captions = [f for f in facts if f["kind"] == "caption"]
    assert captions, "no caption fact stored"
    assert "4713" in captions[0]["text"], "the driver did not actually read the card"


def test_an_unknown_driver_refuses_by_name(tmp_path):
    app = _ingested(tmp_path)
    with pytest.raises(TeeError) as e:
        app.registry.call("ex_prepare", {"source": "card", "driver": "telepathy"})
    assert e.value.code == "extract_bad_driver"
    assert "in_band" in e.value.fix


def test_an_unreachable_provider_refuses_with_both_ways_out(tmp_path, monkeypatch):
    """Never a silent fallback to in-band: a blind host told 'read it
    yourself' has been given nothing."""
    app = _ingested(tmp_path)
    monkeypatch.setattr(vlm.LocalVlmDriver, "available", staticmethod(lambda: False))
    with pytest.raises(TeeError) as e:
        app.registry.call("ex_prepare", {"source": "card", "driver": "local"})
    assert e.value.code == "extract_local_unavailable"
    assert "litellm" in e.value.fix and "in_band" in e.value.fix


def test_in_band_is_still_the_default(tmp_path):
    """A host that CAN see is still the cheapest reader; the local driver
    is the fallback, not a replacement."""
    app = _ingested(tmp_path)
    packet = app.registry.call("ex_prepare", {"source": "card"})
    assert "job" not in packet
    assert packet["drivers"]["in_band"]["available"] is True


def test_the_a9_docstring_names_three_drivers():
    doc = vlm.__doc__ or ""
    assert "THREE drivers" in doc
    assert "opencode" in doc  # the case that broke the two-driver assumption
