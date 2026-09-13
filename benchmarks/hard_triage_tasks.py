"""Triage cases hard enough that a 27B actually fails some of them.

`gen_distill.py`'s seven families are formulaic - a drift traceback with an
empty context, or a grounded one whose answer sits in plain sight - and both
27B rungs answered 35/35 on them. A rung that never fails has no variance, so
no correlation with another rung can be computed, and rho for the pair the
cascade most depends on came back `n/a`.

These families keep the property that makes grading free - the correct
`confidence` is known BY CONSTRUCTION - while attacking the two shortcuts a
model can otherwise take:

  * SEDUCTIVE BUT INSUFFICIENT. A context is supplied and looks authoritative,
    but does not actually cover the failing call: a signature for a different
    function, a deprecation with no installed version, a near-miss symbol name.
    Pattern-matching answers `grounded`; the correct answer is
    `needs_verification`, because the evidence in hand does not settle it.
  * SUFFICIENT BUT BURIED. The answer IS present, under noise or below a
    chained traceback whose last frame is not the root cause. Skimming answers
    `needs_verification`; the correct answer is `grounded`.

Both shortcuts are the A30 boundary from opposite sides, which is what makes
them a fair test rather than a trick: a model that reads the evidence and
weighs whether it is sufficient gets them all right.
"""

from __future__ import annotations

import json
import random

_NOISE = [
    '  File "runner.py", line {n}, in _dispatch',
    "    return handler(payload, context=ctx)",
    '  File "middleware.py", line {n}, in wrapped',
    "    result = fn(*args, **kwargs)",
    '  File "retry.py", line {n}, in attempt',
    "    return inner()",
]
LIBS = ["polars", "xarray", "trimesh", "networkx", "pyarrow", "rasterio", "sympy"]
FUNCS = ["resample", "reproject", "simplify", "decimate", "interpolate", "tessellate"]
KWARGS = ["tolerance", "preserve_topology", "engine", "fill_value", "how"]


def _case(failure: str, context: str, confidence: str, family: str) -> dict:
    return {"failure": failure, "context": context, "expect": confidence, "family": family}


def wrong_function_signature(rng: random.Random) -> dict:
    """A signature IS given - for a different function. Insufficient."""
    lib, fn, other = rng.choice(LIBS), rng.choice(FUNCS), rng.choice(FUNCS)
    while other == fn:
        other = rng.choice(FUNCS)
    kw = rng.choice(KWARGS)
    return _case(
        f'  File "job.py", line {rng.randint(4, 90)}, in run\n'
        f"    {lib}.{fn}(frame, {kw}=0.5)\n"
        f"TypeError: {fn}() got an unexpected keyword argument '{kw}'",
        f"Source of {lib}.{other}:\n    def {other}(frame, {kw}=None, *, strict=False): ...",
        "needs_verification",
        "wrong_function_signature",
    )


def deprecation_without_version(rng: random.Random) -> dict:
    """A changelog line with no installed version. Insufficient."""
    lib, kw = rng.choice(LIBS), rng.choice(KWARGS)
    return _case(
        f'  File "job.py", line {rng.randint(4, 90)}, in run\n'
        f"    frame.agg(data, {kw}=True)\n"
        f"TypeError: agg() got an unexpected keyword argument '{kw}'",
        f"CHANGELOG for {lib}:\n  2.0.0 - '{kw}' was removed from agg().\n"
        f"  1.4.0 - '{kw}' deprecated.\n(The installed version is not recorded here.)",
        "needs_verification",
        "deprecation_without_version",
    )


def near_miss_symbol(rng: random.Random) -> dict:
    """The context defines a symbol one character away. Insufficient."""
    lib = rng.choice(LIBS)
    stem = rng.choice(["Frame", "Buffer", "Layer", "Mesh"])
    return _case(
        f'  File "job.py", line {rng.randint(4, 90)}, in run\n'
        f"    from {lib}.core import {stem}Reader\n"
        f"ImportError: cannot import name '{stem}Reader' from '{lib}.core'",
        f"{lib}/core/__init__.py defines:\n"
        f"    class {stem}Writer: ...\n    class {stem}Handle: ...",
        "needs_verification",
        "near_miss_symbol",
    )


def grounded_but_buried(rng: random.Random) -> dict:
    """The enum IS listed, after noise. Sufficient."""
    lib = rng.choice(LIBS)
    noise = "\n".join(line.format(n=rng.randint(10, 400)) for line in _NOISE)
    return _case(
        f"Traceback (most recent call last):\n{noise}\n"
        f'  File "job.py", line {rng.randint(4, 90)}, in run\n'
        f"    {lib}.write(path, mode='overwrite')\n"
        "ValueError: invalid mode 'overwrite'",
        f"{noise}\n\nSignature: {lib}.write(path, mode) where mode is one of "
        "'w', 'a', 'x'.\nThe caller passed 'overwrite'.",
        "grounded",
        "grounded_but_buried",
    )


def grounded_chained_traceback(rng: random.Random) -> dict:
    """Two exceptions; the ROOT is stated in the context. Sufficient."""
    lib = rng.choice(LIBS)
    return _case(
        "Traceback (most recent call last):\n"
        f'  File "{lib}/io.py", line {rng.randint(10, 90)}, in _open\n'
        "    handle = open(path)\n"
        "FileNotFoundError: [Errno 2] No such file or directory: 'tiles/03.tif'\n\n"
        "During handling of the above exception, another exception occurred:\n\n"
        f'  File "job.py", line {rng.randint(4, 90)}, in run\n'
        f"    {lib}.load(path)\n"
        "RuntimeError: loader failed",
        "The manifest lists tiles/01.tif and tiles/02.tif only; tiles/03.tif was "
        "never produced by the previous step.",
        "grounded",
        "grounded_chained_traceback",
    )


def plausible_but_unstated(rng: random.Random) -> dict:
    """Convention suggests a rename; nothing states it. Insufficient."""
    lib, kw = rng.choice(LIBS), rng.choice(KWARGS)
    return _case(
        f'  File "job.py", line {rng.randint(4, 90)}, in run\n'
        f"    {lib}.build(mesh, {kw}=1e-3)\n"
        f"TypeError: build() got an unexpected keyword argument '{kw}'",
        f"Other {lib} functions in this file use `{kw}_mm` as their parameter "
        f"name. No signature for build() is available here.",
        "needs_verification",
        "plausible_but_unstated",
    )


FAMILIES = [
    wrong_function_signature,
    deprecation_without_version,
    near_miss_symbol,
    grounded_but_buried,
    grounded_chained_traceback,
    plausible_but_unstated,
]


def tasks(count: int, seed: int) -> list[dict]:
    from tee.llm.chores import _TRIAGE_SYSTEM

    rng = random.Random(seed)
    out = []
    for index in range(count):
        family = FAMILIES[index % len(FAMILIES)]
        case = family(rng)
        evidence = f"Failure evidence:\n{case['failure']}"
        if case["context"]:
            evidence += f"\n\nContext (source/op):\n{case['context']}"
        out.append(
            {
                "system": _TRIAGE_SYSTEM,
                "prompt": evidence,
                "expect": case["expect"],
                "family": case["family"],
            }
        )
    return out


if __name__ == "__main__":
    import collections

    sample = tasks(12, 1)
    print(json.dumps(collections.Counter(t["expect"] for t in sample), indent=1))
