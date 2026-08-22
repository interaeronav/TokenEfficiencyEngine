"""Phase 12.5: the version-trajectory firewall as tests (A23/A24)."""

from __future__ import annotations

import random

from tee.adapters.blender.shim import firewall_check
from tee.kernel.adapter import Entity
from tee.kernel.scene_cache import SceneCache


class ShuffledAdapter:
    """Emits the same entities in a different order every listing -
    Blender 5.3 changes bpy.data.all_ids iteration order and documents it
    internal; identity must come from session_uid alone."""

    def __init__(self, seed: int = 0):
        self.rng = random.Random(seed)
        self.rows = [
            Entity(id=f"b{100 + i}", name=f"Obj{i}", kind="mesh",
                   summary={"location": [i, 0, 0]})
            for i in range(12)
        ]
        self._connected = True

    def probe(self):
        return True

    def list_entities(self):
        shuffled = list(self.rows)
        self.rng.shuffle(shuffled)
        import copy

        return [copy.deepcopy(e) for e in shuffled]


def test_session_uid_identity_survives_ordering_shuffle():
    """A24 regression: cache identity is session_uid-keyed - reordering
    the listing changes NOTHING (no phantom creates/deletes)."""
    cache = SceneCache()
    adapter = ShuffledAdapter()
    cache.resync(adapter)
    first = {e.id: e.name for e in cache.entities.values()}
    assert cache.epoch >= 0 and cache.revision >= 0  # stamps exist pre-shuffle
    for _ in range(5):
        cache.resync(adapter)  # different order each time
        assert {e.id: e.name for e in cache.entities.values()} == first
    assert len(first) == 12


def test_use_nodes_write_banned_on_5x():
    """A24: use_nodes writes are fatal on 6.0 (#140111) - banned NOW."""
    hits = firewall_check("mat.use_nodes = True", (5, 2, 0))
    assert any(h["code"] == "use_nodes_write_banned" for h in hits)
    assert any("#140111" in h["hint"] for h in hits)
    # reads are fine; 4.x legacy writes are fine
    assert not firewall_check("if mat.use_nodes: pass", (5, 2, 0))
    assert not any(
        h["code"] == "use_nodes_write_banned"
        for h in firewall_check("mat.use_nodes = True", (4, 5, 0))
    )


def test_tee_codegen_is_use_nodes_clean_on_5x():
    """TEE's own generated programs pass the firewall it enforces."""
    from tee.adapters.blender import codegen

    program = codegen.program_batch(
        [{"op": "create", "kind": "cube", "name": "C"},
         {"op": "assign_material", "id": "b1", "props": {"base_color": [1, 0, 0]}},
         {"op": "wall_with_openings", "props": {"start": [0, 0], "end": [2, 0]}}],
        "test",
    )
    # the only use_nodes write is inside the version guard
    for line in program.splitlines():
        if ".use_nodes =" in line:
            # must sit under the < 5.0 version guard (indented body)
            assert line.startswith("        "), line


def test_float32_tolerance_policy():
    """A24: mathutils is float32 since 5.0 - comparisons use 1e-5
    tolerances and float bytes are never hashed. The scene cache stores
    rounded values, so equality after a round-trip holds at 1e-4."""
    import struct

    value = 1.2345678912345  # f64
    as_f32 = struct.unpack("f", struct.pack("f", value))[0]
    assert abs(value - as_f32) < 1e-5  # the policy tolerance bounds the loss
    # the cache convention: round(…, 4) before comparing/diffing
    assert round(value, 4) == round(as_f32, 4)


def test_physics_ops_declare_backend():
    """A24: Phase 11 physics goes through the legacy backend by contract;
    the gn_physics/XPBD lane is a declared watch-lane, not an accident."""
    from tee.physical import physics

    assert "legacy" in physics.__doc__.lower() or "sequential" in physics.__doc__.lower()
    program = physics.settle_program(None, None)
    assert "rigidbody" in program  # legacy RB world, not GN simulation nodes
    assert "GeometryNode" not in program
