"""`create sheet` and the `flat` kernel method: sheet metal on the wire (P5b).

Importing this module registers the verb and the method - nothing else does,
and nothing here imports OCP, so the document can lazily import it the first
time a batch says `create sheet` and pay only for `flat.py`'s arithmetic.

One op builds a whole sheet-metal part, because the press-brake model is
small enough to say in one object and a batch per flange would be four calls
where one does (hard rule 3):

    {"op": "create", "kind": "sheet", "name": "brk", "props": {
        "t": 2, "width": 50, "material": "steel_s275",
        "flanges": [{"len": 60}, {"len": 40, "angle": 90, "r": 2, "dir": "up"}],
        "holes": [{"flange": "f1", "at": [15, 25], "std": "M5 clearance normal"}],
        "k": 0.44, "relief": {"width": 3, "extra": 1}}}

`len` is the OUTSIDE length of a flange (apex to apex, or apex to free end) -
what a drawing dimensions and what a shop measures; the flat portion is what
is left after each bend's outside setback, and the flat length is the sum of
those plus one bend allowance per bend. W3 (t 2, width 50, flanges 60 and
40 at 90 deg r 2) lands at `ba_mm 4.524`, `bd_mm 3.476`, `flat_mm
[96.524, 50]`, `folded_bbox_mm [60, 50, 40]` and folded - flat = +18.850 mm3.

Defaults, all echoed in `assumed` the first time they are leaned on (Law 19,
"default and declare"): `k` 0.44 (see flat.py - THIS kernel's choice inside
the typical 0.3-0.5 range, not a standard), `r` = t (the shop rule of thumb
for mild steel; a production part passes r), `angle` 90 deg, `dir` up,
material none.

The `flat` method behind `pk_flat` writes the flat pattern a laser shop
reads: DXF with `$INSUNITS = 4` (mm) on the four layers OUTLINE / BEND_UP /
BEND_DOWN / HOLES, and the same drawing as SVG. Both are byte-identical on
repeat (Law 7).

A sheet does NOT join `Document.fingerprint()`. `fingerprint_sources` is
append-only and unconditional once appended, so registering it on the first
sheet would change the digest of a document whose only sheet was later rolled
back - and Law 16 says a failed batch leaves the fingerprint exactly as it
was. The sheet carries its own `Sheet.fingerprint()` in its entity row
instead, and the script remains the state.
"""

from __future__ import annotations

from typing import Any

from partkiln.client import LocalKernel, register_method
from partkiln.document import CommandError, Document, register_kind
from partkiln.sheetmetal.flat import DEFAULT_K, FORMULA_SOURCE, K_NOTE, K_TYPICAL, Flat
from partkiln.sheetmetal.fold import Sheet

_FLANGE_KEYS = ("len", "angle", "r", "dir")
_HOLE_KEYS = ("flange", "at", "dia", "std", "name")
_RELIEF_KEYS = ("width", "extra")


def _need(args: dict[str, Any], key: str, what: str) -> Any:
    if args.get(key) is None:
        raise CommandError(f"create sheet needs {key}: {what}.", code="pk_needs")
    return args[key]


def _unknown(given: dict[str, Any], known: tuple[str, ...], where: str) -> None:
    extra = sorted(k for k in given if k not in known)
    if extra:
        raise CommandError(
            f"{where}: unknown field(s) {', '.join(extra)}. Fields: {', '.join(known)}.",
            code="pk_bad_op",
        )


def _std_dia(spec: str, assumed: dict[str, Any], notes: list[str]) -> float:
    """`'M5 clearance normal'` | `'M5 clearance'` | `'M5 tap'` -> a diameter in mm.

    The same grammar `features.hole` uses, minus the halves a laser-cut sheet
    hole does not have (no seat, no cosmetic thread): one wording, so a model
    that learned it for a drilled hole does not have to learn it twice.
    """
    from partkiln import standards

    words = str(spec).split()
    if len(words) < 2:
        raise CommandError(
            f"std {spec!r} is not a hole standard. Forms: 'M5 clearance normal|close|loose' "
            "(ISO 273) or 'M5 tap' (the tap drill).",
            code="pk_needs",
        )
    size, what = words[0], words[1].lower()
    if what == "clearance":
        series = words[2].lower() if len(words) > 2 else "normal"
        if len(words) <= 2:
            assumed["series"] = "normal"
        row = standards.clearance_hole(size, series)
        notes.append(
            f"{row['size']} clearance {series}: {row['dia_mm']:g} mm per {row['authority']} "
            f"({row['licence']})"
        )
        return float(row["dia_mm"])
    if what == "tap":
        row = standards.tap_drill(size)
        notes.append(f"{row['size']} tap drill {row['drill_mm']:g} mm ({row['licence']})")
        return float(row["drill_mm"])
    raise CommandError(
        f"std {spec!r}: the second word is 'clearance' or 'tap', not {words[1]!r}.",
        code="pk_needs",
    )


