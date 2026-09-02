"""partkiln as a TEE adapter: mechanical parts through the existing 17-tool surface.

A66 P4. This package holds the process side first: `wire.SidecarKernel`
speaks NDJSON to `python -m partkiln.worker` in the sidecar venv that
survives the extension wipe. The adapter class (`adapter.PartkilnAdapter`)
and the 14 `pk_*` virtual tools (`tools.py`) land on top of it; nothing here
imports partkiln at runtime, so the server boots whether or not the kernel
is installed.
"""
