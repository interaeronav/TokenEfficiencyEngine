"""Compose the Okongo as-scanned drawing set, critic-in-the-loop.

Run from the repo root with the server venv:

    server/.venv/bin/python drafting/examples/okongo_reissue.py

It expects a levelled cloud already in the pc_* workspace (see
`docs/pointcloud-lane.md`) and writes the sheets to ~/Downloads.

This lives in examples/ rather than in the package because what goes INSIDE a
sheet is the project's business; `drafting` owns only the standards-compliant
frame and the two critic tiers.
"""

import json
import sys
import textwrap

sys.path.insert(0, "/Users/john/TokenEfficiencyEngine/server/src")
sys.path.insert(0, "/Users/john/TokenEfficiencyEngine/drafting/src")
from pathlib import Path

import numpy as np
from matplotlib.patches import Polygon
from PIL import Image
from tee.pointcloud import slice2d
from tee.pointcloud.store import CloudStore

from drafting import loop
from drafting import standards as S
from drafting.compose import ACCENT, FAINT, GREY, INK, MUTED, compose
from drafting.critic import critique
from drafting.linework import close_corners, poche_bodies
from drafting.okongo import as_issued

SCRATCH = Path(
    "/private/tmp/claude-501/-Users-john-TokenEfficiencyEngine/1d43fd51-eeff-4925-b1bd-bb2fba2d38c1/scratchpad"
)
WORK = SCRATCH / "okongo-work"
OUT = Path.home() / "Downloads/Okongo-Scan-Test"
OUT.mkdir(parents=True, exist_ok=True)
lid = json.loads((WORK / "outputs.json").read_text())["lid"]
P = CloudStore(WORK).points(lid)
band = slice2d.band(P, 1.20, 0.05)
RAW, _ = slice2d.fit_ortho(band)
SEGS = close_corners(RAW)
BODIES = poche_bodies(SEGS, band[:, :2])
POCHED = set()
for b in BODIES:
    for s_ in SEGS:
        pos = (s_["a"][0] + s_["b"][0]) / 2 if abs(s_["a"][0] - s_["b"][0]) < 0.05 else None
        if pos is not None and min(abs(pos - b.a[0]), abs(pos - b.d[0])) < 0.02:
            POCHED.add(id(s_))
        pos = (s_["a"][1] + s_["b"][1]) / 2 if abs(s_["a"][1] - s_["b"][1]) < 0.05 else None
        if pos is not None and min(abs(pos - b.a[1]), abs(pos - b.d[1])) < 0.02:
            POCHED.add(id(s_))
print(f"linework: {len(SEGS)} faces, {len(BODIES)} poche bodies")


def _principal(segs, axis, min_len=0.9):
    return sorted(
        (s_["a"][axis] + s_["b"][axis]) / 2
        for s_ in segs
        if abs(s_["a"][axis] - s_["b"][axis]) < 0.05
        and abs(s_["a"][1 - axis] - s_["b"][1 - axis]) > 0.05
        and s_["length_m"] > min_len
    )


_X, _Y = _principal(SEGS, 0), _principal(SEGS, 1)
# Named walls are DERIVED from the current fit, never carried forward as
# constants: re-levelling moves them by a few millimetres and a stale constant
# would put a figured dimension on a wall that is no longer there.
W_W, W_E = _X[0], _X[-1]
R2_E = min(_X[1:-1], key=lambda v: abs(v - (W_W + 1.5)))


# Which surface a dimension goes to is a real question here, and the two sides
# of Room 01 answer it differently.
#
# A BARE wall is the OUTERMOST return: furniture always stands inside it, so
# searching a wide window and taking the extreme peak finds the wall. Searching
# a narrow band and taking the innermost peak finds the wardrobe instead - that
# mistake put the north wall 186 mm out.
#
# The west side is the exception. It is not one plane: four surfaces over about
# 460 mm, blockwork with a built-in run in front of it, all along the room's
# full length. A tape touches the INNERMOST of those, so that is what the
# dimension goes to, and the sheet says so.
def _outermost(points, axis, side, lo, hi, olo, ohi, zlo=1.10, zhi=1.35):
    """The bare wall: the extreme dense surface across a wide window.

    `olo`/`ohi` bound the OTHER axis to this room. Without them the search runs
    out into the lobby and returns its wall instead - 82 mm of error, and the
    kind that looks like a plausible dimension.
    """
    sel = points[
        (points[:, 2] > zlo)
        & (points[:, 2] < zhi)
        & (points[:, axis] > lo)
        & (points[:, axis] < hi)
        & (points[:, 1 - axis] > olo)
        & (points[:, 1 - axis] < ohi)
    ]
    counts, edges = np.histogram(sel[:, axis], bins=200)
    strong = np.where(counts > 0.30 * counts.max())[0]
    i = strong.max() if side > 0 else strong.min()
    centre = float((edges[i] + edges[i + 1]) / 2)
    return float(np.median(sel[np.abs(sel[:, axis] - centre) < 0.03][:, axis]))


