"""critique -> correct -> critique again, until it stops improving.

The loop is the point. A single pass tells you a drawing is wrong; a loop
tells you whether your corrections actually fixed it, and stops when they
no longer do. It terminates on a fixed point, not on a fixed iteration count,
and it reports what survived - because some findings need a human and looping
harder will never clear them.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from drafting import standards as S
from drafting.critic import critique
from drafting.spec import DrawingSet

MAX_PASSES = 8


@dataclass
class Pass:
    index: int
    before: int
    fixed: int
    after: int
    blocking: int


@dataclass
class LoopResult:
    passes: list[Pass] = field(default_factory=list)
    changes: list[S.Finding] = field(default_factory=list)
    remaining: list[S.Finding] = field(default_factory=list)
    converged: bool = False

    def summary(self) -> str:
        rows = [
            f"  pass {p.index}: {p.before:3d} open -> fixed {p.fixed:3d} -> "
            f"{p.after:3d} open ({p.blocking} blocking)"
            for p in self.passes
        ]
        tail = "converged" if self.converged else f"stopped at {MAX_PASSES} passes"
        return "\n".join([*rows, f"  {tail}; {len(self.remaining)} need a human"])


def run(dset: DrawingSet, **correction_inputs) -> LoopResult:
    from drafting.corrector import correct

    result = LoopResult()
    previous = None
    for index in range(1, MAX_PASSES + 1):
        before = critique(dset)
        fixes = correct(dset, **correction_inputs)
        after = critique(dset)
        result.passes.append(
            Pass(index, len(before.open), len(fixes.findings), len(after.open), len(after.blocking))
        )
        result.changes.extend(fixes.findings)
        if len(after.open) == previous or not fixes.findings:
            result.converged = True
            result.remaining = after.open
            break
        previous = len(after.open)
    else:
        result.remaining = critique(dset).open
    return result
