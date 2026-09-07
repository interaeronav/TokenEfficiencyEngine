"""The flight-dynamics lane (A75): a polar becomes an aircraft that flies.

JSBSim is **LGPL-2.0-or-later** and is used as a library, in-process, unmodified
and dynamically linked - the case LGPL section 6 is written for, ruled in
`docs/DECISIONS.md` (2026-09-07). Its licence is not what its metadata says:
PyPI declares `LGPLv2+` for the whole distribution while the wheel installs one
console script, `jsbsim/script.py`, under **GPL-3.0-or-later**. The gate in
`server/tests/test_flightdyn_licences.py` therefore reads the grant in each
installed file's own header rather than trusting `importlib.metadata`.

Nothing upstream is vendored. The wheel ships 60 aircraft and a directory of
engines; this lane uses the installed root or writes its own files, and the
goldens under `tests/data/flightdyn` carry `generated-by`.

Two measured facts shape the code rather than decorate it:

* `FGLinearization` on an aircraft whose `<propulsion>` is empty **kills the
  process** - SIGSEGV, no exception. So `fd_modes` refuses an engineless
  aircraft in our own code, and the heavy calls run out-of-process anyway.
* JSBSim's own `do_trim` cannot trim a generated aircraft: it evaluates the
  turbine before it has spooled, sees no throttle authority on `udot`, and
  reports `qdot` - the wrong axis. `trim.py` solves it ourselves instead.

The lane is stdlib at import time. numpy lives in the optional `flightdyn`
extra and is imported in exactly one place.
"""

from __future__ import annotations

__all__ = ["register_flightdyn_tools"]


def register_flightdyn_tools(app, project_root):  # pragma: no cover - thin re-export
    from tee.flightdyn.tools import register_flightdyn_tools as _register

    return _register(app, project_root)