def _built_in_face(points, lo=-1.75, hi=-1.15, zlo=1.10, zhi=1.35):
    """The west assembly's room-side face - the densest return nearest the room."""
    sel = points[
        (points[:, 2] > zlo) & (points[:, 2] < zhi) & (points[:, 0] > lo) & (points[:, 0] < hi)
    ]
    counts, edges = np.histogram(sel[:, 0], bins=60)
    strong = np.where(counts > 0.30 * counts.max())[0]
    centre = float((edges[strong.max()] + edges[strong.max() + 1]) / 2)
    return float(np.median(sel[np.abs(sel[:, 0] - centre) < 0.025][:, 0]))


R1_W = _built_in_face(P)
R1_E = _outermost(P, 0, +1, 0.0, 1.72, -2.20, 1.50)
WEST_LAYERS = 4
# COMPASS, fixed by the owner on 2026-09-04 naming the cabinet wall as SOUTH:
# their south is this frame's -x. One named wall fixes the other three, to
# within the building's own skew. Nothing here is surveyed - the scan frame
# came from the dominant wall azimuth, which is not a bearing.
NORTH_BEARING_DEG = 90.0
W_S = _Y[0]
W_N = min((v for v in _Y if v > 1.2), default=_Y[-1])
R2_N = min((v for v in _Y if 0.5 < v < 1.4), default=W_N)
print(
    f"derived walls: W {W_W:.3f} E {W_E:.3f} S {W_S:.3f} N {W_N:.3f} | "
    f"R2_E {R2_E:.3f} R1_W {R1_W:.3f} R2_N {R2_N:.3f}"
)
CUT_A = ((-3.45, -1.80), (1.85, -1.80))
CUT_B = ((0.95, -2.60), (0.95, 2.60))


# --- the opening chain the corrector refused to invent, measured instead ----
def openings(segs, x_target, tol=0.09):
    runs = sorted(
        (min(s["a"][1], s["b"][1]), max(s["a"][1], s["b"][1]))
        for s in segs
        if abs((s["a"][0] + s["b"][0]) / 2 - x_target) < tol and abs(s["a"][0] - s["b"][0]) < 0.05
    )
    gaps = []
    for (_, e), (s2, _) in zip(runs, runs[1:]):
        if s2 - e > 0.30:
            gaps.append((e, s2))
    return gaps


DOOR = max(openings(SEGS, -1.54) + openings(SEGS, -1.66), key=lambda g: g[1] - g[0], default=None)
print(
    "door opening measured:",
    None
    if DOOR is None
    else f"{(DOOR[1] - DOOR[0]) * 1000:.0f} mm at y {DOOR[0]:.2f}..{DOOR[1]:.2f}",
)

# --- run the loop ----------------------------------------------------------
dset = as_issued()
before = critique(dset)
res = loop.run(
    dset,
    project={
        "project": "Okongo Oneleiwa",
        "client": "J. Nangolo (owner)",
        "scale": "",
        "date": "2026-09-04",
        "revision": "P06",
        "revision_note": "Cabinet run traced on E4 at owner's direction.",
        "drawn_by": "TEE pc_* (A67)",
        "checked_by": "",
    },
    rooms={"ROOM 01": "BEDROOM", "ROOM 02": "EN-SUITE / STORE"},
    cuts={"A": ("SK-01", 270.0), "B": ("SK-01", 180.0)},
    provenance=(
        "iPhone LiDAR (3D Scanner App 2.5), 1,520,736 points; levelled to 0.0000 deg, "
        "floor-plane RMS 13.0 mm. TAPE-CHECKED 2026-09-04 on two baselines. No scale "
        "correction applied - see the note on face ambiguity."
    ),
)
# the measured chain closes the last finding honestly
if DOOR:
    dset.by_number("SK-01").views[0].dimension_chains.append("opening")
