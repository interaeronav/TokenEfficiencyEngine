"""The Fusion lane (A69): Autodesk Fusion as a live GUI lane on the owner's
own document, through the TEE bridge add-in."""

from tee.adapters.fusion.wire import DEFAULT_PORT, FusionWire

__all__ = ["DEFAULT_PORT", "FusionWire"]
