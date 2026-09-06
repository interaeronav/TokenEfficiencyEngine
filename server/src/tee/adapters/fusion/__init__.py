"""The Fusion lane (A69): Autodesk Fusion as a live GUI lane on the owner's
own document, through a bridge add-in - the TEE add-in (TCP 9881) or the
FusionMcpBridge the owner's Mac already runs (HTTP 8766), whichever answers."""

from tee.adapters.fusion.wire import (
    DEFAULT_HTTP_PORT,
    DEFAULT_PORT,
    FusionAutoWire,
    FusionHttpWire,
    FusionWire,
)

__all__ = ["DEFAULT_HTTP_PORT", "DEFAULT_PORT", "FusionAutoWire", "FusionHttpWire", "FusionWire"]
