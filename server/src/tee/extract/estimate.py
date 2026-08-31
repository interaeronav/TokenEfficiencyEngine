"""SI-B22 — dimensions ESTIMATED from a photo, under a stated mitigation.

The extraction discipline reported measurements only where a measurement
existed. That is right for drawings, where `DIMENSION.get_measurement()` is
ground truth, and wrong for the case it most often meets: a site photo with
no scale bar and no drawing, where refusing to answer withholds a usable
number because it cannot be a perfect one.

**This does not relax the discipline; it extends it to a new source.** The
A40 law already in `docs/DECISIONS.md` — "accuracy claims carry their
source's honesty band" — is the rule being applied, not bent. So an
estimate is produced ONLY when all three hold:

1. **A mitigation is named.** Something of known size, measured in the same
   pixels. No reference, no estimate — the refusal is the feature.
2. **An honest band travels with it.** The tolerance of the reference and
   the pixel-picking error propagate into the answer, so the caller is told
   +/- what, and why.
3. **It can never be read as measured.** The value lands in
   `estimated_mm`, never `mm`. A consumer looking for a measurement does
   not accidentally find an estimate.

**TEE never supplies the reference's real size.** Asking a model what a
"standard door" measures is how a hallucinated 2032 mm becomes a structural
dimension; door leaves, brick courses and window modules all vary by region
and era. The caller supplies the size they know, and TEE does the
arithmetic and the error propagation on it. The one exception is ISO 216
paper, which is an international standard with exact millimetre sizes — an
A4 sheet taped to a wall is the cheapest scale reference on any site.

**The assumption that invalidates everything.** A scale in metres-per-pixel
holds only in the plane the reference sits in. A reference on the near wall
does not scale the far wall, and nothing here can detect that from the
numbers alone. Every result says so, and `coplanar` must be affirmed by the
caller — a deliberate speed bump, not paperwork.
"""

from __future__ import annotations

import math
from typing import Any

from tee.kernel.errors import TeeError

# ISO 216 short/long edge in millimetres. EXACT by the standard, which is
# why these are the only sizes TEE will supply on its own behalf.
ISO_216 = {
    "a0": (841, 1189), "a1": (594, 841), "a2": (420, 594), "a3": (297, 420),
    "a4": (210, 297), "a5": (148, 210), "a6": (105, 148),
}  # fmt: skip

# Pixel-picking error assumed for a human or model clicking two endpoints.
# Two endpoints, so the edge error is sqrt(2) x the per-point error.
POINT_PICK_PX = 2.0
EDGE_PICK_PX = POINT_PICK_PX * math.sqrt(2)

# A reference smaller than this cannot carry a scale worth reporting: the
# picking error alone swamps it.
MIN_REFERENCE_PX = 40.0


def _reference_mm(spec: dict[str, Any]) -> tuple[float, float, str]:
    """(size_mm, tolerance_mm, how it was established). Refuses rather than
    guessing a size TEE was not given."""
    iso = str(spec.get("reference_iso216") or "").strip().lower()
    if iso:
        if iso not in ISO_216:
            raise TeeError(
                "estimate_bad_reference",
                f"'{iso}' is not an ISO 216 size.",
                fix=f"Use one of: {', '.join(sorted(ISO_216))}.",
            )
        short, long_ = ISO_216[iso]
        edge = str(spec.get("reference_edge") or "long").lower()
        if edge not in ("short", "long"):
            raise TeeError(
                "estimate_bad_reference",
                f"reference_edge='{edge}' is not 'short' or 'long'.",
                fix="Say which edge of the sheet you measured.",
            )
        mm = float(long_ if edge == "long" else short)
        # ISO 216 is exact; the trimming tolerance is +/-1 mm at these sizes.
        return mm, 1.0, f"ISO 216 {iso.upper()} {edge} edge ({mm:.0f} mm, exact by standard)"

    raw = spec.get("reference_mm")
    if raw is None:
        raise TeeError(
            "estimate_no_reference",
            "An estimate needs something of known size in the same photo.",
            fix="Give reference_mm (what you know it measures) and "
            "reference_px (how long it is in the image), or "
            'reference_iso216: "a4" for a sheet of paper in shot. TEE will '
            "not supply the size itself - a guessed door height becomes a "
            "structural dimension.",
        )
    try:
        mm = float(raw)
    except (TypeError, ValueError) as exc:
        raise TeeError(
            "estimate_bad_reference", "reference_mm must be a number.", fix="e.g. 900 for a door."
        ) from exc
    if mm <= 0:
        raise TeeError(
            "estimate_bad_reference", "reference_mm must be positive.", fix="Give a real length."
        )
    tol = spec.get("reference_tolerance_mm")
    if tol is None:
        # Unstated tolerance is not zero tolerance. 2% is a deliberately
        # unflattering default so an unqualified reference widens the band.
        tol_mm, how = mm * 0.02, f"{mm:.0f} mm as supplied, tolerance unstated (2% assumed)"
    else:
        tol_mm = abs(float(tol))
        how = f"{mm:.0f} mm as supplied, +/-{tol_mm:g} mm"
    return mm, tol_mm, how


