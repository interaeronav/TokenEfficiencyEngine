---
id: gxgd.game_disciplines
title: Game development disciplines — who does what, and what it pays
domain: 28_graphic_and_game_design
tags: [game-design, careers, roles, level-designer, narrative-designer, systems-designer, technical-designer, gameplay-programmer, engine-programmer, graphics-programmer, tools-programmer, technical-artist, environment-artist, character-artist, animator, vfx-artist, ui-artist, concept-artist, audio-designer, composer, producer, qa, live-ops, salary]
jurisdiction: global
status: stable
confidence: medium
updated: 2026-08-25
applies_to: "Role definitions are current practice. Salary anchors are US BLS May 2024 occupational medians; game-specific bands are marked where unverified."
unit_system: metric
sources:
  - {title: "Arts and Design Occupations", url: "https://www.bls.gov/ooh/arts-and-design/home.htm", publisher: "US Bureau of Labor Statistics", accessed: 2026-08-25}
  - {title: "Graphic Designers", url: "https://www.bls.gov/ooh/arts-and-design/graphic-designers.htm", publisher: "US Bureau of Labor Statistics", accessed: 2026-08-25}
  - {title: "Software Developers, QA Analysts, and Testers", url: "https://www.bls.gov/ooh/computer-and-information-technology/software-developers.htm", publisher: "US Bureau of Labor Statistics", accessed: 2026-08-25}
  - {title: "Web Developers and Digital Designers", url: "https://www.bls.gov/ooh/computer-and-information-technology/web-developers.htm", publisher: "US Bureau of Labor Statistics", accessed: 2026-08-25}
  - {title: "Writers and Authors", url: "https://www.bls.gov/ooh/media-and-communication/writers-and-authors.htm", publisher: "US Bureau of Labor Statistics", accessed: 2026-08-25}
  - {title: "Level design", url: "https://en.wikipedia.org/wiki/Level_design", publisher: "Wikipedia", accessed: 2026-08-25}
  - {title: "2023–2025 video game industry layoffs", url: "https://en.wikipedia.org/wiki/2023%E2%80%932025_video_game_industry_layoffs", publisher: "Wikipedia", accessed: 2026-08-25}
related: [gxgd.overview, gxgd.game_theory, gxgd.game_education, gxgd.studios, gxgd.engines_tools, gxgd.portfolio, envasset.overview, envasset.pipeline]
---

# Game development disciplines — who does what, and what it pays

**Summary.** A modern AAA team runs 150–800 people across roughly twenty distinct disciplines; an indie team runs three to fifteen people wearing all of them. This file defines each role, states the skills that actually get someone hired into it, describes what the portfolio must show, and gives a salary anchor. **Salary honesty note:** there is no single authoritative public games salary dataset, so this file anchors each role to the closest US Bureau of Labor Statistics occupational median (May 2024, published 2025) and marks any game-specific band as unverified rather than inventing a number.

## Key facts — the salary anchors

All figures **US, May 2024, US Bureau of Labor Statistics**, national medians across all industries:

| BLS occupation | Median | 10th pct | 90th pct |
|---|---|---|---|
| **Software developers** | **US$133,080** | <US$79,850 | >US$211,450 |
| Software publishers sector (developers) | US$149,990 | — | — |
| **QA analysts and testers** | **US$102,610** | — | — |
| **Art directors** | **US$111,040** | — | — |
| **Special effects artists and animators** | **US$99,800** | — | — |
| **Web and digital interface designers** | **US$98,090** | <US$47,840 | >US$192,180 |
| Web developers | US$90,930 | — | — |
| **Industrial designers** | US$79,450 | — | — |
| **Writers and authors** | **US$72,270** | <US$41,080 | >US$133,680 |
| **Graphic designers** | **US$61,300** | <US$37,600 | >US$103,030 |
| All occupations (US) | US$49,500 | — | — |

> ⚠️ These are national, all-industry medians. Games-industry pay differs from them in both directions: senior roles at large publishers in Los Angeles, Seattle, Montréal or Stockholm exceed them substantially; entry-level and QA roles, especially at outsourcing vendors, fall well below. Cost-of-living-adjusted, a Montréal or Warsaw salary is often competitive with a nominally higher California one. **No games-specific salary survey was verified in this pass** — see Open questions.