# --------------------------------------------------------------------------- create sheet


@register_kind("sheet")
def _k_sheet(doc: Document, args: dict[str, Any], assumed: dict[str, Any]) -> dict[str, Any]:
    """Build a flat pattern from a flange chain and hand back its scalars."""
    name = doc.new_name(args, "sheet", doc.sheets)
    notes: list[str] = []
    t = doc.length(_need(args, "t", "the sheet thickness"), assumed)
    width = doc.length(_need(args, "width", "the width across the bends"), assumed)

    raw = _need(args, "flanges", "a list of {len, angle, r, dir}, the base first")
    if not isinstance(raw, list | tuple) or not raw:
        raise CommandError(
            "flanges is a non-empty list like [{len: 60}, {len: 40, angle: 90, r: 2, dir: 'up'}]; "
            "the first entry is the base and takes only len.",
            code="pk_needs",
        )
    k = args.get("k")
    if k is None:
        k = DEFAULT_K
        doc.assume_once(assumed, "k", DEFAULT_K)
        notes.append(K_NOTE)
    k = float(k)
    if not K_TYPICAL[0] <= k <= K_TYPICAL[1]:
        # A note, not a refusal: 0 < k < 1 is arithmetically fine and a shop
        # that measured an odd one is right and we are not. It still gets
        # said out loud, because it is far more often a typo.
        notes.append(
            f"k = {k:g} is outside the typical {K_TYPICAL[0]}-{K_TYPICAL[1]} range - accepted, "
            "but check it against the bend table it came from"
        )

    flanges: list[dict[str, Any]] = []
    for index, entry in enumerate(raw):
        if not isinstance(entry, dict):
            raise CommandError(
                f"flange {index + 1} is {entry!r}; each flange is an object like "
                "{len: 40, angle: 90, r: 2, dir: 'up'}.",
                code="pk_needs",
            )
        _unknown(entry, _FLANGE_KEYS, f"flange f{index + 1}")
        spec: dict[str, Any] = {
            "len": doc.length(
                _need(entry, "len", f"the outside length of flange f{index + 1}"), assumed
            )
        }
        if index == 0:
            extra = sorted(key for key in ("angle", "r", "dir") if key in entry)
            if extra:
                raise CommandError(
                    f"flange f1 is the base: it has no bend, so {', '.join(extra)} belong(s) on "
                    "the flange that folds off it (the next entry).",
                    code="pk_spec_conflict",
                )
        else:
            angle = entry.get("angle")
            if angle is None:
                doc.assume_once(assumed, "bend_angle", "90deg")
                angle = 90.0
            spec["angle"] = doc.angle(angle, assumed)
            radius = entry.get("r")
            if radius is None:
                doc.assume_once(assumed, "bend_r", "r = t")
                radius = t
            spec["r"] = doc.length(radius, assumed)
            direction = entry.get("dir")
            if direction is None:
                doc.assume_once(assumed, "bend_dir", "up")
                direction = "up"
            if direction not in ("up", "down"):
                raise CommandError(
                    f"flange f{index + 1}: dir is 'up' or 'down', not {direction!r}.",
                    code="pk_needs",
                )
            spec["dir"] = direction
        flanges.append(spec)

    relief = args.get("relief")
    if relief is not None:
        if not isinstance(relief, dict):
            raise CommandError(
                "relief is an object {width: <len>, extra: <len>}: the notch cut at each end of "
                "every bend zone so the bend does not tear the flange beside it.",
                code="pk_needs",
            )
        _unknown(relief, _RELIEF_KEYS, "relief")
        relief = {
            "width": doc.length(_need(relief, "width", "how far the notch reaches in"), assumed),
            "extra": doc.length(relief.get("extra", 0.0), assumed),
        }

    material = args.get("material")
    if material is None:
        assumed["material"] = None
    else:
        from partkiln import materials

        material = materials.resolve(str(material))

    flat = Flat.from_flanges(t, width, flanges, k, relief)
    for index, entry in enumerate(args.get("holes") or ()):
        _add_hole(doc, flat, index, entry, assumed, notes)

    sheet = Sheet(name, flat, material, k, notes)
    doc.sheets[name] = sheet
    notes.append(flat.volume_note())
    notes.append(FORMULA_SOURCE)
    return {**sheet.summary(), "notes": notes}


