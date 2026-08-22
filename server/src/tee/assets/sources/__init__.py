"""Source backend registry (A13). Tier-1: Poly Haven, ambientCG,
Poly Pizza, Smithsonian Open Access. Guarded opt-in: Sketchfab.

Excluded by decision (do not add without a DECISIONS.md entry): Fab /
Megascans (no API, ToS), ShareTextures (ToS bans automated downloads),
OpenGameArt (GPL contamination), Objaverse (provenance disputes),
BlenderKit third-party API use (needs written permission).
"""

from __future__ import annotations

import os
from typing import Any

from tee.assets.sources.ambientcg import AmbientCG
from tee.assets.sources.base import SourceBackend
from tee.assets.sources.polyhaven import PolyHaven
from tee.assets.sources.polypizza import PolyPizza
from tee.assets.sources.sketchfab import Sketchfab
from tee.assets.sources.smithsonian import Smithsonian


def build_backends(store, config: dict[str, Any] | None = None) -> dict[str, SourceBackend]:
    """Instantiate the enabled backends. Keyless tier-1 backends are always
    on; keyed ones activate when their key is present (env first, config
    second); Sketchfab only on explicit opt-in ([assets] sketchfab=true)."""
    config = config or {}
    backends: dict[str, SourceBackend] = {
        "polyhaven": PolyHaven(store),
        "ambientcg": AmbientCG(store),
    }
    polypizza_key = os.environ.get("TEE_POLYPIZZA_KEY") or config.get("polypizza_key")
    if polypizza_key:
        backends["polypizza"] = PolyPizza(store, api_key=str(polypizza_key))
    smithsonian_key = os.environ.get("TEE_SMITHSONIAN_KEY") or config.get("smithsonian_key")
    if smithsonian_key:
        backends["smithsonian"] = Smithsonian(store, api_key=str(smithsonian_key))
    if config.get("sketchfab"):
        token = os.environ.get("TEE_SKETCHFAB_TOKEN") or config.get("sketchfab_token")
        backends["sketchfab"] = Sketchfab(store, token=str(token) if token else None)
    only = config.get("backends")
    if isinstance(only, list) and only:
        backends = {k: v for k, v in backends.items() if k in only}
    return backends