after = critique(dset)
print(f"\nloop: {len(before)} -> {len(after.open)} open findings, {len(after.blocking)} blocking")
for f in after.open:
    print("   surviving:", f.line())

SK = {s.number: s for s in dset.sheets}
for s in dset.sheets:
    # a re-issue carries the re-issue's date, not the first issue's
    s.title_block.fields["date"] = "2026-09-04"
    s.title_block.fields["scale"] = (
        "1:%d @ A3" % s.views[0].scale_denominator if s.views[0].kind != "pictorial" else "NTS @ A3"
    )


def dim(ax, p1, p2, txt, off, vertical=False, size=7.1):
    p1 = np.array(p1, float)
    p2 = np.array(p2, float)
    n = np.array([off, 0.0]) if vertical else np.array([0.0, off])
    a, b = p1 + n, p2 + n
    ax.annotate(
        "",
        xy=b,
        xytext=a,
        zorder=8,
        arrowprops=dict(
            arrowstyle="<|-|>",
            color=MUTED,
            lw=cv.pen("hatch"),
            mutation_scale=6,
            shrinkA=0,
            shrinkB=0,
        ),
    )
    for q, p in ((a, p1), (b, p2)):
        ax.plot(
            [p[0], q[0]], [p[1], q[1]], color=MUTED, lw=cv.pen("hatch"), ls=(0, (2, 2)), zorder=7
        )
    m = (a + b) / 2
    ax.text(
        m[0],
        m[1],
        txt,
        ha="center",
        va="center",
        fontsize=size,
        color=INK,
        zorder=9,
        rotation=(90 if vertical else 0),
        bbox=dict(fc="white", ec="none", pad=1.2),
    )


# =============================================================== SK-01 PLAN
sheet = SK["SK-01"]
V = sheet.views[0]
SC = V.scale_denominator
lo = np.array([P[:, 0].min() - 0.55, P[:, 1].min() - 0.75])
hi = np.array([P[:, 0].max() + 0.55, P[:, 1].max() + 0.55])


