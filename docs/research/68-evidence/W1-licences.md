**W1 — Licence audit (fetched 2026-09-02; primary sources only)**

Machine: arm64, default `python3` = 3.14.7 (local). Project licence: `server/pyproject.toml:8` `license = { text = "MIT" }`; seamkiln likewise (`seamkiln/pyproject.toml:7`). Existing licence gate pattern: `seamkiln/tests/test_licences.py` (BANNED map + NON_COMMERCIAL_MARKERS + transitive-closure scan of declared deps).

## 1. Per-item findings

**Open CASCADE Technology 7.9** — LGPL-2.1 (only; no "or later") + "Open CASCADE exception (version 1.0)". README: "under the terms of the GNU Lesser General Public License version 2.1 ... with a special exception defined in the file OCCT_LGPL_EXCEPTION.txt" — https://raw.githubusercontent.com/Open-Cascade-SAS/OCCT/master/README.md. Exception text verbatim: "The object code form of a 'work that uses the Library' can incorporate material from a header file that is part of the Library. As a special exception to the GNU Lesser General Public License version 2.1, you may distribute such object code incorporating material from header files provided with the Open CASCADE Technology libraries (including code of CDL generic classes) under terms of your choice, provided that you give prominent notice in supporting documentation to this code that it makes use of or is based on facilities provided by the Open CASCADE Technology software." — https://raw.githubusercontent.com/Open-Cascade-SAS/OCCT/master/OCCT_LGPL_EXCEPTION.txt. V7_9_3 published 2025-12-06 (https://api.github.com/repos/Open-Cascade-SAS/OCCT/releases/tags/V7_9_3); OCCT 8.0.0 2026-05-07, 8.0.1 2026-07-30 (https://github.com/Open-Cascade-SAS/OCCT/releases). conda-forge records occt as `LGPL-2.1-only` (local: `/Applications/FreeCAD.app/Contents/Resources/conda-meta/occt-7.8.1-all_h869bdd7_203.json`). **Verdict: OPTIONAL-ONLY** (dynamic link via a separately-installed wheel; obligations: LGPL text + OCCT copyright notice, user can replace the library — satisfied by pip-separate wheel — plus the exception's "prominent notice in supporting documentation").

