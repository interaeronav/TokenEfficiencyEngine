---
id: fusion.resources
title: Fusion resources — a tested link register
domain: 15_software_autodesk_fusion
tags: [fusion, resources, documentation, api-reference, forums, learning, certification, youtube, add-ins, books, link-register]
jurisdiction: global
status: stable
confidence: high
updated: 2026-08-25
applies_to: "Links tested by direct fetch on 2026-08-25. Autodesk restructures URLs often — re-test before relying on a dead link."
sources:
  - {title: "Fusion API Reference (browsable)", url: "https://autodeskfusion360.github.io/FusionAPIReference/", publisher: "Autodesk", accessed: 2026-08-25}
  - {title: "Fusion API and Scripts forum", url: "https://forums.autodesk.com/t5/fusion-api-and-scripts/bd-p/22", publisher: "Autodesk", accessed: 2026-08-25}
  - {title: "Autodesk Post Processor Library", url: "https://cam.autodesk.com/hsmposts", publisher: "Autodesk", accessed: 2026-08-25}
  - {title: "Autodesk Learning hub", url: "https://www.autodesk.com/learn", publisher: "Autodesk", accessed: 2026-08-25}
  - {title: "Autodesk certification overview", url: "https://www.autodesk.com/certification/overview", publisher: "Autodesk", accessed: 2026-08-25}
  - {title: "Autodesk University", url: "https://www.autodesk.com/autodesk-university/", publisher: "Autodesk", accessed: 2026-08-25}
related: [fusion.api, fusion.overview, fusion.cam]
---

# Fusion resources — a tested link register

**Summary.** Every link in this file was fetched on **2026-08-25** and is marked with what actually came back. Autodesk restructures URLs frequently — several long-cited addresses (`apps.autodesk.com`, the personal-use restriction articles, the startup campaign page) returned 404 or redirected on the day of testing, and those are recorded as such rather than quietly repeated. Where a page renders entirely in JavaScript, its content could not be captured programmatically and that is noted too; the URL is still good in a browser.

## Key facts

- The **most useful single resource for an AI agent** is `github.com/AutodeskFusion360/FusionAPIReference` — HTML docs, C++ headers and **Python stubs** in one repo, with an `llms.txt` explicitly "for LLM ingestion", updated as of the **May 2026** release.
- The Autodesk App Store at `apps.autodesk.com` now **redirects to `marketplace.autodesk.com`**.
- Fusion certifications are **valid for 2 years**; exam list prices (checked 2026-08-25): Certified Associate **US$150**, Certified Professional **US$200**, Certified Expert **US$250**.

## Legend

| Mark | Meaning |
|---|---|
| ✅ | Fetched successfully on 2026-08-25, content confirmed |
| ⚠️ | URL resolves but content is JavaScript-rendered and could not be captured; open in a browser |
| ↪ | Redirects to a different URL |
| ❌ | Returned 404 / refused on 2026-08-25 |
| ○ | Not tested in this session |

---

## 1. Official documentation and reference

| Resource | URL | Status |
|---|---|---|
| **Fusion API Reference, browsable** — class pages at `.../Fusion_API_Documentation/files/<ClassName>.htm`, members at `<ClassName>_<member>.htm` | https://autodeskfusion360.github.io/FusionAPIReference/ | ✅ |
| **FusionAPIReference repo** — HTML docs + C++ headers + **Python stubs** + `llms.txt` for RAG | https://github.com/AutodeskFusion360/FusionAPIReference | ✅ |
| Fusion product overview | https://www.autodesk.com/products/fusion-360/overview | ✅ |
| Fusion pricing | https://www.autodesk.com/products/fusion-360/pricing | ⚠️ (prices injected by JS) |
| Fusion for personal use | https://www.autodesk.com/products/fusion-360/personal | ✅ |
| Fusion extensions | https://www.autodesk.com/products/fusion-360/extensions | ✅ |
| Manufacturing Extension | https://www.autodesk.com/products/fusion-360/manufacturing-extension | ✅ |
| Simulation Extension | https://www.autodesk.com/products/fusion-360/simulation-extension | ✅ |
| Nesting & Fabrication Extension (now folded into Manufacturing) | https://www.autodesk.com/products/fusion-360/nesting-fabrication-extension | ✅ |
| System requirements | https://www.autodesk.com/support/technical/article/caas/sfdcarticles/sfdcarticles/System-requirements-for-Autodesk-Fusion-360.html | ⚠️ |
| Autodesk Education plan | https://www.autodesk.com/education/edu-software/overview | ✅ |
| Fusion help (main) | https://help.autodesk.com/view/fusion360/ENU/ | ⚠️ (client-rendered; usable in a browser) |
| Personal-use feature restrictions article | *various `sfdcarticles` URLs* | ❌ (all 404 on 2026-08-25) |
| Fusion for Startups campaign | https://www.autodesk.com/campaigns/fusion-360-for-startups | ❌ |

