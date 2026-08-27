---
id: blender.resources
title: Blender resources, documentation and learning register
domain: software_blender
tags: [blender, documentation, manual, python-api, training, youtube, forums, stackexchange, books, assets, licences]
jurisdiction: global
status: stable
confidence: high
updated: 2026-08-25
applies_to: "Blender 5.2 LTS (docs.blender.org/latest tracks the current release)"
unit_system: metric
sources:
  - {title: "Blender Manual", url: "https://docs.blender.org/manual/en/latest/index.html", publisher: "Blender Foundation", accessed: 2026-08-25}
  - {title: "Blender Python API Reference", url: "https://docs.blender.org/api/current/index.html", publisher: "Blender Foundation", accessed: 2026-08-25}
  - {title: "Blender Developer Documentation", url: "https://developer.blender.org/docs/", publisher: "Blender Foundation", accessed: 2026-08-25}
  - {title: "Blender Studio", url: "https://studio.blender.org/training/", publisher: "Blender Studio", accessed: 2026-08-25}
  - {title: "Blender Artists forum", url: "https://blenderartists.org/", publisher: "Blender Artists", accessed: 2026-08-25}
  - {title: "Blender Stack Exchange", url: "https://blender.stackexchange.com/", publisher: "Stack Exchange", accessed: 2026-08-25}
  - {title: "The Blender Python API — Chris Conlan", url: "https://link.springer.com/book/10.1007/978-1-4842-2802-9", publisher: "Apress", accessed: 2026-08-25}
  - {title: "Poly Haven licence", url: "https://polyhaven.com/license", publisher: "Poly Haven", accessed: 2026-08-25}
related: [blender.overview, blender.python_api, blender.addons_architecture]
---

# Blender resources, documentation and learning register

**Summary.** Every URL in this file was requested on 2026-08-25 and returned HTTP 200 unless a status is noted against it. The register is ordered by usefulness for an agent-driven architectural and joinery workflow: primary documentation first (because it is the only source you should ever quote an operator name from), then training, then community, then assets. Where a resource's licence matters for commercial client work in Namibia, it is stated.

## Key facts

| Resource | URL | Note |
|---|---|---|
| Blender Manual (current) | https://docs.blender.org/manual/en/latest/ | Tracks the latest release (5.2 LTS) |
| Python API Reference (current) | https://docs.blender.org/api/current/ | Version-matched to the manual |
| Developer documentation | https://developer.blender.org/docs/ | Release notes, build instructions, module docs |
| Downloads and release notes | https://www.blender.org/download/ | Also `/download/lts/` and `/download/releases/` |
| Extensions platform | https://extensions.blender.org/ | Official add-on repository since 4.2 |
| Blender Studio | https://studio.blender.org/ | Training and production files, €11.50/month |
| Blender Artists | https://blenderartists.org/ | The main community forum |
| Blender Stack Exchange | https://blender.stackexchange.com/ | Q&A; the best source for scripting answers |
| DevTalk | https://devtalk.blender.org/ | Developer-facing discussion, add-on releases |
| Poly Haven | https://polyhaven.com/ | **CC0** HDRIs, textures, models |
| ambientCG | https://ambientcg.com/ | **CC0** textures and HDRIs |
| BlenderKit | https://www.blenderkit.com/ | Mixed free/paid; **check the per-asset licence** |
| Bonsai docs | https://docs.bonsaibim.org/ | IFC in Blender |
| projects.blender.org | https://projects.blender.org/ | Source and issue tracker — **returned HTTP 403 to an automated request**; works in a normal browser |

## Primary documentation — use this, not memory

### The Blender Manual

**https://docs.blender.org/manual/en/latest/**

The authoritative description of every panel, tool, modifier and node. Two properties make it the right first stop for an agent:

1. Every documented property carries the RNA reference label it maps to (`bpy.types.SolidifyModifier.thickness`, `bpy.ops.wm.obj_import`), so the manual doubles as a name lookup for scripting.
2. Version-pinned URLs exist: swap `latest` for `5.2`, `4.5` or `dev` (`https://docs.blender.org/manual/en/4.5/`) to read the docs for a specific build.

Sections that carry this domain:

| Topic | Path under `/manual/en/latest/` |
|---|---|
| Units and scene properties | `scene_layout/scene/properties.html` |
| Modifiers (all) | `modeling/modifiers/index.html` |
| Geometry Nodes (all) | `modeling/geometry_nodes/index.html` |
| Attributes reference | `modeling/geometry_nodes/attributes_reference.html` |
| Snapping and the transform modal map | `modeling/transform/modal_map.html` |
| Mesh analysis (fabrication checks) | `modeling/meshes/mesh_analysis.html` |
| UV editing | `modeling/meshes/uv/index.html` |
| Principled BSDF | `render/shader_nodes/shader/principled.html` |
| Colour management | `render/color_management/index.html` |
| Cycles GPU rendering | `render/cycles/gpu_rendering.html` |
| Cycles sampling | `render/cycles/render_settings/sampling.html` |
| EEVEE raytracing | `render/eevee/render_settings/raytracing.html` |
| Light objects and power | `render/lights/light_object.html` |
| Cameras | `render/cameras.html` |
| Import/export (core formats) | `files/import_export/index.html` |
| Import/export (add-on formats) | `addons/import_export/index.html` |
| Asset browser | `editors/asset_browser.html` |
| Asset libraries | `files/asset_libraries/index.html` |
| Command-line arguments | `advanced/command_line/arguments.html` |
| Extension arguments | `advanced/command_line/extension_arguments.html` |
| Creating extensions | `advanced/extensions/getting_started.html` |
| Python wheels in extensions | `advanced/extensions/python_wheels.html` |
| Deploying Blender in production | `advanced/deploying_blender.html` |

> The manual pages have a very long navigation sidebar. Automated fetchers frequently return only the navigation and no body. If a fetch comes back as a table of contents, use a locally bundled documentation set (several Blender MCP servers ship version-matched manual and API bundles with full-text search) or open the page in a browser.

### The Python API Reference

**https://docs.blender.org/api/current/**

Generated from the running build, so it is exact for that version. The pages that repay reading in full:

- `info_quickstart.html` — the ten-minute orientation.
- `info_overview.html` — how `bpy` relates to Blender's internals.
- `info_gotchas.html` and `info_gotchas_operators.html` — **read these before writing anything non-trivial.** The operator gotchas page explains why polls fail and how to diagnose them.
- `bpy.ops.html` — operators and the context-override contract.
- `bpy.types.Context.html` — `temp_override` and `logging_set`.
- `bpy.types.Mesh.html` — `from_pydata`, `validate`.
- `bmesh.ops.html` — every bmesh operator with its full signature.
- `mathutils.html` — `Vector`, `Matrix`, `Euler`, `Quaternion`, `Color`.
- `bpy.props.html` — property definitions for add-ons.
- `bpy.types.NodeTreeInterface.html` — node group sockets from Python.

Version-pinned equivalents exist at `https://docs.blender.org/api/5.2/` and so on.

### Developer documentation and release notes

**https://developer.blender.org/docs/**

Release notes per version, including **Python API breaking changes** — the page to read before upgrading a working automation stack across a major version. Source and issues live at **https://projects.blender.org/** (returned 403 to an automated request in this pass; open it in a browser).

## Training

### Blender Studio — https://studio.blender.org/training/

The Blender Foundation's own animation studio publishes courses, documentation, production lessons and workshops, plus the complete production files from its open movies. Subscription **€11.50/month** for an individual; team subscriptions from €500/month. Categories relevant here: Geometry Nodes, Lighting, Rendering, Shading. As of this survey the featured courses include *Customizing Material Assets* (which introduces the new 5.2 material assets and covers shader-node technique) and *3D Printing with Blender*.

The subscription funds Blender development, which is a reasonable secondary argument for it. **The licence on the downloadable production files is not stated on the welcome page — check each asset's own page before using one in paid client work.**

### CG Cookie — https://cgcookie.com/ (returned HTTP 403 to an automated request; opens normally in a browser)

Long-running paid Blender training with a structured curriculum and exercises. Free tier available. Its YouTube channel is **https://www.youtube.com/@cg_cookie**.

## YouTube channels

All handles below were checked and resolve (a non-existent handle returns 404, so a 200 confirms the channel exists). Content descriptions are from the channel's own about text where it was retrievable.