def _add_hole(
    doc: Document,
    flat: Flat,
    index: int,
    entry: Any,
    assumed: dict[str, Any],
    notes: list[str],
) -> None:
    if not isinstance(entry, dict):
        raise CommandError(
            f"hole {index + 1} is {entry!r}; each hole is an object like "
            "{flange: 'f1', at: [15, 25], dia: 5.5} or {..., std: 'M5 clearance normal'}.",
            code="pk_needs",
        )
    _unknown(entry, _HOLE_KEYS, f"hole {index + 1}")
    source = ""
    if entry.get("std") is not None:
        if entry.get("dia") is not None:
            raise CommandError(
                f"hole {index + 1}: give dia OR std, not both.", code="pk_spec_conflict"
            )
        before = len(notes)
        dia = _std_dia(str(entry["std"]), assumed, notes)
        source = notes[before] if len(notes) > before else str(entry["std"])
    elif entry.get("dia") is not None:
        dia = doc.length(entry["dia"], assumed)
    else:
        raise CommandError(
            f"hole {index + 1} needs dia: <len> or std: 'M5 clearance normal' | 'M5 tap'.",
            code="pk_needs",
        )
    at = entry.get("at")
    if not isinstance(at, list | tuple) or len(at) != 2:
        raise CommandError(
            f"hole {index + 1}: at is [x, y] - x along the flange from where its flat portion "
            "begins, y across the width - or, with no flange, [x, y] on the flat itself.",
            code="pk_needs",
        )
    flat.add_hole(
        dia,
        (doc.length(at[0], assumed), doc.length(at[1], assumed)),
        entry.get("flange"),
        entry.get("name"),
        source,
    )


# --------------------------------------------------------------------------- the flat method


def _sheet_of(doc: Document, params: dict[str, Any]) -> Sheet:
    ref = params.get("sheet") or params.get("of") or params.get("name")
    known = ", ".join(f"sheet:{n}" for n in sorted(doc.sheets)) or "(none)"
    if ref is None:
        if len(doc.sheets) == 1:
            return next(iter(doc.sheets.values()))
        raise CommandError(
            f"flat needs sheet: which sheet to flatten. Sheets: {known}.",
            code="pk_needs" if doc.sheets else "pk_ref_empty",
        )
    key = str(ref)[6:] if str(ref).startswith("sheet:") else str(ref)
    sheet = doc.sheets.get(key)
    if sheet is None:
        raise CommandError(f"no sheet {ref!r}. Sheets: {known}.", code="pk_ref_unknown")
    return sheet


@register_method("flat")
def _m_flat(kernel: LocalKernel, params: dict[str, Any]) -> dict[str, Any]:
    """`pk_flat`'s backend: the flat pattern as DXF and SVG, plus its numbers.

    `out` is a path; its suffix is ignored and one file per requested format
    is written beside it, so `out: "out/brk"` gives `out/brk.dxf` and
    `out/brk.svg`. Neither file needs the B-rep kernel: a flat pattern is 2D
    by definition, which is why the shop can have it while OCP is still
    warming (Law 17).
    """
    sheet = _sheet_of(kernel.document, params)
    out = params.get("out")
    if not out:
        raise CommandError(
            "flat needs out: where to write the flat pattern (the suffix is added per "
            "format, e.g. out/brk -> out/brk.dxf, out/brk.svg).",
            code="pk_needs",
        )
    from pathlib import Path

    # `formats` is this method's own word; `format` (singular) is what
    # `methods.m_export` passes when it routes `export format=dxf of=<sheet>`
    # here, so the two lanes write the same file from the same code.
    formats = params.get("formats") or params.get("format") or ("dxf", "svg")
    if isinstance(formats, str):
        formats = (formats,)
    writers = {"dxf": sheet.flat.write_dxf, "svg": sheet.flat.write_svg}
    unknown = sorted({str(f).lower() for f in formats} - set(writers))
    if unknown:
        raise CommandError(
            f"flat writes dxf and svg, not {', '.join(unknown)}. For a solid use export "
            "(step/stl/glb) on the sheet's folded body.",
            code="pk_bad_op",
        )
    stem = Path(str(out)).with_suffix("")
    files: dict[str, Any] = {}
    for fmt in dict.fromkeys(str(f).lower() for f in formats):
        files[fmt] = writers[fmt](stem.with_suffix(f".{fmt}"))
    out_row: dict[str, Any] = {
        **sheet.summary(),
        "files": files,
        "layers": list(files.get("dxf", files[next(iter(files))]).get("layers", ())),
        "units": "mm",
        "notes": [sheet.flat.volume_note(), FORMULA_SOURCE, *sheet.notes],
    }
    if len(files) == 1:
        # One file asked for, one file reported the way an export reports it:
        # `m_export` hands this straight back to the caller.
        only = next(iter(files.values()))
        out_row.update({"path": only["path"], "bytes": only["bytes"], "format": only["format"]})
    return out_row


__all__ = ["_k_sheet", "_m_flat"]
