import pytest
from fixtures_extract import DJI_SRT, make_audio, make_scene_frames, make_video

from tee.extract.audio import extract_audio
from tee.extract.video import extract_video, fetch_frame, parse_dji_srt, probe_duration_s


@pytest.fixture(scope="module")
def video_path(tmp_path_factory):
    tmp = tmp_path_factory.mktemp("video")
    frames = make_scene_frames(tmp / "frames")
    return make_video(tmp / "walkthrough.mp4", frames)


def test_video_keyframes_and_index(video_path, tmp_path):
    duration = probe_duration_s(video_path)
    assert duration == pytest.approx(6.0, abs=0.5)  # 30 frames at 5 fps

    facts = extract_video(video_path, tmp_path)
    keyframes = [f for f in facts if f["kind"] == "keyframe"]
    assert 2 <= len(keyframes) <= 15  # three visual scenes, deduped
    assert all("pts_time" in k and "phash" in k and "thumb" in k for k in keyframes)
    times = [k["pts_time"] for k in keyframes]
    assert times == sorted(times)


def test_frame_fetch_by_timestamp(video_path, tmp_path):
    out = fetch_frame(video_path, 3.0, tmp_path / "frame.jpg")
    assert out.exists() and out.stat().st_size > 500


def test_dji_srt_parsing():
    facts = parse_dji_srt(DJI_SRT)
    assert len(facts) == 1
    path_fact = facts[0]
    assert path_fact["kind"] == "flight_path"
    assert path_fact["tier"] == "gps_prior"
    assert path_fact["samples"] == 5
    # the straight run collapses; the turn at sample 3 survives
    assert 3 <= len(path_fact["path"]) <= 5
    assert path_fact["path"][0]["lat"] == pytest.approx(-22.57)
    assert path_fact["path"][0]["rel_alt"] == 30.0


def test_audio_transcription_and_language(tmp_path):
    wav = make_audio(tmp_path / "brief.wav")
    if wav is None:
        pytest.skip("espeak-ng not installed")
    facts = extract_audio(wav, tmp_path, model_size="tiny")
    notes = [f for f in facts if f["kind"] == "note"]
    if notes:
        pytest.skip(f"whisper unavailable: {notes[0]['note']}")
    header = next(f for f in facts if f["kind"] == "transcript")
    assert header["language"] == "en"
    segments = [f for f in facts if f["kind"] == "transcript_segment"]
    assert segments
    full_text = " ".join(s["text"].lower() for s in segments)
    assert "bedroom" in full_text
    assert "budget" in full_text
    assert all(s["end_s"] >= s["start_s"] for s in segments)