def plan_body(canvas):
    global cv
    cv = canvas
    plan_w = (hi[0] - lo[0]) * 1000 / SC
    plan_h = (hi[1] - lo[1]) * 1000 / SC
    ax, aw, ah = canvas.view_axes(
        (8 + 274) / 2 - plan_w / 2,
        (86 + 264) / 2 - plan_h / 2,
        ((lo[0], lo[1]), (hi[0], hi[1])),
        SC,
    )
    P_ = lambda cat, cut=False: S.resolve_pen(cat, SC, cut=cut) * S.POINTS_PER_MM
    for g in np.arange(np.ceil(lo[0]), hi[0], 1.0):
        ax.axvline(g, color=FAINT, lw=P_("grid"), zorder=0)
    for g in np.arange(np.ceil(lo[1]), hi[1], 1.0):
        ax.axhline(g, color=FAINT, lw=P_("grid"), zorder=0)
    # the survey evidence is HALFTONE - present, legible, plainly background
    ax.scatter(band[:, 0], band[:, 1], s=0.4, c=[S.halftone(GREY, 0.55)], linewidths=0, zorder=1)
    # POCHE: a cut solid is filled, not two thin parallel lines
    for b in BODIES:
        ax.add_patch(Polygon(b.polygon, closed=True, fc="#2b2b2b", ec="none", zorder=3))
    # cut faces heavy, everything beyond the cut light
    for s in SEGS:
        cut = s["length_m"] >= 0.9
        cat = "partition" if id(s) in POCHED else ("wall" if cut else "furniture")
        ax.plot(
            [s["a"][0], s["b"][0]],
            [s["a"][1], s["b"][1]],
            color=INK,
            lw=S.resolve_pen(cat, SC, cut=cut) * S.POINTS_PER_MM,
            solid_capstyle="butt",
            zorder=4,
        )
    # three chains: overall, grid-to-grid, opening
    dim(ax, (W_W, W_S), (W_E, W_S), f"{(W_E - W_W) * 1000:.0f}", -0.95)
    dim(ax, (W_W, W_S), (R2_E, W_S), f"{(R2_E - W_W) * 1000:.0f}", -0.52)
    dim(ax, (R1_W, W_S), (R1_E, W_S), f"{(R1_E - R1_W) * 1000:.0f}", -0.52)
    dim(ax, (W_E, W_S), (W_E, W_N), f"{(W_N - W_S) * 1000:.0f}", 0.52, vertical=True)
    if DOOR:
        dim(
            ax,
            (R2_E, DOOR[0]),
            (R2_E, DOOR[1]),
            f"{(DOOR[1] - DOOR[0]) * 1000:.0f}",
            -0.62,
            vertical=True,
            size=6.8,
        )
        ax.annotate(
            "OPENING",
            xy=(R2_E - 0.05, (DOOR[0] + DOOR[1]) / 2),
            xytext=(-2.72, 1.55),
            fontsize=7.1,
            color=ACCENT,
            zorder=10,
            ha="center",
            bbox=dict(fc="white", ec="none", pad=1.0),
            arrowprops=dict(arrowstyle="->", color=ACCENT, lw=canvas.pen("hatch")),
        )
    for m in sheet.markers:
        canvas.section_mark(ax, m.tag, *(CUT_A if m.tag == "A" else CUT_B), m.target_sheet)
    # Room identification masks the geometry behind it, as a dimension figure
    # does - the reader needs the name, not the stipple under it.
    mask = dict(fc="white", ec="none", pad=1.4)
    for r, cx, cy in ((V.rooms[0], (R1_W + W_E) / 2, -0.55), (V.rooms[1], (W_W + R2_E) / 2, -0.55)):
        ax.text(
            cx, cy, r.name, ha="center", fontsize=9.9, weight="bold", color=INK, zorder=9, bbox=mask
        )
        ax.text(
            cx, cy - 0.30, r.number, ha="center", fontsize=7.1, color=MUTED, zorder=9, bbox=mask
        )
        ax.text(
            cx,
            cy - 0.56,
            f"{r.area_m2:.1f} m²",
            ha="center",
            fontsize=7.1,
            color=MUTED,
            zorder=9,
            bbox=mask,
        )
    ax.annotate(
        "CABINET RUN (owner)\nfour surfaces, 460 deep\nsee SK-03 / E4",
        xy=(R1_W - 0.06, -1.30),
        xytext=(0.30, -2.00),
        fontsize=6.6,
        color=ACCENT,
        zorder=10,
        ha="center",
        bbox=dict(fc="white", ec="none", pad=1.0),
        arrowprops=dict(arrowstyle="->", color=ACCENT, lw=canvas.pen("hatch")),
    )
    ax.text(
        -0.55,
        2.52,
        "LOBBY / OPENING",
        ha="center",
        fontsize=7.1,
        weight="bold",
        color=INK,
        zorder=9,
        bbox=dict(fc="white", ec="none", pad=1.0),
    )
    canvas.north_point(ax, hi[0] - 0.75, hi[1] - 0.95, 0.36, NORTH_BEARING_DEG, basis="PER OWNER")
    canvas.scale_bar(150, 14, SC)
    canvas.notes_panel(
        30,
        102,
        [
            "LEGEND   pens resolved from category and view scale (1:%d)" % SC,
            "  halftone  measured LiDAR returns in the 50 mm section band (25,432 pts)",
            "  poche     wall CUT by this view, filled only where both faces were measured",
            "            and nothing was returned between them (%d body)" % len(BODIES),
            "  heavy / light outline   cut by this view / seen beyond it",
            "  blue chain              section cut line with direction of view",
            "",
            f"  TAPE CHECK 2026-09-04    N-S  scan {(W_N - W_S) * 1000:.0f}  tape 3960  "
            f"{3960 - (W_N - W_S) * 1000:+.0f} mm",
            f"                           E-W  scan {(R1_E - R1_W) * 1000:.0f}  tape 2880  "
            f"{2880 - (R1_E - R1_W) * 1000:+.0f} mm",
            "  NO SCALE CORRECTION IS WARRANTED. Both axes read slightly SHORT but by",
            "  different amounts, so no single factor fits. The E-W is the worse of the two",
            "  because that side of Room 01 presents FOUR parallel surfaces over about",
            "  460 mm, each running the room's full length. The scan CANNOT tell which is",
            "  structure and which is a full-height fitting: to a scanner they look the",
            "  same. This dimension goes to the INNERMOST. CONFIRM THE FACE before ordering.",
            "  COMPASS fixed by the owner naming the cabinet wall SOUTH; the other three",
            "  follow. Not surveyed - no bearing was measured.",
            "",
            "  EXTERIOR WALL THICKNESS IS NOT SHOWN: the scan is interior-only.",
        ],
    )


cv1 = compose(sheet, plan_body)
from drafting.legibility import inspect

