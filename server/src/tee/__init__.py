"""Token Efficiency Engine - MCP server + API layer for Unreal Engine and Blender."""

from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as _version

# Read from the installed distribution rather than restating it here.
#
# This was a hardcoded literal, and it drifted: the 0.10.0 bundle shipped
# with pyproject saying 0.10.0 and `tee --version` saying 0.9.0, because
# bumping the release touched three files and this was a fourth. A version
# the server reports about ITSELF should not be a second opinion.
try:
    __version__ = _version("tee-engine")
except PackageNotFoundError:  # running from a source tree, never installed
    __version__ = "0+unknown"