**Structural context for every number below:** the industry cut over 10,500 roles in 2023 and ~14,600 in 2024, with a further ~4,600 and 22 studio closures in the first half of 2026. **Junior positions were cut first** — UK junior postings fell from 9.4% of the market in 2022 to 2.9% in 2023. In this market, *provable productivity on day one* beats potential in every hiring conversation.

---

## Design disciplines

### Game designer (generalist / creative director track)

**The job.** Owns what the game *is*: the pillars, the core loop, the verb set, the feel. Writes feature briefs, runs playtests, arbitrates between disciplines, and says no. At director level, holds the vision across a multi-year project and defends it to executives.

**Skills.** Systems thinking; the ability to prototype an idea rather than describe it; written and verbal communication (the majority of the job); playtest facilitation; enough scripting to build something; deep, analytical knowledge of games across genres — not just the ones you like.

**Portfolio.** Shipped or finished games, however small. Design documents for real projects with the *outcome* stated. Written analysis of existing games that goes past opinion. Game jam entries. **Ideas alone are worthless in this discipline** — every studio receives hundreds of design pitches and hires none of them.

**Salary anchor.** No BLS occupation maps cleanly. Practitioner reports place experienced designers between the art-director and software-developer bands. **`needs-verification`.**

**Route in.** Almost never direct. Enter as technical designer, level designer, QA analyst or production coordinator and move across.

### Level designer

**The job.** Builds the spaces and the pacing inside them: blockout, encounter placement, sightlines, affordances, scripted events, the teaching sequence for new mechanics. Works from pre-production to ship. Level design "did not exist as a discipline" in the 1970s–2000s — a single programmer laid out maps — and the modern role now typically requires "skills as both a visual artist and game designer".

**Skills.** Spatial composition and architectural literacy; the engine's level tools (Unreal editor, Unity, Hammer, Radiant, proprietary); scripting for encounters; a working understanding of AI navigation and streaming; the ability to iterate on playtest feedback without defending your first layout.

**Portfolio.** **Playable levels**, not screenshots. Provide a downloadable build, a two-minute walkthrough video, and a written breakdown: intent, the intensity curve, the teaching sequence, what changed after playtesting. Mods for *Half-Life 2*, *Portal 2*, *Skyrim*, *Doom* or CS map-making are directly legible to hiring managers. Two excellent levels beat ten mediocre ones.

**Salary anchor.** Practitioner reports place level designers near or slightly below the art-director band at senior level. **`needs-verification`.**

### Narrative designer

**The job.** The structure that delivers story: quest architecture, branching and its costs, dialogue systems, barks, environmental storytelling, codex design, cutscene budget, and keeping mechanics and story saying the same thing. Distinct from a **game writer**, who produces the prose and dialogue itself.

**Skills.** Writing, obviously — but also systems thinking, node-based dialogue tooling (Twine, Ink, articy:draft, Yarn Spinner, proprietary), the discipline of writing to a technical constraint (character limits, VO budget, localisation cost), and a genuine understanding of what mechanics can express.

**Portfolio.** Interactive fiction (Twine and Ink pieces are the standard credential), a branching quest built in a real engine or mod, samples of barks and systemic dialogue, and a written analysis of a game's narrative structure. Screenplays and novels are weak evidence — they demonstrate writing but not narrative *design*.

**Salary anchor.** BLS **Writers and authors: US$72,270** (May 2024), 90th percentile >US$133,680. Games narrative roles skew above the general writing median but the mapping is imperfect. **`needs-verification`** for games specifically.

### Systems designer

**The job.** The numbers: combat maths, damage formulae, economy, loot tables, progression curves, difficulty tuning, character/ability balance. On live-service games this is the discipline most directly coupled to revenue and the most continuously employed post-launch.

**Skills.** Spreadsheet fluency to an unusual level; statistics and probability; the ability to build a simulation or Monte Carlo model of your own system; data analysis (SQL, Python, a BI tool); scripting; and the temperament to be told by telemetry that you were wrong.

**Portfolio.** A documented, tuned system with the *model* shown — the spreadsheet, the curves, the simulation, the before-and-after data. Board and card games are excellent evidence here because the system is fully visible. Balance analyses of existing games with real data behind them.

**Salary anchor.** Sits between the design and data-analyst bands. **`needs-verification`.**

### Technical designer