leg = inspect(cv1)
print(f"\nSK-01 legibility: {len(leg)} findings")
for f in leg.findings:
    print("   ", f.line())
cv1.save(OUT / "01-floor-plan.pdf", OUT / "01-floor-plan.png")
print("SK-01 re-issued at 1:%d" % SC)

# ============================================================ SK-02 SECTIONS
sheet2 = SK["SK-02"]
SC2 = sheet2.views[0].scale_denominator


def sec_body(canvas):
    global cv
    cv = canvas
    for k, (view, cut, caption) in enumerate(
        zip(
            sheet2.views,
            (CUT_A, CUT_B),
            ("looking north — through both rooms", "looking west — through Room 01"),
        )
    ):
        sec = slice2d.section_band(P, list(cut[0]), list(cut[1]), 0.12)
        L = float(np.hypot(cut[1][0] - cut[0][0], cut[1][1] - cut[0][1]))
        ax, aw, ah = canvas.view_axes(
            32,
            canvas.h - 58 - k * 104 - (3.85 * 1000 / SC2),
            ((-0.35, -0.40), (L + 0.35, 3.45)),
            SC2,
        )
        ax.scatter(sec[:, 0], sec[:, 1], s=0.55, c=GREY, alpha=0.75, linewidths=0, zorder=1)
        for lvl, lab in ((0.0, "FFL  ±0.000"), (2.604, "SOFFIT  +2.604")):
            ax.plot(
                [-0.25, L + 0.25], [lvl, lvl], color="#c0392b", lw=canvas.pen("beyond"), zorder=4
            )
            ax.text(L + 0.30, lvl, lab, fontsize=7.1, color="#c0392b", va="center", zorder=9)
        dim(ax, (L + 0.10, 0.0), (L + 0.10, 2.604), "2604", 0.0, vertical=True)
        tag = S.section_tag(view.name)
        ax.text(0, 3.38, f"SECTION {tag}–{tag}", fontsize=9.9, weight="bold", color=INK, va="top")
        ax.text(
            0, 3.10, f"{caption}   ·   cut line shown on SK-01", fontsize=7.1, color=MUTED, va="top"
        )
    canvas.scale_bar(150, 30, SC2)
    canvas.notes_panel(32, 44, [sheet2.level_datum, *textwrap.wrap(sheet2.provenance, 92)])


cv2 = compose(sheet2, sec_body)
leg2 = inspect(cv2)
print(f"SK-02 legibility: {len(leg2)} findings")
for f in leg2.findings:
    print("   ", f.line())
cv2.save(OUT / "02-sections.pdf", OUT / "02-sections.png")

# ================================================================= SK-03 3D
sheet5 = SK["SK-03"]
sheet5.number = "SK-05"
sheet5.title_block.fields["drawing_number"] = "SK-05"
sheet5.title_block.fields["drawing_title"] = "POINT-CLOUD VIEWS"
VIEWS = [
    ("v_cutaway.png", "CUTAWAY AXONOMETRIC", "ceiling removed above +2.35 m"),
    ("v_iso-ne.png", "AXONOMETRIC — from north-east", "full point cloud, true colour"),
    ("v_iso-nw.png", "AXONOMETRIC — from north-west", "full point cloud, true colour"),
    ("v_plan-oblique.png", "OBLIQUE — steep, from above", "reads the room layout"),
]


def d3_body(canvas):
    grid = [(24, 140, 172, 104), (214, 140, 172, 104), (24, 26, 172, 104), (214, 26, 172, 104)]
    for (fn, cap, sub), (x, y, w_, h_) in zip(VIEWS, grid):
        src = SCRATCH / fn
        if not src.is_file():
            continue
        im = Image.open(src)
        im.thumbnail((int(w_ * 8), int(h_ * 8)))
        a = canvas.fig.add_axes([x / canvas.w, y / canvas.h, w_ / canvas.w, h_ / canvas.h])
        a.imshow(np.asarray(im))
        a.axis("off")
        canvas.text(x, y + h_ + 6.0, cap, "subtitle", weight="bold")
        canvas.text(x, y + h_ + 1.6, sub, "note", color=MUTED)
    canvas.text(
        24,
        17,
        "NOT A MESH AND NOT A RECONSTRUCTION — these are the measured points, "
        "drawn with a depth buffer.",
        "note",
        weight="bold",
    )
    canvas.text(
        24,
        12,
        "Where the scan did not reach the drawing is empty, and that absence is information.",
        "note",
        color=MUTED,
    )


