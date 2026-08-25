---
id: gxgd.overview
title: Graphic and game design — domain overview
domain: 28_graphic_and_game_design
tags: [graphic-design, game-design, visual-identity, typography, ui-ux, motion, illustration, level-design, narrative-design, technical-art, production, overview, domain-map]
jurisdiction: global
status: stable
confidence: high
updated: 2026-08-25
applies_to: "Practice and education as of August 2026. Salary and tuition figures carry their own dates inline."
unit_system: metric
sources:
  - {title: "Graphic Designers — Occupational Outlook Handbook", url: "https://www.bls.gov/ooh/arts-and-design/graphic-designers.htm", publisher: "US Bureau of Labor Statistics", accessed: 2026-08-25}
  - {title: "Software Developers, QA Analysts and Testers — Occupational Outlook Handbook", url: "https://www.bls.gov/ooh/computer-and-information-technology/software-developers.htm", publisher: "US Bureau of Labor Statistics", accessed: 2026-08-25}
  - {title: "2023–2025 video game industry layoffs", url: "https://en.wikipedia.org/wiki/2023%E2%80%932025_video_game_industry_layoffs", publisher: "Wikipedia", accessed: 2026-08-25}
  - {title: "Video game industry layoffs tracker", url: "https://publish.obsidian.md/vg-layoffs", publisher: "Farhan Noor / videogamelayoffs.com", accessed: 2026-08-25}
  - {title: "MDA framework", url: "https://en.wikipedia.org/wiki/MDA_framework", publisher: "Wikipedia", accessed: 2026-08-25}
  - {title: "Level design", url: "https://en.wikipedia.org/wiki/Level_design", publisher: "Wikipedia", accessed: 2026-08-25}
related: [gxgd.gd_education, gxgd.gd_fundamentals, gxgd.gd_canon, gxgd.uiux, gxgd.game_education, gxgd.game_theory, gxgd.game_disciplines, gxgd.studios, gxgd.engines_tools, gxgd.portfolio, gxgd.resources, envasset.overview, ue.overview]
---

# Graphic and game design — domain overview

**Summary.** This domain covers two fields that share a vocabulary and almost nothing else structurally: **graphic design** — the shaping of communication through type, image, colour and layout — and **game design** — the shaping of player experience through rules, systems and space. They meet in the middle at UI/UX, motion and technical art. This file is the map: it names the distinct disciplines, says what each one actually produces, states which files in this folder go deep on what, and flags where this domain deliberately hands off to `25_environmental_asset_creation` (3D asset craft) and `13_software_unreal_engine` (engine specifics). The honest headline for 2026: both fields have a healthy *practice* and a brutal *entry-level market*.

## Key facts

| Item | Value |
|---|---|
| US median annual wage, graphic designers | **US$61,300** (May 2024, BLS); 10th percentile <US$37,600, 90th percentile >US$103,030 |
| US graphic designer employment | 265,900 jobs (2024); projected growth **2%** 2024–34 ("slower than average") |
| US median annual wage, software developers | **US$133,080** (May 2024, BLS); software publishers sector median US$149,990 |
| Game industry layoffs, 2023 | >10,500 roles |
| Game industry layoffs, 2024 | ~14,600 roles — more than 2022 and 2023 combined |
| Game industry layoffs, 2026 (to 1 July 2026) | ~4,600 roles, 22 studios closed |
| UK junior game roles as share of postings | 9.4% (2022) → 2.9% (2023) |
| Canonical game-design framework | MDA — Mechanics, Dynamics, Aesthetics (Hunicke, LeBlanc, Zubek) |
| Canonical usability framework | Nielsen's 10 usability heuristics (1994) |
| Canonical layout framework | Müller-Brockmann's modular grid (*Grid Systems in Graphic Design*, 1981) |
| Text contrast minimum, WCAG 2.2 Level AA | **4.5:1** normal text, **3:1** large text (≥18 pt, or ≥14 pt bold) |

