# 68 — Mechanical CAD lane: an Autodesk Inventor-class tool, headless first (2026-09-02)

Research of record for **A66** (`partkiln`). Every licence, platform and OCCT
claim below was fetched on 2026-09-02 (URLs inline) or measured on this
machine (tagged `measured 2026-09-02`). The evidence is the seven discovery
reports (E1 integration map, E2 reuse map, E3 conventions, W1 licences, W2
Inventor parity, W3 OCCT facts, W4 prior art), the critic's memo, the design
synthesis and three adversarial refuter verdicts run against the installed
OCP 7.9.3 and the tree — all copied under `68-evidence/` with the probe
scripts and the P0a measurement log. `CLAUDE_A66_SCRIPT.md` is the plan of
record; §8 summarises its design and cites it rather than restating it.
Claims carried from earlier TEE research are marked `(doc NN)`.

## 1. The parity target — what Inventor actually is

One loop, repeated: **sketch (constrained, dimensioned) → features → part
(feature tree + parameters) → assembly (mates, joints, DOF, interference,
BOM) → drawing (views, dimensions read back from the model, hole table, parts
list) → sheet-metal flat pattern → export.** Everything else is decoration on
that loop. Inventory from the 2026 help (W2; autodesk.com sells **Inventor
2027** as of 2026-09-02, the help mirror read is 2026). URL shorthand:
`H26/` = `https://help.autodesk.com/cloudhelp/2026/ENU/Inventor-Help/files/`,
`IL26/` = `…/2026/ENU/Inventor-iLogic/files/`, `API26/` =
`…/2026/ENU/Inventor-API/files/`, `WN26/` = `…/2026/ENU/Inventor-WhatsNew/files/`,
`DA/` = `https://aps.autodesk.com/en/docs/design-automation/v3/`.

| Group | Capability (condensed) | Source pages |
| --- | --- | --- |
| A. Sketching | 2D sketch on a plane and 3D sketch; twelve geometric constraints (Coincident, Collinear, Concentric, Fix, Parallel, Perpendicular, Horizontal, Vertical, Equal, Smooth G2, Symmetric, Tangent); one General Dimension yielding linear/aligned/angular/radius/diameter by selection, **normal vs driven**; dimension text as expressions creating parameters; model/user/reference/linked parameters with units and multi-value lists; sketch blocks with flexible instances; 3D curves (helix, curve on face, silhouette, intersection, project) | `H26/GUID-97C8CDC5-AAAD-4A6F-BB84-24DB5C90C7A3.htm`, `GUID-A85A7A30-7D81-4C75-8769-CAD034EEA930`, `GUID-026FE8D3-AFBB-4834-BC18-73D9CFF78185`, `GUID-595F9D8E-9EEA-4446-91AB-830E5BAE548E`, `GUID-D4403D63-95CE-4392-A73E-DBB1B8C8C110`, `GUID-37BA1DCE-6BC4-41CD-A36D-577F31B304FC` |
| B. Part features | Sketched: Extrude, Revolve, Sweep, Loft, Coil, Rib, Emboss, Decal. Placed: Fillet, Chamfer, Hole (Simple / Clearance / Tapped / Taper Tapped; seats None / Counterbore / Spotface / Countersink; termination Distance / Through All / To), Thread (**cosmetic**, driven by a data sheet), Draft, Shell. Split, Combine (join/cut/intersect), multi-body. Patterns Rectangular / Circular / Sketch-Driven / Mirror with suppressed occurrences. Work planes/axes/points. Table-driven families, direct edit, T-spline freeform, model states | `H26/GUID-236B12FC-DC32-4BCA-A53D-FCB17382EEB6`, `GUID-1FE5C77C-167B-4F89-BC39-FBFD7B27C197`, `GUID-94EB6947-0347-4888-870D-4BA22DB144D8`, `GUID-C0848D58-12CB-4605-8165-0836232927F0`, `GUID-349C84EE-2D24-4DFC-A239-AFD55E5441AD`, `GUID-9B3D1B72-340A-4F3E-9AD1-80E6DDD91ED2`, `GUID-045A1EA5-DCEF-4998-B832-DB2B2C8CF7F5`, `GUID-1B294EE9-07B9-4F25-A73E-2B4C4FF751A6`, `GUID-3C3258FE-E5B2-4219-BE90-BD8011580855`, `GUID-DC6E4550-B2C1-4F6F-BAC3-66C34EA49A6F`, `GUID-8E771DBE-1107-4AE8-BE3E-AF3A7977F3C6` |
| C. Assembly | Constraints Mate/Flush, Angle, Tangent, Insert, Symmetry, Motion, Transitional, Constraint Set, with limits. Joints **Rigid 0 / Rotational 1R / Slider 1T / Cylindrical 1T+1R / Planar 2T+1R / Ball 3R**. DOF display. Analyze Interference → volume + centroid. BOM Model Data / Structured / Parts Only with virtual components. Frame Generator, Tube & Pipe, Bolted Connection, Design Accelerator, iAssemblies, Presentations, Cable & Harness | `H26/GUID-F3831D6A-EC93-403E-89D2-813DA374EF0B`, `GUID-6AA68E8F-7C97-4806-8483-3941DE915E70`, `GUID-CF4462AF-CEC6-4B8B-8F86-72D9AC9A3574`, `GUID-33B4E343-12DF-48F0-8E00-A72DDFDBA778`, `GUID-6C58657F-C902-433F-9AA6-22A2ACA09F16`, `GUID-953F560A-C2D3-4031-8348-762054C7C779`, `GUID-4B3A972D-F41B-4206-B6CE-420003B455FE`, `GUID-3A51B44B-7C58-44F2-A608-3932A9F787E7`, `GUID-24104648-BE41-49C7-9DD0-1AF2BAFC102E`, `GUID-6E529299-CAB9-4F5C-B100-7901D877B83F`, `GUID-2A480981-2E53-4408-BFA9-290C14F03C95`, `GUID-D90EF17B-D6CD-4782-B528-7B7F3F3CC7F5` |
| D. Drawings | Views Base / Projected / Auxiliary / Section / Detail / Overlay / Draft / Broken / Break Out / Slice. Dimensions General / Baseline / Ordinate / Retrieved; hole, thread, chamfer and bend notes; GD&T symbols; balloons; parts lists; hole / bend / revision tables. Templates `.idw`/`.dwg`. Drafting standards ANSI, BSI, DIN, GB, GOST, ISO, JIS; first vs third angle set on the standard. Export DWG, DXF, PDF, 3D PDF, DWF, raster | `H26/GUID-C53DAB48-BA5F-4377-842D-BB8F3E5962A0`, `GUID-67CAF102-A3FF-41D3-B842-194A089287FE`, `GUID-CF762D0C-A1F0-4D2C-8727-EB84A573E10F`, `GUID-4E9E529B-DDDA-4DFE-9F9F-2715D8F09E1B`, `GUID-47DEB3A8-4C02-4FA3-9C3E-F0FF11F93395`, `GUID-6450DA22-2432-4C40-B9D0-16EB44B340A5`, `GUID-53853AEB-F2BD-4ACF-BD90-6EBCE8034CAB`, `GUID-E5F37303-F3F8-4000-958F-9294D6A6807F`, `GUID-08D6DD13-3066-4210-9F19-5F7E8DB8AD5D` |
| E. Sheet metal | Face, Flange, Contour Flange, Contour Roll, Lofted Flange, Hem, Fold, Bend, Cut, Corner Seam / Round / Chamfer, Punch Tool, Rip, Unfold / Refold, Flat Pattern (bend lines, punch marks, A-side, DXF with layers). Unfold rule: K-factor, bend table, or custom equation. Sheet Metal Rule: thickness, material, relief, bend radius, transitions | `H26/GUID-E59E4255-1802-49B1-92B8-9369582AECD2`, `GUID-FB7A33B7-0914-4C41-A62C-4D363B67A30C`, `TO-CREATE-A-SHEET-METAL-CONTOUR-FLANGE.htm`, `GUID-1B336854-4ED3-4C32-ADCB-E7A407485D80`, `GUID-4141CA32-0DCE-4806-AE73-EF9CD97B0206`, `GUID-D186BB03-6995-46FA-B73F-575A45F2D370`, `GUID-D1EBE010-86D3-49CC-88B3-522F9A0CCA3B` |
| F. Automation (the contrast) | iLogic rules = VB.NET in the document; Forms; Event Triggers. The API is COM Automation reached from VBA, add-ins, a standalone EXE, or Apprentice. Apprentice Server: free, UI-less, **read-only** B-Rep. Inventor Server: ships only as the Vault Job Processor engine. Design Automation cloud: `InventorCoreConsole.exe`, a .NET 8 add-in DLL, 900 s default / 43,200 s max per WorkItem, 64 KB payload; $3 (one Flex token) per 12 processing minutes after 300 free minutes a month. Windows 10/11 64-bit only. Autodesk MCP servers exist for Product Help, Fusion and Revit — **none for Inventor**; the 2027 Autodesk Assistant is an in-app panel | `IL26/GUID-EF53484C-D750-41F8-9AB1-032B73BB071F`, `IL26/GUID-223E9090-5118-406D-9D80-EC247997A7F4`, `API26/GettingStarted.htm`, `API26/Apprentice_Overview.htm`, Vault-Admin `GUID-CDD7E780-3322-4560-AA31-43025A845824`, Vault-Install `GUID-30A964D6-E937-4271-B6AC-C515D9091DEE`, `DA/reference/cmdLine/cmdLine-inventor`, `DA/developers_guide/restrictions/`, `DA/developers_guide/rate-limits/da-rate-limits`, `DA/developers_guide/engine-lifecycle`, <https://www.autodesk.com/products/autodesk-platform-services/product-details>, <https://www.autodesk.com/blogs/design-and-manufacturing/inventor-on-mac/>, <https://www.autodesk.com/solutions/autodesk-ai/autodesk-mcp-servers>, <https://blog.autodesk.io/from-commands-to-conversations-exploring-autodesk-assistant-in-inventor-2027/> |
| G. Simulation and other — out of scope | Stress Analysis, Dynamic Simulation, Inventor Nastran, Inventor CAM, Mold Design, frame analysis | `H26/GUID-61F01A5D-7E54-45A1-9698-7BB11F0AEE94`, `H26/GET-STARTED-W-DYNSIM.htm`, `https://help.autodesk.com/cloudhelp/2026/ENU/NINCAD-UsersGuide/files/GUID-C117BC73-CF85-4D12-A8FC-C6345CF21DA6.htm` |
| H. Formats | Native (proprietary): `.ipt .iam .idw/.dwg .ipn .ide .ipj`. Import: STEP AP203E2 / AP214 / **AP242**, IGES, Parasolid, SAT, JT, STL, OBJ, IFC, CATIA, Creo, NX, SolidWorks, Solid Edge, Rhino, Alias, Fusion, DWG/DXF, RVT. Export: STEP AP203E2 / AP214 / AP242, IGES 5.3, Parasolid, SAT, JT, STL, OBJ, **glTF/.glb (export-only)**, USDz (export-only), IFC, QIF, DWG, DXF, PDF, 3D PDF, DWF, raster. Absent: **3MF**, FBX, glTF import | `H26/GUID-AF41FA87-7588-4698-9C41-756A01EBE7F4` (2026 translator table), `GUID-7CF00AFC-D40C-4FFC-B781-338AE2476527`, `GUID-4B7BF20E-AB83-4C85-9EC6-74ACA18EFF43`, `GUID-08D6DD13-3066-4210-9F19-5F7E8DB8AD5D`, <https://www.autodesk.com/support/technical/article/caas/sfdcarticles/sfdcarticles/Export-a-part-as-3MF-file-format-in-Inventor.html> |