| Channel | Handle | Why |
|---|---|---|
| **Blender (official)** | https://www.youtube.com/@BlenderOfficial | Release videos, conference talks, official demos |
| **Blender Studio** | https://www.youtube.com/@BlenderStudio | Production technique from the Foundation's own studio |
| **Erindale** | https://www.youtube.com/@Erindale | **The** Geometry Nodes channel. Self-described: "a huge Blender nerd… teaching Blender and sharing proceduralism." Covers procedural generation, shader nodes, parametric design and architectural visualisation. Founded @nodegroup. |
| **The CG Essentials** | https://www.youtube.com/@TheCGEssentials | Run by Justin; short, practical Blender tips and tutorials for beginners and experienced users, heavy on modelling technique. A good archviz-adjacent source. |
| **Curtis Holt** | https://www.youtube.com/@CurtisHolt | 3D artist and software developer; geometry nodes, motion graphics, VFX, and Blender **coding** — the closest thing to a scripting channel |
| **Blender Guru** (Andrew Price) | https://www.youtube.com/@blenderguru | The Donut series is still the best zero-to-competent path; also strong on lighting and material realism |
| **Grant Abbitt** | https://www.youtube.com/@grabbitt | Patient, structured fundamentals |
| **CG Cookie** | https://www.youtube.com/@cg_cookie | Free companion content to the paid courses |
| **Josh Gambrell** | https://www.youtube.com/@JoshGambrell | Hard-surface modelling — directly transferable to ironmongery, fittings and machined joinery detail |
| **Blender Bros** | https://www.youtube.com/@Blenderbros | Hard-surface workflow (the Hard Ops/Boxcutter school) |
| **Polyfjord** | https://www.youtube.com/@polyfjord | Procedural and simulation technique, unusually clear |
| **Ducky 3D** | https://www.youtube.com/@TheDucky3D | Procedural materials and shader technique |
| **Ian Hubert** | https://www.youtube.com/@ianhubert2 | "Lazy tutorials" — one-minute, extremely high-value environment and set-extension tricks |
| **Derek Elliott** | https://www.youtube.com/@DerekElliott | Product-style modelling and rendering; the right register for a furniture piece |

For architectural visualisation specifically, the honest position is that the strongest material is not on any single channel: it is Erindale for the procedural side, Blender Guru for lighting and realism, and the manual for everything dimensional. Channels branded "archviz" vary enormously in rigour, and many teach habits (unapplied scale, no unit setup, decorative rather than dimensional modelling) that are actively harmful for a project that must be built.

## Forums and Q&A

### Blender Stack Exchange — https://blender.stackexchange.com/

**The single most useful community resource for this domain.** Strict Q&A format, high signal, heavily used by the Python API community. When you need to know why an operator fails, how to address a geometry-node socket from Python, or what a modifier property is called, this is where the answer already exists. Search it before asking anything.

### Blender Artists — https://blenderartists.org/

The long-established general forum: work-in-progress critique, add-on release threads, jobs, and the *Blender Tests* and *Coding* sections. Slower and more conversational than Stack Exchange; better for "is this a good way to approach X" than for "why does this line fail".

### DevTalk — https://devtalk.blender.org/

Developer-facing. Add-on authors announce releases here, module teams post design documents, and the Python API changes get discussed before they ship. Worth watching if you maintain automation across versions.

### Bonsai / IfcOpenShell community

Documentation at **https://docs.bonsaibim.org/**; the project links to its own community channels from **https://bonsaibim.org/**. For IFC questions this is the only place with real depth.

## Books

Books date faster than Blender releases, so treat all of them as conceptual rather than as reference.

- **Chris Conlan, *The Blender Python API: Precision 3D Modeling and Add-on Development*, Apress, 2017.** ISBN 978-1-4842-2801-2 (softcover), 978-1-4842-2802-9 (eBook). https://link.springer.com/book/10.1007/978-1-4842-2802-9 — **verified**. Written for Blender 2.7x, so the specific API calls are dated, but the structural material (how add-ons register, how to think about `bpy.data` vs operators, how to build precision geometry from code) is the best treatment of this subject in book form and maps directly onto the approach in file `06`.
- **John M. Blain, *The Complete Guide to Blender Graphics: Computer Modeling & Animation*, CRC Press / Routledge.** Runs to many editions tracking the current Blender release; a comprehensive general reference. Routledge's site blocks automated requests, so the **current edition number, year and ISBN are unverified** here — check the publisher's catalogue.
- Packt publishes a rolling *Blender 3D by Example* / *Blender for Architecture*-style list. Their product pages returned HTTP 403 to automated requests; **titles, editions and ISBNs are unverified** and should be checked before purchase.

For the architectural and joinery content itself, the reading lists in domains `01_architecture` and `06_joinery_and_woodwork` matter far more than any Blender book. Blender is the instrument; the discipline is elsewhere.

## Assets and textures, with licences

| Source | URL | Licence | Notes |
|---|---|---|---|
| **Poly Haven** | https://polyhaven.com/ · licence at https://polyhaven.com/license | **CC0** | Any purpose including commercial, redistributable, **no attribution required**. Site logos, promotional renders and copy remain copyrighted. HDRIs, PBR textures, models. |
| **ambientCG** | https://ambientcg.com/ | **CC0** | Textures to 8K, photogrammetry materials, HDRIs, Substance source files. Personal and commercial use, redistribution permitted. |
| **Blender Essentials** | bundled with Blender; extended online from 5.2 | Ships with Blender | Parametric materials, compositing effects, HDR backgrounds, downloaded on demand |
| **Blender Studio assets** | https://studio.blender.org/ | Subscription; **per-asset licence not stated on the welcome page** | Verify before commercial use |
| **BlenderKit** | https://www.blenderkit.com/ | Mixed — free and paid, **per-asset** | Has an in-Blender add-on. Always check the individual asset's licence; "free" is not the same as CC0. |