cv5 = compose(sheet5, d3_body)
leg5 = inspect(cv5)
print(f"SK-05 legibility: {len(leg5)} findings")
for f in leg5.findings:
    print("   ", f.line())
cv5.save(OUT / "05-point-cloud-views.pdf", OUT / "05-point-cloud-views.png", dpi=175)

# ------------------------------------------------------------- the record
final = critique(dset)
lines = [
    "# Drafting critique — Okongo as-scanned set",
    "",
    f"Run {__import__('datetime').date.today()}. Rules: {len(S.RULES)}, "
    f"basis SANS 10143 via TEE KB `arch.drawing_documentation` (confidence medium).",
    "",
    "## Tier 1 — standards conformance (checks the specification)",
    "",
    f"- findings on the set as issued: **{len(before)}**",
    f"- corrections applied automatically: **{len(res.changes)}**",
    f"- open after the loop: **{len(final.open)}** ({len(final.blocking)} blocking)",
    "",
    "```",
    res.summary(),
    "```",
    "",
    "## Tier 2 — legibility (checks the plotted sheet)",
    "",
    f"- SK-01 {len(leg)} · SK-02 {len(leg2)} · SK-05 {len(leg5)} findings after correction",
    "",
    "## What was changed",
    "",
]
seen = set()
for f in res.changes:
    key = (f.rule, f.where.split("/")[-1], f.detail)
    if key in seen:
        continue
    seen.add(key)
    lines.append(f"- `{f.rule}` {f.where} — {f.detail}")
lines += [
    "",
    "## What a human still has to do",
    "",
    "- **CHECKED BY is unset on every sheet.** The corrector prints an explicit "
    "placeholder rather than inventing initials; an unchecked drawing that looks "
    "checked is worse than one that visibly is not.",
    "- **The scale is still UNVERIFIED.** Two tape readings would close it.",
    "",
]
(OUT / "drafting-critique.md").write_text("\n".join(lines))
print("\ncritique report written")

# ==================================================== SK-03 INTERNAL ELEVATIONS
from matplotlib.patches import Polygon as MplPoly

from drafting import views3d as V
from drafting.spec import Line, Sheet, Text, TitleBlock, View

# Derived from the SAME faces the plan dimensions to. This had been a
# hard-coded box from an older fit, so the elevations quoted widths the plan
# did not - 2883 against the plan's 2854.
R1 = dict(w=R1_W, e=R1_E, s=W_S, n=W_N)
CEILING = float(np.percentile(P[:, 2], 99.8))
# COMPASS: fixed by the owner (2026-09-04) identifying E4 as the SOUTH wall,
# the one carrying the bedroom cabinets. One named wall fixes the other three,
# to within the building's own skew from true north. Nothing here is surveyed:
# the scan frame came from the dominant wall azimuth, which is not a bearing.
ELEVS = [
    ("E1", "WEST wall of Room 01", 1, R1["n"], R1["w"], R1["e"], -1.0),
    ("E2", "NORTH wall of Room 01", 0, R1["e"], R1["s"], R1["n"], -1.0),
    ("E3", "EAST wall of Room 01", 1, R1["s"], R1["w"], R1["e"], +1.0),
    ("E4", "SOUTH wall of Room 01 - CABINET RUN", 0, R1["w"], R1["s"], R1["n"], +1.0),
]
SC3 = 50


def _new_sheet(number, title, subtitle, views):
    src = SK["SK-01"]
    return Sheet(
        number=number,
        title=title,
        subtitle=subtitle,
        views=views,
        texts=[Text(t.role, t.height_mm) for t in src.texts],
        lines=[Line(ln.role, ln.width_mm) for ln in src.lines],
        title_block=TitleBlock(
            fields=dict(src.title_block.fields), notes=list(src.title_block.notes)
        ),
        level_datum=SK["SK-02"].level_datum,
        provenance=src.provenance,
    )


sheet3 = _new_sheet(
    "SK-03",
    "INTERNAL ELEVATIONS — as-scanned survey",
    "Room 01, each wall square-on   ·   DEPTH-SHADED: pale = at the wall, dark = "
    "proud of it, white = nothing returned   ·   blue = traced envelope (E4 only)",
    [
        View("ga_elevation", f"ELEVATION {tag}", SC3, levels=["FFL ±0.000", "SOFFIT +2.604"])
        for tag, _, _, _, _, _, _ in ELEVS
    ],
)
sheet3.title_block.fields["drawing_title"] = "INTERNAL ELEVATIONS"
sheet3.title_block.fields["drawing_number"] = "SK-03"
sheet3.title_block.fields["scale"] = f"1:{SC3} @ A3"