**cadquery-ocp (OCP)** — wheel metadata Apache-2.0 (https://pypi.org/pypi/cadquery-ocp/json); OCP repo LICENSE Apache-2.0 (https://raw.githubusercontent.com/CadQuery/OCP/master/LICENSE). Apache covers the binding only; the OCCT dylibs inside are LGPL-2.1+exception. `requires_python >=3.10,<3.15`; 7.9.3.1.1 requires `cadquery-ocp-proxy==7.9.3.1.1` and `vtk==9.6.2`. macOS arm64 wheels (https://pypi.org/simple/cadquery-ocp/): `cadquery_ocp-7.9.3.0-cp{310,311,312,313}-macosx_11_0_arm64.whl`, `cadquery_ocp-7.9.3.1-cp{310,311,312,313}-macosx_11_0_arm64.whl`, `cadquery_ocp-7.9.3.1.1-cp{310,311,312,313,314}-macosx_11_0_arm64.whl`. No 8.x on PyPI (highest 7.9.3.1.1), although GitHub has OCP 8.0.0.0 (2026-08-27, "wrapping OCCT 8.0.0") and 8.0.0.1 (2026-08-29); 7.9.3.0 (2025-12-27) is "based on OCCT 7.9.3", 7.9.3.1.1 (2026-05-25) is a "dummy release for PyPI support" — https://api.github.com/repos/CadQuery/OCP/releases. `cadquery-ocp-novtk` 7.9.3.1.1: Apache-2.0, no vtk dep, arm64 wheels cp310–cp314 (https://pypi.org/pypi/cadquery-ocp-novtk/json). `cadquery-ocp-proxy` 7.9.3.1.1 Apache-2.0, pure-python (https://pypi.org/pypi/cadquery-ocp-proxy/json). **Verdict: OPTIONAL-ONLY** (carries OCCT).

**cadquery 2.8.0** — Apache-2.0, `requires_python>=3.11`; requires_dist: `cadquery-ocp<8.0,>=7.9.3.1`, `ezdxf>=1.3.0`, `multimethod<2.0,>=1.11`, `nlopt<3.0,>=2.9.0`, `runtype`, `casadi`, `trame`, `trame-vtk`, `trame-components`, `trame-vuetify`, `pyparsing>=3.0.0`, `scipy`, `numba` — https://pypi.org/pypi/cadquery/json (no pyproject.toml on master: 404). Import chain verified: `cadquery/__init__.py` → `from .assembly import ...` (https://raw.githubusercontent.com/CadQuery/cadquery/master/cadquery/__init__.py); `assembly.py` → `from .occ_impl.solver import ...` (https://raw.githubusercontent.com/CadQuery/cadquery/master/cadquery/assembly.py); `solver.py` → `import casadi as ca` at top level, solver = casadi `Opti` with `"ipopt"` (https://raw.githubusercontent.com/CadQuery/cadquery/master/cadquery/occ_impl/solver.py). So `import cadquery` loads casadi unconditionally. **Verdict: OPTIONAL-ONLY at best** (drags two LGPL native libs, below).
- casadi 3.8.0 — **LGPL-3.0-or-later** confirmed: PyPI `info.license` "GNU Lesser General Public License v3 or later (LGPLv3+)" (https://pypi.org/pypi/casadi/3.8.0/json); repo LICENSE.txt LGPL-3.0 (https://raw.githubusercontent.com/casadi/casadi/main/LICENSE.txt). arm64 wheels: `casadi-3.8.0-cp311-abi3-macosx_11_0_arm64.whl` (abi3 ⇒ 3.11+), plus cp310/cp39/cp38 arm64. OPTIONAL-ONLY.
- nlopt 2.11.0 wheel — PyPI metadata says **MIT** (author Daniel Bok; https://pypi.org/pypi/nlopt/json), but upstream COPYING: the luksan directory is "LGPL, version 2.1 or later" and "the compiled NLopt library is governed by the terms of the LGPL"; MIT only "when built without the luksan directory" (https://raw.githubusercontent.com/stevengj/nlopt/master/COPYING; same at https://nlopt.readthedocs.io/en/latest/NLopt_License_and_Copyright/). nlopt-python's build passes only `-DNLOPT_GUILE=OFF -DNLOPT_MATLAB=OFF -DNLOPT_OCTAVE=OFF`, no `NLOPT_LUKSAN=OFF` (https://raw.githubusercontent.com/DanielBok/nlopt-python/master/extensions.py), and its LICENSE file carries both LGPL-2.1+ and MIT texts (https://raw.githubusercontent.com/DanielBok/nlopt-python/master/LICENSE). **Effective licence of the PyPI wheel: LGPL-2.1-or-later.** arm64 wheels cp310–cp314. OPTIONAL-ONLY.
- vtk 9.7.0 — BSD-3-Clause; arm64 wheels cp310–cp314 (https://pypi.org/pypi/vtk/9.7.0/json); vtk 9.6.2 (the version cadquery-ocp pins) arm64 cp39–cp314 (https://pypi.org/pypi/vtk/9.6.2/json). CORE-OK (but huge).
- trame 3.13.2 — **Apache-2.0** (not MIT) (https://pypi.org/pypi/trame/json); trame-vtk 2.11.16 BSD-3-Clause (https://pypi.org/pypi/trame-vtk/json); trame-vuetify 3.2.5 MIT (https://pypi.org/pypi/trame-vuetify/json); trame-components 2.5.0 Apache-2.0 (https://pypi.org/pypi/trame-components/json). CORE-OK.
- multimethod 2.1 — Apache-2.0, Python ≥3.11 (https://pypi.org/pypi/multimethod/json). runtype 0.5.3 MIT (https://pypi.org/pypi/runtype/json). pyparsing 3.3.2 MIT (https://pypi.org/pypi/pyparsing/json). numba 0.67.0 BSD-2-Clause (https://pypi.org/pypi/numba/json, https://raw.githubusercontent.com/numba/numba/main/LICENSE). scipy 1.18.1 BSD-3-Clause (https://pypi.org/pypi/scipy/json). ezdxf 1.4.4 MIT (https://pypi.org/pypi/ezdxf/json). All CORE-OK.

**build123d 0.11.1** — Apache-2.0, `requires_python >=3.10,<3.15` (https://pypi.org/pypi/build123d/json; pyproject `license = {text = "Apache-2.0"}` https://raw.githubusercontent.com/gumyr/build123d/dev/pyproject.toml). PyPI requires_dist: `cadquery-ocp-novtk<8.0,>=7.9`, `typing_extensions` (PSF-2.0), `numpy<3,>=2` (BSD-3-Clause AND 0BSD AND MIT AND Zlib AND CC0-1.0, https://pypi.org/pypi/numpy/json), `svgpathtools>=1.5.1` (MIT, https://pypi.org/pypi/svgpathtools/json), `anytree` (Apache-2.0, https://raw.githubusercontent.com/c0fec0de/anytree/main/LICENSE — PyPI metadata is null), `ezdxf` (MIT), `ipython` (BSD-3), `ocpsvg>=0.6,<0.7` (Apache-2.0 per https://raw.githubusercontent.com/snoyer/ocpsvg/main/LICENSE — PyPI metadata null; dep `svgelements` MIT https://pypi.org/pypi/svgelements/json), `ocp_gordon` 0.2.2 Apache-2.0 (https://pypi.org/pypi/ocp-gordon/json), `trianglesolver` 1.2 MIT (https://pypi.org/pypi/trianglesolver/json), `sympy` BSD-3, `scipy` BSD-3, `scikit-learn` BSD-3-Clause, `webcolors` BSD-3, `requests` Apache-2.0, `lib3mf>=2.4.1` (non-linux-aarch64) / `py-lib3mf>=2.4.1` (linux aarch64 only). **dev-branch pyproject additionally adds** `fonttools` (MIT), `bd_materials>=0.2.0,<0.3.0` and `threejs-materials>=1.2.1,<1.3.0`. `ocp-tessellate` and `ocp_vscode` are NOT build123d deps (ocp_vscode is an extra). **Verdict: OPTIONAL-ONLY** (only because of OCCT via cadquery-ocp-novtk; every Python dep is permissive).
- bd_materials 0.2.4 — **NO LICENCE FOUND**: PyPI `license`, `license_expression`, `license_files`, classifiers all null; repo https://github.com/bernhard-42/bd_materials shows no licence in footer/README; `LICENSE` 404; GitHub licence API 404 (https://pypi.org/pypi/bd-materials/json). Unlicensed = all rights reserved by default. CANNOT-SHIP until it gets a licence. threejs-materials 1.2.3 Apache-2.0 (https://pypi.org/pypi/threejs-materials/json).
- lib3mf 2.5.0 — BSD classifier on PyPI, repo LICENSE BSD-2-Clause ("Copyright (C) 2019 3MF Consortium", https://raw.githubusercontent.com/3MFConsortium/lib3mf/master/LICENSE); wheel `lib3mf-2.5.0-py3-none-macosx_10_9_universal2.whl` (https://pypi.org/pypi/lib3mf/json). CORE-OK. py-lib3mf 2.5.0 — PyPI metadata "Apache-2.0"; only `manylinux_2_24_aarch64` wheels, no macOS (https://pypi.org/pypi/py-lib3mf/json). Irrelevant on macOS.

**py-slvs 1.0.6** — PyPI `license` "GNU General Public License 3.0", author Zheng Lei (realthunder), home https://github.com/realthunder/slvs_py (GPL-3.0 in repo; binds a fork "based on SOLVESPACE v2.3") — https://pypi.org/pypi/py-slvs/json. arm64 wheels 1.0.6: cp38–cp313 `macosx_11_0_arm64` (no cp314) — https://pypi.org/simple/py-slvs/. **SolveSpace/libslvs**: COPYING.txt is plain GPL-3.0, **no linking exception** (https://raw.githubusercontent.com/solvespace/solvespace/master/COPYING.txt). **python-solvespace 3.0.8**: GPL-3.0-or-later (KmolYuan); macOS wheels only cp310 x86_64 and cp311 universal2 (https://pypi.org/pypi/python-solvespace/json). **Verdict: OUT-OF-PROCESS-ONLY** (all three).

**pythonocc-core** — LGPL-3.0 (https://raw.githubusercontent.com/tpaviot/pythonocc-core/master/LICENSE). OPTIONAL-ONLY, and redundant with OCP.

**manifold3d 3.5.2** — Apache-2.0 (https://raw.githubusercontent.com/elalish/manifold/master/LICENSE; PyPI classifier), arm64 wheels cp310–cp314 + cp314t, `requires_python>=3.9` (https://pypi.org/pypi/manifold3d/3.5.2/json). CORE-OK.
**trimesh 5.1.0** — MIT (https://pypi.org/pypi/trimesh/json). CORE-OK.
**ezdxf 1.4.4** — MIT. CORE-OK.
**fpdf2 2.8.8** — `license_expression: LGPL-3.0-only` (https://pypi.org/pypi/fpdf2/json). OPTIONAL-ONLY; already isolated: `server/pyproject.toml:81-84` `[pdf]` extra (`fpdf2>=2.8.8`, `pypdf>=5.1.0`) and `seamkiln/pyproject.toml:48-51` `[plot]` extra.
**svgwrite 1.4.3** — MIT; project marked inactive, bugfix-only since 1.4.2 (https://pypi.org/pypi/svgwrite/json). CORE-OK (svgpathtools MIT is the maintained alternative).
**gmsh 4.15.0** — GPL-2.0-or-later with a named exception: "The copyright holders of Gmsh give you permission to combine Gmsh with code included in the standard release of Netgen ..., METIS ..., OpenCASCADE ... and ParaView ... under their respective licenses." (https://gmsh.info/LICENSE.txt). Bundled locally: `/Applications/FreeCAD.app/Contents/Resources/bin/gmsh`, conda-meta `gmsh-4.15.0` licence `GPL-2.0-or-later`. OUT-OF-PROCESS-ONLY.
**CalculiX ccx 2.23** — GPL-2.0-or-later: source header "GNU General Public License ... either version 2 of the License, or (at your option) any later version" (https://raw.githubusercontent.com/Dhondtguido/CalculiX/master/src/CalculiX.h); dhondt.de links GPL v2, latest 2.23 (http://www.dhondt.de/). Bundled locally: `/Applications/FreeCAD.app/Contents/Resources/bin/ccx`, conda-meta `calculix-2.23` `GPL-2.0-or-later`. OUT-OF-PROCESS-ONLY.
**FreeCAD 1.1.3** (tag 1.1.3, published 2026-07-25T04:53:36Z, https://api.github.com/repos/FreeCAD/FreeCAD/releases/latest) — source headers: "GNU Library General Public License (LGPL) ... either version 2 of the License, or (at your option) any later version" = LGPL-2.0-or-later (https://raw.githubusercontent.com/FreeCAD/FreeCAD/main/src/App/Application.h); repo LICENSE file is the LGPL-2.1 text (https://raw.githubusercontent.com/FreeCAD/FreeCAD/main/LICENSE); wiki licence page blocked by Anubis. Local `/Applications/FreeCAD.app` is 1.1.3 and bundles occt 7.8.1 (LGPL-2.1-only), pyside6 6.8.3 (LGPL-3.0-only), qt6-main 6.8.3, vtk 9.3.1, ifcopenshell 0.8.4, gmsh, calculix (conda-meta). Verdict: library is OPTIONAL-ONLY; as shipped (.app with GPL binaries inside) treat as OUT-OF-PROCESS.
**FreeCAD SheetMetal WB 0.8.22** — `<license file="LICENSE">LGPL-2.1-or-later</license>` (https://raw.githubusercontent.com/shaise/FreeCAD_SheetMetal/master/package.xml); relicensed from GPL3 in 0.4.00 (README release notes, https://github.com/shaise/FreeCAD_SheetMetal). Runs inside FreeCAD ⇒ out-of-process.
**neka-nat/freecad-mcp** — MIT ("Copyright (c) 2025 Shirokuma (k tanaka)", https://raw.githubusercontent.com/neka-nat/freecad-mcp/main/LICENSE); MCP server driving FreeCAD over RPC + addon workbench. CORE-OK (pattern reusable).
**sympy 1.14.0** BSD-3 (https://pypi.org/pypi/sympy/json); **networkx 3.6.1** BSD-3-Clause (https://pypi.org/pypi/networkx/json); **numpy 2.5.2** BSD-3-Clause AND 0BSD AND MIT AND Zlib AND CC0-1.0 (https://pypi.org/pypi/numpy/json); **pint 0.25.3** BSD-3-Clause (https://pypi.org/pypi/pint/json, https://raw.githubusercontent.com/hgrecco/pint/master/LICENSE). All CORE-OK.
**ocp-tessellate 3.5.0** — Apache-2.0; deps webcolors, numpy, cachetools, imagesize, typing_extensions (https://pypi.org/pypi/ocp-tessellate/json). CORE-OK (only useful with OCP).

**ISO thread / hole data sources**
- **bd_warehouse 0.3.0 (Apache-2.0)** — LICENSE verified (https://raw.githubusercontent.com/gumyr/bd_warehouse/main/LICENSE). `src/bd_warehouse/data/` holds 48 CSVs incl. `clearance_hole_sizes.csv` (124 rows, `Size,Close,Normal,Loose`, M1…M150 + #0…4"; e.g. `M3,3.2,3.4,3.6`), `tap_hole_sizes.csv` (100 rows `Size,Soft,Hard`, e.g. `M2-0.45,1.55,1.7`), `drill_sizes.csv`, `socket_head_cap_parameters.csv` (ISO 4762 + ASME B18.3; sizes embed coarse pitch `M3-0.5`, `M4-0.7`…), hex head/nut, washers, set screws, `iso_228_1.csv` (BSP), DIN 471/472, bearings, o-rings — https://github.com/gumyr/bd_warehouse/tree/main/src/bd_warehouse/data, https://raw.githubusercontent.com/gumyr/bd_warehouse/main/src/bd_warehouse/data/clearance_hole_sizes.csv. Fastener docs enumerate ISO 4762/4032/4033/4035/4036/7380/14580/7048/1207/2009/14582/14581/10642/7046/4017/4014/1580/14583/7045/2010/7047/14584/4026/7089–7094, DIN 1587/557/967, ASME B18.6.3/B18.3/B18.21.1; ISO 273 is not named (its clearance data is the CSV above) — https://bd-warehouse.readthedocs.io/en/latest/fastener.html. `thread.py` has IsoThread/AcmeThread/MetricTrapezoidalThread/BSPP/Whitworth but no ISO 261 pitch table. **CORE-OK data source.**
- **threadlib (BSD-3-Clause)** — `THREAD_TABLE.scad`: "Metric threads (coarse, fine, and super-fine pitches) M0.25 to M600", UNC/UNF/UNEF/n-UN, BSP G1/16–G6, PCO-1881/1810, RMS — https://github.com/adrianschlatter/threadlib, licence via https://api.github.com/repos/adrianschlatter/threadlib/license. **CORE-OK data source** for the ISO 261 pitch table (convert .scad → CSV, keep attribution).
- **Wikipedia "ISO metric screw thread"** — ISO 262 table (nominal 1–64 mm, R10/R20, coarse & fine pitch), no minor-diameter column; footer "Text is available under the Creative Commons Attribution-ShareAlike 4.0 License" — https://en.wikipedia.org/wiki/ISO_metric_screw_thread. ShareAlike ⇒ not a source file for an MIT package; cross-check only.
- **BOLTS** — bolttools LGPL-2.1-or-later; "At the moment BOLTS is licensed under GPL 3.0+, as this is the most restrictive license of all components" — https://boltsparts.github.io/en/docs/0.4/document/general/licensing.html. Avoid as data source.
- **FreeCAD FastenersWB 0.5.65** — `GPL-2.0-or-later` (https://raw.githubusercontent.com/shaise/FreeCAD_FastenersWB/master/package.xml). Its tables cannot be copied into core.
- No CC0/MIT ISO 261/262/273 dataset found on GitHub/PyPI (search 2026-09-02); ISO documents themselves are ISO-copyrighted (iteh/regbar samples); handbook copies are copyrighted. Derive from public formulas (ISO 68-1: H = 0.866025·P, d1 = d − 1.082532·P, d2 = d − 0.649519·P) when a table is missing.

## (a) MINEFIELD TABLE

| Component | Licence (verified) | Verdict |
| --- | --- | --- |
| OCCT 7.9.3 | LGPL-2.1-only + OCCT exception 1.0 | OPTIONAL-ONLY |
| cadquery-ocp / -novtk / -proxy 7.9.3.1.1 | Apache-2.0 binding over LGPL OCCT dylibs | OPTIONAL-ONLY |
| cadquery 2.8.0 | Apache-2.0, but eager `casadi` (LGPL-3.0+) + `nlopt` wheel (effectively LGPL-2.1+) | OPTIONAL-ONLY (not core) |
| casadi 3.8.0 | LGPL-3.0-or-later | OPTIONAL-ONLY |
| nlopt 2.11.0 (PyPI wheel) | metadata MIT; compiled with luksan ⇒ LGPL-2.1-or-later | OPTIONAL-ONLY |
| vtk 9.6.2 / 9.7.0 | BSD-3-Clause | CORE-OK (heavy; avoid) |
| trame / -components | Apache-2.0 | CORE-OK |
| trame-vtk | BSD-3-Clause | CORE-OK |
| trame-vuetify | MIT | CORE-OK |
| multimethod 2.1 | Apache-2.0 | CORE-OK |
| runtype, pyparsing, ezdxf, svgwrite, svgpathtools, svgelements, trimesh, trianglesolver, fonttools | MIT | CORE-OK |
| numba | BSD-2-Clause | CORE-OK |
| scipy, sympy, networkx, pint, scikit-learn, webcolors, ipython, vtk | BSD-3-Clause | CORE-OK |
| numpy | BSD-3 AND 0BSD AND MIT AND Zlib AND CC0-1.0 | CORE-OK |
| build123d 0.11.1 | Apache-2.0 (only OCCT beneath is LGPL) | OPTIONAL-ONLY (via OCP) |
| ocpsvg, ocp_gordon, anytree, ocp-tessellate, threejs-materials, requests | Apache-2.0 | CORE-OK |
| bd_materials 0.2.4 | **no licence anywhere** | CANNOT-SHIP (until licensed) |
| lib3mf 2.5.0 (universal2 wheel) | BSD-2-Clause | CORE-OK |
| py-lib3mf 2.5.0 | Apache-2.0 metadata; linux-aarch64 only | n/a on macOS |
| manifold3d 3.5.2 | Apache-2.0 | CORE-OK |
| pythonocc-core | LGPL-3.0 | OPTIONAL-ONLY |
| fpdf2 2.8.8 | LGPL-3.0-only | OPTIONAL-ONLY (already `[pdf]`) |
| py-slvs 1.0.6 / SolveSpace / python-solvespace 3.0.8 | GPL-3.0 (no exception) / GPL-3.0-or-later | OUT-OF-PROCESS-ONLY |
| gmsh 4.15.0 | GPL-2.0-or-later (+ OCCT/Netgen/METIS/ParaView combine exception) | OUT-OF-PROCESS-ONLY |
| CalculiX ccx 2.23 | GPL-2.0-or-later | OUT-OF-PROCESS-ONLY |
| FreeCAD 1.1.3 (.app) | LGPL-2.0-or-later; app bundles GPL gmsh/ccx, LGPL-3.0-only PySide6, OCCT 7.8.1 | OUT-OF-PROCESS (RPC) |
| FreeCAD SheetMetal 0.8.22 | LGPL-2.1-or-later | OUT-OF-PROCESS (inside FreeCAD) |
| FreeCAD FastenersWB 0.5.65 (and its tables) | GPL-2.0-or-later | OUT-OF-PROCESS; data CANNOT be copied |
| freecad-mcp | MIT | CORE-OK |
| bd_warehouse data CSVs | Apache-2.0 | CORE-OK (attribution + NOTICE) |
| threadlib THREAD_TABLE | BSD-3-Clause | CORE-OK (attribution) |
| Wikipedia ISO 262 table | CC BY-SA 4.0 | cross-check only (ShareAlike) |
| BOLTS | GPL-3.0+ overall (bolttools LGPL-2.1+) | avoid as data |
| ISO standard texts, handbook tables | proprietary | CANNOT-SHIP |

## (b) Recommended permissive core (all wheels present for macOS arm64, cp311–cp314)

- Kernel/mesh: `manifold3d` (Apache-2.0, mesh CSG), `trimesh` (MIT), `numpy`, `scipy`, `sympy`, `networkx`, `pint` (BSD-3).
- 2D/exchange: `ezdxf` (MIT), `svgpathtools` (MIT; svgwrite is inactive), `lib3mf` (BSD-2).
- Standards data: vendored CSVs from `bd_warehouse` (Apache-2.0) for clearance/tap/drill/ISO 4762/4014/4017/nuts/washers, and `threadlib`'s table (BSD-3) for ISO 261 coarse/fine/superfine + UN + BSP pitches; carry both attributions in NOTICE.
- `[brep]` extra (OPTIONAL-ONLY): `build123d` + `cadquery-ocp-novtk` (Apache-2.0 over OCCT LGPL-2.1+exc). Pin `build123d<0.12` until bd_materials is licensed. Ship OCCT LGPL text + the exception's "prominent notice".
- Out-of-process adapters (subprocess/RPC, never imported): FreeCAD 1.1.3 (+SheetMetal), gmsh, ccx, SolveSpace via py-slvs.
- Excluded from core: cadquery (casadi/nlopt), pythonocc-core, fpdf2 (stays in `[pdf]`), vtk/trame stack.

## (c) Traps

1. `import cadquery` eagerly imports casadi (LGPL-3.0+) through `__init__ → assembly → occ_impl.solver`; no lazy path exists. cadquery cannot sit in an MIT core.
2. The `nlopt` PyPI wheel says MIT but is built with luksan (no `NLOPT_LUKSAN=OFF`), so upstream's own COPYING makes it LGPL-2.1+. Licence scanners will pass it wrongly.
3. `cadquery-ocp` metadata says Apache-2.0 while the payload is OCCT (LGPL-2.1+exception); scanners under-report — add OCCT to NOTICE manually.
4. `cadquery-ocp` 7.9.3.1.1 pins `vtk==9.6.2`; use `cadquery-ocp-novtk` (what build123d already uses).
5. py-slvs / python-solvespace / libslvs are GPL-3.0 with no linking exception; python-solvespace has no cp312+ macOS wheels and py-slvs stops at cp313 — the default python here is 3.14.7.
6. build123d's dev pyproject adds `bd_materials`, which has no licence at all (PyPI null, repo has no LICENSE); PyPI 0.11.1 does not yet require it — the next release will.
7. FastenersWB tables are GPL-2.0+, BOLTS is GPL-3.0+, Wikipedia is CC BY-SA 4.0: none may be copied into MIT data files; bd_warehouse (Apache-2.0) and threadlib (BSD-3) are the clean sources.
8. FreeCAD.app 1.1.3 on this machine embeds OCCT 7.8.1, not 7.9.3 — B-rep/STEP results from the "FreeCAD extra" and the "OCP extra" come from different kernels.
9. OCP 8.0.0.x (OCCT 8.0.0) exists on GitHub since 2026-08-27 but is not on PyPI; cadquery 2.8 and build123d pin `<8.0`.
10. multimethod 2.1 and cadquery 2.8 require Python ≥3.11; `cadquery-ocp` caps at `<3.15`.
11. `ocpsvg` and `anytree` publish no licence metadata on PyPI (both Apache-2.0 in-repo) — expect false positives from `pip-licenses`-style gates; `seamkiln/tests/test_licences.py` reads licence text from installed metadata and would need the repo-verified value hard-coded.
12. casadi bundles IPOPT and other third-party solvers whose licences (EPL/MUMPS etc.) were not audited here.