> ⚠️ Do not treat "graphic designer" and "game designer" as adjacent job titles that a portfolio can straddle. They are hired by different people, on different evidence, into different pay bands. A person can hold both skills; a *portfolio* that tries to hold both usually convinces nobody. See `10_portfolio-and-breaking-in.md`.

## The two fields, stated plainly

**Graphic design** is the discipline of making meaning legible and persuasive using type, image, colour, space and sequence. Its output is artefacts: a book, a poster, a wordmark, an annual report, a signage system, a packaging range, a website, a title sequence, a set of brand guidelines. Its core intellectual move is *reduction* — removing everything that is not carrying the message, then arranging what remains so the eye takes it in the order you intend.

**Game design** is the discipline of designing an *experience the designer does not directly author* — you build rules, systems and spaces, and the player produces the experience by acting inside them. Its output is not an artefact but a machine that produces artefacts: every playthrough is different. Its core intellectual move is *second-order design* — you cannot place the moment, you can only make the moment likely.

The two share tools (Figma, Photoshop, Illustrator), share a colour and typography literacy, and share a professional ethic that the audience's comprehension is the measure of success. They diverge on everything else: graphic design is usually a solo or small-team craft on a weeks-to-months cycle, game design is usually a large-team engineering discipline on a two-to-six-year cycle.

## The disciplines, one by one

### Graphic-design side

**Graphic design (generalist).** Layout, type, image, print and screen. Still the largest single employment category. In practice most "graphic designers" today spend the bulk of their time on digital and social output, not print.

**Visual identity / branding.** The design of a coherent system — wordmark, marque, colour palette, type system, photographic and illustrative direction, tone of voice, application rules — plus the *guidelines document* that lets other people apply it without the designer present. This is where the money and the reputational prestige sit. Studios that lead: Pentagram, Collins, DIA, Order, Base, Studio Dumbar, Bureau Mirko Borsche. See `03`.

**Typography and type design.** Two different jobs. *Typography* is the use of existing typefaces — measure, leading, tracking, hierarchy, optical adjustment. *Type design* is drawing the letterforms themselves, a specialist craft with its own schools (KABK The Hague's TypeMedia, Reading's MATD) and its own tools (Glyphs, FontLab, RoboFont). See `02` for typography, `03` for the historic type designers.

**UI/UX and digital product design.** Now larger by headcount and better paid than classical graphic design in most Western markets. Research → information architecture → interaction → interface → design system → handoff. It has its own literature, its own metrics and its own hiring ritual. See `04`.

**Motion design.** Type and image in time: title sequences, broadcast identity, explainer video, UI micro-interaction, social-first vertical motion. Tooling is After Effects, Cinema 4D/Blender, Rive and Lottie for runtime motion. Sits between graphic design and animation.

**Illustration.** A distinct authorial practice, usually freelance, usually commissioned by designers and art directors rather than employed alongside them. In games it is largely absorbed into *concept art* and *marketing key art*.

### Game side

**Game designer (generalist / creative).** Owns what the game *is*: the core loop, the pillars, the verb set, the moment-to-moment feel. On a small team this is one person; on a large team it fragments into the specialisms below and a creative director sits over them.

**Level designer.** Builds the space and the pacing inside it — blockout, encounter placement, sightlines, affordances, teaching without tutorials. Historically not a separate profession at all: through the 1970s–2000s a single programmer laid out the maps, and the role only crystallised as environments grew. Modern level designers usually need *both* visual-artist and game-designer skills. See `06`.

**Narrative designer.** Distinct from "writer". A writer produces prose and dialogue; a narrative designer produces the *structure* that makes prose land — quest architecture, branching, barks, environmental storytelling, the relationship between mechanics and theme.

**Systems designer.** Owns the numbers: combat maths, economy, loot tables, progression curves, difficulty. Spreadsheet-native. On live-service games this is the discipline most directly coupled to revenue.

**Technical designer.** The bridge role — scripts in Blueprint/visual scripting or light code, builds designer-facing tools, prototypes mechanics that programmers later harden. Frequently the most hireable design profile in a contracted market because it is provably productive on day one.

