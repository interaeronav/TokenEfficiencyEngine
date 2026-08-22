# 37 — Simulation as verification (2026-08-22)

## Published settle-test thresholds

BlenderProc (runs in Blender — closest prior art): min 4 s / max 40 s
sim, quiescence check every 2 s (Δloc ≤ 1 cm AND Δrot ≤ 0.1 rad per
window), 10 substeps / 10 iterations, bake final poses, discard sim.
Isaac Sim: dt 1/90, ≤ 250 steps, settled at |v| < 0.01. Kubric: 240 Hz,
sim-first-render-after. Engine sleep criteria: PhysX 5e-5·(tolSpeed)²;
Bullet 0.8/1.0. Misplaced-drift verdicts (2-5 cm / 5-10°) are
engineering convention, not literature — labeled as such.

## Static gates carry most of the value

Revealed preference: ProcTHOR uses rejection sampling, Infinigen a
constraint solver — settle sims mainly for random drops. The cheap
always-on check is **CoM-projection-inside-support-polygon with a
stability margin** (contacts from TEE's existing raycast battery; pure
Python); stacks check cumulatively per interface (ShapeStacks' ground
truth is exactly this analytic criterion — vision models hit only
77-85%, analytics beat learning when contacts are known). PhyScene's
Scene-wise / Asset-wise Collision Rate metrics are reusable report
fields.

## Sim-ready standards

**NVIDIA SimReady Foundation is open-sourced Apache-2.0 (2026)**:
Requirements → Capabilities → Profiles + a `simready-validate` static
CLI — sim-readiness is validated by STATIC schema/rule checking, not by
running sims. UsdPhysics (RigidBodyAPI/CollisionAPI/MassAPI/
MaterialAPI; AOUSD Physics WG since Dec 2024) is the vocabulary; UE
reads USD colliders since 5.4; Blender has no native UsdPhysics
(post-process with pxr). omniverse-asset-validator emits severity +
location + a CALLABLE FIX — TEE's fail-loud-cheap rule shipped as a
product; mirror it.

## Collision proxies

**CoACD (MIT, pip, headless, collision-aware, threshold default 0.05)**
= canonical; V-HACD (BSD-3) deprecated in its favor. Cache proxies per
asset hash. Single hull ≪ V-HACD ≪ CoACD fidelity for concave
containers — where settle tests most need cavity preservation.

## Determinism & honest boundaries

Same-machine fixed-dt runs are deterministic (Bullet, PhysX; UE
`-Deterministic`); cross-run tolerances are set by MEASURING the
variance floor and asserting above it (CARLA/UE verification study).
Boundaries, stated in fact wording: a settle proves "rest-stable under
rigid-body settle (engine, dt, proxies)" — NEVER "structurally sound"
(impulse solvers are not structural analysis; claiming more is
theater). Cloth drape = opt-in visual aid (no pass/fail metric,
10-100× cost). Door swing = SWEPT-ARC static sampling over the joint
range (Solibri checks clearance statically; PartNet-Mobility annotates
kinematics, not dynamics).

## The TEE verification ladder (A19)

Tier 0 — static, always-on, milliseconds: penetration + support raycast
+ CoM-margin facts. Tier 1 — settle test, opt-in, seconds: Bullet-in-
Blender with CoACD proxies, BlenderProc-style quiescence, compact
report {settled, steps, moved > threshold, penetrating, unstable} +
optional adopt-settled-poses repair. Tier 2 — mechanism checks:
swept-range collision sampling over annotated joint limits; dynamic
hinge sim only on request. Sim-readiness gating via UsdPhysics
vocabulary + SimReady-style requirements with callable fixes.
