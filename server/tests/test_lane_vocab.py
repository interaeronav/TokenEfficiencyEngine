"""A68: every shipped vocab() equals the dispatcher it describes.

A declaration that drifts from its interpreter routes batches to a lane that
will refuse them, so each one is held to the source it stands for: Blender's
to the strings codegen runs inside Blender, Godot's to the bridge's GDScript,
partkiln's to the kernel's own kind registry, seamkiln's and Unreal's and
FreeCAD's to their translators' refusal texts."""

from __future__ import annotations

import inspect
import re
import subprocess
import sys
from pathlib import Path

import pytest

from tee.adapters.blender import codegen
from tee.adapters.blender.adapter import BlenderAdapter
from tee.adapters.freecad import codegen as freecad_codegen
from tee.adapters.freecad.adapter import FreeCADAdapter
from tee.adapters.godot.adapter import BRIDGE_OPS, GodotAdapter
from tee.adapters.partkiln import adapter as partkiln_adapter
from tee.adapters.seamkiln import adapter as seamkiln_adapter
from tee.adapters.unreal import codegen as unreal_codegen
from tee.adapters.unreal.adapter import UnrealAdapter
from tee.kernel.adapter import FakeAdapter, LaneVocab

REPO = Path(__file__).resolve().parents[2]


def _between(text: str, start: str, end: str) -> str:
    i = text.index(start)
    j = text.index(end, i)
    return text[i:j]


def test_blender_ops_are_the_interpreter_arms():
    arms = set(re.findall(r'_kind == "(\w+)"', codegen.BATCH_INTERPRETER))
    assert arms == set(codegen.BASE_OPS)
    assert BlenderAdapter(wire=object()).vocab().ops == codegen.BASE_OPS + codegen._MODELING_OPS


def test_blender_kinds_are_what__create_makes():
    src = inspect.getsource(codegen)
    body = _between(src, "def _create(op):", "def _assign_material")
    prims = re.search(r"kind in \((.*?)\)", body, re.DOTALL).group(1)
    kinds = set(re.findall(r'"(\w+)"', prims)) | set(re.findall(r'kind == "(\w+)"', body))
    assert kinds == set(codegen.CREATE_KINDS)
    assert 'kind = op.get("kind", "cube")' in body  # the reason kind_optional is True


def test_blender_import_suffixes_are_what__import_file_takes():
    src = inspect.getsource(codegen)
    body = _between(src, "def _import_file(op):", "_SETTABLE =")
    tests = re.findall(r"ext (?:in \(|== )([^:\n]+):", body)
    flat = {s for expr in tests for s in re.findall(r'"(\w+)"', expr)}
    assert flat == set(codegen.IMPORT_SUFFIXES)
    assert BlenderAdapter(wire=object()).vocab().imports == codegen.IMPORT_SUFFIXES


def test_godot_ops_are_the_bridge_arms():
    script = (REPO / "adapters" / "godot" / "tee_bridge" / "bridge.gd").read_text()
    commands = _between(script, "match name:", '"status": "ok", "result": payload')
    arms = re.findall(r'^\t{3}"(\w+)":', commands, re.MULTILINE)
    assert tuple(arms) == BRIDGE_OPS
    assert GodotAdapter(wire=object()).vocab().ops == BRIDGE_OPS
    assert GodotAdapter(wire=object()).vocab().renders is False


def test_partkiln_kinds_are_the_kernels_own():
    document = pytest.importorskip("partkiln.document")
    document.load_verb_modules()
    assert tuple(document.KINDS) == partkiln_adapter._CREATE_KINDS
    assert tuple(document.VERBS) == partkiln_adapter._BASE_VERBS


def test_partkiln_vocab_is_static_and_refreshes_from_the_kernel(tmp_path):
    from fixtures_partkiln import FakeKernel

    adapter = partkiln_adapter.PartkilnAdapter(tmp_path, kernel=FakeKernel())
    vocab = adapter.vocab()
    assert vocab.ops == partkiln_adapter._WIRE_OPS
    assert vocab.kinds == partkiln_adapter._CREATE_KINDS  # the closed set, no kernel asked
    assert vocab.kind_optional is False and vocab.renders is False
    adapter.verbs()  # the kernel answered: its kinds replace the closed set
    assert adapter.vocab().kinds == (
        "chamfer",
        "extrude",
        "fillet",
        "hole",
        "object",
        "part",
        "sketch",
    )


def test_partkiln_vocab_loads_neither_partkiln_nor_ocp():
    probe = (
        "import sys; from tee.adapters.partkiln.adapter import PartkilnAdapter; "
        "PartkilnAdapter('.').vocab(); "
        "bad = [m for m in sys.modules if m == 'partkiln' or m.startswith(('partkiln.', 'OCP'))]; "
        "print(bad)"
    )
    out = subprocess.run([sys.executable, "-c", probe], capture_output=True, text=True, check=True)
    assert out.stdout.strip() == "[]", out.stdout


def test_seamkiln_kinds_are_the_translators():
    src = inspect.getsource(seamkiln_adapter._translate)
    named = re.search(r'fix="Kinds: (.*?)\."', src).group(1)
    assert set(named.split(", ")) == set(seamkiln_adapter._KINDS)
    vocab = seamkiln_adapter.SeamkilnAdapter(".").vocab()
    assert vocab.ops == seamkiln_adapter._WIRE_OPS and vocab.kind_optional is False


def test_unreal_ops_are_what_its_codegen_compiles():
    src = inspect.getsource(unreal_codegen)
    supported = re.search(r"supported: ([\w, ]+)\)", src).group(1)
    assert tuple(supported.split(", ")) == UnrealAdapter(wire=_Silent()).vocab().ops


def test_freecad_ops_are_its_batch_actions():
    src = inspect.getsource(freecad_codegen.compile_batch)
    arms = re.findall(r'action == "(\w+)"', src)
    assert tuple(arms) == FreeCADAdapter(wire=_Silent()).vocab().ops


def test_every_shipped_lane_says_what_it_is_for():
    for vocab in (
        FakeAdapter().vocab(),
        BlenderAdapter(wire=object()).vocab(),
        GodotAdapter(wire=object()).vocab(),
        seamkiln_adapter.SeamkilnAdapter(".").vocab(),
        UnrealAdapter(wire=_Silent()).vocab(),
        FreeCADAdapter(wire=_Silent()).vocab(),
    ):
        assert isinstance(vocab, LaneVocab) and vocab.purpose


def test_a_vocab_judges_an_op_the_way_the_router_does():
    v = LaneVocab(ops=("create", "set"), kinds=("part",), kind_optional=False)
    assert v.accepts({"op": "create", "kind": "part"})
    assert not v.accepts({"op": "create"})  # kind required
    assert not v.accepts({"op": "create", "kind": "cube"})
    assert v.accepts({"op": "set", "id": "x"}) and not v.accepts({"op": "delete", "id": "x"})
    assert LaneVocab().accepts({"op": "anything", "kind": "whatever"})


class _Silent:
    """A wire that is never asked: vocab() must not touch it."""

    url = "http://127.0.0.1:0"

    def __getattr__(self, name):
        raise AssertionError(f"vocab() reached the wire ({name})")
