# partkiln

A headless, AI-native mechanical CAD kernel: constrained 2D sketches, a
feature tree (extrude, revolve, sweep, loft, holes, fillets, chamfers, shells,
drafts, patterns, mirrors), parts with named parameters, assemblies with
mates, joints, degrees of freedom, interference and a bill of materials,
drawings whose dimensions are read back from the model, and exports (STEP
AP242, IGES, BREP, STL, 3MF, OBJ, glTF, DXF, SVG, PDF) — on Open CASCADE
through the OCP wheel, **headless first**.

The core loop is the one Autodesk Inventor established:

```
sketch -> features -> part -> assembly -> drawing -> export
```

The difference is the surface. The incumbent's automation is a Windows COM
API, a read-only headless server, or a metered cloud sandbox; here the script
*is* the product: a `Document` holds the model, every mutation is a
`Command`, every `Command` is recorded, and `Document.replay(script)` rebuilds
the model to the same fingerprint in any process on any OS. TEE drives it
through `tee_batch` with zero new always-loaded tools.

Built inside the TokenEfficiencyEngine project (see `../CLAUDE_A66_SCRIPT.md`),
structured as a self-contained package so it can move to its own repository
without surgery — the `seamkiln/` and `voxkiln/` precedent.

## Status

Early (A66 P0). `tests/test_licences.py` is the licence gate: MIT core,
permissive-only in-process dependencies, OCCT (LGPL-2.1 with the OCCT
exception) as the one named weak-copyleft dependency. Read it before adding a
dependency.

## No Autodesk marks

Feature parity with the incumbent is the goal; its containers, chrome and
marks are not. partkiln reads and writes open interchange only, never
`.ipt/.iam/.idw`, and ships no Autodesk name in any tool, verb or entity.
