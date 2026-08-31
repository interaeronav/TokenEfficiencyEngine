"""A46 close-out — the version the server reports is not a second opinion.

`tee/__init__.py` restated the version as a literal, separate from
pyproject. They drifted: the 0.10.0 bundle shipped with the distribution
metadata saying 0.10.0 while `tee --version` and the MCP handshake both
said 0.9.0, because a release bump touched three files and this was a
fourth. Same shape as the P2a defect - one question, two answers.
"""

from __future__ import annotations

from importlib.metadata import version

import tee


def test_the_reported_version_is_the_installed_one():
    assert tee.__version__ == version("tee-engine")


def test_the_version_is_not_a_literal_in_the_source():
    """The guard that keeps it from being re-hardcoded by a future bump."""
    import pathlib
    import re

    src = pathlib.Path(tee.__file__).read_text()
    assert not re.search(r'^__version__\s*=\s*["\']\d', src, re.M), (
        "__version__ is a literal again - it will drift from pyproject"
    )