> ⚠️ `help.autodesk.com` serves its content from JavaScript, so it cannot be scraped by a fetch tool and is unavailable to an agent working from raw HTTP. **For programmatic API lookups, use `autodeskfusion360.github.io/FusionAPIReference/` or the local corpus in the GitHub repo instead** — this is the single most useful thing in this file.

## 2. Autodesk Platform Services (cloud APIs)

| Resource | URL | Status |
|---|---|---|
| Fusion Data API developer guide (GraphQL over hub/project/component data) | https://aps.autodesk.com/en/docs/fusiondata/v1/developers_guide/overview/ | ⚠️ |
| APS Fusion Data marketing page | https://aps.autodesk.com/fusion-data-api | ❌ (403 to automated fetch) |
| **Design Automation for Fusion samples** — run Fusion headlessly in the cloud | https://github.com/AutodeskFusion360/DesignAutomationSamples | ✅ |

## 3. Autodesk's own sample code and dev tools (GitHub)

The `AutodeskFusion360` organisation holds about 30 repositories. Verified on 2026-08-25:

| Repo | What it is |
|---|---|
| **FusionAPIReference** | The full API corpus, LLM-ready |
| **FusionMCPSample** | ✅ **MCP server add-in** — lets an external AI agent call into a running Fusion. Exposes `execute_api_script`, `get_screenshot`, `get_api_documentation`. Uses Fusion's custom-event system for thread-safe API calls. MIT |
| **Fusion360DevTools** | "A collection of utilities to assist in developing Fusion 360 Add-ins" — `commands/` and `lib/fusion360utils/` scaffolding, by Patrick Rainsberry |
| **ParameterIO_Python** | CSV import/export of user parameters and attributes |
| **SketchChecker_Python** | Checks the active sketch for curves with open ends — the classic "Extrude finds no profile" bug |
| **DXFBulkImport** | Bulk DXF import. MIT |
| **DXFSplineToPolyline_Python** | Converts splines to polylines on sketch export — **useful for CNC controls that handle arcs and lines but not splines** |
| **DesignAutomationSamples** | Cloud/headless Fusion samples. MIT |
| **ContourGroove_Cpp** | A C++ add-in, as a worked C++ example |
| **AutodeskFusion360.github.io** | The API docs site source |

Organisation root: https://github.com/AutodeskFusion360 ✅

## 4. Community add-ins and frameworks

| Resource | URL | Status | Notes |
|---|---|---|---|
| **Dogbone** — dogbone / minimal / mortise corner relief for CNC joinery. MIT | https://github.com/DVE2000/Dogbone | ✅ | **The single most useful third-party add-in for a joinery shop.** See `05_sheet-goods-and-joinery-workflow.md` |
| **apper** — "a framework to simplify the creation of Fusion 360 Addin", by Patrick Rainsberry (Autodesk). MIT | https://github.com/tapnair/apper | ✅ | Removes the boilerplate in the add-in skeleton in `09_api-and-automation.md` |
| Patrick Rainsberry's other Fusion utilities | https://github.com/tapnair | ○ | Referenced from apper's README |
| **Autodesk Design & Make Marketplace** (successor to `apps.autodesk.com`) | https://marketplace.autodesk.com/ | ↪ ⚠️ | `apps.autodesk.com/FUSION/...` 302-redirects here. Search results are JS-rendered |

Search the marketplace for `cutlist`, `nesting`, `dogbone`, `parameter` and `BOM`. **Check the last-updated date before installing anything** — the majority of free Fusion add-ins are unmaintained and break on UI changes. For a workflow you rely on daily, own the code (`09_api-and-automation.md`).

## 5. Forums

| Forum | URL | Status |
|---|---|---|
| **Fusion API and Scripts** — "Got a new add-in to share? Need something specialized to be scripted?" | https://forums.autodesk.com/t5/fusion-api-and-scripts/bd-p/22 | ✅ |
| Fusion forum category index | https://forums.autodesk.com/t5/fusion/ct-p/1234 | ✅ |
| Fusion post-processor forum | *board ID not confirmed* | ❌ | Reach it from the Fusion forum index above |

