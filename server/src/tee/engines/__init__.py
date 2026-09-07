"""The engine lane (A76): truth about the local models TEE routes work to.

TEE is a thorough client of local models and never a server of them - that
stays, and this lane never starts, stops, configures or serves anything. What
it adds is evidence. `kernel/machine.py::ENGINES` DECLARES capability,
footprint, latency and senses, and `llm/router.py::_ladder()` sorts the cascade
on those literals; nothing has ever reconciled them against what is actually
answering.

The measurement that made the case, from `docs/research/77-evidence`: the
owner's shim advertises eight routes, and **two of them produce text**. Four
answer HTTP 200 with empty content and a usage block claiming completion
tokens. `local_llm.available()` asks `GET /v1/models` and would call all eight
healthy. So `eng_check` asserts on CONTENT, never on a status code.

Laws this package is built to (doc 77 section 6):

* TEE serves no model - a test asserts this package opens no listening socket.
* The lane measures; the owner declares. It never writes `.tee/config.toml`;
  it prints the line to paste.
* Never start or stop anything, and never touch PROTECTED_PORTS.
* Never call a paid engine - refused by name, not gated behind consent.
* Never download weights; read what is on disk and talk to what is running.
* Senses come from the weights' own config.json, never from behaviour: the
  shim reroutes image requests, so through it every model appears to see.
* A latency number without a warm/cold label is a lie.
* The digest never probes.

Stdlib only, on purpose: `eng_reconcile` must answer on a machine with nothing
installed and nothing running.
"""

from __future__ import annotations

__all__ = ["register_engine_tools"]


def register_engine_tools(app, project_root):  # pragma: no cover - thin re-export
    from tee.engines.tools import register_engine_tools as _register

    return _register(app, project_root)
