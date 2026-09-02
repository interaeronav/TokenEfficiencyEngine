"""partkiln: a headless, AI-native mechanical CAD kernel on OCCT.

`import partkiln` must succeed with no OCP, no Qt and no TEE installed: every
OCP import lives lazily under `partkiln.brep`, the document, units, parameters
and the sketch solver are pure numpy/scipy, and nothing here imports `tee`.
"""

from __future__ import annotations

__version__ = "0.1.0.dev0"

__all__ = ["__version__"]
