---
id: gxgd.gd_fundamentals
title: Graphic design fundamentals — grid, type, colour, composition, production, accessibility
domain: 28_graphic_and_game_design
tags: [graphic-design, grid-systems, typography, type-anatomy, colour-theory, cmyk, spot-colour, gestalt, hierarchy, white-space, prepress, paper-stock, wcag, contrast, brand-identity, guidelines]
jurisdiction: global
status: stable
confidence: high
updated: 2026-08-25
applies_to: "WCAG 2.2 as published. Print specifications are general trade practice — confirm tolerances with the specific printer."
unit_system: metric
sources:
  - {title: "Understanding SC 1.4.3 Contrast (Minimum)", url: "https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html", publisher: "W3C Web Accessibility Initiative", accessed: 2026-08-25}
  - {title: "International Typographic Style", url: "https://en.wikipedia.org/wiki/International_Typographic_Style", publisher: "Wikipedia", accessed: 2026-08-25}
  - {title: "Massimo Vignelli", url: "https://en.wikipedia.org/wiki/Massimo_Vignelli", publisher: "Wikipedia", accessed: 2026-08-25}
  - {title: "Otl Aicher", url: "https://en.wikipedia.org/wiki/Otl_Aicher", publisher: "Wikipedia", accessed: 2026-08-25}
  - {title: "Design tokens — Material Design 3", url: "https://m3.material.io/foundations/design-tokens/overview", publisher: "Google", accessed: 2026-08-25}
related: [gxgd.overview, gxgd.gd_education, gxgd.gd_canon, gxgd.uiux, gxgd.resources]
---

# Graphic design fundamentals — grid, type, colour, composition, production, accessibility

**Summary.** This is the checkable craft. Everything here can be verified against a rule, a ratio or a specification rather than taste: how a grid is constructed and why, the anatomy and classification of type and the numeric rules for setting it, how colour behaves in additive and subtractive systems, what gestalt principles predict about grouping, what a printer needs to produce the file correctly, and what WCAG requires numerically. It closes with the structure of a brand identity system and the guidelines document that carries it. Aesthetic judgement is downstream of all of this; without it, "taste" is guessing.

## Key facts

| Item | Value |
|---|---|
| WCAG 2.2 AA text contrast | **4.5:1** normal text; **3:1** large text |
| WCAG 2.2 AAA text contrast | **7:1** normal text; **4.5:1** large text |
| WCAG definition of large text | **≥18 pt**, or **≥14 pt bold** (≈24 px and ≈18.5 px respectively) |
| WCAG 2.2 non-text contrast (SC 1.4.11) | **3:1** for UI components and meaningful graphics |
| Contrast exceptions | Logotypes; incidental, decorative, invisible or inactive-component text |
| Comfortable measure (line length) | **45–75 characters**, ~66 optimal, single column |
| Default leading heuristic | **120–145%** of type size for body text; tighter as size increases |
| Standard bleed | **3 mm** (Europe/metric) or **0.125 in** (US) |
| Standard safety/quiet margin from trim | **≥3 mm**, commonly 5 mm |
| Print resolution for continuous-tone images | **300 ppi at final size** (150 lpi × 2) |
| Line-art / bitmap resolution | **1200 ppi** |
| Rich black (CMYK) | typically **60/40/40/100** — confirm with printer's total ink limit |
| Total area coverage (TAC) limit, coated sheet | commonly **300–320%**; uncoated/newsprint lower (240–260%) |
| Paper weight ranges | Text stock ~80–150 gsm; cover ~200–350 gsm |

> ⚠️ Contrast ratio is computed from *relative luminance*, not from perceptual lightness. Two colours with the same apparent "brightness" can fail. Always compute the ratio; never eyeball it. WCAG 2.2 SC 1.4.3 exempts logotypes and incidental text — that exemption is narrow and is not a licence to ship low-contrast body copy.

---

## 1. The grid and layout systems

### Why a grid

A grid is not a decorative device; it is a decision-cache. It pre-answers "where does this go?" so attention can go to what things *mean*. Its second function is consistency across a set — pages of a book, screens of a product, items in a campaign — so a reader learns the system once and then navigates without re-learning.

