"""The pattern kernel: panels, seams, allowance, interchange, plotting.

Import-light on purpose - `shapely` and `ezdxf` load with the submodules
that need them, so `import seamkiln.pattern` stays cheap.
"""

from seamkiln.pattern.model import (
    EdgeRef,
    GradeRule,
    InternalLine,
    LineKind,
    Mark,
    MarkKind,
    Panel,
    Pattern,
    Seam,
    SeamCheck,
    grade,
    mirror,
    true_up,
    unfold,
)

__all__ = [
    "EdgeRef",
    "GradeRule",
    "InternalLine",
    "LineKind",
    "Mark",
    "MarkKind",
    "Panel",
    "Pattern",
    "Seam",
    "SeamCheck",
    "grade",
    "mirror",
    "true_up",
    "unfold",
]