**Technical artist.** The other bridge role, on the art side: shaders, rigging, procedural asset generation (Houdini), performance budgets, pipeline tooling. See `09`, and `25_environmental_asset_creation` for the asset-authoring craft itself.

### Production and adjacent

**Producer / production manager.** Schedule, scope, dependencies, risk, and the political work of keeping disciplines aligned. Not a junior role and not a design role, though many designers drift into it.

**QA.** Historically the entry door into games, and still one of the few remaining ones — but increasingly outsourced to specialist vendors (Keywords and similar), which weakens it as a route into design.

**Live ops.** Post-launch content cadence, events, balance patches, monetisation tuning, telemetry. A discipline that barely existed in 2010 and now employs large numbers.

**Audio design and composition.** Middleware-native (Wwise, FMOD). Small teams, high specialism, often contract.

See `07_game-development-disciplines.md` for the full role-by-role treatment with skills, portfolio expectations and salary bands.

## How this folder is organised

| File | What it holds |
|---|---|
| `01_graphic-design-education.md` | Schools worldwide and in southern Africa, curricula year by year, portfolio requirements, cost, and a concrete self-taught substitute curriculum |
| `02_graphic-design-fundamentals.md` | The craft: grids, typography, colour, composition, hierarchy, print production, accessibility, identity systems |
| `03_graphic-design-canon.md` | The history and the people, movement by movement, with the essential books |
| `04_ui-ux-and-digital-product.md` | Research, IA, interaction, design systems, Figma, testing, handoff, metrics |
| `05_game-design-education.md` | The game schools that matter, with programme names, cost and reputation — and the degree-versus-portfolio question |
| `06_game-design-theory-and-practice.md` | Loops, MDA, the elemental tetrad, systems, economy, flow, game feel, level design, narrative, multiplayer, monetisation, playtesting |
| `07_game-development-disciplines.md` | Every role on a game team: job, skills, portfolio, salary band with source and year |
| `08_top-game-studios.md` | The register of studios and publishers, plus the 2023–2026 contraction |
| `09_engines-tools-and-technical-art.md` | Engines, middleware, version control, build pipelines, technical art, platform certification |
| `10_portfolio-and-breaking-in.md` | The practical career file — portfolios, jams, mods, internships, GDC, interviews, the 2026 market |
| `11_books-courses-and-resources.md` | Annotated register of books, talks, courses and communities with URLs |

## Deliberate handoffs to other domains

This domain does **not** duplicate:

- **3D asset craft** — modelling, sculpting, texturing, scanning, foliage, terrain, look-dev, photoreal principles. That is `25_environmental_asset_creation`. When this domain says "environment artist", the *how* lives there.
- **Unreal Engine specifics** — Blueprints, Nanite, Lumen, Datasmith, Python automation, packaging, licensing. That is `13_software_unreal_engine`. File `09` here covers engine *choice* and the comparative landscape, not Unreal's menus.
- **Blender and Fusion mechanics** — `14_software_blender`, `15_software_autodesk_fusion`.
- **Interior and spatial design** — `19_interior_design`.
- **Education psychology and learning design** — `22_psychology_and_education`.

Where a topic genuinely sits on the boundary (technical art, shaders, optimisation), this domain states the *role and career shape* and points to the other domain for the *technique*.

## The 2026 state of both fields, honestly

**Graphic design** is not shrinking, but it is not growing either — BLS projects 2% employment growth 2024–34 against a 3% all-occupations baseline, with roughly 20,000 US openings a year, almost all replacement rather than expansion. The median wage of US$61,300 (May 2024) sits well below software. The pressure is coming from three directions at once: template platforms absorbing the low end, in-house marketing teams absorbing the mid, and generative tooling absorbing routine production work (resizing, mockups, first-pass layout, stock illustration). What has *not* been absorbed is the top: identity strategy, editorial judgement, typographic craft at the level that survives scrutiny, and the ability to argue a design decision to a sceptical executive. The field is barbelling.

