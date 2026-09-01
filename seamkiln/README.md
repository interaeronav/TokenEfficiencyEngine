# seamkiln

A garment CAD and drape kernel: 2D pattern pieces, sewing relationships,
drape on a parametric body, fit measurement — **headless first**, with a
GUI that is a client of the same core rather than a second code path.

The core loop is the one Marvelous Designer and CLO3D established:

```
2D panels -> sewing -> arrange around a body -> simulate -> measure fit -> export
```

The difference is the surface. The incumbents' automation is in-app and
sold on an enterprise tier; here the script *is* the product, the GUI
constructs the same command objects a script does, and a GUI session
exports the script that reproduces it exactly.

Built inside the TokenEfficiencyEngine project (see `../CLAUDE_A53_SCRIPT.md`
and `../docs/research/67-garment-cad-lane.md`), structured as a
self-contained package so it can move to its own repository without
surgery — the `voxkiln/` precedent.

## Status

Early. `seamkiln.solver` holds the XPBD kernel and its backends, chosen by
measurement (`python -m seamkiln.bench.bakeoff`), not by preference.

## The licence gate

This domain is mined: the best-documented open garment pipeline in the
world drapes through a **non-commercial** simulator fork, SMPL is
non-commercial, and the standard triangulation library cannot ship in a
commercial product. `tests/test_licences.py` fails the build if any of
them ever enters the dependency closure. Read it before adding a
dependency.
