"""Voxkiln: AI-first local image-to-3D generation, built on Microsoft
TRELLIS.2 (MIT).

The public surface is deliberately tiny (decision A28): `generate` /
`submit` / `wait` / `query` on a `JobStore`, plus `doctor()`. Everything
heavy (torch, the vendored pipeline) loads lazily - `import voxkiln` works
on a machine with no GPU stack and reports its unavailability honestly
instead of crashing.
"""

from __future__ import annotations

import os as _os

# MUST be set BEFORE torch is imported anywhere in the process. PyTorch reads
# it when the MPS backend initialises, so setting it later - e.g. in
# Engine.load(), which runs long after probe() imported torch - is a no-op and
# the run dies on the first op without an MPS kernel
# (`aten::segment_reduce`, sparse basic.py:283). Harmless off Apple Silicon.
# The cost is real and belongs in the record: ops that fall back run on CPU,
# which is a silent perf cliff (research 45).
_os.environ.setdefault("PYTORCH_ENABLE_MPS_FALLBACK", "1")

__version__ = "0.1.0"
UPSTREAM_COMMIT = "75fbf0183001ed9876c8dbb35de6b68552ee08bd"
MODEL_REPO = "microsoft/TRELLIS.2-4B"
# The image-conditioning tower the pipeline config names. It is GATED on the
# Hub ("gated: manual"), so having the 15 GB of TRELLIS weights cached is NOT
# sufficient to generate - see doctor's gated_weights check.
IMAGE_COND_REPO = "facebook/dinov3-vitl16-pretrain-lvd1689m"

__all__ = [
    "IMAGE_COND_REPO",
    "MODEL_REPO",
    "UPSTREAM_COMMIT",
    "__version__",
]
