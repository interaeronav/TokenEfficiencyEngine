# partkiln setup — the mechanical CAD lane (A66)

Two routes reach the kernel, and they fail differently. Read both before
installing anything: the wrong one on this machine silently replaces a
working OCCT wheel.

| route | interpreter | when it is right |
| --- | --- | --- |
| **in-process** | `server/.venv/bin/python` (the repo dev venv, Python 3.11 with OCP already installed) | development in this checkout |
| **sidecar** | `~/TEE/.tee/sidecars/partkiln/bin/python` | **production**, and the only route that survives an upgrade |

`tee doctor` prints which one is live, both interpreters' versions, and the
OCCT version behind them.

## Python 3.11 only

`partkiln` declares `>=3.11,<3.15`, but the OCP wheel is the real constraint:
build every venv for this lane with `--python 3.11`. The default `python3` on
this machine is 3.14 — never build anything for this lane with it. The Claude
Desktop extension venv is **3.13 with no OCP at all**, which is precisely why
the sidecar exists.

## Dev install (this checkout)

```bash
uv pip install --python server/.venv/bin/python -e partkiln
```

**Never add `[brep]` here.** `server/.venv` already has `cadquery-ocp`, and
the `[brep]` extra pulls `cadquery-ocp-novtk`, which ships the *same*
top-level `OCP/` package — installing it would clobber the wheel that is
already working (measured, P0a row 3). The extra exists for a venv that has
no OCP yet; `partkiln` accepts either wheel by `find_spec("OCP")`.

## Production install (the sidecar that survives upgrades)

```bash
uv venv --python 3.11 ~/TEE/.tee/sidecars/partkiln
uv pip install --python ~/TEE/.tee/sidecars/partkiln/bin/python \
    -e <repo>/partkiln[brep]
```

Why a second venv at all: **every `.mcpb` install rebuilds the extension venv
from the lock and deletes anything extra, including an editable install.** The
sidecar venv under `~/TEE/.tee/sidecars/` is outside that blast radius, and
`tee_purge` leaves it alone too. So the sidecar is not a fallback — it is the
route production takes, and the in-process kernel is the developer's
convenience.

The server spawns it as `python -m partkiln.worker` and speaks newline-JSON
over its pipes. It is persistent for the server's life, one request in
flight, and a request that overruns its deadline **kills** the worker — OCCT
offers no cancellation from Python, so that is the only guard there is. The
adapter then respawns it and replays the script (0.09–0.46 s per 100 cuts) and
notes the respawn in the next diff.

## Serve

**From Claude Desktop you do not start a server; the extension does, and it
serves three lanes at once** (`--adapter blender --adapter partkiln
--adapter seamkiln`, since the multi-adapter change of 2026-09-04). Blender
is the declared default, so a batch with no `adapter=` goes there; a partkiln
batch says `adapter=partkiln`. `pk_probe` answering `pk_not_served` means an
older one-adapter bundle is installed, not a missing kernel - reinstall the
current `.mcpb`. The kernel itself still has to be installed on one of the
two routes below; the extension's own venv is wiped on every upgrade, which
is why the sidecar route exists.


```bash
tee serve --adapter partkiln --project ~/parts
```

Building the app submits `partkiln_warm` as an **interactive job**: `import
OCP` costs about 26 s in a cold venv and 0.29 s warm, and Law 17 says no call
ever waits on that. So:

* `pk_probe`, `tee_scene_summary` and `tee_checkpoint` answer immediately,
  from the in-process command mirror (a checkpoint taken then says
  `brep: false` and restores by replay);
* a `tee_batch` that lands inside the warm-up waits two seconds and then
  refuses `pk_warming` with the job id — poll it with `tee_job`.

## Configuration

`.tee/config.toml` in the project:

```toml
[partkiln]
python = "~/TEE/.tee/sidecars/partkiln/bin/python"   # override the sidecar interpreter
batch_timeout_s = 60                                  # under kernel/script.py MAX_SECONDS=120
```

Both are optional. `ProjectConfig` drops tables it does not know, so a
`[partkiln]` block only takes effect on a server that has this field — if a
setting seems ignored, check `tee doctor` first.

## Verifying the install

```bash
tee doctor                       # names the mode, both interpreters and OCCT
```

and from a session:

```
tee_call(name="pk_probe")        # mode, warm state, OCCT, formats, licences
tee_search_tools("export STEP")  # pk_export should come back top-3
```

`pk_probe` refusing `pk_kernel_absent` means neither route is present; its fix
line carries both install commands verbatim.

## Tests

```bash
cd partkiln && PYTHONPATH=src uv run --project ../server python -m pytest -q tests/
cd server   && uv run python -m pytest -q tests/test_partkiln_adapter.py \
                                          tests/test_partkiln_translate.py \
                                          tests/test_partkiln_live.py \
                                          tests/test_partkiln_wire.py
```

The adapter and translate suites need no kernel at all (a `FakeKernel` of
plain arithmetic). The live suite skips cleanly without OCP, and its sidecar
tests are `-m dcc` with a 300 s timeout because a genuinely cold import does
not fit the suite's 60 s default.