> ⚠️ For a paid Namibian residential project, only use assets whose licence explicitly permits commercial use and, ideally, redistribution — because the model file you hand to a client *is* a redistribution. CC0 is the only licence that removes all doubt. Record the source and licence of every downloaded asset in the project folder; a `LICENCES.md` next to the textures costs nothing and settles arguments later.

## A minimum reading order for this domain

1. Manual ▸ *Getting Started* and *Scene Layout* — 1 hour.
2. Manual ▸ *Modeling ▸ Modifiers* — skim all, read Array, Mirror, Solidify, Bevel, Boolean properly.
3. API ▸ `info_quickstart`, `info_gotchas`, `info_gotchas_operators` — 1 hour, and it will save ten.
4. Manual ▸ *Geometry Nodes ▸ Fields* and *Attributes*, then build the parametric wall from file `03`.
5. Erindale's geometry-nodes playlist, selectively.
6. Manual ▸ *Render ▸ Color Management* and *Cycles ▸ Sampling*.
7. This domain's file `06`, and then write the wardrobe script yourself rather than pasting it.

## Sources

- [Blender Manual](https://docs.blender.org/manual/en/latest/index.html) — HTTP 200, accessed 2026-08-25
- [Blender Python API Reference](https://docs.blender.org/api/current/index.html) — HTTP 200, accessed 2026-08-25
- [Blender Developer Documentation](https://developer.blender.org/docs/) — HTTP 200, accessed 2026-08-25
- [blender.org](https://www.blender.org/) — HTTP 200, accessed 2026-08-25
- [Blender Extensions platform](https://extensions.blender.org/) — HTTP 200, accessed 2026-08-25
- [Blender Studio training](https://studio.blender.org/training/) — HTTP 200, accessed 2026-08-25
- [Blender Artists](https://blenderartists.org/) — HTTP 200, accessed 2026-08-25
- [Blender Stack Exchange](https://blender.stackexchange.com/) — HTTP 200, accessed 2026-08-25
- [DevTalk](https://devtalk.blender.org/) — HTTP 200, accessed 2026-08-25
- [Poly Haven](https://polyhaven.com/) and [its licence page](https://polyhaven.com/license) — accessed 2026-08-25
- [ambientCG](https://ambientcg.com/) — accessed 2026-08-25
- [BlenderKit](https://www.blenderkit.com/) — HTTP 200, accessed 2026-08-25
- [Bonsai documentation](https://docs.bonsaibim.org/) — accessed 2026-08-25
- [Chris Conlan, *The Blender Python API*, Apress 2017](https://link.springer.com/book/10.1007/978-1-4842-2802-9) — accessed 2026-08-25
- YouTube handles checked 2026-08-25 (a non-existent handle returns 404; all listed handles returned 200): [@BlenderOfficial](https://www.youtube.com/@BlenderOfficial), [@BlenderStudio](https://www.youtube.com/@BlenderStudio), [@Erindale](https://www.youtube.com/@Erindale), [@TheCGEssentials](https://www.youtube.com/@TheCGEssentials), [@CurtisHolt](https://www.youtube.com/@CurtisHolt), [@blenderguru](https://www.youtube.com/@blenderguru), [@grabbitt](https://www.youtube.com/@grabbitt), [@cg_cookie](https://www.youtube.com/@cg_cookie), [@JoshGambrell](https://www.youtube.com/@JoshGambrell), [@Blenderbros](https://www.youtube.com/@Blenderbros), [@polyfjord](https://www.youtube.com/@polyfjord), [@TheDucky3D](https://www.youtube.com/@TheDucky3D), [@ianhubert2](https://www.youtube.com/@ianhubert2), [@DerekElliott](https://www.youtube.com/@DerekElliott)

## Open questions

- `https://projects.blender.org/` and `https://cgcookie.com/` both returned **HTTP 403** to automated requests. The sites exist and work in a browser; the status is a bot block, not a dead link.
- Channel subject matter was confirmed from the channel's own about text only for The CG Essentials, Erindale and Curtis Holt. The others are listed from established reputation — **needs-verification** if precise attribution matters.
- Blender Studio's **asset licence** is not stated on its welcome page.
- **Book editions, years and ISBNs for the CRC/Routledge and Packt titles are unverified** because both publishers block automated requests.
- No Blender-specific book aimed squarely at architectural or joinery practice was found and verified in this pass; if one exists, this register misses it.
