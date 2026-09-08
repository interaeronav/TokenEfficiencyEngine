"""ParaView state files: the handoff from a headless case to a human's screen.

A `.pvsm` is XML ParaView writes for itself, so TEE does not compose one -
it drives `pvpython` to build the pipeline and calls `SaveState`, the same
arm's-length posture the rest of this lane takes (no `vtk`, no `paraview`
import ever happens in this process). The reader block is
`paraview._reader_lines`, so a state opens exactly what `wt_view` renders.

Two kinds, and the difference was measured on 2026-09-07 rather than assumed
(doc 73 §2.7):

* **full** - reader, surface, colouring, scalar bar, camera, last time step.
  **206,584 bytes** over a 16,000-cell case as this module writes it, and it
  needs a display: with none it SEGFAULTS (rc 139), offscreen flag included,
  which is the fault doc 72 recorded for rendering.
* **pipeline** - reader, mesh regions, arrays, time, and nothing shown.
  **17,233 bytes**, rc 0, no display and no xvfb needed.

Both open at the last time step, and that took a second measurement to get
right (doc 73 §2.10): `SaveState` carries the ANIMATION SCENE's time, so a
state that set only the view's reloaded at t=0 - the initial field, coloured
and framed exactly like the solution.

So the writer asks for `full`, and falls back to `pipeline` where nothing can
render. Both open the case; only one arrives coloured. The reply says which,
because a caller told "opened" deserves to know what they will see.

The path of the case appears exactly ONCE in the XML, so a state that has to
follow a moved case is a one-string rewrite rather than a regeneration - which
is why `relocate()` exists and is a dozen lines.
"""

from __future__ import annotations

import os
import platform
import shutil
from pathlib import Path

from tee.kernel.errors import TeeError
from tee.windtunnel import paraview

KINDS = ("full", "pipeline")

# The last time step has to be set on the ANIMATION SCENE, not only on the
# view. A state that sets `rv.ViewTime` alone reloads at 0.0 - measured on
# 5.11.2, doc 73 §2.10 - so the human who opened the handoff would be looking
# at the initial field while believing it was the solution. The scene carries
# the time through SaveState, and a state with no view (kind='pipeline') has
# nowhere else to put it.
_SCENE_TIME = (
    "    scene = GetAnimationScene()\n"
    "    scene.UpdateAnimationUsingDataTimeSteps()\n"
    "    scene.AnimationTime = ts[-1]"
)

# The field each preset colours by, keyed the way wt_view keys them so one
# vocabulary serves the render and the handoff. None = no colouring.
_FIELD = {"pressure": "p", "velocity": "U", "cp": "p", "mesh": None, "residuals": None}


def can_render() -> bool:
    """Whether a render view can be created here at all.

    macOS always can. Elsewhere it takes a DISPLAY, or `xvfb-run` to invent
    one; `--force-offscreen-rendering` does NOT save the apt build, measured.
    """
    if platform.system() == "Darwin":
        return True
    if os.environ.get("DISPLAY"):
        return True
    return bool(shutil.which("xvfb-run"))


def state_script(
    source: Path, out_pvsm: Path, *, view: str = "pressure", kind: str = "full"
) -> str:
    """The pvpython script that builds the pipeline and saves the state."""
    if kind not in KINDS:
        raise TeeError(
            "wt_bad_action",
            f"'{kind}' is not a state kind.",
            fix=f"One of: {', '.join(KINDS)}.",
        )
    if view not in paraview.VIEWS:
        raise TeeError(
            "wt_bad_view",
            f"'{view}' is not a view preset.",
            fix=f"One of: {', '.join(paraview.VIEWS)}.",
        )
    lines = [f"# {paraview.GENERATED_BY}", "from paraview.simple import *"]
    lines += paraview._reader_lines(source)
    if kind == "full":
        field = _FIELD[view]
        lines += [
            "rv = GetActiveViewOrCreate('RenderView')",
            "rv.OrientationAxesVisibility = 1",
            "d = Show(src, rv)",
            f"d.SetRepresentationType({'Surface With Edges' if view == 'mesh' else 'Surface'!r})",
        ]
        if field:
            lines += [
                f"ColorBy(d, ('CELLS', {field!r}))",
                "d.RescaleTransferFunctionToDataRange(True, False)",
                "d.SetScalarBarVisibility(rv, True)",
            ]
        else:
            # `ColorBy(d, None)` is the documented way to turn colouring off
            # and it RAISES here: on 5.11.2 it re-reads the representation's
            # current association, which is 'NONE' when the data carries no
            # array to auto-colour by - a meshed case that has not run, which
            # is exactly what this view is for (measured 2026-09-07, doc 73
            # §2.10). The tuple form names a valid association and unsets
            # the array, and works in both worlds.
            lines += ["ColorBy(d, ('CELLS', None))"]
        lines += [
            "if hasattr(ts, '__len__') and len(ts):",
            _SCENE_TIME,
            "    rv.ViewTime = ts[-1]",
            "rv.ResetCamera()",
            "Render(rv)",
        ]
    else:
        lines += ["if hasattr(ts, '__len__') and len(ts):", _SCENE_TIME]
    lines += [f"SaveState({str(out_pvsm)!r})", "print('OK')"]
    return "\n".join(lines) + "\n"


def write(
    pvpython: str,
    source: Path,
    out_pvsm: Path,
    *,
    view: str = "pressure",
    kind: str | None = None,
    timeout_s: float = 180.0,
) -> dict[str, object]:
    """Write a state file beside its case and report what was written.

    `kind=None` means "the best this machine can do": `full` where a render
    view can exist, `pipeline` where it cannot. An explicit `full` on a
    machine that cannot render is NOT quietly downgraded - it refuses, because
    a caller who asked for the coloured one should hear that they cannot have
    it rather than be handed something else.
    """
    if kind is None:
        kind = "full" if can_render() else "pipeline"
    elif kind == "full" and not can_render():
        raise TeeError(
            "wt_no_display",
            "A state with a view needs a render view, and this machine has none "
            "(no DISPLAY, no xvfb-run).",
            fix="Install xvfb (`apt-get install xvfb`), run where there is a display, "
            "or ask for kind='pipeline' - it opens the same case, uncoloured.",
        )
    render = kind == "full"
    out_pvsm.parent.mkdir(parents=True, exist_ok=True)
    script = state_script(source, out_pvsm, view=view, kind=kind)
    paraview.run_script(pvpython, script, out_pvsm.parent, render=render, timeout_s=timeout_s)
    if not out_pvsm.is_file():
        raise TeeError(
            "wt_state_failed",
            "pvpython reported success but wrote no state file.",
            fix=f"Check {out_pvsm.parent}/pv_script.py and the case it points at.",
        )
    return {
        "state": str(out_pvsm),
        "kind": kind,
        "bytes": out_pvsm.stat().st_size,
        "view": view if kind == "full" else None,
        "source": str(source),
    }


def relocate(pvsm: Path, old_source: Path, new_source: Path) -> int:
    """Re-point a state at a case that has moved.

    Measured: the case path appears exactly once in a state ParaView wrote, so
    this is a string substitution rather than a regeneration. Returns how many
    occurrences were replaced, so a caller can tell 0 (nothing to do, or the
    wrong pair) from 1 (done).
    """
    text = pvsm.read_text()
    n = text.count(str(old_source))
    if n:
        pvsm.write_text(text.replace(str(old_source), str(new_source)))
    return n
