"""Rung-1 distillation set for the triage chore (A34 M4, owner-directed).

Generates chat-format JSONL teaching the ONE behavior the trap suite
proved missing across three models: correct deferral on API-drift
failures (kwarg gone / module attr gone / import name gone) WITHOUT
losing grounded competence on evidence-complete failures.

Deterministic and programmatic: for drift families the correct label is
known by construction (needs_verification + what to check), so no
teacher is needed; grounded families carry equally constructed labels.
Every example uses the PRODUCTION triage system prompt (chores.REVISION
r2) so the adapter learns the behavior under the template it will serve.

Holdout hygiene: the eval trap suite's exact fixtures (bpy
primitive_cube_add/rotation, unreal.EditorLevelLibrary, bpy.types
Annotation, bmesh holes_fill enum, the NoneType free() control) are
BLACKLISTED from generation vocabulary - the suite stays untainted.

Usage: python gen_distill.py [--per-family 400] [--out data/]
Output: data/train.jsonl, data/valid.jsonl (mlx_lm.lora chat format -
verify the expected format against `mlx_lm.lora --help` at run time;
the flag surface drifts between releases).
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "server" / "src"))

from tee.llm.chores import _TRIAGE_SYSTEM

# Vocabulary pools. The eval-suite identifiers are deliberately absent.
LIBS = [
    "pandas", "numpy", "requests", "flask", "django", "sqlalchemy", "matplotlib",
    "scipy", "pillow", "click", "pydantic", "httpx", "fastapi", "torch", "keras",
    "openpyxl", "lxml", "yaml", "redis", "boto3", "jinja2", "celery", "paramiko",
    "psycopg2", "shapely", "trimesh", "networkx", "sympy", "seaborn", "plotly",
    "attrs", "arrow", "pendulum", "tqdm", "rich", "typer", "uvicorn", "aiohttp",
]  # fmt: skip
FUNCS = [
    "read_table", "to_frame", "connect", "render_page", "load_config", "make_grid",
    "fit_model", "resize_batch", "open_stream", "parse_tree", "dump_rows", "walk_dir",
    "merge_frames", "sample_points", "build_index", "query_range", "write_chunk",
    "encode_batch", "spawn_worker", "flush_cache", "rotate_keys", "trace_span",
]  # fmt: skip
KWARGS = [
    "strict_mode", "chunk_size", "on_error", "retry_policy", "encoding_hint",
    "max_depth", "keep_order", "line_buffer", "fast_path", "legacy_axis",
    "auto_close", "warn_only", "coerce_types", "sparse_ok", "backend_hint",
]  # fmt: skip
ATTRS = [
    "SessionPool", "FrameWriter", "GridSampler", "AsyncRunner", "TableLoader",
    "StreamCodec", "BatchPlanner", "CacheJanitor", "PathResolver", "SpanTracer",
]  # fmt: skip

BLACKLIST = {"primitive_cube_add", "rotation", "EditorLevelLibrary", "Annotation", "holes_fill"}

# Paraphrase pools (a2): the decision must be the learnable signal, not the
# phrasing - a1's rigid templates trained phrase-association and produced
# chimera answers on the controls.
DRIFT_DIAG = [
    "This {lib} version does not accept '{kw}' on {fn}().",
    "{fn}() no longer takes a '{kw}' argument in the installed {lib}.",
    "The installed {lib} dropped the '{kw}' parameter of {fn}().",
    "'{kw}' is not a parameter of {fn}() in this {lib} build.",
]
DRIFT_FIX = [
    "Keep the intended behavior: check {fn}()'s current parameters in the {lib} docs before editing the call.",  # noqa: E501
    "Verify what replaced '{kw}' in the installed {lib} documentation; removing it would change behavior.",  # noqa: E501
    "Look up {fn}() in the {lib} changelog for the successor of '{kw}', then update the call.",
    "The replacement name is not in the evidence - confirm it against the {lib} docs first.",
]
ENUM_ERRORS = [
    "TypeError: enum \"{bad}\" not found in {good}",
    "ValueError: '{bad}' is not a valid mode, must be one of {good}",
    "ValueError: invalid choice: '{bad}' (choose from {good})",
    "TypeError: mode expected one of {good}, got '{bad}'",
]
ENUM_DIAG = [
    "'{bad}' is not a valid value; the error lists the valid set.",
    "The mode '{bad}' does not exist - the accepted values are right in the error.",
    "'{bad}' is rejected because only {good} are accepted.",
]
ENUM_FIX = [
    "Use one of {good} - the full set is in the evidence.",
    "Replace '{bad}' with the matching value from {good}.",
    "Pick the appropriate mode from {good}; no lookup needed.",
]


def _clean(pool: list[str]) -> list[str]:
    return [x for x in pool if x not in BLACKLIST]


def _drift_kwarg(rng: random.Random) -> dict:
    lib, fn, kw = rng.choice(_clean(LIBS)), rng.choice(_clean(FUNCS)), rng.choice(_clean(KWARGS))
    failure = (
        f"Traceback (most recent call last):\n"
        f'  File "job.py", line {rng.randint(3, 40)}, in <module>\n'
        f"    {lib}.{fn}(data, {kw}=True)\n"
        f"TypeError: {fn}() got an unexpected keyword argument '{kw}'"
    )
    answer = {
        "diagnosis": rng.choice(DRIFT_DIAG).format(lib=lib, fn=fn, kw=kw),
        "fix": rng.choice(DRIFT_FIX).format(lib=lib, fn=fn, kw=kw),
        "confidence": "needs_verification",
    }
    return _example(failure, "", answer)


def _drift_attr(rng: random.Random) -> dict:
    lib, attr = rng.choice(_clean(LIBS)), rng.choice(_clean(ATTRS))
    failure = (
        f"Traceback (most recent call last):\n"
        f'  File "run.py", line {rng.randint(2, 30)}, in <module>\n'
        f"    worker = {lib}.{attr}()\n"
        f"AttributeError: module '{lib}' has no attribute '{attr}'"
    )
    answer = {
        "diagnosis": f"'{attr}' no longer exists on this {lib} version.",
        "fix": f"The replacement API is not in the evidence - check the {lib} "
        f"changelog/docs for what superseded {attr} before rewriting.",
        "confidence": "needs_verification",
    }
    return _example(failure, "", answer)


def _drift_import(rng: random.Random) -> dict:
    lib, attr = rng.choice(_clean(LIBS)), rng.choice(_clean(ATTRS))
    failure = (
        f"Traceback (most recent call last):\n"
        f'  File "tool.py", line 1, in <module>\n'
        f"    from {lib}.types import {attr}\n"
        f"ImportError: cannot import name '{attr}' from '{lib}.types'"
    )
    answer = {
        "diagnosis": f"'{attr}' is not importable from {lib}.types in this version.",
        "fix": f"Verify where {attr} moved (or what replaced it) in the installed "
        f"{lib} docs; the correct import path is not in the evidence.",
        "confidence": "needs_verification",
    }
    return _example(failure, "", answer)


def _grounded_none(rng: random.Random) -> dict:
    # `_fn` is unused BY DESIGN and must not be deleted: rng.choice advances
    # the generator, so removing the draw would shift every later value and
    # silently regenerate different fixtures.
    _fn, method = rng.choice(_clean(FUNCS)), rng.choice(["close", "commit", "flush", "release"])
    line = rng.randint(3, 25)
    failure = (
        f"Traceback (most recent call last):\n"
        f'  File "op.py", line {line}, in <module>\n'
        f"    handle.{method}()\n"
        f"AttributeError: 'NoneType' object has no attribute '{method}'"
    )
    context = f"line {line - 1}: handle = registry.get(name)  # returns None when absent"
    answer = {
        "diagnosis": "handle is None because registry.get(name) found nothing.",
        "fix": f"Guard before use: if handle: handle.{method}() - or fail loud "
        "when the name must exist.",
        "confidence": "grounded",
    }
    return _example(failure, context, answer)


def _grounded_enum(rng: random.Random) -> dict:
    fn = rng.choice(_clean(FUNCS))
    good = tuple(rng.sample(["FAST", "SAFE", "FULL", "NONE", "AUTO", "STRICT", "LOOSE"], 3))
    bad = rng.choice(["TURBO", "MAX", "ULTRA", "QUICK", "BEST"])
    failure = (
        f"Traceback (most recent call last):\n"
        f'  File "cfg.py", line {rng.randint(2, 20)}, in <module>\n'
        f"    {fn}(mode='{bad}')\n" + rng.choice(ENUM_ERRORS).format(bad=bad, good=good)
    )
    answer = {
        "diagnosis": rng.choice(ENUM_DIAG).format(bad=bad, good=good),
        "fix": rng.choice(ENUM_FIX).format(bad=bad, good=good),
        "confidence": "grounded",
    }
    return _example(failure, "", answer)


def _grounded_suggestion(rng: random.Random) -> dict:
    """Looks like drift, but the error itself names the replacement - the
    boundary case a1 got wrong in reverse: this must stay grounded."""
    lib, fn = rng.choice(_clean(LIBS)), rng.choice(_clean(FUNCS))
    kw = rng.choice(_clean(KWARGS))
    typo = kw[:-2] + kw[-1] if len(kw) > 3 else kw + "s"
    failure = (
        f"Traceback (most recent call last):\n"
        f'  File "job.py", line {rng.randint(3, 30)}, in <module>\n'
        f"    {lib}.{fn}(data, {typo}=True)\n"
        f"TypeError: {fn}() got an unexpected keyword argument '{typo}'. "
        f"Did you mean '{kw}'?"
    )
    answer = {
        "diagnosis": f"'{typo}' is a typo; the error itself suggests '{kw}'.",
        "fix": f"Rename the argument to '{kw}' - the correct name is in the evidence.",
        "confidence": "grounded",
    }
    return _example(failure, "", answer)


def _grounded_index(rng: random.Random) -> dict:
    line = rng.randint(3, 20)
    failure = (
        f"Traceback (most recent call last):\n"
        f'  File "pick.py", line {line}, in <module>\n'
        f"    last = rows[len(rows)]\n"
        f"IndexError: list index out of range"
    )
    context = f"line {line - 1}: rows = fetch_rows()  # non-empty list"
    answer = {
        "diagnosis": "rows[len(rows)] is one past the end; the last index is len(rows)-1.",
        "fix": "Use rows[-1] (or rows[len(rows)-1]).",
        "confidence": "grounded",
    }
    return _example(failure, context, answer)


def _example(failure: str, context: str, answer: dict) -> dict:
    evidence = f"Failure evidence:\n{failure}"
    if context:
        evidence += f"\n\nContext (source/op):\n{context}"
    return {
        "messages": [
            {"role": "system", "content": _TRIAGE_SYSTEM},
            {"role": "user", "content": evidence},
            {"role": "assistant", "content": json.dumps(answer)},
        ]
    }


FAMILIES = [_drift_kwarg, _drift_attr, _drift_import, _grounded_none,
            _grounded_enum, _grounded_suggestion, _grounded_index]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--per-family", type=int, default=400)
    parser.add_argument("--out", default=str(Path(__file__).parent / "data"))
    parser.add_argument("--seed", type=int, default=34)
    args = parser.parse_args()
    rng = random.Random(args.seed)
    examples = [family(rng) for family in FAMILIES for _ in range(args.per_family)]
    rng.shuffle(examples)
    split = max(1, len(examples) // 20)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "valid.jsonl").write_text("\n".join(json.dumps(e) for e in examples[:split]) + "\n")
    (out / "train.jsonl").write_text("\n".join(json.dumps(e) for e in examples[split:]) + "\n")
    print(f"{len(examples) - split} train / {split} valid -> {out}")


if __name__ == "__main__":
    main()
