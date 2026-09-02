"""Assemblies: poses, mates, joints, a solver, interference and a BOM (A66 P3).

A library over poses and shapes. The document verbs (`create component |
mate | joint`) are wired above this package; here a component is a name,
a part, a pose and a shape reference, and a mate holds frames the caller
already resolved from named sub-shapes (Law 13). `partkiln.assembly`
imports no OCP: the solver and the BOM run on numpy/scipy alone, and
`interference` reaches the kernel lazily through `partkiln.brep`.
"""

from __future__ import annotations

from partkiln.assembly.bom import bom
from partkiln.assembly.interference import clearance, interference, placed, report
from partkiln.assembly.model import (
    JOINT_KINDS,
    MATE_KINDS,
    Assembly,
    Component,
    FrameRef,
    Joint,
    Mate,
    Pose,
    Ref,
)
from partkiln.assembly.solver import SolveReport, apply_poses, solve

__all__ = [
    "JOINT_KINDS",
    "MATE_KINDS",
    "Assembly",
    "Component",
    "FrameRef",
    "Joint",
    "Mate",
    "Pose",
    "Ref",
    "SolveReport",
    "apply_poses",
    "bom",
    "clearance",
    "interference",
    "placed",
    "report",
    "solve",
]