**The job.** The bridge: builds prototypes, scripts gameplay in Blueprint or C#, wires systems, builds designer-facing tools, and takes designs from "described" to "working" without occupying a programmer. Frequently the highest-demand design role because the output is immediately usable.

**Skills.** Visual scripting to a professional standard (Unreal Blueprint especially), real code (C++/C#) at a working level, engine architecture literacy, debugging and profiling, and design judgement.

**Portfolio.** Working systems in a real engine — an inventory system, an ability framework, an AI behaviour set, a procedural generator — with the source available and the architecture explained. Tools you built for other people to use are the strongest single item.

**Salary anchor.** Closest to BLS **Software developers: US$133,080** at senior level; junior technical designers earn well below that. **`needs-verification`** for games specifically.

---

## Programming disciplines

### Gameplay programmer

**The job.** Implements the mechanics: player controller, camera, combat, AI behaviour, interaction, abilities, inventory. Works most closely with designers of any programming role and absorbs the most churn, because gameplay is what iterates.

**Skills.** C++ (Unreal) or C# (Unity) to a high standard; 3D maths (vectors, matrices, quaternions, interpolation); state machines and behaviour trees; animation systems and root motion; networking basics; profiling; and tolerance for rewriting your own work repeatedly.

**Portfolio.** A GitHub repository with readable, commented code. A playable build. Ideally a technical write-up of one hard problem you solved. Contributions to an open-source engine (Godot, O3DE, Bevy) are strong signals.

**Salary anchor.** BLS **Software developers: US$133,080** median, software-publishers sector **US$149,990**; 90th percentile >US$211,450. Games programming historically pays *below* general software for equivalent skill — this is a well-documented industry norm and is one reason the discipline loses people to fintech and general tech.

### Engine programmer

**The job.** Builds and maintains the runtime — memory management, threading and job systems, asset streaming, serialisation, platform abstraction, build systems. On studios with proprietary engines (Rockstar's RAGE, Remedy's Northlight, Capcom's RE Engine, Naughty Dog's in-house engine, EA's Frostbite, Ubisoft's Anvil/Snowdrop) this is a large permanent team.

**Skills.** Deep C++; computer architecture, cache behaviour and data-oriented design; multithreading; platform SDKs; performance measurement as a habit rather than an activity.

**Portfolio.** Your own engine or renderer, however small, with the source public. A profiler-driven optimisation write-up. This is the discipline where DigiPen's engine-from-scratch curriculum converts most directly.

**Salary anchor.** Top of the software-developer distribution; commonly toward the **US$211,450 90th percentile** at senior level in high-cost markets. **`needs-verification`** for games specifically.

### Graphics programmer

**The job.** Rendering: the render pipeline, shaders, lighting, shadows, post-processing, GPU performance. The scarcest and most transferable programming discipline in games — the same skills serve film, simulation, automotive, XR and ML infrastructure.

**Skills.** HLSL/GLSL and shader authoring; the modern graphics APIs (DirectX 12, Vulkan, Metal); the rendering literature (PBR theory, real-time global illumination, temporal techniques); linear algebra and signal processing; GPU architecture and profiling (RenderDoc, PIX, Nsight).

**Portfolio.** A renderer you wrote. Shader work with the maths explained. A GPU optimisation case study with before/after frame times. Implementations of published papers.

**Salary anchor.** The highest-paid programming discipline in games; sits at or above the software-developer 90th percentile in senior roles. **`needs-verification`.**

### Tools programmer

**The job.** Builds the editors, importers, validators, batch processors and pipeline automation the rest of the studio uses. Chronically under-valued and structurally load-bearing: tools quality sets the iteration speed of every other discipline.

**Skills.** C++ and C#; Python; UI frameworks (Qt, ImGui, editor extensions); an understanding of every downstream discipline's workflow; the patience to gather requirements from artists who cannot articulate them.

**Portfolio.** Tools other people actually use. Engine editor plugins. A pipeline automation script with the time saved quantified. See `13_software_unreal_engine` file `06` for the Python automation surface.

**Salary anchor.** BLS **Software developers: US$133,080**. **`needs-verification`** for games specifically.

---

## Art disciplines

> The *craft* of these roles — modelling, sculpting, texturing, scanning, foliage, terrain, look-dev — is covered in depth in **`25_environmental_asset_creation`**. This file covers the role shape, portfolio and pay.

### Technical artist

**The job.** The art-side bridge: shaders and materials, rigging and skinning, procedural content (Houdini), performance budgets, LOD and optimisation, and building tools for artists. Often the person who diagnoses why the frame rate collapsed.

**Skills.** Shader authoring (node graphs and code); Python and MEL/MaxScript; Houdini and procedural thinking; rigging; profiling; and a genuine understanding of both artistic intent and engine constraints.

**Portfolio.** Shaders with breakdowns. A Houdini digital asset that generates something useful. A rig demonstration. A tool with a before/after time saving. An optimisation case study with real numbers.

**Salary anchor.** Typically the highest-paid art-adjacent discipline, above BLS **Special effects artists and animators: US$99,800**, often approaching programmer bands. **`needs-verification`.**

### Environment artist

**The job.** Builds the world: modular kits, props, terrain, materials, set dressing, and the assembly of levels into shippable art. Works from level-design blockouts.

**Skills.** Modelling (Maya, Blender, 3ds Max), high-to-low poly and baking, UVs, texturing (Substance Painter/Designer), trim sheets and modular kit design, photogrammetry, engine assembly and lighting, and a strong grasp of real-world reference and composition. See `25_environmental_asset_creation` files `01`–`09`.

**Portfolio.** Two to four **fully realised environments**, rendered in-engine, at 1920×1080 or higher, with wireframes, texture sheets, material breakdowns and polycounts shown. A modular kit demonstration. Real-world reference boards alongside the result. ArtStation is the de facto submission platform.

**Salary anchor.** BLS **Special effects artists and animators: US$99,800** is the closest match, though it spans film and games. **`needs-verification`** for games specifically.

### Character artist

**The job.** Sculpts, retopologises, textures and prepares characters and creatures for rig and animation. The most technically demanding pure-art discipline.

**Skills.** ZBrush sculpting at a high level; anatomy — genuinely, not approximately; retopology; UV layout; texturing including skin, hair and cloth; grooming (XGen, Ornatrix, Blender hair); and the technical requirements of the target rig.

**Portfolio.** Three to five finished characters with turnarounds, wireframes, sculpt progression, texture maps, and real-time renders in the target engine. Anatomy studies. A stylised piece and a realistic piece if you want breadth considered.

**Salary anchor.** BLS **Special effects artists and animators: US$99,800**. **`needs-verification`.**

### Animator

**The job.** Gameplay animation (locomotion, combat, traversal, transitions) or cinematic animation. Gameplay animation is the harder and more games-specific craft, because animations must blend, interrupt and respond rather than play.

**Skills.** The twelve principles applied to interactive constraints; Maya or Blender; motion capture cleanup; state machines and blend trees in-engine; root motion; and an understanding of frame-level responsiveness (see `06 §6`).

**Portfolio.** A demo reel of 60–90 seconds, best work first, with the in-engine context shown, not just a viewport playblast. A locomotion set (idle, walk, run, turn, stop) is the single most-requested item. Show the blend tree.

**Salary anchor.** BLS **Special effects artists and animators: US$99,800**.

### VFX artist

**The job.** Real-time effects: explosions, magic, weather, impacts, destruction, fluid and smoke. Sits between art and technical art.

**Skills.** Niagara (Unreal) or VFX Graph/Shuriken (Unity); shader authoring; Houdini for simulation and flipbook generation; timing and readability (a VFX must communicate gameplay state, not just look good); and rigorous performance discipline — overdraw is the usual culprit in an effects-heavy frame.

**Portfolio.** A reel with each effect shown in isolation and in gameplay context, with particle counts and cost stated. Breakdowns of the shader and the texture work.

**Salary anchor.** Above the animator/SFX-artist band in most markets. **`needs-verification`.**

### UI artist / UI designer

**The job.** HUD, menus, inventory, map, tutorial overlays. The role where graphic design skills transfer most directly into games — and where they are most needed, because games UI is frequently poor.

**Skills.** Typography and layout (see `02`); UMG (Unreal) or uGUI/UI Toolkit (Unity); animation of UI; localisation-safe layout; console and controller navigation patterns; accessibility (colourblind modes, text scaling, subtitle systems); and readability at 3 m on a television, which is the constraint most PC-trained designers miss.

**Portfolio.** Full UI flows, not single screens. Show the same screen at multiple resolutions and in a long language (German is the standard stress test). Show the controller navigation map. An implemented, interactive UI in a real engine beats a Figma file.

**Salary anchor.** Between BLS **Graphic designers (US$61,300)** and **Web and digital interface designers (US$98,090)** depending on how technical the role is.

### Concept artist

**The job.** Visual development: characters, environments, props, key art, mood and colour scripts. Produces the target the production artists build toward. Shrinking as a full-time role in favour of contract work, and the discipline most directly exposed to generative image tooling.

**Skills.** Drawing and painting fundamentals to a very high level; perspective; anatomy; colour and light; design thinking (a concept must be *buildable*); 3D blockout for photobashing and camera setup; speed.

**Portfolio.** Finished pieces plus **process** — thumbnails, iterations, callouts, orthographic sheets. Design variations on a single brief demonstrate more than ten unrelated finished paintings. Show that you can work in someone else's style.

**Salary anchor.** BLS **Special effects artists and animators: US$99,800** is generous for this role; concept artists typically earn less, and freelance rates vary enormously. **`needs-verification`.**

### Art director

**The job.** Owns the visual target and the consistency of everything shipped against it. Builds style guides, reviews work, hires, and translates the creative director's intent into art-team direction.

**Salary anchor.** BLS **Art directors: US$111,040** (May 2024).

---

## Audio disciplines

### Audio designer / sound designer

**The job.** Records, designs and implements every non-music sound: weapons, footsteps, UI, ambience, creature vocalisations. Implementation is half the job — a great sound triggered badly is a bad sound.

**Skills.** Field recording; a DAW (Reaper, Pro Tools, Nuendo); sound design synthesis and layering; **Wwise or FMOD implementation** (this is the hiring filter); a grasp of mixing, DSP, occlusion, reverb zones and dynamic mixing systems; and enough scripting to wire events.

**Portfolio.** A redesign reel — take existing game footage, strip the audio, replace it entirely, and show a before/after. A Wwise or FMOD project file demonstrating an adaptive system. An implemented playable demo.

**Salary anchor.** No clean BLS mapping. **`needs-verification`.**

### Composer

**The job.** Writes the score, usually as a contractor rather than staff. Games scoring is distinguished by **interactivity** — the music must respond to state, loop indefinitely without fatigue, and layer or transition seamlessly.

**Skills.** Composition and orchestration; a DAW and a sample library rig; **vertical layering and horizontal re-sequencing** techniques; Wwise/FMOD implementation; and the business skills of a freelancer.

**Portfolio.** An interactive music demo where the listener can trigger state changes and hear the transitions — this demonstrates the games-specific craft that a linear reel cannot.

**Salary anchor.** Project-fee based; no reliable public median. **`needs-verification`.**

---

## Production and support

### Producer

**The job.** Schedule, scope, dependencies, risk, communication, and removing obstacles. Not a design role, though it is often confused for one. On a large project the production organisation is what determines whether the game ships.

**Skills.** Project management (agile in practice, whatever the process is called); estimation; dependency and risk management; the political skill to say no; genuine literacy in every discipline's constraints; Jira/Shotgun/Perforce fluency.

**Portfolio.** Shipped projects with your role and its scope stated. Evidence of managing a real team through a real deadline — game jams and student capstones count if you led them. Certifications (PMP, Scrum) are worth little in games relative to shipped credits.

**Salary anchor.** No clean BLS mapping. Senior producers typically sit near or above the art-director band. **`needs-verification`.**

### QA — quality assurance

**The job.** Finds, reproduces, isolates and documents defects. Splits into **manual/functional QA**, **compliance/certification QA** (checking against platform TRC/TCR/lotcheck requirements — see `09`), **localisation QA**, and **QA automation/SDET**, which builds automated test infrastructure and is a genuine engineering role.

**Skills.** Systematic exploration; precise, reproducible bug writing (the single most valuable QA skill and the rarest); bug tracker discipline; platform certification knowledge; and for automation, real programming.

**Portfolio.** Bug reports you have written. For automation, a test harness on GitHub. Demonstrated familiarity with a platform's certification requirements is a strong differentiator.

**Salary anchor.** BLS **QA analysts and testers: US$102,610** (May 2024) — but note this is the software-industry figure and **games QA pays materially below it**, particularly at outsourcing vendors, where contract and hourly arrangements are the norm. Games QA has been among the most heavily outsourced and most heavily unionised (the ZeniMax and Microsoft-recognised QA units) parts of the industry. **`needs-verification`** for games-specific figures.

**Route note.** QA was historically *the* entry door into games and to a lesser extent still is — but its outsourcing has weakened it as a route into design or programming. Treat it as a valid entry point only if the studio has a stated internal-mobility path.

### Live ops

**The job.** Everything after launch: content cadence, seasonal events, battle passes, balance patches, telemetry analysis, community response, and revenue management. On a successful live-service title this team is larger than the original development team.

**Skills.** Data analysis (SQL, dashboards); systems and economy design; release management; community literacy; and the nerve to make balance decisions that will be publicly hated.

**Portfolio.** Evidence of running something live with data — a modded server, a community you operate, a small live game with published retention figures.

**Salary anchor.** Varies enormously with seniority and revenue responsibility. **`needs-verification`.**

### Community manager, user researcher, data analyst, localisation

Named for completeness: **community managers** (the studio's public interface and its early-warning system), **user researchers** (run the playtest programme professionally — see `06 §11`), **data analysts** (own the telemetry pipeline and the dashboards), and **localisation managers** (coordinate translation, cultural adaptation and LQA — a discipline that must be involved in *design*, not only at the end, because UI that cannot hold German or Japanese has to be rebuilt).

---

## Team shapes

| Team size | Typical composition |
|---|---|
| **1** | Everything. Realistic output: a tightly scoped 2D or systems-driven game. *Stardew Valley* is the proof this can succeed at enormous scale. |
| **2–5** | 1–2 programmers, 1–2 artists, one person doing design and production. Contract audio. *Team Cherry*, *Motion Twin*, *Supergiant* at founding (seven staff). |
| **10–30** | Discipline leads emerge; a dedicated producer; a technical artist becomes affordable; audio still contract. |
| **50–150** | Full discipline specialisation; separate design sub-disciplines; a tools team; internal QA. |
| **150–800+** | Multiple sub-teams per discipline; a dedicated engine team; external co-development studios; a production organisation with its own hierarchy. Rockstar reported **over 2,000 employees as of 2018**. |
| **Support model** | Very large projects are increasingly co-developed across a network of studios and outsourcing vendors — art outsourcing, QA outsourcing, and full co-dev partners. |

---

## Sources

- [Arts and Design Occupations](https://www.bls.gov/ooh/arts-and-design/home.htm) — US Bureau of Labor Statistics
- [Graphic Designers](https://www.bls.gov/ooh/arts-and-design/graphic-designers.htm) — US Bureau of Labor Statistics
- [Software Developers, QA Analysts, and Testers](https://www.bls.gov/ooh/computer-and-information-technology/software-developers.htm) — US Bureau of Labor Statistics
- [Web Developers and Digital Designers](https://www.bls.gov/ooh/computer-and-information-technology/web-developers.htm) — US Bureau of Labor Statistics
- [Writers and Authors](https://www.bls.gov/ooh/media-and-communication/writers-and-authors.htm) — US Bureau of Labor Statistics
- [Level design](https://en.wikipedia.org/wiki/Level_design) — Wikipedia
- [2023–2025 video game industry layoffs](https://en.wikipedia.org/wiki/2023%E2%80%932025_video_game_industry_layoffs) — Wikipedia
- [Rockstar Games](https://en.wikipedia.org/wiki/Rockstar_Games) — Wikipedia (headcount)
- [Supergiant Games](https://en.wikipedia.org/wiki/Supergiant_Games) — Wikipedia (team size)

## Open questions

- **No games-specific salary survey was verified.** Attempts to fetch the Skillsearch Games & Interactive salary survey failed (404). Every band marked `needs-verification` above needs a figure from a real survey — candidates to try: Skillsearch's annual survey, the Game Developer Collective salary survey, GDC State of the Industry, Hays and Amiqus UK reports, and Levels.fyi for the large public companies.
- BLS "special effects artists and animators" spans film, TV, games and advertising, and does not separate games; the US$99,800 median is therefore an imprecise proxy for every art role above.
- The claim that games programming pays below general software for equivalent skill is a widely reported industry norm but was not verified against a dataset here.
- Games QA pay relative to the BLS QA-analyst median is asserted from industry reporting, not from a verified dataset.
- No non-US salary anchors were obtained. UK, Canadian, EU, and **[ZA]** South African figures are entirely absent and would materially improve this file.

