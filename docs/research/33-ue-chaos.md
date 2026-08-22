# 33 — UE 5.8 Chaos: the scriptable surface (2026-08-22)

- **PIE/SIE from Python (5.8)**: LevelEditorSubsystem
  editor_play_simulate / editor_request_begin_play /
  editor_request_end_play / is_in_play_in_editor. HARD CAVEAT: the
  editor does not tick while a Python call executes — blocking loops
  freeze the sim; sanctioned patterns are slate post-tick callbacks or
  MANY SHORT REMOTE CALLS (sim advances between them) — which is
  exactly TEE's request/response cadence. Readback via
  UnrealEditorSubsystem.get_game_world(); editor↔PIE actor mapping by
  name/path. "Keep Simulation Changes" has NO API → TEE's settle macro
  (read play-world transforms → end play → write to editor actors →
  return a diff) replaces it, better.
- **Determinism (Epic's words)**: cross-machine "Close, but not
  perfect"; same-machine opt-in via p.Chaos.Solver.Deterministic +
  fixed-timestep async physics (PhysicsSettings.tick_physics_async,
  async_fixed_time_step_size; ChaosSolverConfiguration iterations all
  Python-settable). Epic's Networked Physics engineers AROUND
  non-determinism. → tolerance-based assertions only.
- **Subsystems**: Destruction = Dataflow-based, PRODUCTION-READY,
  automatable ("process thousands of assets automatically"; Lego
  Fortnite tested; 5.8 adds Dataflow Python — surface UNVERIFIED).
  Chaos Cloth = Dataflow editor default in 5.8; structure/params
  automatable, weight painting not. Flesh Experimental (skip). Niagara
  Fluids Beta + GPU-crash warnings + non-deterministic → last-resort
  VFX, pixel-verified only. Modular Vehicles Experimental (skip).
- **Official MCP plugin**: NO simulation/PIE toolset, no rigid-body
  ops. PhysicsAssetToolset (17 tools: ragdoll CreateFromMesh, bodies/
  constraints/shapes/limits); DataflowAgentToolset (22 tools: create
  ChaosClothAsset/GeometryCollection/Flesh/Groom, node-graph edits, NO
  evaluation). Everything else via generic ObjectTools property
  writes; ProgrammaticToolset blocks `import unreal` → free-form needs
  Python Remote Execution. AutomationTestToolset bridges to tests.
- **Physical materials (verified)**: friction/static_friction/
  restitution + combine modes, density g/cm³, raise_mass_to_power
  (explicit non-physical fudge), sleep thresholds. Mass = SIMPLE
  collision volume × density → assets without simple collision (or
  complex-as-simple) CANNOT simulate → Phase 9 import validator adds:
  simple collision present, complexity mode, phys material, mass sane.
- **Headless**: -ExecutePythonScript has no ticking world → authoring
  only. Sanctioned sim route: **Functional Tests headless** (`-game
  -NullRHI -ExecCmds="Automation RunTests <f>;Quit"` — physics ticks
  normally); tests are Blueprint-authorable via MCP BlueprintTools →
  TEE can GENERATE a physics test, run it, parse pass/fail. Data
  Validation plugin = CI host for sim-ready checks; Gauntlet = scale
  path; Chaos Visual Debugger via console cvars = heavyweight human
  hand-off evidence, never agent context.
- **Proposed ops**: physics.set_body / material.create+assign (echo
  computed mass) / constraint presets / physics.settle (flagship:
  SIE + poll-across-calls + all-asleep stop + transform diff) /
  validate_sim_ready / test.run / ragdoll.setup / destruction.fracture
  (Dataflow template-first) / solver.configure. Adapter rules:
  serialize calls, probe is_in_play_in_editor before mutating,
  destruction event-data generation OFF by default.