**Games** are in the deepest contraction of their history. Over 10,500 roles went in 2023, ~14,600 in 2024 — more than 2022 and 2023 combined — with continued cuts through 2025 and ~4,600 more plus 22 studio closures in the first half of 2026 alone. Embracer alone cut 7,761 people, closed or divested 44 studios and cancelled 80 projects. More than 30 studios shut outright, including Monolith Productions, Arkane Austin, Tango Gameworks (later revived under Krafton), Ready at Dawn, Volition, Sony's London Studio, Pixelopus and Firewalk. The stated causes are consistent across sources: pandemic-era over-hiring against demand that reverted to trend, AAA budgets rising from the US$50–150M band to US$200M+ (with Call of Duty and GTA-scale projects cited at US$250–300M+), higher interest rates ending cheap capital, and failed strategic bets on metaverse and live-service.

The structural consequence matters more than the headline number: **junior roles have been eliminated first**. UK junior postings fell from 9.4% of the market in 2022 to 2.9% in 2023. The industry is currently consuming a talent pipeline it is not replenishing. Anyone entering in 2026 should read `10` before reading anything else in this folder.

The counter-current is real but small: solo and micro-team success is at an all-time high. *Stardew Valley* (one person, released 2016) passed **50 million copies by February 2026**. *Hollow Knight: Silksong* (Team Cherry, a handful of people) sold **over 7 million copies by mid-December 2025** after 5 million players in three days. *Balatro*, *Vampire Survivors*, *Dave the Diver* and *Lethal Company* all point the same way. The economics of the mid-budget AAA project have broken; the economics of the tightly-scoped, distinctive small project have never been better.

## How to use this domain

If you are **learning graphic design**: `02` → `03` → `01` → `11`. Fundamentals before history before schools.

If you are **learning game design**: `06` → `07` → `05` → `10`. Theory and role-map before schools, because the school decision only makes sense once you know which role you want.

If you are **hiring or briefing**: `07` for role definitions and bands, `08` for who does what well, `04` for product-design vocabulary.

If you are **an agent producing work in this domain**: `02` and `04` contain the checkable rules (contrast ratios, grid maths, measure, token structure). `06` contains the checkable game-design heuristics. Prefer those over aesthetic assertion.

## Sources

- [Graphic Designers — Occupational Outlook Handbook](https://www.bls.gov/ooh/arts-and-design/graphic-designers.htm) — US Bureau of Labor Statistics
- [Software Developers, QA Analysts, and Testers — Occupational Outlook Handbook](https://www.bls.gov/ooh/computer-and-information-technology/software-developers.htm) — US Bureau of Labor Statistics
- [2023–2025 video game industry layoffs](https://en.wikipedia.org/wiki/2023%E2%80%932025_video_game_industry_layoffs) — Wikipedia
- [Video game industry layoffs tracker](https://publish.obsidian.md/vg-layoffs) — videogamelayoffs.com
- [MDA framework](https://en.wikipedia.org/wiki/MDA_framework) — Wikipedia
- [Level design](https://en.wikipedia.org/wiki/Level_design) — Wikipedia
- [Understanding SC 1.4.3 Contrast (Minimum)](https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html) — W3C WAI
- [10 Usability Heuristics for User Interface Design](https://www.nngroup.com/articles/ten-usability-heuristics/) — Nielsen Norman Group
- [Stardew Valley](https://en.wikipedia.org/wiki/Stardew_Valley) — Wikipedia
- [Hollow Knight: Silksong](https://en.wikipedia.org/wiki/Hollow_Knight:_Silksong) — Wikipedia

## Open questions

- No verified 2026 figure was obtained for total *global* game industry headcount, so the layoff totals above cannot be expressed as a percentage of the workforce.
- BLS "graphic designers" excludes many UI/UX roles, which are classified under web developers and digital designers; a like-for-like combined design wage figure was not verified.
- 2025 full-year layoff totals were not obtained as a single verified number; the Wikipedia article covers 2023–2025 but gives an explicit annual total only for 2023 and 2024.

