from tee.kernel.budget import estimate_tokens
from tee.kernel.memory import ProjectMemory


def test_remember_and_note_roundtrip(tmp_path):
    mem = ProjectMemory(tmp_path)
    mem.remember("blender_version", "5.2.0")
    mem.note("built the donut base mesh")
    fresh = ProjectMemory(tmp_path)  # reload from disk
    pre = fresh.preamble()
    assert pre["facts"]["blender_version"] == "5.2.0"
    assert any("donut" in n["text"] for n in pre["notes"])


def test_preamble_is_capped(tmp_path):
    mem = ProjectMemory(tmp_path)
    for i in range(40):
        mem.note(f"note {i}: " + "detail " * 40)
    pre = mem.preamble(max_tokens=500)
    assert estimate_tokens(pre) <= 500
    # newest notes survive
    assert pre["notes"][-1]["text"].startswith("note 39")
    assert pre["truncated"]


def test_corrupt_memory_file_recovers(tmp_path):
    mem = ProjectMemory(tmp_path)
    mem.remember("k", "v")
    mem.path.write_text("{not json")
    fresh = ProjectMemory(tmp_path)
    assert fresh.preamble()["facts"] == {}
    assert fresh.path.with_suffix(".corrupt.json").exists()
    fresh.remember("k2", "v2")  # can save again
    assert ProjectMemory(tmp_path).preamble()["facts"] == {"k2": "v2"}


def test_non_dict_json_memory_recovers(tmp_path):
    mem = ProjectMemory(tmp_path)
    mem.remember("k", "v")
    mem.path.write_text("[1, 2, 3]")  # valid JSON, wrong shape
    fresh = ProjectMemory(tmp_path)
    assert fresh.preamble()["facts"] == {}
    fresh.remember("k2", "v2")
    assert ProjectMemory(tmp_path).preamble()["facts"] == {"k2": "v2"}


def test_preamble_cap_holds_even_with_fat_facts(tmp_path):
    mem = ProjectMemory(tmp_path)
    for i in range(40):
        mem.remember(f"fact_{i}", "detail " * 60)  # each value capped at 500 chars
    pre = mem.preamble(max_tokens=500)
    assert estimate_tokens(pre) <= 500
    assert pre["truncated"]
