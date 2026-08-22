"""License gate (decision A13): SPDX allowlist, failing CLOSED.

Two distinct concerns are tracked separately per backend: the ASSET license
(what the downloaded work is under) and the SITE ToS (what the API/host
permits). The gate below rules on asset licenses; site-ToS constraints live
on each backend as declared facts (docs + doctor output), because a ToS is a
contract with the operator, not a property of the file.

Anything not explicitly allowed is blocked: NC, ND, GPL, unknown, missing,
"free" without a license id - all refused before a byte enters the cache.
"""

from __future__ import annotations

from dataclasses import dataclass

from tee.kernel.errors import TeeError

# Always-allowed SPDX ids (A13).
ALLOWED = {
    "CC0-1.0",
    "CC-BY-4.0",
    "CC-BY-3.0",
    "CC-PDDC",  # public-domain dedication (Smithsonian uses CC0; PD kept for museum sources)
}

# Allowed only when the project opts in ([assets] allow_sa = true):
# share-alike obligations propagate into the user's distribution.
SA_LICENSES = {"CC-BY-SA-4.0", "CC-BY-SA-3.0"}

# Common aliases seen in the wild, normalized to SPDX before gating.
_ALIASES = {
    "cc0": "CC0-1.0",
    "cc-0": "CC0-1.0",
    "cc zero": "CC0-1.0",
    "creative commons 0": "CC0-1.0",
    "public domain": "CC-PDDC",
    "pd": "CC-PDDC",
    "cc by": "CC-BY-4.0",
    "cc-by": "CC-BY-4.0",
    "cc by 4.0": "CC-BY-4.0",
    "cc-by 4.0": "CC-BY-4.0",
    "cc by 3.0": "CC-BY-3.0",
    "cc-by-sa": "CC-BY-SA-4.0",
    "cc by-sa": "CC-BY-SA-4.0",
    "cc by-sa 4.0": "CC-BY-SA-4.0",
}

# Canonical license text locations, snapshotted into the attribution
# manifest at download time (platform churn survives; A13).
LICENSE_TEXT_URLS = {
    "CC0-1.0": "https://creativecommons.org/publicdomain/zero/1.0/legalcode.txt",
    "CC-BY-4.0": "https://creativecommons.org/licenses/by/4.0/legalcode.txt",
    "CC-BY-3.0": "https://creativecommons.org/licenses/by/3.0/legalcode.txt",
    "CC-BY-SA-4.0": "https://creativecommons.org/licenses/by-sa/4.0/legalcode.txt",
    "CC-BY-SA-3.0": "https://creativecommons.org/licenses/by-sa/3.0/legalcode.txt",
    "CC-PDDC": "https://creativecommons.org/publicdomain/mark/1.0/",
}

ATTRIBUTION_REQUIRED = {"CC-BY-4.0", "CC-BY-3.0", "CC-BY-SA-4.0", "CC-BY-SA-3.0"}


def normalize_spdx(license_id: str | None) -> str | None:
    """Best-effort mapping of backend license strings to SPDX ids. Returns
    None when the input cannot be identified - which the gate then blocks."""
    if not license_id:
        return None
    text = license_id.strip()
    if text in ALLOWED or text in SA_LICENSES:
        return text
    return _ALIASES.get(text.lower())


@dataclass
class LicenseDecision:
    spdx: str
    allowed: bool
    attribution_required: bool
    note: str | None = None


def gate(license_id: str | None, *, allow_sa: bool = False) -> LicenseDecision:
    """Rule on one asset license. Raises TeeError (license_blocked) for
    anything outside the allowlist - the caller must not cache the asset."""
    spdx = normalize_spdx(license_id)
    if spdx is None:
        raise TeeError(
            "license_blocked",
            f"License '{license_id or '(missing)'}' is not identifiable as an "
            "allowed SPDX id - refusing to cache (fail-closed).",
            fix="Allowed: CC0-1.0, CC-BY-4.0/3.0 (SA behind [assets] allow_sa). "
            "NC/ND/GPL/unknown are never cached.",
        )
    if spdx in SA_LICENSES:
        if not allow_sa:
            raise TeeError(
                "license_blocked",
                f"{spdx} is share-alike: derivative distributions must carry the "
                "same license. Blocked by default.",
                fix="Opt in with `allow_sa = true` under [assets] in .tee/config.toml "
                "if the project accepts SA obligations.",
            )
        return LicenseDecision(
            spdx,
            True,
            True,
            note="share-alike: distribution of derivatives must be under the same license",
        )
    if spdx not in ALLOWED:
        raise TeeError(
            "license_blocked",
            f"License '{spdx}' is not on the allowlist - refusing to cache.",
            fix="Allowed: CC0-1.0, CC-BY-4.0/3.0 (SA behind [assets] allow_sa).",
        )
    return LicenseDecision(spdx, True, spdx in ATTRIBUTION_REQUIRED)
