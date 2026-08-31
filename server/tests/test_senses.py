"""A47 — senses a blind host can borrow, and the honesty they carry.

The owner ran DeepSeek locally as the HOST model in opencode, asked TEE
about an image, and was told machine vision was not a feature TEE offered.
It was true: decision A9 hands file paths to the host because "it reads
media with its own tools", and tee_media returns pixels. A working
LocalVlmDriver sat in extract/vlm.py that ex_prepare advertised and nothing
ever called.

These tests pin the three rules. The third is the point: an answer that
arrives as if the asking model had seen the image is the failure this lane
exists to prevent, not the feature it offers.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from tee import senses
from tee.kernel.errors import TeeError

SCRATCH = Path(
    "/private/tmp/claude-501/-Users-john-TokenEfficiencyEngine/54493178-b179-4f16-8309-d9a53217aa2f/scratchpad"
)
CARD = SCRATCH / "probe.png"
SPOKEN = SCRATCH / "spoken.aiff"

# Live-provider tests: a cold vision start is ~36 s measured, and under
# full-suite contention (the provider evicted by earlier activity) the
# default 60 s per-test timeout flakes. The long timeout is the honest
# price of testing against the real provider rather than a mock.
live_slow = pytest.mark.timeout(240)

needs_vision = pytest.mark.skipif(
    not __import__("tee.kernel.local_vlm", fromlist=["x"]).available(timeout=1.0)
    or not CARD.is_file(),
    reason="local vision provider not reachable",
)
needs_audio = pytest.mark.skipif(
    __import__("importlib.util", fromlist=["x"]).find_spec("faster_whisper") is None
    or not SPOKEN.is_file(),
    reason="faster-whisper or the spoken fixture is absent",
)


# -- the honesty rules ------------------------------------------------------


@needs_vision
@live_slow
def test_every_answer_names_who_actually_looked(tmp_path):
    r = senses.describe({"path": str(CARD), "question": "Read the card."}, state_dir=tmp_path)
    assert "qwen-vl" in r["provided_by"]
    assert r["sense"] == "vision"
    assert "never saw the pixels" in r["note"]


@needs_vision
@live_slow
def test_the_answer_is_not_dressed_up_as_sight(tmp_path):
    """The note is not decoration. A model reading this is reading a summary
    another model wrote, and must be told so in the same payload."""
    r = senses.describe({"path": str(CARD)}, state_dir=tmp_path)
    assert "A description, not the image" in r["note"]
    assert "what was worth mentioning" in r["note"]


@needs_vision
@live_slow
def test_nothing_leaves_the_machine(tmp_path):
    r = senses.describe({"path": str(CARD)}, state_dir=tmp_path)
    assert r["cost"]["off_machine_calls"] == 0
    assert r["cost"]["usd"] == 0.0


@needs_vision
@live_slow
def test_it_reads_what_no_model_could_guess(tmp_path):
    """The fixture says PLINTH K-4713 - unguessable, so a correct answer is
    proof of sight rather than of plausible invention."""
    r = senses.describe(
        {"path": str(CARD), "question": "Read the text exactly.", "max_tokens": 60},
        state_dir=tmp_path,
    )
    assert "4713" in r["answer"]


@needs_vision
@live_slow
def test_context_is_used_not_merely_carried(tmp_path):
    """Measured before the build: given a spec, the provider answers the
    DELTA against it. That is what makes this useful for site forensics
    rather than captioning."""
    r = senses.describe(
        {
            "path": str(CARD),
            "context": "The schedule says this card should read CURE 28 DAYS.",
            "question": "Does the card match the schedule?",
            "max_tokens": 120,
        },
        state_dir=tmp_path,
    )
    assert "21" in r["answer"]  # it must notice the card says 21, not 28


# -- the cache --------------------------------------------------------------


@needs_vision
@live_slow
def test_the_same_question_twice_costs_the_provider_once(tmp_path):
    spec = {"path": str(CARD), "question": "Read the card.", "max_tokens": 60}
    first = senses.describe(spec, state_dir=tmp_path)
    second = senses.describe(spec, state_dir=tmp_path)
    assert first["cached"] is False and second["cached"] is True
    assert second["answer"] == first["answer"]
    assert second["cost"]["wall_s"] == 0.0


def test_the_cache_key_is_exact_never_perceptual():
    """extract/images.py has phash dedupe and it is the WRONG tool here: two
    frames a hamming-5 apart are the same photo for grouping and emphatically
    not for 'what does this label say'. One flipped pixel must miss."""
    a = senses._cache_key(b"\x89PNG-aaaa", "q", "", "m")
    b = senses._cache_key(b"\x89PNG-aaab", "q", "", "m")
    assert a != b
    # and the question is part of the key: same image, new question, new call
    assert senses._cache_key(b"x", "q1", "", "m") != senses._cache_key(b"x", "q2", "", "m")
    # as is the context, which changes the answer
    assert senses._cache_key(b"x", "q", "c1", "m") != senses._cache_key(b"x", "q", "c2", "m")


def test_the_cache_is_bounded(tmp_path):
    """A cache that grows forever in a state dir nobody prunes is a leak."""
    senses._save_cache(tmp_path, {f"k{i}": {"answer": "a"} for i in range(260)})
    assert len(json.loads((tmp_path / "senses-cache.json").read_text())) == 200


def test_an_unwritable_state_dir_never_fails_the_answer(tmp_path):
    bad = tmp_path / "f"
    bad.write_text("a file, not a directory")
    senses._save_cache(bad, {"k": {"answer": "a"}})  # must not raise
    assert senses._load_cache(bad) == {}


# -- refusals ---------------------------------------------------------------


def test_a_missing_file_refuses_with_a_fix():
    with pytest.raises(TeeError) as e:
        senses.describe({"path": "/nope/absent.jpg"})
    assert e.value.code == "sense_missing_file"


def test_an_unreadable_media_type_refuses_by_name(tmp_path):
    p = tmp_path / "notes.txt"
    p.write_text("hello")
    with pytest.raises(TeeError) as e:
        senses.describe({"path": str(p)})
    assert e.value.code == "sense_unsupported_media"
    assert ".heic" in e.value.fix  # the supported list is named


def test_no_path_refuses():
    with pytest.raises(TeeError) as e:
        senses.describe({})
    assert e.value.code == "sense_no_path"
    with pytest.raises(TeeError):
        senses.transcribe({})


def test_a_bad_whisper_size_names_the_measured_default():
    with pytest.raises(TeeError) as e:
        senses.transcribe({"path": str(SPOKEN), "model_size": "enormous"})
    assert "base is the" in e.value.fix


# -- audio ------------------------------------------------------------------


@needs_audio
def test_speech_comes_back_as_text(tmp_path):
    r = senses.transcribe({"path": str(SPOKEN)}, state_dir=tmp_path)
    assert "roof sheeting" in r["answer"]
    assert r["sense"] == "audio" and r["language"] == "en"
    assert r["cost"]["off_machine_calls"] == 0
    assert "tone, speaker" in r["note"]  # what a transcript LOSES is stated


# -- registration -----------------------------------------------------------


def test_both_senses_are_read_tier_and_explicitly_tabled():
    """A45's lesson: explicit tabling, never a family prefix. A prefix
    silently admits whatever gets named next."""
    from tee.kernel import trust

    assert trust.capability_for("sense_describe") == "read-extract"
    assert trust.capability_for("sense_transcribe") == "read-extract"
    assert "sense_describe" in trust._EXPLICIT


def test_a_blind_host_can_actually_find_them(tmp_path):
    """The bug was discoverability. Before this lane, asking TEE's own
    search to describe an image returned med_instance_tags ('Pixel data is
    never returned') - truthful and useless."""
    from tee.app import TeeApp
    from tee.senses import register_sense_tools

    app = TeeApp({}, project_root=tmp_path)
    register_sense_tools(app, tmp_path)
    top = [i["name"] for i in app.registry.search("describe what is in an image")["items"]][:3]
    assert "sense_describe" in top
    heard = [i["name"] for i in app.registry.search("transcribe audio speech")["items"]][:3]
    assert "sense_transcribe" in heard


def test_registration_does_not_depend_on_the_provider_being_up(tmp_path, monkeypatch):
    """A tool that vanishes when its provider is down is indistinguishable
    from one that never existed - the exact confusion this lane ends."""
    from tee.app import TeeApp
    from tee.kernel import local_vlm
    from tee.senses import register_sense_tools

    monkeypatch.setattr(local_vlm, "available", lambda **kw: False)
    app = TeeApp({}, project_root=tmp_path)
    register_sense_tools(app, tmp_path)
    assert "sense_describe" in app.registry._tools


# -- the eviction disclosure (A48 P0.2) -------------------------------------


def test_the_eviction_note_is_configured_not_guessed_from_a_stopwatch():
    """It used to fire on `wall >= COLD_START_S`. Measured through this
    module, the sequence was text 10.75 / vision 3.03 / vision 0.85 / text
    10.34 / text 0.79 - the eviction is paid by the NEXT TEXT TURN, not by
    the vision call, which never crossed the threshold. The warning that
    existed to disclose the cost never fired once."""
    note = senses._eviction_note({"evicts": ["dsflash"], "cost": {"swap_s": 10.0}})
    assert "NEXT TEXT TURN" in note and "~10.0s" in note
    assert "later than you expect" in note


def test_a_machine_whose_eye_coexists_says_nothing():
    """Most machines. Silence is correct - there is nothing to disclose."""
    assert senses._eviction_note({"evicts": [], "cost": {}}) is None


@needs_vision
@live_slow
def test_a_cached_answer_evicts_nothing_and_says_nothing(tmp_path):
    spec = {"path": str(CARD), "question": "Read the card.", "max_tokens": 40}
    senses.describe(spec, state_dir=tmp_path)
    second = senses.describe(spec, state_dir=tmp_path)
    assert second["cached"] is True
    assert "swap_note" not in second
