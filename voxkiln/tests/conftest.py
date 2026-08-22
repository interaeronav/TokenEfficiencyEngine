import os
import sys
from pathlib import Path

# Portable backends for the vendored tree, set before any trellis2 import.
os.environ.setdefault("SPARSE_ATTN_BACKEND", "sdpa")
os.environ.setdefault("SPARSE_CONV_BACKEND", "none")

_VENDOR = Path(__file__).resolve().parent.parent / "vendor"
for p in (_VENDOR, _VENDOR / "o-voxel"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))