**The gap worth building into.** In Inventor the GUI is the product and
every headless route is a derivative of it: (1) every write path is a COM
client of a running, licensed Inventor on Windows — no macOS, no Linux
(`API26/GettingStarted.htm`; Autodesk's own blog on Inventor and the Mac);
(2) local headless is read-only (Apprentice) or licence-bound (Inventor
Server, shipped inside the Vault Job Processor under terms limited to
automating Vault and excluding third-party products); (3) cloud headless is
metered and capped — Design Automation at $3 per 12 processing minutes,
900 s default per WorkItem, a low-privilege Windows sandbox with no Content
Center / Frame Generator / Tube & Pipe / Design Accelerator; (4) the LLM
integration is in-app and 2027-only — the Assistant is enabled by MCP, and
per Autodesk's developer blog it does not yet create or modify geometry,
while the product blog claims it applies changes across components (the two
are cited, not reconciled). Third-party COM wrappers on Windows exist
(`github.com/NeonGlay/inventor-mcp` and others). A kernel whose **primary
surface is the script**, callable from a plain process on any OS, with the
GUI as one more client, is therefore not a clone: it is the inversion of the
incumbent's architecture — the same logic as doc 67 §1 on Marvelous
Designer's in-app, enterprise-tier API. Parity target = the loop above with
A–E as the checklist; F is the contrast; G is out of scope.

**Price.** $2,585/year for one user, paid annually; $216/month billed
monthly on an annual plan; $320 month-to-month
(<https://www.autodesk.com/products/inventor/buy>, 2026-09-02, product
labelled Inventor 2027).

**IP guardrail.** Feature parity is fine; the containers and the chrome are
not. Open interchange only (STEP AP242/AP214/AP203, IGES, BREP, STL/OBJ/
3MF/glTF, DXF/SVG/PDF). Never reverse-engineer `.ipt/.iam/.idw/.ipn/.ide`,
never copy ribbon/browser chrome, never redistribute Autodesk-shipped data
(`Thread.xls`, Content Center libraries, bend tables, templates) — regenerate
from public standards with their own citations. Shipped names carry no
Autodesk mark; the enumerated list the P0b test matches as whole tokens over
package name, tool names, verbs, entity kinds, tool descriptions/tags,
pyproject metadata and `data/manifest.json` (never docs — this document must
name the incumbent) is: `autodesk inventor forge fusion vault nastran anycad
ilogic ipart iassembly ifeature imate apprentice "content center" "design
accelerator"`. **Forge** is on the list because it was Autodesk's developer
platform brand for a decade before becoming Autodesk Platform Services
(APS blog, 2022-11-28) — the refuter struck `forgekiln` from the candidate
names for exactly that reason. The chosen name is `partkiln`, prefix `pk_`,
verified absent from `_FAMILY` and `_EXPLICIT` in `kernel/trust.py`.

## 2. The licence minefield — the finding that matters most

The owner's ruling for this lane (2026-09-02) is **shippable, like
seamkiln**: `partkiln` is MIT, permissive-only in-process, OCCT the one
weak-copyleft dependency, GPL never in-process, enforced by a licence-gate
test. (The critic's first memo item — A45's "just for me" posture in
DECISIONS vs A53's "cannot ship" framing — was put to the owner and closed
that way.) Verified 2026-09-02 against primary sources by W1 and re-checked
through `tee_web_lookup` on PyPI's JSON API:

| Component | Licence (verified) | Verdict |
| --- | --- | --- |
| **OCCT 7.9.3** | LGPL-2.1-only + Open CASCADE exception 1.0 (`OCCT_LGPL_EXCEPTION.txt`) | **the ONE named exception** — dynamically linked via a pip-separate wheel; LGPL text + copyright notice + the exception's "prominent notice in supporting documentation" (OCCT exception text) shipped in `NOTICE` |
| cadquery-ocp / -novtk / -proxy 7.9.3.1.1 | Apache-2.0 binding over the LGPL OCCT dylibs | `[brep]` extra; scanners under-report — OCCT added to NOTICE by hand |
| cadquery 2.8.0 | Apache-2.0, but `__init__ → assembly → occ_impl.solver` does `import casadi` at top level; the installed `occ_impl.shapes` imports `OCP.IVtkOCC` and `occ_impl.assembly` imports `vtkmodules.vtkRenderingCore` eagerly | **banned in-process** (1.16 s warm import, casadi + VTK every time) |
| casadi 3.8.0 | LGPL-3.0-or-later | banned; scipy `least_squares` is the replacement for both solvers |
| nlopt 2.11.0 PyPI wheel | metadata says MIT; built with the luksan directory, which upstream's COPYING makes LGPL-2.1-or-later | banned — and the "effective LGPL" is W1's inference from build flags, moot because it is never used |
| vtk 9.6.2 / 9.7.0 | BSD-3-Clause | clean but ~600 MB; the whole point of the novtk wheel |
| build123d 0.11.1 | Apache-2.0; every Python dependency permissive | not a runtime dependency; its dev-branch pyproject adds **bd_materials** |
| bd_materials 0.2.4 | **no licence anywhere** — PyPI fields null, no `LICENSE` in the repo, GitHub licence API 404 | cannot ship; pin `build123d<0.12` if it is ever declared |
| lib3mf 2.5.0 | BSD-2-Clause (3MF Consortium) | `[threemf]` optional; trimesh writes 3MF without it |
| manifold3d 3.5.2, trimesh 5.x, ezdxf 1.4.4, svgpathtools | Apache-2.0 / MIT / MIT / MIT | core-clean |
| numpy, scipy, sympy, networkx, pint | BSD family (numpy: BSD-3 AND 0BSD AND MIT AND Zlib AND CC0-1.0) | core-clean |
| fpdf2 2.8.8 | LGPL-3.0-only (`license_expression` on PyPI) | `[pdf]` extra only, never core — the same isolation `server/pyproject.toml` and seamkiln already use |
| **py-slvs 1.0.6 / SolveSpace / python-solvespace 3.0.8** | GPL-3.0, **no linking exception** (SolveSpace `COPYING.txt`); GPL-3.0-or-later | never in-process; dev-only oracle from `server/.venv` for P0 row 16 |
| pythonocc-core | LGPL-3.0 | redundant with OCP; banned |
| gmsh 4.15.0 / CalculiX 2.23 | GPL-2.0-or-later | out of process only (FEA is out of scope anyway) |
| FreeCAD 1.1.3 (.app) | LGPL-2.0-or-later library; the app bundles GPL gmsh/ccx, LGPL-3.0-only PySide6, **OCCT 7.8.1** | stays the A37 RPC adapter, never imported |
| FreeCAD SheetMetal 0.8.22 / FastenersWB 0.5.65 | LGPL-2.1-or-later / **GPL-2.0-or-later** (and its `FsData/*.csv`) | scheme may be studied; code and tables never vendored |
| **bd_warehouse data CSVs** | Apache-2.0 (`clearance_hole_sizes.csv` 124 rows `Size,Close,Normal,Loose`; `tap_hole_sizes.csv`; drill sizes; ISO 4762 / 4014 / 4017 / 4032 / 7089 tables) | **the clean standards data**, attribution in NOTICE |
| **threadlib `THREAD_TABLE.scad`** | BSD-3-Clause | the ISO 261 pitch table (converted to CSV, attributed) |
| Wikipedia ISO 262 / bending tables | CC BY-SA 4.0 | formula citations only (share-alike); never a data file |
| BOLTS | GPL-3.0+ overall (bolttools LGPL-2.1+) | never a data source |
| ISO standard texts, handbook tables | proprietary | cite the standard number as authority; never reproduce text |

Sources: <https://raw.githubusercontent.com/Open-Cascade-SAS/OCCT/master/OCCT_LGPL_EXCEPTION.txt>,
<https://pypi.org/pypi/cadquery-ocp/json>, <https://pypi.org/pypi/cadquery-ocp-novtk/json>,
<https://pypi.org/pypi/cadquery/json>, <https://raw.githubusercontent.com/CadQuery/cadquery/master/cadquery/occ_impl/solver.py>,
<https://pypi.org/pypi/casadi/3.8.0/json>, <https://raw.githubusercontent.com/stevengj/nlopt/master/COPYING>,
<https://raw.githubusercontent.com/DanielBok/nlopt-python/master/extensions.py>,
<https://pypi.org/pypi/build123d/json>, <https://pypi.org/pypi/bd-materials/json>,
<https://pypi.org/pypi/py-slvs/json>, <https://raw.githubusercontent.com/solvespace/solvespace/master/COPYING.txt>,
<https://pypi.org/pypi/fpdf2/json>, <https://raw.githubusercontent.com/gumyr/bd_warehouse/main/LICENSE>,
<https://github.com/adrianschlatter/threadlib>, <https://raw.githubusercontent.com/shaise/FreeCAD_FastenersWB/master/package.xml>,
<https://boltsparts.github.io/en/docs/0.4/document/general/licensing.html>.

**The traps, each now a pinned test (P0b):**

1. `import cadquery` loads casadi unconditionally — there is no lazy path;
   an MIT core cannot contain it.
2. **Both OCP wheels ship the top-level `OCP/` package** — 397 (novtk) and
   403 (vtk) `OCP/` entries in the wheel RECORDs (`measured 2026-09-02`,
   `68-evidence/p0a-measure.log`). Co-installing `cadquery-ocp-novtk` into
   `server/.venv` clobbers the VTK wheel already there; `[brep]` accepts
   either carrier by `find_spec("OCP")` and the dev-venv install line omits
   `[brep]`. `KNOWN_PAYLOADS` is keyed on **both** distribution names, with
   `cadquery-ocp-proxy` (pure Python, Apache-2.0) allowlisted, and the live
   carrier is resolved at test time via `packages_distributions()["OCP"]`.
3. py-slvs / SolveSpace are GPL-3.0 with no exception, and TEE already
   imports py-slvs in-process under `[physical]` for its own lanes — three
   positions in the reports (W1 out-of-process, E2 "reuse as-is", the tree
   in-process) resolved by writing an own scipy sketch solver for the lane
   and leaving `physical/sketch.py` where it is.
4. nlopt's MIT label is wrong (luksan); a scanner reading metadata passes
   it. Banned regardless.
5. bd_materials is unlicensed; build123d's next release will require it.
6. Installed metadata is inconsistent (`measured 2026-09-02`): scipy 1.17.1
   carries an Enthought copyright line as `License`, ezdxf 1.4.4 has
   `License=None`, trimesh 5.0.0 says `The MIT License (MIT)`, vtk says `BSD`,
   cadquery-ocp `Apache-2.0` as free text, cadquery `Apache Public License
   2.0`; only numpy, fpdf2, typing_extensions, pyparsing, pypdf and packaging
   carry a `License-Expression`. A literal SPDX match therefore fails the
   core. The gate reads three sources in order — `License-Expression`, the
   Trove classifier map, a free-text alias table — fails only when all three
   are empty, and parses `AND/OR/WITH` with
   `packaging.licenses.canonicalize_license_expression` (packaging 26.3
   accepts `LGPL-2.1-only WITH OCCT-exception-1.0`). seamkiln's gate has no
   allowlist at all (it substring-matches non-commercial markers), so nothing
   there could be copied.
7. FreeCAD Fasteners (GPL-2), BOLTS (GPL-3) and Wikipedia (CC BY-SA) are
   never vendored; `test_data_files_carry_provenance` asserts every data file
   names `source`, `licence` and `retrieved`, and none cites them.
8. Fixture provenance: the Hugging Face card for `BenchCAD/BenchCAD`
   declares `license: cc-by-4.0` (last modified 2026-06-28; read through
   `tee_web_lookup` 2026-09-02) — confirmed at the card, not only in the
   paper. `huggingface/cadgenbench-data` answers HTTP 401 to fetchers, so
   CADGenBench stays OUT until a card can be read; F1–F8 carry the suite.
   Fusion 360 Gallery (non-commercial research only), Text2CAD (CC BY-NC-SA),
   CAD-Recode (CC BY-NC) and GenCAD-Code (no licence) are `BANNED_DATASETS`.
9. MPL-2.0 is **not** on the allowlist: A53 never shipped an MPL dependency
   (CDT was named as a replacement, not declared), so Law 2 — OCCT is the one
   weak-copyleft exception — stays literally true.

**The one-line version:** the two libraries every CadQuery-era tutorial
reaches for — cadquery for modelling, py-slvs for sketches — cannot sit in
an MIT process, one because of what it imports and one because of what it
is; OCCT itself, reached through the Apache-2.0 novtk binding, can.

## 3. OCCT facts that shape the design

W3 read the `V7_9_0` source tree and the installed OCP 7.9.3.1.1 runtime
(`occt3d.com/dev/doc` documents **8.0.1**, not 7.9 — it says the STEP schema
default is AP214CD; the 7.9 runtime says AP214IS). Three refuters then ran
the load-bearing claims against `server/.venv`; every correction below is
now a pinned test in the script. OCCT dates: 7.9.3 2025-12-06, 8.0.0
2026-05-07, 8.0.1 2026-07-30; OCP 8.0.0.x exists on GitHub (2026-08-27) but
not on PyPI; cadquery 2.8 and build123d pin `<8.0`.

1. **STEP schema ordering (`measured 2026-09-02`).**
   `Interface_Static.CVal_s("write.step.schema")` is `''` until
   `STEPControl_Controller.Init_s()`, then `AP214IS`; only `AP203 / AP214CD /
   AP214DIS / AP214IS / AP242DIS` are accepted (`"AP242"` → False). The
   schema is captured at the writer's **first `Transfer`**: set before it →
   `FILE_SCHEMA(('AP242_MANAGED_MODEL_BASED_3D_ENGINEERING_MIM_LF'))`; set
   after it → the file stays `AUTOMOTIVE_DESIGN {1 0 10303 214 …}`; then
   `Model(True)` + re-`Transfer` fixes it. `Model(True)` therefore only
   resets a reused writer — and `STEPCAFControl_Writer` has no `Model` at all
   (reach it through `ChangeWriter()`). `write.step.unit` and
   `xstep.cascade.unit` default to `MM`; `STEPCAFControl_Writer` reads
   `XCAFDoc_LengthUnit` from the document and scales ×1000. F8 (ten named
   parts) writes in 0.15 s and reads back in 0.408 s with 10 products, 1,060
   faces, Σ 5,204,814.21 mm³ and the names intact.
2. **HLR is ten compounds under a named projector.** `HLRBRep_HLRToShape`
   exposes `VCompound`, `Rg1LineVCompound`, `RgNLineVCompound`,
   `OutLineVCompound`, `IsoLineVCompound` and their hidden twins; TechDraw
   extracts all ten. Visible = V + Rg1LineV + OutLineV, hidden = H + Rg1LineH
   + OutLineH (build123d's convention). `Hide()` must be called. F1 measured
   per compound: front `gp_Dir(0,-1,0)` V 4 | H 9 + OutLineH 1; top
   `(0,0,-1)` 5 | 5; right `(1,0,0)` 4 | H 10 + OutLineH 2. No projector
   reproduces the synthesis's "8 visible / 9 hidden". On F1 with all 15
   edges filleted r1 `VCompound` is **not** empty (V 9, Rg1LineV 17 | H 14,
   Rg1LineH 19, OutLineH 3); it was empty only on W3's 120×80×10 plate with
   12 holes and 96 fillets, which is therefore the trap fixture. A renderer
   that reads `VCompound` alone drops the tangent lines. `HLRBRep_PolyAlgo`
   needs the whole shape meshed first (TechDraw's own warning), returns
   polylines, and is **not** faster: 105 ms vs 91 ms exact on 530 faces, with
   26,520 hidden fragments against 2,520 edges. Exact HLR is the only path.
   Section views: `BRepAlgoAPI_Section` returns only edges; a hatched face is
   a half-space prism cut then HLR, TechDraw's method.
3. **No glue on cuts.** F5 (220×220×12 plate, 100 × Ø8): 100 sequential
   `BRepAlgoAPI_Cut` 0.46–0.52 s; ONE n-ary cut via `SetArguments` /
   `SetTools` (`SetRunParallel(True)`) 0.09–0.10 s, identical topology and
   volume 520,481.421 mm³. `SetGlue(BOPAlgo_GlueShift)` on the same cut ran
   in 0.014 s and returned **the uncut plate** — 580,800 mm³, 6 faces — with
   `IsDone() == True`. Glue modes are for touching copies (pattern fuses),
   never intersecting cuts; `BRepAlgoAPI_Cut` binds no `HasErrors`. This is
   Law 11 (a boolean that changes no topology is a failed boolean) with its
   evidence. `SimplifyResult()` is a no-op on F5 but F2's 13-face pin depends
   on `ShapeUpgrade_UnifySameDomain` (raw fuse 11 faces → 8 unified → 9 with
   the fillet → 13 with four holes; 16 without unification).
4. **Counts are unique sub-shapes.** `TopExp_Explorer` visits a shared edge
   once per owning face: F5 624 explorer vs **312** unique
   (`TopExp.MapShapes_s`), F1 30 vs 15, F2 33. The first probe
   (`68-evidence/probe-brep_probe.py`) used the explorer; Law 20 came from it.
5. **The history API is narrower than the docs suggest.** `BRepTools_History`
   binds `Generated / Modified / IsRemoved / Merge / AddGenerated /
   AddModified / Remove / IsSupportedType_s` — no `IsDeleted` — and only the
   no-arg constructor; supported types vertex / edge / face / solid (wire,
   shell, compound False). `History()` exists only on `BRepAlgoAPI_Cut /
   Fuse / Common / Splitter`, `BRepFeat_MakeCylindricalHole` and
   `ShapeUpgrade_UnifySameDomain`; `MakePrism / MakeRevol / MakeFillet /
   MakeChamfer / DraftAngle / MakePipeShell / ThruSections / MakeThickSolid /
   MakeDPrism / Transform` have per-sub-shape `Generated(s) / Modified(s) /
   IsDeleted(s)` only. So every non-boolean feature builds its history by
   hand and merges the boolean's and UnifySameDomain's. Measured on F1's
   fillet: `Generated` per vertical edge `[1, 1, 1, 1, 0]`, `Modified` per
   face `[1, 1, 1, 1, 1, 1, 0]` (the cylinder wall untouched), faces 7 → 11.
   OCAF `TNaming` is bound but not adopted — it drags `TDocStd` persistence
   for nothing the history maps do not give.
6. **Taper.** `BRepFeat_MakeDPrism` needs an existing base solid and one of
   its faces, so it cannot create a part's first body; `LocOpe_DPrism(face,
   height, angle)` does (`measured 2026-09-02`: 100×60 face, height 10, +3° →
   59,085.191 mm³ / 6 faces, top centroid z 9.99 because height is measured
   along the drafted wall; −3° → 60,756.864 mm³ / 10 faces including four
   conical corner patches). `BRepFeat_MakeCylindricalHole` has no
   counterbore or countersink (both libraries subtract primitives instead);
   `BRepOffsetAPI_DraftAngle` tapers only planar, cylindrical or conical
   faces; shells go through `MakeThickSolidByJoin`; a fillet that cannot
   build reports `NbFaultyContours` (r = 12 on F1's top-front edge of a 10 mm
   plate → `IsDone() False`, `NbFaultyContours() == 1`).
7. **Seam edges.** `dir=Z` on F1 matches **five** straight edges: the four
   corners and the cylinder's seam (`BRep_Tool.IsClosed_s(edge, face)`).
   OCCT accepts the seam in `BRepFilletAPI_MakeFillet` and silently generates
   nothing for it. Selectors exclude seam edges by default and report the
   exclusion; an edge whose `Generated` is empty is reported `failed`.
8. **No cancellation from Python.** `Message_ProgressIndicator` is abstract
   with no pybind trampoline (subclassing raises "No constructor defined");
   no subclass exists anywhere in `OCP.OCP`; `Message_ProgressRange` exposes
   only `Close / IsActive / More / UserBreak` and a default range is
   inactive. The sidecar deadline plus kill/respawn/replay is the only guard;
   an in-process `LocalKernel` has none, so `job: true` work always runs
   through the sidecar.
9. **glTF needs the unit AND the input coordinate system.** A fresh
   `RWGltf_CafWriter` converter reports `HasInputCS False`, `InputLengthUnit
   -1` (no conversion). `XCAFDoc_DocumentTool.SetLengthUnit_s(doc, 0.001)`
   fixes the scale; `ChangeCoordinateSystemConverter().SetInputCoordinateSystem(RWMesh_CoordinateSystem_Zup)`
   fixes the axis. F1 measured through `tee.assets.gltf.probe`: unit + Z-up
   → `extents_m [0.1, 0.01, 0.06]` / `dims_zup_m [0.1, 0.06, 0.01]` (correct);
   no unit → `[100, 10, 60]` (10 mm = 10 m); unit only → `[0.1, 0.06, 0.01]`
   (lying on its side, which Blender's importer then stands on edge). The
   glTF 2.0 spec is right-handed, +Y up, metres; the writer rotates only when
   told the input is Z-up. seamkiln's "a GLB needs no transform" rule (A65
   Law 17) is correct there only because seamkiln's source frame is already
   Y-up; copied to a Z-up kernel it is the double-convert trap inverted.
10. **Mesh determinism is measured, not documented.** No OCCT statement
    covers `BRepMesh_IncrementalMesh` under `InParallel`; the SHA-256 of all
    nodes and triangles of F5 at 0.05 and 0.3 mm was identical for serial and
    three parallel runs (`115a72d6f9dbe8cf`, `b999ee27d66f1f33`) — pinned by
    a test, never assumed. 7.9 defaults: `Deflection 0.001`, `Angle 0.5`,
    `Relative False`, `InParallel False`; build123d's `tolerance` is a
    **relative** deflection, ours is absolute.
11. **`BRepBndLib.Add_s` is enlarged by tolerances**; `AddOptimal_s` is the
    tight box (build123d defaults to it; cadquery only when `tol` is passed).
12. **`OCP.RWObj` and `OCP.RWPly` are unbound** although `libTKDEOBJ` /
    `libTKDEPLY` ship in the wheel (`ocp.toml` at 7.9.3.1.1 lists neither):
    OBJ and 3MF go through trimesh (5.0.0's `export_3MF` writes
    `unit="millimeter"`, verified). 3MF is not in OCCT at all.
13. **Checkpoints.** `BRepTools.Write_s(shape, path, False, False,
    TopTools_FormatVersion_VERSION_3)` writes the 100-hole plate without
    triangulation in 81 KB, 1.4–3 ms; `Read_s` 1 ms; volume identical
    (`measured 2026-09-02`). The B-rep fingerprint (sorted, rounded per-face
    area + centroid) of the same script was identical in two fresh processes.
14. **IGES is not thread-safe** (OCCT's own guide) — it runs under the
    kernel's one lock.

## 4. Prior art and token pathologies

W4 audited the agent surfaces for CAD in the format of doc 47's Tripo/Meshy
audit (licences re-checked via the GitHub API on 2026-09-02):

| Surface | Tools | Dumps / pixels by default | Ids, diff, checkpoint | Licence | Verdict |
| --- | --- | --- | --- | --- | --- |
| pzfreo/build123d-mcp | 25 (`measure`, `validate`, `clearance`, `interference`, `verify_spec`, `save/restore/diff_snapshot`, `render_view`…) | numbers first, render opt-in; "topology counts unchanged = failed cut" | snapshots; failed code never advances state | Apache-2.0 | **steal** — the closest thing to TEE's shape |
| jdilla1277/agentcad | 11 CLI/MCP (`run`, `measure`, `check-spec`, `diff`…) | structured JSON, `--preview` opt-in | versioned parts, volume diff | Apache-2.0 | steal `check-spec` |
| neka-nat/freecad-mcp | 15 (doc 53 measured) | **every property dumped, screenshot ON by default** | none | MIT | already fronted by TEE (doc 53); text mode 26–38 tok/op |
| KittyCAD/mcp (Zoo) | ~25 `zoo_*` incl. `mock_execute_kcl`, `lint_and_fix_kcl`, `get_sketch_constraint_status` | no; `snapshot` = one JPEG | session; no diff | MIT | steal the pre-flight trio; **avoid** $0.50/min hosted metering of every retry |
| AutodeskFusion360/FusionMCPSample | 3 (`execute_api_script`, `get_screenshot`, `get_api_documentation`) | script + screenshot | none | MIT | Autodesk's own shape = code-exec + docs + pixels |
| faust-machines/fusion360-mcp-server | **89** | targeted | `undo`; one operation per call or the add-in crashes | MIT | avoid |
| fozzfut/FusionMCP · frankhommers/autodesk-fusion-mcp · hedless/onshape-mcp · alisamsam/solidworks-mcp · SolidworksMCP-python | ~80 · 11 · 45 · 22 · 109 | — | timeline-group undo · dotted-path generic call · Onshape deterministic ids · implicit "active sketch" · — | MIT-ish (several with no LICENSE file) | steal the undo group and the ids; avoid the surfaces and implicit state |
| eyfel/mcp-server-solidworks (SolidPilot) | 46 + a feature-graph IR | — | index-based, self-described edit-fragile | **AGPL-3.0** | idea only; never vendor |
| Onshape FeatureScript MCP (PTC Labs, 2026-08-13) | unpublished | — | writes Feature Studios, not Part Studio geometry | app store | the compile→run→errors loop |
| blender-mcp / Blender Lab (docs 03, 47) | 25 / 19 read-only | full `get_scene_info` / summary-first + bundled RST docs | — | MIT / — | avoid / steal read-first + docs |

Vendor reality, 2026-09: Autodesk's Neural CAD is pre-beta and outputs
meshes; the shipped LLM lane is prompt-to-command; no Autodesk-published
Inventor MCP exists. Onshape's AI Advisor cannot see the model; FeatureScript
MCP is its first geometry-affecting lane. Zoo meters by the second.

**What the research says fails (W4 §2).** Text2CAD-Bench: invalidity on its
hardest tier 68–70% for GPT-5.2 and Claude-4.5-Sonnet; sweep, loft and shell
lead the execution failures. BenchCAD: eight failure modes including
spatial-frame errors (extruding from XY when XZ was meant) and roughly 64% of
nominally successful edits silently corrupting unrelated features. CADSmith:
gaps invisible in rendered views that volume/bbox/count checks catch.
ProCAD: invalidity 4.8% → 0.9% when the model clarifies an inconsistent spec
first. CADDesigner: Pass@1 46% with every run "successful"; removing type
annotations 45% → 32%. Embodied CAD: local/global frame mixing on mirrored
features. AssemCAD: phantom bores and all-coincident parts. AgentsCAD:
face ids reallocated after a STEP re-read. TexoCAD's field notes: index-based
sketch constraints trip every model tested. The eight recurring pathologies:
wrong plane/direction, stale selectors after an upstream edit, constraints by
invisible index, booleans that "succeed" with unchanged topology,
sweep/loft/shell misuse, unitless numbers, under-specified prompts, silent
corruption on edit.

**The eleven design rules (W4 §6), each tied to a pathology and to where the
script answers it:** (1) one batch = one ordered feature list, one kernel
transaction, one diff — D5; (2) every entity named at creation, never
addressed by index; selectors are declarative queries re-evaluated at regen —
D6, Law 13; (3) sketches report DOF status and named conflicts, never raw
index constraints — P1; (4) explicit frames and units on every number — D4,
Law 12; (5) numeric assertions are the default evidence, renders opt-in and
last; a no-change boolean is flagged — D7, Law 11; (6) diffs and checkpoints
per batch with edit-impact reporting — D3, Law 14; (7) spec-check before
"done" — `pk_check`; (8) errors are (cause, location, fix) triples and a
failed batch never advances state — D8; (9) pre-flight is free, kernel time
scarce — `pk_lint`; (10) ask only when the spec is inconsistent, otherwise
default and declare — Law 19; (11) progressive disclosure with bundled,
versioned docs. W4's own rule 11 proposed "≤ 6 always-loaded verbs
(`cad_batch` …)"; the critic struck it — TEE's invariant is **17
always-loaded tools and zero new ones**, `cad_` has deliberately no family
row in the trust table, and the long tail is 14 explicit `pk_*` virtual
tools reached through `tee_search_tools`.

## 5. What this machine and this repo already have

`measured 2026-09-02` unless noted. Apple M5 Max, 18 cores, 128 GB, macOS
26.6.2. Four interpreters matter, and only one is right: `server/.venv` =
Python 3.11.15 with `cadquery-ocp 7.9.3.1.1` (the VTK wheel), `cadquery
2.8.0`, `py-slvs 1.0.6`, `ezdxf 1.4.4`, `trimesh 5.0.0`, `scipy 1.17.1`,
`fpdf2 2.8.8`, `vtk 9.6.2`, `packaging 26.3` (numpy 2.4.6 per doc 67,
2026-09-01); `~/TEE/.tee/sidecars/cad/bin/python` = 3.11.15 with the same
OCP wheel (the 1.4 GB A46 sidecar: vtkmodules 607 MB, OCP 234 MB, casadi
161 MB, llvmlite 130 MB — W3 §10); the **Claude Desktop extension venv is
Python 3.13.9 with no `OCP`** (`find_spec("OCP")` is None; `cad_probe`
through the live TEE confirms cadquery absent; it does hold seamkiln); the
default `python3` is **3.14.7 — never build anything with it** (cadquery-ocp
caps `<3.15`; py-slvs has no cp314 wheel). `cadquery-ocp-novtk`, `build123d`
and `lib3mf` are absent from every venv. `import OCP` from the VTK wheel maps
its VTK dylibs but does not import the `vtk` Python package (`vtkmodules`
absent from `sys.modules`; 0.28–1.2 s warm); `import OCP.IVtkOCC` is what
pulls VTK in, and cadquery does that eagerly.

The OCP wheels on PyPI (W1): `cadquery-ocp 7.9.3.1.1` requires
`cadquery-ocp-proxy==7.9.3.1.1` and `vtk==9.6.2`; `cadquery-ocp-novtk
7.9.3.1.1` requires only the proxy; both publish `macosx_11_0_arm64` wheels
for cp310–cp314; nothing 8.x is on PyPI.

**The P0a measurement table** (PROGRESS, 2026-09-02, verbatim). Two fresh
`uv venv --python 3.11` environments, one per wheel, each installed once and
imported four times with `PYTHONDONTWRITEBYTECODE=1`; the 36-class binding
one-liner ran in each (`68-evidence/p0a-measure.sh`, `p0a-measure.log`):

```
                              cadquery-ocp-novtk 7.9.3.1.1   cadquery-ocp 7.9.3.1.1 (vtk)
install (network)             9.9 s                          2.0 s (cached)
site-packages                 223 MB (all of it OCP)         914 MB (OCP 232 MB + vtk)
OCP.cpython-311-darwin.so     144 MB, 0 VTK dylibs linked    145 MB, libTKIVtk + 10 libvtk*
wheel RECORD entries OCP/     397                            403  (both ship top-level OCP/)
import OCP, COLD (run 1)      26.2 s                         38.7 s
import OCP, warm (runs 2-4)   0.29 s                         0.33 s
classes bound                 36/36                          36/36
RSS after import              251 MB                         288 MB
vtkmodules in sys.modules     False                          False
```

Recount while writing this doc (`otool -L` on both scratch venvs,
2026-09-02): `measure.log`'s `vtk_links=1 / 11` counts `otool`'s own first
line, the file path, which contains `venv_novtk` / `venv_vtk`; the real link
lines are **0** for novtk and **10** for the VTK wheel — `libTKIVtk` plus the
nine `libvtk*` dylibs W3 §10 lists (one fewer than the table's "10 libvtk*").

Rows 7–17 from `rows.py` in `server/.venv` (OCP direct; a concurrent
seamkiln test run was contending, so wall times are upper bounds;
`68-evidence/p0a-rows.py`, `p0a-rows.json`):

```
F1 plate 100x60x10 - d10         V 59214.602  faces 7  unique edges 15
F2 bracket (fuse+unify, fillet r6, 4x d6.6)   V 44916.967  faces 13  edges 33  build 0.01 s  fp 8d2f6429c818a423
F5 plate, ONE n-ary cut of 100 holes (no glue, RunParallel)  V 520481.421  faces 106  edges 312  0.103 s
F6 block / pin / d11 interference  30429.204 / 3141.593 / 329.867 mm3
HLR F1 front (0,-1,0)   V 4 + Rg1V 0 + OutV 0 | H 9 + Rg1H 0 + OutH 1 (0.4 ms)
HLR F1 top   (0,0,-1)   V 5 + Rg1V 0 + OutV 0 | H 5 + Rg1H 0 + OutH 0 (0.1 ms)
HLR F1 right (1,0,0)    V 4 + Rg1V 0 + OutV 0 | H 10 + Rg1H 0 + OutH 2 (0.3 ms)
W3 plate 120x80x10, 12x d6, ALL edges filleted r1 (62 faces): front V 9 + Rg1V 17 + OutV 0 | H 91 + Rg1H 63 + OutH 36 (20.3 ms)
5 x F5 stacked (530 faces): exact V 20 + Rg1V 0 + OutV 0 | H 2520 + Rg1H 0 + OutH 500 (90.7 ms)
                                   poly  V 20 + Rg1V 0 + OutV 0 | H 26520 + Rg1H 0 + OutH 500 (105.4 ms)   <- polylines fragment 10x, and it is not faster
STEP default after Init_s          AP214IS
  schema set BEFORE first Transfer -> FILE_SCHEMA(( 'AP242_MANAGED_MODEL_BASED_3D_ENGINEERING_MIM_
  schema set AFTER Transfer         -> FILE_SCHEMA(('AUTOMOTIVE_DESIGN { 1 0 10303 214 1 1 1 1 }'))   (the trap)
  then Model(True) + re-Transfer    -> FILE_SCHEMA(( 'AP242_MANAGED_MODEL_BASED_3D_ENGINEERING_MIM_
F8 = 10 x F5 via STEPCAFControl_Writer with names: write 0.15 s, FILE_SCHEMA(( 'AP242_MANAGED_MODEL_BASED_3D_ENGINEERING_MIM_
  read back via STEPCAFControl_Reader: 0.408 s, products 10, faces 1060, sum V 5204814.21, names ['plate_0', 'plate_1', 'plate_2']...
GLB F1  LengthUnit + Zup input CS   extents_m [0.1, 0.01, 0.06]  dims_zup_m [0.1, 0.06, 0.01]   <- the correct file
GLB F1  no LengthUnit                extents_m [100.0, 10.0, 60.0]                                      <- 10 mm = 10 m
GLB F1  LengthUnit only              extents_m [0.1, 0.06, 0.01]                                      <- lying on its side
History, fillet r2 on F1 dir=Z edges: 5 raw edges (4 corners + the cylinder SEAM); Generated per edge [1, 1, 1, 1, 0] (the seam generates nothing); Modified per face [1, 1, 1, 1, 1, 1, 0] (the cylinder wall untouched); faces after 11
Per-op wall (ms): extrude 0.1  hole x1 1.6  hole x100 n-ary 119.7  fillet 8 2.1  fillet all-W3 7.4  fuse+unify 1.5  HLR F1 0.4  HLR 5xF5 90.7  STEP write F5 13.5  STEP read F5 43.8  GLB F1 1.5  mesh F5 0.05 mm 42.0
```

Earlier the same day, OCP direct in `server/.venv` (PROGRESS A66 header):
box − Ø10 cut + exact `BRepGProp` volume 17 ms; fillet 8 edges 13 ms; STEP
AP242 write/read 13 / 6 ms with the volume identical; mesh + STL 4 ms,
watertight; GLB 7 ms; the 100-hole plate sequential 0.46 s vs n-ary 0.09 s;
`freecadcmd` 1.1.3 module import 0.38 s / 67 MB RSS. Every per-op class is
under 125 ms on these fixtures, so `MAX_BATCH_S` starts at 60 s with the
`job: true` route reserved for real assembly imports and drawings of hundreds
of faces.

`shapely` + `ezdxf` + `trimesh` + `scipy` + `numpy` were already the
licence-audited base of seamkiln (doc 67 §6); this lane adds the OCP novtk
wheel in its own sidecar venv and nothing else to the core.

## 6. TEE-side reuse map (why this belongs here)

E2 mapped every need to code already in the tree (`file:line` in the
evidence copy):

| Need | Existing TEE lane | How it is reused |
| --- | --- | --- |
| declarative part ops, one round trip, zero new always-loaded tools | `tee_batch` + the `Adapter` protocol; seamkiln's `adapters/seamkiln/` (14 `sk_*` tools, metadata-only registration at `app.py:204-211`) | the same shape: `_translate` wire op → kernel command, `_record` → `Diff` **with `upserts`** (or `SceneCache` goes blind) |
| feature tree, replay, fingerprint | `seamkiln/session.py` `Command` / `history` / `script()` / `replay()` / `fingerprint()` / closed `_VERBS` | `Document` is the same object with parts, assemblies and drawings |
| "what changed" | `tee_diff`, the diff discipline, `SceneCache` net semantics | edit impact = `changed / unchanged / failed` per downstream feature |
| checkpoint / rollback | `checkpoints.py` (`_KEEP = 20`, `discard_snapshot` hook) + seamkiln's replay-the-script law | script + `.brep` cache; mismatch → replay |
| a persistent kernel process | `gateway/wire.py:32-225` (NDJSON over `Popen(bufsize=0)`, `select()` 1 s ticks, `_dead()` naming the exit code) + `fleet/_cad_worker.py` (fd-swap of stdout, imports nothing from `tee`) + `fleet/cad.py:206` sidecar discovery + `purge.py:78-88` (sidecars are a capability, not garbage) | `SidecarKernel`; the one-shot `_cad_worker` re-imports OCP per call and is **not** reused as written |
| long work | `kernel/jobs.py` (`submit`, `qos="interactive"`, taint snapshot across the thread hop; no manager timeout) | the warm-up job (Law 17) and `job: true` exports/drawings/replays |
| trust | `kernel/trust.py:179-188` — the `cad_`/`trade_` rule: no family row, every writer tabled | 14 explicit `_EXPLICIT` rows; an untabled tool is a startup crash (`registry.py:86-91`) |
| cross-kernel read-back | `fleet/cad.py cad_measure` (STEP/BREP via OCCT, STL in pure Python) | the acceptance oracle; routing it through `pk_measure` is a named gap |
| 2D constraints | `physical/sketch.py` (py-slvs, `[physical]`) | **not** reused: GPL and a metres contract; dev-only oracle for P0 row 16 |
| drawing read-back law | `adapters/freecad/tools.py:75-79` (a dimension created in the same dispatch as its view caches 0.0 — touch, recompute, read) | Law 15: a dimension is read from the model, `agree` asserted |
| sheets and tech docs | `pdf_compose` (A48; fpdf2 2.8.8 already exposes `draw_path/line/polygon` and `fpdf.svg.SVGObject` — no vector block yet) | `partkiln[pdf]` writes its own sheets; a `vector` block for `pdf_compose` is a named gap |
| DXF ground truth | `extract/documents.py` (`DIMENSION.get_measurement()`, `INSUNITS_TO_M`, record-a-question-not-a-guess) | the DXF acceptance test |
| handoff units and axes | `seamkiln/handoff.py` `Target` table (blender Z/right/1.0, unreal Z/left/0.01, godot Y/right/1.0…), refuse-rather-than-guess for undriven targets; `assets/importer.py` read-back verification + `assets/envelopes.py` scale bands; `assets/gltf.py probe` | SOURCE = (partkiln, Z-up, right, 0.001 m); GLB needs no transform **because the writer rotates** |
| material cards with an honesty tier | `physical/materials.py` + `materials_eng.json` (`value / unit / source / honesty`), `seamkiln/materials.py` (`measured` needs a source) | `data/materials.json` cards with EN 1993-1-1 / EN 10025-2 / EN 10130 authorities |
| rule checks | `physical/joinery.py` (severity + source + verified stamp; `not_evaluated` is never conformance) | `pk_check` verdicts `{rule, got, limit, fix}` |
| benchmark | `benchmarks/run_benchmarks.py` `run_seamkiln_scenario` via `_safe(...)`, `estimate_tokens` at 3.5 chars/token | the bracket scenario and its edit row |
| a second opinion on a picture | `sense_*` (A47/A51) — advice, not measurement | `capture()` refuses in v1 and names the text routes; Blender renders on request |
| facts with citations | `kb` + `tee_web_lookup` | the KB has **no** mechanical coverage (no threads, GD&T, fits, K-factors, welds — `kb_search` 2026-09-02); the lane authors its own data with provenance |

## 7. Why FreeCAD is not the kernel

Doc 52 asked for headless CAD "just like Blender" and A37 answered with
FreeCAD over RPC; the critic's item 14 required the question to be re-put
for this lane. Measured 2026-09-02: `freecadcmd` 1.1.3 imports its modules
in 0.38 s at 67 MB RSS, and the headless sketch + TechDraw probe ended with
"Application unexpectedly terminated". TechDraw's SVG/PDF page export is
GUI-bound upstream (#5710; only DXF works headless — `adapters/freecad/
tools.py`). The app embeds **OCCT 7.8.1**, not the 7.9.3 the OCP wheel
carries, so its numbers and OCP's come from different kernels. Sketcher
constraints are integer-indexed (`Sketcher.Constraint('Coincident', geoId1,
posId1, geoId2, posId2)`) — the documented LLM failure mode in W4. Its
toponaming mitigation (`ElementMap`, `source;op;tag` names) is LGPL code:
the scheme is taken (roles instead of indices, history first, fingerprint
second), the code is not. OCP direct does every core op in milliseconds with
exact mass properties. FreeCAD stays the A37 `fc_*` adapter.

## 8. The AI-native surface in one page

The design of record is `CLAUDE_A66_SCRIPT.md` §D1–D9 and its Laws 11–20;
this is the summary. Kernel and wire speak **mm / deg**; unit-suffixed
strings (`"0.5in"`, `"90deg"`) are accepted everywhere a length or angle is,
a bare number is the document unit and the diff says so once (`assumed`),
`strict_units` makes it a refusal. Names are `≤ 24` chars `[a-z0-9_]`, or
`<kind><n>`; multi-instance children are `h.1, h.2 …`; a parameter name or
expression (`"W/2 - 5mm"`, AST-whitelisted, no `eval`) is legal wherever a
length is.

**D5 — the batch vocabulary (closed; an unknown op lists every verb; the
prop table is the script's D5).** `param_set`; `set doc`; `create part |
sketch | extrude | revolve | sweep | loft | hole | fillet | chamfer | shell |
draft | pattern | mirror | combine | split | plane | axis | point |
component | mate | joint | drawing | sheet`; `set` / `delete` (refuses
naming dependents unless `cascade`); `export` (STEP/IGES/BREP/STL/OBJ/3MF/
GLB/DXF/SVG/PDF with schema, tolerance, handoff target, `job`); `check`.
Sketch profiles are presets (rect, circle, slot, polygon, poly, arc) with
entities tagged at creation, twelve constraint kinds by tag and
driving|driven dims; a hole takes a diameter or a standard (`"M6 clearance
normal"`, `"M6 tap"`) with counterbore / countersink / spotface seats and a
cosmetic thread; a fillet or chamfer size is design intent and refuses a
default; joints are rigid / revolute / slider / cylindrical / planar / ball
(no `fit` in v1); a drawing carries views (front/top/right/iso/section/
detail/aux), dimensions read back from the model, a hole table, a parts list
and a title block; `create sheet` is the flat-first sheet-metal object.

**D6 — names, never indices.** Roles materialised from the hand-built merged
history: `extrude.start/.end/.side.<segtag>`, `revolve.outer/.inner/.cap.a`,
`hole.wall/.bottom/.seat`, `fillet.face[i]`, `shell.inner[i]`, imported
bodies `import.face[k]` by fingerprint only (surface type, area, centroid,
normal rounded 1e-3 mm). Selectors are declarative strings evaluated at regen
and echoed as counts — `"plate:edges(dir=Z)"` with filters `normal=`, `dir=`,
`of=`, `loop=`, `type=`, `r=`, `len>`, `area>`, `convex|concave`, `nearest=`,
`created_by=`, `not()`; seam edges excluded by default and reported;
cardinality declared by the field (0 → `pk_ref_empty`, many where one →
`pk_ref_ambiguous` with candidates); after a regen, history → fingerprint
(Δ ≤ 1e-3) → `pk_ref_stale` naming the history event, the nearest candidate
with its Δ mm and the selector that would have survived. Never a silent
re-target.

**D7 — entities and the diff.** Ids `doc`, `param:W`, `plane:XY`, `sk:base`,
`feat:plate`, `part:bracket`, `cmp:` / `mate:` / `jt:` / `asm`, `dwg:` /
`vw:` / `dim:`, `sheet:`, `export:`; concise rows ~20 tokens, a 12-feature
part ~300. Every feature answers with `{status, volume_mm3, delta_mm3,
bbox_mm, faces, edges, solids, assumed, resolved, names}`; a cut, hole or
combine that removes nothing refuses `pk_no_effect`; `set`/`param_set`
answer `{changed:[{feature, delta_mm3, faces}], unchanged, failed,
volume_mm3, fingerprint}` — BenchCAD's 64% silent corruption as a diff line;
sketches answer `{dof, status, conflicts, redundant, closed, area_mm2}`;
one `details.asm` per batch carries DOF, interference volumes with
centroids, clearances and contacts; dimensions carry `{value_mm,
projected_mm, agree}`; exports `{path, bytes, format, units, roundtrip,
watertight, triangles}`. No `ms` on the wire; never geometry.

**D8 — assume / needs.** Defaults are declared once; a self-contradictory
spec raises ONE `pk_spec_conflict` whose `fix` is a numbered `needs:` list
(≤ 3, with options) collected across the batch; a required field with no
safe default refuses `pk_needs`; the batch rolls back to its checkpoint and
says so. The refusal codes (`pk_bad_op pk_kernel_absent pk_not_served
pk_warming pk_too_long pk_plane_missing pk_plane_mismatch pk_unit_unknown
pk_unit_kind pk_unitless pk_ref_unknown pk_ref_stale pk_ref_ambiguous
pk_ref_empty pk_no_effect pk_sketch_overconstrained pk_sketch_open
pk_spec_conflict pk_needs pk_part_ambiguous pk_delete_blocked pk_op_failed
pk_checkpoint_missing pk_capture_text_first`) each name the geometry (frame,
bbox, history cause, nearest candidate, `NbFaultyContours`) and the exact fix.

**D9 — fourteen virtual tools, each an explicit trust row, no family.**
Read: `pk_probe`, `pk_verbs`, `pk_lint` (pre-flight without the kernel),
`pk_query`, `pk_measure`, `pk_check`, `pk_standards` (ISO 273/262 via
bd_warehouse with source and licence), `pk_materials`, `pk_bom`. Write
artifacts: `pk_drawing`, `pk_export`, `pk_flat`. Write scene: `pk_import`,
`pk_script`. Process model (D2): `LocalKernel` in-process when
`find_spec("OCP")` succeeds (the dev venv), `SidecarKernel` over NDJSON from
`~/TEE/.tee/sidecars/partkiln` in production (the 3.13.9 extension runtime
has no OCP and is wiped on every upgrade; the sidecar survives both the wipe
and `tee_purge`); a warm-up job at boot, `pk_warming` for a call that lands
inside the cold import, `list_entities()` and `snapshot()` answered from the
in-process mirror while warming (because `run_batch` calls `warm()` →
`list_entities()` and then the checkpoint **before** `execute()`); a dead
worker is respawned and the script replayed. Checkpoints (D3): the script is
the state, the `.brep` is a cache.

## 9. Defects found while doing this research

1. **The 140 s first import was never measured.** `docs/PROGRESS.md:6718`,
   `docs/setup-fleet.md:166` and `CLAUDE_A46_SCRIPT.md:36` attribute it to
   Python compiling OCP's bytecode; `OCP/__init__.py` is one line and the
   325 sub-packages are stubs, and compiling cadquery's entire 606-module
   closure in memory takes 0.51 s (W3 §10). Measured in fresh venvs
   (`68-evidence/p0a-measure.log`): cold `import OCP` is **26.2 s** (novtk)
   / **38.7 s** (vtk), paid once per venv; warm 0.29 / 0.33 s. The cost is
   native first-load — W3's account is page-in plus macOS code-signature
   validation of the ad-hoc-signed 144 MB `.so` (`codesign -dvv`: 34,808
   page hashes) — and a design built around 140 s of bytecode (a precompile
   step, a daemon) would have solved a number that did not exist.
2. **cadquery's GLB is 1000× too big.** `exportGLTF/exportGLB` never sets
   `XCAFDoc_LengthUnit` (no `LengthUnit` anywhere in the installed 2.8.0),
   so a 10 mm part lands in Blender as 10 m; it does rotate −90° about X
   itself. build123d sets the unit. The lane's writer sets both the unit and
   the Z-up input coordinate system and pins both negatives (§3.9).
3. **FreeCAD's headless sketch + TechDraw probe crashes** ("Application
   unexpectedly terminated") on 1.1.3, and its page export is GUI-bound
   (#5710) — recorded as the P0c ruling (§7).
4. **`server/src/tee/physical/sketch.py` promises metres and is fed
   millimetres.** Its docstring says all lengths are metres; the FreeCAD
   adapter passes mm as bare numbers and calls the solver unit-agnostic; its
   docstring says an unanchored sketch has 2 free DOF while the code allows
   3 (`sketch.py:209`); solved points are rounded to 1e-6 (metres = 1e-3 mm).
   Left as it is for TEE's own lanes (its dependency is GPL py-slvs); the
   P0 row 16 oracle drives `py_slvs` directly in mm. The reuse map's "reuse
   as-is" was wrong on both counts.
5. **`tee.assets.gltf.probe` requires a `pathlib.Path`.** A `str` raises
   `AttributeError: 'str' object has no attribute 'suffix'` at
   `server/src/tee/assets/gltf.py:182` (refuter 1). The acceptance tests pass
   a `Path`; the signature should say so.
6. **`CHANGELOG.md` had no 0.19.0 entry** although `server/pyproject.toml`,
   `server/Makefile` and `packaging/mcpb_manifest.json` all said 0.19.0 —
   the seamkiln lane shipped without a release note (E3 §9). Written
   retroactively alongside this doc.
7. **`docs/research/00-index.md` stopped at doc 48** while the corpus ran to
   67 (noticed at A53, `PROGRESS.md:8720`, left as "its own task"). Rows
   49–68 added alongside this doc.
8. Smaller, recorded in the refuters: E3 cited `server/pyproject.toml:3` for
   the version line (it is `:4`); the synthesis cited `gateway/wire.py:70-227`
   in a 225-line file; `ProjectConfig.load()` silently drops an unknown
   `[partkiln]` table (a `config.py` field is on the touch list); server
   tests die at 60 s (`pytest-timeout`), so cold-spawn tests are `-m dcc`
   with `@pytest.mark.timeout(300)`.

## 10. P0 answered these (2026-09-02 — measured, see PROGRESS)

| # | Question | Answer |
| --- | --- | --- |
| 1 | Cold and warm `import OCP` on fresh venvs | novtk 26.2 s cold / 0.29 s warm; vtk 38.7 / 0.33 — a warm-up job suffices; no daemon, no precompile |
| 2 | novtk footprint and VTK links | 223 MB site-packages, all OCP; `.so` 144 MB linking 0 VTK dylibs (vtk wheel: 914 MB, 10 links) |
| 3 | do both wheels ship `OCP/` | yes — 397 / 403 RECORD entries; co-install hazard recorded |
| 4 | binding coverage on novtk | 36/36 classes bound, including `LocOpe_DPrism`, `HLRBRep_HLRToShape`, `RWMesh_CoordinateSystem` |
| 6 | RSS after import | 251 MB (novtk) / 288 MB (vtk); after F5 not recorded |
| 7 | F5 sequential vs n-ary, glue negative | 0.46 s vs 0.09–0.10 s; 520,481.421 mm³; 106 faces; 312 unique edges; glue returns the uncut plate with `IsDone()` True |
| 8 | HLR per compound, exact vs poly | the counts in §5; `VCompound` non-empty on F1 and the 12-hole plate; poly 105 ms vs exact 91 ms on 530 faces |
| 9 | STEP schema ordering | `'' → AP214IS → AP242DIS`; set-before-Transfer AP242, set-after stays AP214, `Model(True)` recovers |
| 10 | F8 import | 0.408 s, 10 products, 1,060 faces, Σ 5,204,814.21, names intact |
| 11 | mesh hash serial vs parallel | identical at 0.05 and 0.3 mm (refuter 1, vtk wheel) |
| 12 | fingerprint across processes | identical for the 100-hole plate in two fresh processes; F2/F6 fingerprints recorded once (`8d2f6429c818a423`, `adab39337a43df7d` / `7c2af783c4e6aa88`) |
| 13 | GLB of F1, both negatives | `[0.1, 0.01, 0.06]` / `[100, 10, 60]` / `[0.1, 0.06, 0.01]` |
| 14 | BREP checkpoint vs replay | 81 KB, 1.4–3 ms write, 1 ms read vs 0.09–0.46 s replay |
| 15 | history on F1's fillet | `Generated` `[1, 1, 1, 1, 0]` (seam → 0), `Modified` `[1, 1, 1, 1, 1, 1, 0]`, faces 7 → 11 |
| 17 | per-op wall times | all under 125 ms (the line in §5); `MAX_BATCH_S` 60 s |
| 18 | fixture provenance | BenchCAD `cc-by-4.0` on the HF card; CADGenBench card HTTP 401 → OUT |
| — | FreeCAD as kernel (P0c) | no — crash, GUI-bound pages, OCCT 7.8.1, index constraints |

**Rows 5 and 16, measured after this document was first written
(2026-09-02, later the same day; PROGRESS "A66 P0a rows 5 and 16"):** the
scipy sketch solver agrees with a py-slvs (SolveSpace) oracle on 20 anchored
sketches to a maximum coordinate delta of 3.09e-10 mm (SolveSpace's own
convergence floor, `CONVERGE_TOLERANCE = 1e-8` in solver units) with DOF
agreeing 20/20 and nine supplementary unanchored/under/over cases 9/9;
py-slvs 1.0.6's `System.addSymmetricLine` stores the wrong constraint type
(100016, SYMMETRIC_VERT) and ignores the line. A persistent NDJSON worker
answers its first reply 13–15 ms after spawn, pays the warm OCP import
(0.29 s) once, and answers a volume query on the 100-hole plate in 2.5 ms of
which the protocol is 0.02 ms; RSS 17.5 MB idle → 297 MB after the plate. The
built transport (P4) measures spawn→ready 0.11 s (0.38 s with `--warm`) and
0.018 ms per ping.

## 10b. Open questions

1. **Row 5** — the 60-line NDJSON worker prototype: spawn → `ready` and the
   first / 100th `measure` (expected: warm import + ~50 ms, then ≤ 2 ms).
   Unmeasured until P4 builds the worker.
2. **Row 6, second half** — RSS after F5, per job worker (two workers × the
   residency on a 128 GB machine; the number still goes in the table).
3. **Row 12** — F2 and F6 fingerprints in two fresh processes (measured once
   each; the 100-hole plate was measured twice).
4. **Row 16** — the own scipy sketch solver against py-slvs driven directly
   in mm on 20 anchored sketches: coordinates ≤ 1e-6 mm or the measured floor,
   DOF equal on 20/20. Decides nothing about the design; pins its accuracy.
5. CADGenBench's data licence: the paper's "ODC-BY" cannot be reproduced
   because the card answers 401; stays OUT until read.
6. Inventor 2027's What's New was not consulted (the inventory is 2026 help);
   the two Autodesk blogs disagree on whether the 2027 Assistant modifies
   geometry; the forum claim that one Vault licence covers three headless
   instances was 403 to fetch; the 2026 plastic-features page was not
   fetched.
7. nlopt's effective licence is an inference from build flags and casadi's
   bundled IPOPT/MUMPS were not audited — both moot while both are banned,
   both recorded so nobody un-bans them on the metadata.
8. ISO 286 limits and fits have no permissive data source found
   (2026-09-02 search); `fit` stays out of v1 (L2). Coil/helix and modelled
   threads are L1 (helix construction is in OCCT; threads live in
   bd_warehouse, Apache-2.0).
9. The GUI: the owner chose headless-first with a PySide6 client of the same
   core as a later phase (A53 Law 3); unscheduled.
10. Cross-platform fingerprints (Linux CI vs arm64): byte identity is
    promised within one platform only; golden volumes at 1e-6 relative.