def elev_body(canvas):
    P_ = lambda cat, cut=False: S.resolve_pen(cat, SC3, cut=cut) * S.POINTS_PER_MM
    cols = 2
    for k, (tag, name, axis, pos, lo, hi, look) in enumerate(ELEVS):
        # Inset off the return walls: their faces sit exactly at lo/hi and
        # otherwise print as black bands down both edges of every elevation.
        pts = V.elevation(P, axis, pos, lo + 0.04, hi - 0.04, look, depth=0.60)
        width = float(pts[:, 0].max())
        img, extent = V.depth_raster(pts, z_hi=CEILING)
        # Tracing is opt-in and only on the wall the OWNER identified as
        # carrying joinery. On a bare wall a rectangle round every proud
        # patch would be inventing furniture out of clutter.
        traced = V.trace_outlines(img, extent) if "CABINET" in name else []
        cx, cy = 26 + (k % cols) * (width * 1000 / SC3 + 44), 168 - (k // cols) * 88
        ax, _, _ = canvas.view_axes(cx, cy, ((-0.25, -0.30), (width + 0.25, 3.55)), SC3)
        # Depth-shaded: at the wall is pale, proud toward the viewer is dark,
        # and a cell with no return stays white so an opening reads as a hole.
        # Flat stipple threw all three away and gave four identical grey boxes.
        ax.imshow(
            img,
            extent=extent,
            origin="lower",
            cmap="bone_r",
            vmin=0.0,
            vmax=0.35,
            interpolation="nearest",
            zorder=1,
        )
        for lvl in (0.0, 2.604):
            ax.plot(
                [-0.2, width + 0.2], [lvl, lvl], color="#c0392b", lw=P_("floor", cut=True), zorder=4
            )
        ax.plot([0, 0], [0, 2.604], color=INK, lw=P_("wall", cut=True), zorder=4)
        ax.plot([width, width], [0, 2.604], color=INK, lw=P_("wall", cut=True), zorder=4)
        ax.text(0, 3.50, f"ELEVATION {tag}", fontsize=8.5, weight="bold", color=INK, va="top")
        ax.text(0, 3.24, name, fontsize=7.1, color=MUTED, va="top")
        for o in traced:
            ax.add_patch(
                MplPoly(
                    [(o.x0, o.z0), (o.x1, o.z0), (o.x1, o.z1), (o.x0, o.z1)],
                    closed=True,
                    fc="none",
                    ec=ACCENT,
                    lw=S.resolve_pen("furniture", SC3, cut=True) * S.POINTS_PER_MM,
                    zorder=5,
                )
            )
            dim(ax, (o.x0, o.z1 + 0.16), (o.x1, o.z1 + 0.16), f"{o.width_mm:.0f}", 0.0, size=6.6)
            dim(
                ax,
                (o.x0 - 0.14, o.z0),
                (o.x0 - 0.14, o.z1),
                f"{o.height_mm:.0f}",
                0.0,
                vertical=True,
                size=6.6,
            )
            ax.text(
                (o.x0 + o.x1) / 2,
                o.z0 + 0.10,
                f"TRACED ENVELOPE\nproud {o.depth_m * 1000:.0f} mm\n{o.fill:.0%} of it returned",
                ha="center",
                va="bottom",
                fontsize=6.0,
                color=ACCENT,
                zorder=9,
                bbox=dict(fc="white", ec="none", pad=1.0),
            )
        ax.text(
            width, -0.16, f"{width * 1000:.0f}", fontsize=7.1, color=MUTED, ha="right", va="top"
        )
        dim(
            ax,
            (width + 0.14, 0.0),
            (width + 0.14, CEILING),
            f"{CEILING * 1000:.0f}",
            0.0,
            vertical=True,
            size=6.8,
        )
    canvas.scale_bar(300, 100, SC3)
    canvas.notes_panel(
        26,
        74,
        [
            "Each wall square-on. Every return within 600 mm is kept and shaded by",
            "its DEPTH from the wall, so a cabinet reads dark and an opening, which",
            "returns nothing, reads white. The shading is measurement, not reading.",
            "",
            "TRACING is opt-in and only on E4, the wall the OWNER named as carrying",
            "the cabinets. A rectangle round a proud region IS a reading of the depth",
            "map, so it is blue, called an ENVELOPE, and states how much of its own",
            "area returned - 23% here means the extent is measured, the face is not.",
            "Widths are inset 40 mm off each return wall, whose own face would",
            "otherwise print as a black band down both edges.",
            "",
            sheet3.level_datum,
            "",
            # 108 chars wraps this provenance to exactly two lines. A [:2]
            # slice would fit it too, and would silently drop the tail of a
            # statement about how the survey was measured.
            *textwrap.wrap(sheet3.provenance, 108),
        ],
    )


cv_e = compose(sheet3, elev_body)
leg_e = inspect(cv_e)
print(f"SK-03 legibility: {len(leg_e)} findings")
for f in leg_e.findings:
    print("   ", f.line())
cv_e.save(OUT / "03-internal-elevations.pdf", OUT / "03-internal-elevations.png")

# ================================================= SK-04 DRAWN AXONOMETRIC
SC4 = 50
QUADS = V.wall_quads(SEGS, P)
sheet4 = _new_sheet(
    "SK-04",
    "AXONOMETRIC — as-scanned survey",
    "Each fitted wall face extruded over the height ITS OWN returns cover   ·   "
    "a drawing, not a render: nothing here was smoothed, filled or assumed",
    [View("pictorial", "axonometric", 0)],
)
sheet4.title_block.fields["drawing_title"] = "AXONOMETRIC"
sheet4.title_block.fields["drawing_number"] = "SK-04"
sheet4.title_block.fields["scale"] = "NTS @ A3"


def axo_body(canvas):
    P_ = lambda cat, cut=False: S.resolve_pen(cat, SC4, cut=cut) * S.POINTS_PER_MM
    for k, (az, el, label) in enumerate(
        [(45, 28, "from the SOUTH-EAST"), (135, 28, "from the SOUTH-WEST")]
    ):
        M = V.iso_matrix(az, el)
        ordered = V.painter_order(QUADS, M)
        proj = [V.project(q["corners"], M) for q in ordered]
        allp = np.vstack(proj)
        pad = 0.30
        ax, _, _ = canvas.view_axes(
            24 + k * 176,
            108,
            (
                (allp[:, 0].min() - pad, allp[:, 1].min() - pad),
                (allp[:, 0].max() + pad, allp[:, 1].max() + pad),
            ),
            SC4,
        )
        # floor first, then the walls back to front - solids hide what is behind
        floor = np.array(
            [
                [P[:, 0].min(), P[:, 1].min(), 0],
                [P[:, 0].max(), P[:, 1].min(), 0],
                [P[:, 0].max(), P[:, 1].max(), 0],
                [P[:, 0].min(), P[:, 1].max(), 0],
            ]
        )
        ax.add_patch(
            MplPoly(
                V.project(floor, M),
                closed=True,
                fc="#f2f3f4",
                ec=S.halftone(INK, 0.55),
                lw=P_("floor"),
                zorder=1,
            )
        )
        for q, xy in zip(ordered, proj, strict=True):
            heavy = q["length_m"] >= 0.9
            ax.add_patch(
                MplPoly(xy, closed=True, fc="white", ec=INK, lw=P_("wall", cut=heavy), zorder=2)
            )
        ax.text(
            allp[:, 0].min(),
            allp[:, 1].max() + pad * 0.6,
            label,
            fontsize=7.1,
            color=MUTED,
            va="bottom",
        )
    canvas.notes_panel(
        24,
        92,
        [
            "HOW THIS IS BUILT",
            "  every fitted wall face is extruded from the base to the top that ITS OWN",
            "  returns cover, so a partial-height element draws partial-height rather",
            "  than being stretched to the ceiling. %d faces became %d solids."
            % (len(SEGS), len(QUADS)),
            "  Solids are drawn back to front, so what is nearer hides what is behind.",
            "",
            "  NO CEILING IS DRAWN and exterior wall thickness is not shown: the scan is",
            "  interior-only, so neither surface was ever measured.",
            "",
            *textwrap.wrap(sheet4.provenance, 92),
        ],
    )


cv4 = compose(sheet4, axo_body)
leg4 = inspect(cv4)
print(f"SK-04 legibility: {len(leg4)} findings")
for f in leg4.findings:
    print("   ", f.line())
cv4.save(OUT / "04-axonometric.pdf", OUT / "04-axonometric.png")