The canonical treatment is Josef Müller-Brockmann's *Grid Systems in Graphic Design* (1981), which formalised what the Swiss school had been doing since the 1950s: an objective, mathematically derived structure that removes the designer's arbitrary preference from placement decisions.

### Constructing a grid

**Margins first.** Choose margins before columns. Classical book proportions (Van de Graaf canon, Tschichold's golden canon) set a text block whose margins run roughly inner : top : outer : bottom in a 2:3:4:6 relationship — a small inner margin because facing pages share it, a large bottom margin because the hand holds the book there. Screens invert this: consistent gutters, larger top for status/nav.

**Columns.** The column count is chosen so the resulting measure is readable at your body size, and so subdivisions give useful widths. Even counts (2, 4, 6, 8, 12) subdivide well; odd counts (3, 5, 7) produce asymmetry and a natural focal offset. 12 is the web default precisely because it divides by 2, 3, 4 and 6.

**Gutters.** Wide enough that adjacent columns do not read as one block. A working rule: gutter ≥ one em of the body size, often 1.5×.

**Modular grid.** Müller-Brockmann's contribution: divide the column grid horizontally as well, producing a field of modules. Images and blocks then snap to module boundaries, which yields the characteristic Swiss look of aligned but irregular blocks. The horizontal divisions are derived from the baseline grid so text and images share alignments.

**Baseline grid.** Set the leading of the body text as the atomic vertical unit, and force every element's vertical position and every other type size's leading to be a whole multiple of it. Consequences: text in adjacent columns aligns line-for-line; captions, headings and images sit on shared horizons; facing pages register. In InDesign this is a document-level setting with "align to baseline grid" on paragraph styles. On the web it is achieved by making line-heights and vertical spacing multiples of a base unit (commonly 4 px or 8 px).

**Modular scale.** Type sizes and spacing derived from a repeated ratio rather than picked ad hoc. Common ratios: 1.125 (major second), 1.2 (minor third), 1.25 (major third), 1.333 (perfect fourth), 1.5 (perfect fifth), 1.618 (golden). Starting from a 16 px base at 1.25: 16 → 20 → 25 → 31.25 → 39 → 48.8. The scale's job is to make size differences *unambiguous* — two sizes that differ by 1 px read as an error, not a hierarchy.

**Breaking the grid.** A grid earns its keep by being broken *once*, deliberately, on the element that must dominate. An unbroken grid is inert; a grid broken everywhere is not a grid.

### Layout systems beyond the grid

- **Compositional axes** — asymmetric layout organised on one or two strong alignment lines rather than a column field (Tschichold's *Die neue Typographie*, 1928).
- **Swiss/International system** — flush-left ragged-right, sans-serif, objective photography, mathematically derived field. See `03`.
- **8-point / 4-point spacing systems** — the digital-product descendant: all spacing, sizing and radii are multiples of 4 or 8. Makes handoff to engineering unambiguous. See `04`.
- **Fluid/responsive grids** — column count changes at breakpoints; the *content* measure, not the device, sets the breakpoints.

---

## 2. Typography in depth

### Anatomy

Learn these because they are how type is discussed and specified, not as trivia:

**Vertical metrics:** baseline, x-height, cap height, ascender, descender, overshoot (round letters extend slightly past the baseline and cap line so they *appear* the same height). **Parts:** stem, bar, crossbar, bowl, counter (enclosed white), aperture (the opening of a counter, e.g. in *c*, *s*, *e*), shoulder, spine (the S), leg, tail, ear (the g), spur, terminal, finial, serif (bracketed, slab, hairline, wedge), stress/axis (the angle through the thin points of a round letter), contrast (thick-to-thin ratio), ink trap.

**Spacing:** sidebearings (space built into each glyph), kerning (pair-specific adjustments stored in the font), tracking/letterspacing (uniform adjustment applied by the designer), word space.

### Classification

The Vox-ATypI system is the academic scheme; in practice designers use a working shorthand:

| Class | Characteristics | Examples |
|---|---|---|
| Humanist / Old Style | Angled stress, small x-height, low contrast, bracketed serifs, angled *e* bar | Garamond, Bembo, Jenson, Sabon |
| Transitional | More vertical stress, higher contrast, sharper serifs | Baskerville, Times New Roman, Caslon (between) |
| Didone / Modern | Vertical stress, extreme contrast, hairline unbracketed serifs | Bodoni, Didot, Walbaum |
| Slab / Egyptian | Heavy rectangular serifs, low contrast | Clarendon, Rockwell, Archer |
| Grotesque | Early sans, slight contrast, closed apertures, tight curves | Akzidenz-Grotesk, Helvetica |
| Neo-grotesque | Refined grotesque, uniform, neutral | Helvetica, Univers, Neue Haas Grotesk |
| Humanist sans | Calligraphic skeleton, open apertures, true italic | Gill Sans, Frutiger, Myriad, Open Sans |
| Geometric sans | Circular *o*, single-storey *a*, constructed | Futura, Avenir, Circular, Poppins |
| Display | Optimised for large sizes only | almost anything at 8 pt is wrong |
| Monospace | Fixed advance width | Courier, JetBrains Mono, SF Mono |

### The great typefaces and their designers

| Typeface | Designer | Year | Note |
|---|---|---|---|
| Garamond | Claude Garamond (16th c.); modern revivals by Jannon, Slimbach (Adobe Garamond, 1989) | c. 1530 | The reference old-style text face |
| Caslon | William Caslon | c. 1725 | "When in doubt, use Caslon" |
| Baskerville | John Baskerville | c. 1757 | Transitional; the bridge to Didone |
| Bodoni | Giambattista Bodoni | c. 1790 | Didone; brutal at small sizes, magnificent large |
| Akzidenz-Grotesk | Berthold foundry | 1896 | The ancestor of Helvetica; the Swiss school's actual working face |
| Futura | Paul Renner | 1927 | Geometric sans; Bauhaus-adjacent |
| Gill Sans | Eric Gill | 1928 | Humanist sans; the British counter-proposal |
| Times New Roman | Stanley Morison & Victor Lardent | 1932 | Newspaper economy face |
| Helvetica | Max Miedinger & Eduard Hoffmann | **1956** | Named for *Helvetia*, Latin for Switzerland |
| Univers | Adrian Frutiger | 1950s (released 1957) | First systematically numbered weight/width family |
| Frutiger | Adrian Frutiger | 1976 | Designed for Charles de Gaulle airport signage; the humanist-sans template |
| Rotis | Otl Aicher | **1988** | Named after his home near Leutkirch im Allgäu |
| Interstate / FF Meta / Interstate | Tobias Frere-Jones / Erik Spiekermann | 1990s | The digital-era workhorses |

Vignelli's argument — that a designer needs perhaps a dozen typefaces and that the rest is "visual pollution" — is worth taking seriously as a discipline even if not as dogma. His own list: Helvetica, Bodoni, Akzidenz-Grotesk, Garamond No. 3, Futura, Times New Roman, Century Expanded.

### Pairing

Rules that actually hold:

1. **Contrast in class, harmony in proportion.** Pair across categories (humanist sans + old-style serif), but match x-height and apparent weight so they sit together at the same optical size.
2. **Two families is usually enough**; three needs justification. A single superfamily with serif and sans cuts (e.g. Freight, Fira, Source, Noto) solves this by construction.
3. **Historical adjacency helps** — faces from the same period share a skeleton.
4. **Do not pair two faces from the same class.** Two geometric sans in one layout reads as a mistake, not a decision.
5. **Give each face a job** — display/heading vs text vs data/UI — and never let them cross.

### Setting text: the numbers

- **Measure:** 45–75 characters per line for single-column continuous text, ~66 optimal. Multi-column can go to 40–50. Wider than 75 and the eye loses the line return.
- **Leading:** 120–145% of type size for body copy. Longer measure → more leading. Larger size → proportionally less (a 48 pt headline may want 95–105%). Negative leading is a display device only.
- **Tracking:** body text at 0; all-caps and small-caps need **+50 to +120 units** (thousandths of an em) because uppercase sidebearings assume mixed-case rhythm; large display sizes usually need slight *negative* tracking because sidebearings are optimised for text sizes.
- **Word spacing / justification:** justified text needs hyphenation on and tuned min/optimal/max word spacing (InDesign default 80/100/133% is a starting point, not an answer). Without hyphenation, justified text produces rivers. Ragged-right is safer and is the Swiss default.
- **Paragraph indication:** first-line indent **or** space-between, never both. Indent ≈ one em, or the leading value.
- **Widows and orphans:** a single word ending a paragraph at the top of a column (widow) and a single line at the bottom (orphan) are both errors. Fix by editing text, adjusting tracking within ±5 units across the paragraph, or changing the measure — in that order.
- **Hierarchy:** achieved by *one variable at a time where possible* — size, weight, case, colour, position, space. Amateur hierarchy changes four at once. The strongest and cheapest hierarchy device is **space**, not size.

### Optical adjustments

Type is a perceptual medium; mathematically correct is often visually wrong.

- **Overshoot:** round and pointed glyphs are drawn slightly taller/deeper than flat ones so they appear equal.
- **Optical alignment / hanging punctuation:** quotation marks, hyphens and some capitals must hang outside the text block to make the edge look straight. InDesign's Optical Margin Alignment; CSS `hanging-punctuation`.
- **Optical sizing:** text cut vs display cut of the same family differ in contrast, spacing and x-height. Variable fonts expose this as an `opsz` axis — use it.
- **Optical centring:** a block centred by measurement looks low; raise it by 2–5% of the container height.
- **Weight compensation:** light weights need slightly more tracking; heavy weights slightly less.

---

## 3. Colour theory and colour systems

### The two systems

**Additive (RGB, screen).** Light. Red + green + blue = white. Gamut is device- and colour-space-dependent: sRGB (the safe web default), Display P3 (wider, now standard on Apple hardware), Rec. 2020 (video/HDR), Adobe RGB (photography). Always specify which space.

**Subtractive (CMYK, print).** Ink absorbing light. Cyan + magenta + yellow theoretically black, practically muddy brown — hence the K plate. CMYK gamut is *smaller* than sRGB in saturated blues, greens and oranges. Saturated RGB colours will shift on conversion; this is not a bug and cannot be fixed by "better printing".

**Spot colour (Pantone/PMS, HKS, Toyo).** A pre-mixed ink applied on its own plate. Use when: the colour is outside CMYK gamut, exact consistency across substrates matters (brand colours), you need metallic/fluorescent, or you are printing 1–2 colours and spot is cheaper than 4-colour process. Specify the *finish variant* — Pantone C (coated), U (uncoated) and M (matte) of the same number look materially different. Note that Pantone's licensing changed and its libraries are no longer bundled free in Adobe apps; access is via a paid Pantone Connect subscription.

### Working models

- **HSB/HSL** for adjusting: hue, saturation, brightness/lightness are the axes designers actually think in.
- **LAB** for device-independent description and for perceptually even interpolation.
- **OKLCH** — the modern perceptual model, now supported in CSS. Superior for generating tonal ramps and for accessible palettes, because equal lightness steps *look* equal. Prefer it for design-token colour ramps.

### Building a palette

1. **One primary** carrying brand recognition. Specify it in every system it will appear in: Pantone (C and U), CMYK, RGB/HEX, and — for anything physical — RAL or NCS for paint and vinyl.
2. **A neutral ramp** of 8–12 steps from near-white to near-black, generated in OKLCH at even lightness intervals. This does 80% of the work in any interface.
3. **Two to four secondaries**, each with a defined role, not just "another brand colour".
4. **Semantic colours** for digital: success, warning, error, info — each with a foreground pair that passes contrast on its background.
5. **Contrast-tested pairs**: publish the *permitted combinations*, not just the swatches. Most brand-guideline failures are that the palette is legal and the combinations are not.

### Colour and meaning

Colour association is cultural and unstable; treat any universal claim sceptically. Two things *are* reliable: **warm advances, cool recedes** (a depth cue, not a preference), and **simultaneous contrast** — a colour's appearance shifts with its surround (Albers' central demonstration in *Interaction of Color*). Never judge a colour in isolation from its context. Roughly 8% of men of northern-European descent have some form of red–green colour vision deficiency, which is why colour must never be the *sole* carrier of meaning (WCAG SC 1.4.1).

---

## 4. Composition, gestalt and hierarchy

### Gestalt principles

These are perceptual predictions, not stylistic preferences — they describe what the visual system *will* do:

- **Proximity** — elements near each other are read as a group. The single most powerful and most under-used layout tool.
- **Similarity** — elements sharing shape, colour, size or orientation are grouped even when separated.
- **Common region** — elements inside a shared boundary (a box, a tint panel) group, and this *overrides* proximity.
- **Continuity** — the eye follows the smoothest path; aligned elements read as a line.
- **Closure** — the eye completes implied shapes (the FedEx arrow; the WWF panda).
- **Figure/ground** — the surface reads as either object or background; ambiguity is a tool (Rubin's vase) or a failure.
- **Common fate** — elements moving together group. Relevant to motion and UI transitions.
- **Prägnanz** — the visual system resolves toward the simplest available interpretation.

### Visual hierarchy

Hierarchy is the answer to "what do I look at first, second, third?" and it must be *decided*, not emergent. The ordering devices, roughly in power order: **position** (top-left in LTR reading cultures; centre of an isolated field), **size**, **weight**, **contrast against surround**, **colour**, **isolation/white space**, **direction/motion**.

Three tests: squint at the layout — the order that survives blur is the real hierarchy. Convert to greyscale — hierarchy carried only by hue is fragile. Show it for two seconds and ask what the viewer remembers.

### White space

Space is not leftover. It performs three jobs: **grouping** (proximity), **emphasis** (isolation makes an element dominant with no other change), and **pacing** (the rhythm at which a reader moves through a sequence). *Micro* white space (letter, word, line spacing) determines readability; *macro* white space (margins, gutters, block separation) determines perceived quality. Generous margins are the cheapest way to make a layout look considered — and the first thing removed by clients who mistake density for value.

### Image treatment

Consistency of treatment matters more than the quality of any single image. Define: crop discipline (a fixed set of aspect ratios), colour grade (a stated look — warmth, contrast, saturation range), subject distance conventions, whether images bleed or sit within the grid, cut-out vs full-frame policy, and a rule for duotone/tint treatments. Silhouettes and cut-outs must share a consistent edge treatment and drop-shadow policy or they will read as assembled from different sources — because they were.

---

## 5. Print production

### Prepress checklist

1. **Bleed** — 3 mm (metric) or 0.125 in (US) beyond trim on every edge where colour or image runs off. Anything less and the trim tolerance shows as white slivers.
2. **Safety margin** — keep essential content ≥3 mm (commonly 5 mm) inside trim.
3. **Trim and fold marks** — offset from trim, not overlapping bleed.
4. **Resolution** — 300 ppi at *final placed size* for continuous tone; 1200 ppi for line art. A 300 ppi image scaled to 200% is a 150 ppi image.
5. **Colour mode** — convert to the printer's specified CMYK profile (e.g. FOGRA51/PSO Coated v3 in Europe, GRACoL 2013 in the US), not to a generic "US Web Coated" default.
6. **Total area coverage** — check maximum ink; typically ≤300–320% on coated sheet, lower on uncoated and newsprint. Exceeding it causes set-off and drying failure.
7. **Rich black** for large solid areas (commonly 60/40/40/100) but **100% K only** for small text — registration error on a four-colour black shows instantly at text size.
8. **Overprint** — black text should overprint, not knock out; check overprint preview before export.
9. **Fonts** — embed or outline. Outlining destroys editability and disables hinting; embed unless the printer demands otherwise.
10. **Spot colours** — named exactly, no duplicate swatches with variant names, and any intended-as-process colours converted.
11. **Export** — PDF/X-4 is the current general-purpose print exchange standard (supports live transparency and ICC); PDF/X-1a where the printer demands flattened CMYK.
12. **Preflight** — run it. Acrobat Pro or the printer's own preflight profile.

### Paper

**Weight** is gsm (grams per square metre) in metric markets, "text"/"cover" basis weights in the US. Text stocks ~80–150 gsm; covers ~200–350 gsm. **Caliper** (thickness) matters independently of weight — bulky uncoated stocks feel heavier than their gsm suggests.

**Surface:** *Coated* (gloss, silk/satin, matt) holds ink on the surface — sharper images, higher contrast, more accurate colour. *Uncoated* absorbs ink — softer, warmer, colours print lighter and dot gain is higher, so images need compensating. *Textured* and *speciality* (laid, felt-marked, cotton) for identity work.

**Grain direction** runs with the fibres; fold *with* the grain or the fold cracks. For books, grain must run parallel to the spine or the book will not open flat.

**Opacity** matters for double-sided printing — show-through is the most common cheap-paper failure.

### Finishing

Foil stamping (hot foil, metallic or pigment), embossing and debossing, spot UV varnish (gloss on matt is the classic contrast), soft-touch lamination, die-cutting, edge painting, letterpress (deep impression on cotton stock), thermography. Binding: saddle-stitch (≤64 pp, cheapest), perfect binding (glued spine, ≥~40 pp), PUR binding (stronger glue, opens flatter), Smyth/section sewn (best, opens flat, expensive), Wire-O and spiral (opens fully flat), Swiss/exposed-spine binding, Japanese stab binding.

Each finishing process needs its own artwork layer, supplied as a **100% spot colour named for the process** (e.g. a spot swatch called "Foil" or "SpotUV") set to overprint, on top of the artwork.

---

## 6. Digital output

Screen work replaces paper constraints with different ones:

- **Colour space** — author in sRGB unless you have a specific P3 pipeline. Tag images. Untagged images are assumed sRGB by most browsers and will shift on wide-gamut displays.
- **Density** — supply raster assets at 2× and 3× or, better, use SVG for anything vector.
- **Format** — SVG for logos, icons and diagrams; WebP or AVIF for photographs; PNG only where lossless raster with alpha is genuinely needed; never JPEG for text-bearing graphics.
- **Type rendering** — hinting, subpixel rendering and font smoothing differ across OS and browser. Test the actual face at the actual size on Windows, not only on macOS, where rendering is more forgiving.
- **Font loading** — subset, self-host or use a font service, and set `font-display: swap` with a metric-matched fallback to avoid layout shift.
- **Dark mode** — do not simply invert. Reduce saturation of brand colours, reduce pure-white text to ~87% opacity or a light grey, and re-test every contrast pair.

---

## 7. Accessibility and contrast

The numbers, from WCAG 2.2:

| Criterion | Level | Requirement |
|---|---|---|
| 1.4.3 Contrast (Minimum) | AA | **4.5:1** normal text, **3:1** large text |
| 1.4.6 Contrast (Enhanced) | AAA | **7:1** normal text, **4.5:1** large text |
| 1.4.11 Non-text Contrast | AA | **3:1** for UI components and meaningful graphics |
| 1.4.1 Use of Colour | A | Colour must not be the only visual means of conveying information |
| 1.4.4 Resize Text | AA | Text resizable to 200% without loss of content or function |
| 1.4.12 Text Spacing | AA | No loss of content at line-height 1.5×, paragraph spacing 2×, letter-spacing 0.12em, word-spacing 0.16em |

**Large text** is defined as **≥18 pt, or ≥14 pt bold** — approximately **24 px** and **18.5 px**. The AAA 7:1 threshold exists to compensate for the contrast-sensitivity loss of roughly 20/80 vision.

**Exceptions to 1.4.3:** text that is part of a logo or brand name has no contrast requirement; nor does incidental text — text in an inactive UI component, pure decoration, invisible text, or text that is part of a picture containing significant other visual content.

Practical rules beyond the minimums: never rely on placeholder text as a label; maintain a visible focus indicator meeting 3:1 against adjacent colours; keep touch targets ≥44×44 px (Apple HIG) / ≥48×48 dp (Material); write meaningful alt text and mark decorative images as such; respect `prefers-reduced-motion`.

---

## 8. Brand identity systems

An identity is not a logo. It is a *system* that lets many people, over many years, produce consistent output without the original designer present.

### The components

**Wordmark / logotype** — the name set as a designed piece of type. Usually the primary asset. Custom-drawn or heavily modified rather than typed.

**Marque / symbol** — an abstract or pictorial mark that can stand alone. Not every brand needs one, and a bad one is worse than none. Test at 16 px favicon size and at building-signage size.

**Lockups** — the defined arrangements of wordmark and marque (horizontal, stacked, mark-only), each with a specified clear space, usually expressed as a fraction of some element of the mark itself so it scales.

**Minimum sizes** — stated for print (mm) and screen (px), separately.

**Colour palette** — as in §3, with Pantone C/U, CMYK, RGB/HEX and RAL/NCS where physical, plus permitted combinations and contrast-verified pairs.

**Type system** — a primary display face, a text face, a UI/system fallback stack, and a licensed-for-web confirmation. State the *scale* (see modular scale, §1) and the rules for hierarchy, not just the names.

**Grid and layout system** — a defined grid for each output family, with worked examples.

**Photographic and illustrative direction** — a stated look with example imagery, plus what is *not* allowed. Negative examples are the most-read pages of any guidelines document.

**Iconography** — a drawn set on a consistent grid, stroke weight and corner radius.

**Motion** — easing curves, duration bands, entry/exit conventions, logo animation.

**Tone of voice** — how the brand writes: 3–5 principles, each with a do/don't sentence pair. This belongs in the identity, not in a separate marketing document.

**Sound** — where relevant, a sonic logo and a defined palette.

### The guidelines document — structure that works

1. **Introduction and brand idea** — one page, the strategic proposition in plain language. Everything downstream must be traceable to it.
2. **Logo** — the assets, lockups, clear space, minimum sizes, permitted backgrounds, and a "misuse" spread showing 8–12 wrong applications.
3. **Colour** — palette with full specifications, proportions (which colour dominates), permitted combinations, accessibility notes.
4. **Typography** — families, licences, scale, hierarchy rules, worked examples, fallbacks.
5. **Layout** — grids, margins, composition principles, worked examples at each output size.
6. **Imagery** — direction, treatment, cropping rules, do/don't.
7. **Iconography and graphic devices.**
8. **Motion.**
9. **Voice.**
10. **Applications** — the whole system applied to real artefacts: stationery, signage, packaging, digital, environmental, merchandise. This section is what makes the rest believable.
11. **Assets and access** — where the files live, formats supplied, who approves exceptions, and a named contact. Guidelines without a governance answer decay within 18 months.

### Two exemplars worth studying

**Otl Aicher's 1972 Munich Olympics identity** — a comprehensive system built on grid systems and a specific bright palette, including a pictogram set designed to work across languages, an official mascot (Waldi, the first Olympic mascot) and a full wayfinding programme. It is the reference case for "identity as infrastructure". Aicher also designed **Rotis** (1988) and shaped Lufthansa's corporate identity.

**Massimo Vignelli's NYC Subway signage and map (1972)** — the case for radical systematisation: a single typeface, a strict grid, a fixed colour code, and a diagrammatic map that abandoned geography for topology. It also demonstrates the political limits of systematisation — the map was withdrawn in 1979 after public resistance, and Vignelli's own definition of the discipline ("semantically correct, syntactically consistent, and pragmatically understandable") arguably lost on the third term.

---

## Sources

- [Understanding SC 1.4.3 Contrast (Minimum)](https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html) — W3C Web Accessibility Initiative
- [International Typographic Style](https://en.wikipedia.org/wiki/International_Typographic_Style) — Wikipedia
- [Massimo Vignelli](https://en.wikipedia.org/wiki/Massimo_Vignelli) — Wikipedia
- [Otl Aicher](https://en.wikipedia.org/wiki/Otl_Aicher) — Wikipedia
- [Design tokens — Material Design 3](https://m3.material.io/foundations/design-tokens/overview) — Google

## Open questions

- Print tolerances (bleed, TAC limits, rich-black recipes, resolution) are stated as general trade practice from professional convention, not from a fetched standards document. ISO 12647 and the specific printer's spec sheet override anything here.
- Pantone Connect's current subscription pricing and the exact status of Pantone libraries inside Adobe applications were not verified in this pass.
- The 8% red–green colour vision deficiency prevalence figure is a widely cited population statistic that was not verified against a primary source here.
- Vox-ATypI was formally retired/revised by ATypI; the current successor classification was not verified. The working shorthand table above is unaffected.