The API and Scripts forum is the most valuable Autodesk community resource for this domain: Autodesk API engineers answer there, and most non-obvious API questions have already been asked. Search it before asking.

The **post-processor forum** is where the Autodesk CAM post team takes modification requests. If you have an odd CNC control, this is historically the most effective route to a working `.cps`.

## 6. CAM and post-processors

| Resource | URL | Status |
|---|---|---|
| **Autodesk Post Processor Library** — filter by Milling / Turning / Mill-Turn / Waterjet / Laser / Plasma / Additive, plus Setup Sheet and Interoperability; and by vendor | https://cam.autodesk.com/hsmposts | ✅ |
| Post Processor Training Guide (PDF) and post API documentation | linked from the post library page above | ○ |

Autodesk's own caveat, quoted: *"it is your sole responsibility to make sure you use components that are compatible with your CNC."* Test every post on air before material.

## 7. Learning paths and certification

| Resource | URL | Status |
|---|---|---|
| **Autodesk Learning hub** — self-paced courses, learning paths by industry, certification prep, personal dashboard | https://www.autodesk.com/learn | ✅ |
| Autodesk certification overview | https://www.autodesk.com/certification/overview | ✅ |
| **Autodesk University** — "The Design & Make Conference"; searchable library of past sessions | https://www.autodesk.com/autodesk-university/ | ✅ |
| AU session search | https://www.autodesk.com/autodesk-university/search | ○ |
| `autodesk.com/learn/ecosystem/fusion-360` | — | ❌ |

**Certification (checked 2026-08-25):** four levels exist across the Autodesk portfolio — Certified User, Certified Associate, Certified Professional, Certified Expert. Fusion certifications are **valid for 2 years**. Retail exam prices: **ACA US$150, ACP US$200, ACE US$250**. Whether all four levels are offered for Fusion specifically is not stated on the overview page — `needs-verification`.

For a joinery practice, certification is worth having only if a client or a tender asks for it. The learning value is in the practice, not the badge.

## 8. YouTube — verified channels

Only channels actually fetched on 2026-08-25 are stated as confirmed.

| Channel | URL | Status | Why |
|---|---|---|---|
| **Product Design Online** (Kevin Kennedy) | https://www.youtube.com/@ProductDesignOnline | ✅ | "Making CAD education accessible to anyone, anywhere"; heavily Fusion-focused; hosts the "Learn Fusion in 30 Days" course; explicitly covers **3D printing, woodworking and product design**. The best starting point for a joiner learning Fusion |
| **NYC CNC** | https://www.youtube.com/@NYCCNC | ✅ | "All things CNC, including Fusion 360 CAD & CAM Tutorials and CNC Machining parts." The reference for CAM practice, work-holding, feeds and speeds and machine setup. Metal-leaning but the CAM principles transfer |
| `@AutodeskFusion` | https://www.youtube.com/@AutodeskFusion | ✅ but **not Autodesk** | The handle exists but the channel described itself as a Russian-language hobbyist channel ("we model various trinkets"). **Do not cite it as official.** Find Autodesk's official channel from the product page rather than by guessing a handle |
| `@adskFusion360`, `autodesk.com/learn/ecosystem/fusion-360` | — | ❌ | Both 404 on 2026-08-25 |
| Vladimir Mariano | https://www.youtube.com/@VladimirMariano | ✅ (exists) | Channel confirmed to exist; content not verifiable from the fetch. Widely cited for **Fusion 360 for woodworkers and CNC routers** — `needs-verification` |

**Other channels commonly recommended for Fusion + furniture/CNC work but NOT verified in this session** (`needs-verification` on both existence and current activity): Lars Christensen (long-running Fusion CAM tutorials), Desktop Makes, Fusion 360 School, Learn Everything About Design, Winston Moy (CNC + Fusion), Making Stuff with Sam, Blacktail Studio and Foureyes Furniture (furniture-making, some Fusion). Search rather than trusting a stale handle.

## 9. Books

Bibliographic details below were **not** verified by fetch in this session — treat as pointers, and check the edition against the current Fusion release before buying, because Fusion's UI changes twice a year and CAD books date fast.

