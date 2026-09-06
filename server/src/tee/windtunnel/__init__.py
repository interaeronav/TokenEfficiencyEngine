"""The wind-tunnel lane (A68): OpenFOAM, SU2, OpenVSP/VSPAERO and ParaView at
arm's length, driven through thirteen `wt_*` virtual tools.

Design of record: docs/research/70-wind-tunnel-lane.md. Plan of record:
CLAUDE_A68_SCRIPT.md. User guide: docs/windtunnel-lane.md.

The boundary: the model never sees a cell. Points, fields, meshes and solver
logs stay on disk; every answer is a digest (no array over 64 elements, no
string over 2 KB) that carries the engine, its version, the mesh hash, a
convergence verdict and an uncertainty label.

Licences, so nobody has to look them up again: OpenFOAM is GPL-3, SU2 is
LGPL-2.1, OpenVSP is NASA Open Source Agreement 1.3, gmsh is GPL-2+ - all
four are SEPARATE PROCESSES, never imported, never vendored; ParaView is
BSD-3 and is driven through its own `pvpython`, never through a `vtk` import.
The only in-process helpers are `meshio` (MIT) and numpy, inside the optional
`[windtunnel]` extra, reached lazily by one function (`report._export_vtu`);
`test_windtunnel_licences.py` is the gate. Importing this package loads none
of them.
"""

__all__ = ["register_windtunnel_tools"]


def register_windtunnel_tools(app, project_root):  # pragma: no cover - re-export
    from tee.windtunnel.tools import register_windtunnel_tools as _reg

    return _reg(app, project_root)