def estimate_length(spec: dict[str, Any]) -> dict[str, Any]:
    """A length in millimetres from a photo, marked estimated, with a band.

    spec: reference_mm + reference_px (or reference_iso216 + reference_edge),
          target_px, coplanar=true, and optionally reference_tolerance_mm,
          label.
    """
    ref_mm, ref_tol_mm, ref_how = _reference_mm(spec)

    try:
        ref_px = float(spec.get("reference_px"))
        target_px = float(spec.get("target_px"))
    except (TypeError, ValueError) as exc:
        raise TeeError(
            "estimate_bad_pixels",
            "reference_px and target_px must both be numbers.",
            fix="Measure both in the SAME image, in pixels.",
        ) from exc
    if ref_px <= 0 or target_px <= 0:
        raise TeeError(
            "estimate_bad_pixels",
            "Pixel lengths must be positive.",
            fix="Measure both in the same image.",
        )
    if ref_px < MIN_REFERENCE_PX:
        raise TeeError(
            "estimate_reference_too_small",
            f"The reference is only {ref_px:.0f} px; below {MIN_REFERENCE_PX:.0f} px "
            "the picking error swamps the answer.",
            fix="Use a larger reference in the frame, or a closer photo.",
        )
    if not bool(spec.get("coplanar")):
        raise TeeError(
            "estimate_not_coplanar",
            "The reference and the thing measured must lie in the same plane.",
            fix="Pass coplanar: true once you have checked that they do. A "
            "scale taken off the near wall does not measure the far wall, "
            "and no arithmetic here can detect that for you.",
        )

    mm_per_px = ref_mm / ref_px
    value_mm = mm_per_px * target_px

    # Relative errors add in quadrature: the reference's own tolerance, and
    # the pixel picking on each of the two edges.
    rel_ref = ref_tol_mm / ref_mm
    rel_ref_px = EDGE_PICK_PX / ref_px
    rel_target_px = EDGE_PICK_PX / target_px
    rel = math.sqrt(rel_ref**2 + rel_ref_px**2 + rel_target_px**2)
    band_mm = value_mm * rel

    return {
        "ok": True,
        # NOT "mm". A consumer looking for a measurement must not find this.
        "estimated_mm": round(value_mm, 1),
        "band_mm": round(band_mm, 1),
        "relative_error": round(rel, 4),
        "label": str(spec.get("label") or "length"),
        "estimated": True,
        "measured": False,
        "method": "reference_scale",
        "mitigation": ref_how,
        "mm_per_px": round(mm_per_px, 5),
        "basis": (
            f"scale from a known reference in the same plane; "
            f"reference tolerance {rel_ref * 100:.1f}%, pixel picking "
            f"{math.sqrt(rel_ref_px**2 + rel_target_px**2) * 100:.1f}% "
            f"(+/-{POINT_PICK_PX:g} px per endpoint)"
        ),
        "assumption": (
            "the reference and the measured feature lie in ONE plane, square "
            "to the camera; perspective and lens distortion are not corrected"
        ),
        "note": (
            "An ESTIMATE, not a measurement. Where a drawing or a survey "
            "exists, that governs and this must not be used."
        ),
    }