| Book | Why | Status |
|---|---|---|
| *Fusion 360 for Makers* — Lydia Sloan Cline (Make: Community) | The best-regarded practical introduction for hobby/maker use, project-driven | ○ `needs-verification` |
| *Learn Autodesk Fusion 360 in 30 Days* — Kevin Kennedy (Packt) | The book of the Product Design Online course | ○ `needs-verification` |
| *CNC Programming Handbook* — Peter Smid | Not Fusion-specific, and the standard reference for what the G-code your post emits actually means. Read this before editing a post | ○ `needs-verification` |
| Autodesk **Post Processor Training Guide** (free PDF from the post library) | The authoritative source for `.cps` editing | ○ |

For the joinery knowledge that Fusion is a tool *for* — wood movement, board specification, hardware, joint selection, quoting — see the `06_joinery_and_woodwork` domain rather than any CAD book.

## 10. A recommended learning path for this project

**Week 1 — modelling fundamentals.** Product Design Online's beginner series, plus this domain's `02` and `03`. Target: build one parametric base unit driven by `CarcassWidth`, `CarcassHeight`, `CarcassDepth`, `BoardThickness`, and prove it rebuilds correctly at the extremes.

**Week 2 — assemblies and documentation.** `04` and `07`. Target: a three-unit kitchen run with correct component structure, joints with limits, an interference check, and a drawing set with a parts list a joiner could price.

**Week 3 — CAM.** NYC CNC's CAM playlists plus `06`. Target: a nested sheet posted to your machine's `.cps`, simulated, dry-run, and one test panel cut and measured.

**Week 4 — automation.** `09` plus the Autodesk sample repos. Target: three working scripts — parameters from CSV, per-panel DXF export, cut list to CSV — installed as one add-in with a button on the Utilities panel.

**Ongoing.** Search the API and Scripts forum before writing anything non-trivial; keep the `FusionAPIReference` repo cloned locally so an agent can look up class names instead of guessing them.

## Sources

- [Fusion API Reference (browsable)](https://autodeskfusion360.github.io/FusionAPIReference/) — Autodesk, accessed 2026-08-25
- [FusionAPIReference repository](https://github.com/AutodeskFusion360/FusionAPIReference) — Autodesk on GitHub, accessed 2026-08-25
- [AutodeskFusion360 GitHub organisation](https://github.com/AutodeskFusion360) — accessed 2026-08-25
- [FusionMCPSample](https://github.com/AutodeskFusion360/FusionMCPSample) — accessed 2026-08-25
- [Fusion360DevTools](https://github.com/AutodeskFusion360/Fusion360DevTools) — accessed 2026-08-25
- [DesignAutomationSamples](https://github.com/AutodeskFusion360/DesignAutomationSamples) — accessed 2026-08-25
- [Dogbone add-in](https://github.com/DVE2000/Dogbone) — DVE2000 on GitHub, accessed 2026-08-25
- [apper add-in framework](https://github.com/tapnair/apper) — Patrick Rainsberry on GitHub, accessed 2026-08-25
- [Fusion API and Scripts forum](https://forums.autodesk.com/t5/fusion-api-and-scripts/bd-p/22) — Autodesk, accessed 2026-08-25
- [Fusion forum category index](https://forums.autodesk.com/t5/fusion/ct-p/1234) — Autodesk, accessed 2026-08-25
- [Autodesk Post Processor Library](https://cam.autodesk.com/hsmposts) — Autodesk, accessed 2026-08-25
- [Autodesk Learning hub](https://www.autodesk.com/learn) — Autodesk, accessed 2026-08-25
- [Autodesk certification overview](https://www.autodesk.com/certification/overview) — Autodesk, accessed 2026-08-25
- [Autodesk University](https://www.autodesk.com/autodesk-university/) — Autodesk, accessed 2026-08-25
- [Autodesk Design & Make Marketplace](https://marketplace.autodesk.com/) — Autodesk, accessed 2026-08-25
- [Product Design Online (YouTube)](https://www.youtube.com/@ProductDesignOnline) — accessed 2026-08-25
- [NYC CNC (YouTube)](https://www.youtube.com/@NYCCNC) — accessed 2026-08-25

## Open questions

- The correct URL/handle for **Autodesk's official Fusion YouTube channel** — two guessed handles were wrong (one 404, one a third-party channel). Find it from the product page.
- The board ID for the **Fusion post-processor forum**.
- Whether Autodesk University's on-demand session library is free to access without registration.
- Whether all four certification levels (User / Associate / Professional / Expert) exist for Fusion specifically.
- Book editions and current-ness — all `needs-verification`.

