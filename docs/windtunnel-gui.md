# The wind-tunnel panel (A72 gap 1, built in A73)

A window over the `wt_*` lane: cases on the left, controls and the last answer
on the right. It exists because a CFD case is a thing you watch — a solve takes
minutes, and pressing Cancel is easier than composing a tool call — and because
the picture belongs to an application that already knows how to draw it.

```bash
uv pip install --python server/.venv/bin/python 'tee-engine[gui]'
server/.venv/bin/python -m tee.windtunnel.gui.app --project ~/TEE
```

PySide6 is LGPL-3.0 and is imported inside functions in one module, so the
package imports with Qt absent and a test asserts it. Nothing is registered as
a console script and **no tool is added**: the always-loaded surface is still
17 tools. A kernel that installs a window on the PATH is not headless-first.

## The one law

**It renders nothing.** A67 ruled that TEE builds no viewer, and partkiln
refused a 3-D pane on the ground that a second-rate GL widget inside Qt would
be a worse picture and a whole new surface to maintain. Both hold here. The
panel drives the lane and hands the picture to ParaView or OpenVSP, which is
what `wt_open` is for.

The second law follows from the first: the window **holds no model of its own**.
There is no cached case list, no remembered verdict, no second copy of anything
the lane already knows. Every pane is the last answer a tool gave, which is the
same compact state a model sees.

## What the window shows

| Pane | Source | Never |
| --- | --- | --- |
| Case list | `wt_case action=list` | a directory walk, a store read |
| Status line | `wt_status` on a tick, after `tee_job` | a solver log, a residual plot |
| Result line | `wt_result` | a bare coefficient — the verdict and the uncertainty label travel with it |
| Output pane | the last answer, or the refusal's message and fix | a traceback |
| Anything visual | — | there is no such pane |

## The controls

Each one builds the arguments a model would send and calls the same tool, so
there is no path through the window that a tool call could not take.

| Button | Tool | Note |
| --- | --- | --- |
| Mesh | `wt_mesh` | a job; the window polls it |
| Run | `wt_run` | a job, with `confirm_cost` — pressing the button IS the confirmation |
| Cancel | *(none)* | the one control with no virtual tool: `tee_job` is an always-loaded MCP tool, so the shell asks the same job manager directly |
| Open in ParaView | `wt_open` | writes the state file; **does not** open a window |
| Open in OpenVSP | `wt_open app=openvsp` | names the `.vsp3`; **does not** open a window |

**The panel never opens a window by itself.** `launch` is not among the
arguments any control builds, and a test walks every control to keep it that
way. Pressing "Open in ParaView" prepares the handoff and prints the command;
you open the application, or ask the tool for `launch=true` deliberately.

## Where the code is, and why it is split that way

| Module | Qt? | Role |
| --- | --- | --- |
| `actions.py` | no | each control builds `(tool, args)`; touches no registry |
| `shell.py` | no | makes the calls, formats what came back, holds the job id |
| `app.py` | **yes** | the window, and nothing else |

partkiln's split, for partkiln's stated reason: a shell whose logic lived in
the widgets would ship untested, *"which is exactly how seamkiln's follow-up
buttons went eleven campaigns unexercised."* All fourteen panel tests drive
`shell` with no window at all, and a fresh interpreter asserts that importing
the package leaves PySide6 out of `sys.modules`.

## What it does not do

- **Render.** See the one law.
- **Poll a solver itself.** `tee_job` owns whether the work is finished and
  `wt_status` owns what the solver is doing; asking the second without the
  first is how a window ends up reporting `running` for a job that died.
- **Create cases.** `wt_case action=create` takes a geometry, conditions and a
  fidelity choice — a form for that would be a worse `wt_case`. Make the case
  from the model or the command line; the panel runs and watches it.
- **Replace the tools.** Everything here is a tool call you could have made.
