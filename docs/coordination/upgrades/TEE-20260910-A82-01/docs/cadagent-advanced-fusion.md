# Advanced CADAgent lessons in Fusion

TEE gives its client AI three executable Fusion lessons: a parametric ventilated
enclosure, a revolved flanged hub and a moving component assembly. Each lesson
contains a complete creation batch, a revision, geometric acceptance values and
export instructions. Request only the lesson needed through the existing guide.

These are authored instructions that a client can inspect and replay. They do
not train a model or establish how an independent CADAgent model performs. The
operations run locally through TEE's Fusion lane; they do not require CADAgent's
standalone chat service. Use a fresh TEE server from this checkout and the
configured Fusion bridge. See [CADAgent integration](cadagent-integration.md)
for installation scope and [the Fusion guide](fusion-lane.md) for the lane.

**Verified live:** all three lessons passed on Fusion **2705.1.15** on
2026-09-10. The run checked creation and revision geometry, reopened all three
F3D files and independently measured the STEP solids with OCCT. The joint
completed 0° → 45° → 90° → 0° → 45° with its 2 mm clearance intact.
[Live evidence](research/80-evidence/advanced-live.json),
[independent export audit](research/80-evidence/advanced-geometry-audit.json).

## Find a lesson

```text
tee_search_tools(query="cadagent")
tee_call(name="lane_guide", args={"adapter":"fusion"})
tee_call(name="lane_guide", args={"adapter":"fusion","topic":"cadagent_enclosure"})
```

The index is compact. Choose one of these topics to receive its full recipe:

| Topic | What the lesson teaches | Source |
|---|---|---|
| `cadagent_enclosure` | Anchor and constrain a footprint, bind dimensions, shell a solid, pattern vents, revise the enclosure. | [Recipe](../server/src/tee/adapters/fusion/recipes/cadagent_enclosure.json) |
| `cadagent_flange` | Revolve a stepped section, drill a central bore, pattern mounting holes around an axis, revise every bore through its seed parameter. | [Recipe](../server/src/tee/adapters/fusion/recipes/cadagent_flange.json) |
| `cadagent_joint` | Create components, connect their faces with a revolute joint, drive the joint and verify the resulting relative motion. | [Recipe](../server/src/tee/adapters/fusion/recipes/cadagent_joint.json) |

## Replay, revise and verify

1. Open a separate empty parametric Fusion design for the lesson, retaining any
   owner documents. The recipes create named parameters and geometry in the
   active design. Check `fu_probe` before submitting a batch so the intended
   document is active.
2. Fetch the selected guide and copy its `ops` array unchanged into
   `lane_preflight` with `adapter:"fusion"`. Preflight checks syntax without
   contacting Fusion; it cannot establish whether geometry will succeed.
3. Execute the same array with `tee_batch(adapter="fusion", ops=...)`. Keep the
   returned `created` IDs and detail rows. An alias such as `@mount.feature`
   exists only within that batch. Object names label geometry; they are not IDs.
4. Measure the actual body or component IDs with `fu_measure`. Read
   `fu_design_stats`, `fu_params` and `fu_timeline` for health, expressions and
   component ownership. When a diff omits a field that echoed an operation,
   refresh a bounded `tee_scene_summary` to resolve the needed entity.
5. Apply `revision.ops` in the same document. The enclosure and flange revisions
   address named parameters. For the joint lesson, replace `{{joint_id}}` with
   the actual created joint ID before preflight and execution. Run the stated
   geometry checks again, preserving both sets of measurements.
6. Export STEP and F3D to local absolute paths. Read STEP independently and
   reopen F3D in a separate document. Check units, solid counts, dimensions and
   volume; check the native archive's parameters or joint as appropriate. IDs
   are document-specific and must be rediscovered after reopening.

The client-side sequence is:

```text
lesson = tee_call(name="lane_guide", args={"adapter":"fusion","topic":"cadagent_flange"})
tee_call(name="lane_preflight", args={"adapter":"fusion","ops":lesson.ops})
created = tee_batch(adapter="fusion", ops=lesson.ops)
# Resolve the actual body ID from created, then measure it.
tee_call(name="fu_measure", args={"of":body_id})
tee_call(name="lane_preflight", args={"adapter":"fusion","ops":lesson.revision.ops})
tee_batch(adapter="fusion", ops=lesson.revision.ops)
tee_call(name="fu_measure", args={"of":body_id})
```

`lesson`, `created` and `body_id` above are client-side variables, not text to
send as JSON. The recipe's own arrays are the executable payloads. A successful
batch is followed by readback; an error must be resolved before continuing.

## Verified geometry

All dimensions are millimetres and volumes are cubic millimetres.

| Lesson | Initial geometry | Revised geometry |
|---|---|---|
| Enclosure | One 120 × 80 × 30 solid enclosure, 3 mm walls/floor and fifteen Ø6 floor vents. Volume 58,955.654975. | `A79E_width=140 mm`, `A79E_depth=40 mm`: 140 × 80 × 40, volume 79,835.654975. |
| Flanged hub | One solid, overall 32 × 80 × 80; Ø80 flange 8 thick and Ø40 hub extending to 32 overall. Ø12 central bore and six Ø6 mounting holes on a Ø60 pitch circle. Volume 65,395.392677. | `A79F_bore_diameter=16 mm`, `A79F_mount_diameter=8 mm`: unchanged outer bounds, volume 61,524.950528. |
| Revolute lever | Two components containing a 40 × 30 × 8 base and a 60 × 12 × 4 lever, with 2 mm face clearance. Total solid volume 12,480. | Joint rotation 45°: lever bounds relative to the base become 50.911688 × 50.911688 × 4; solid volume and clearance stay unchanged. |

The enclosure's footprint must be fully constrained. Its width and depth
parameters must change downstream geometry while the 3 mm walls and floor
remain. The fifteen vent centres move with the support face: initially x = 20, 40,
60, 80, 100; after widening, x = 30, 50, 70, 90, 110. The y coordinates stay
20, 40, 60. The measured grid stays centred with 20 mm spacing. A hole created
at a coordinate is not necessarily anchored at that world coordinate after
its support changes.

The flange lies along the root x axis. Its stepped section touches that axis
without crossing it, producing one closed solid on a full revolution. The
mounting seed starts on the -x flange face, so `at:[30,0]` means y=30, z=0.
The six mounting-hole centres lie on radius 30 in the yz plane at 60° intervals.
Check their individual cylindrical surfaces, radii and locations against the
recipe. A circular-pattern count alone cannot establish that six holes were
drilled. After revision the removed volume must increase by
`1232*pi = 3870.442149` mm³, and all six holes must follow the seed's expression.

The joint lesson uses a rectangular lever so its motion is measurable. Read
the joint's rotation and the lever's actual assembly geometry before and after
the revision. The optional 90° probe must exchange its relative XY bounds to
12 × 60, and returning to 0° must recover 60 × 12. Neither occurrence is
grounded by this recipe: compare motion in the base occurrence's frame rather
than assuming an unchanged world frame. Keep the 2 mm face clearance and both
solid volumes constant. Changing a joint value without changing relative
geometry fails the lesson. For these opposing planar faces, `flip:true` is
required: without it Fusion reported a healthy joint but placed the lever
inside the base. The corrected lever lies at z = 10–14 mm above the base
at z = 0–8 mm in the measured base frame.

## Preserve the result

For an active demonstration design, use local absolute output paths and omit
`of` so STEP/F3D receive the whole design:

```text
tee_call(name="fu_export", args={"format":"step","out":"/absolute/output/lesson.step"})
tee_call(name="fu_export", args={"format":"f3d","out":"/absolute/output/lesson.f3d"})
```

Replace `/absolute/output` with the chosen existing directory. STEP preserves
the exported solid geometry; F3D retains Fusion's editable native design.
Compare reopened results against the same acceptance values instead of relying
on file existence or a viewport image. The joint's native F3D must retain the
two occurrences and revolute connection.

Shells and feature patterns in this integration require native root-component
targets; the circular pattern axis passes through the root origin. The joint
lesson uses the existing component/joint lane separately. These examples cover
modelling and kinematics; they do not establish structural performance,
manufacturing fits, thread geometry or independent AI task completion.

Plan: [A79 P4](../CLAUDE_A79_SCRIPT.md). API grounding:
[research 71](research/71-fusion-lane.md). Integration provenance:
[research 80](research/80-cadagent-integration.md).

## Open the measured examples

The demonstration source documents remain open in Fusion. The final lever is
at 45°. Editable native files and neutral solids from the verified run:

| Example | Native Fusion | STEP |
|---|---|---|
| Enclosure | [F3D](../output/cadagent-advanced/live-20260910T174242220376Z/cadagent_enclosure.f3d) | [STEP](../output/cadagent-advanced/live-20260910T174242220376Z/cadagent_enclosure.step) |
| Flanged hub | [F3D](../output/cadagent-advanced/live-20260910T174242220376Z/cadagent_flange.f3d) | [STEP](../output/cadagent-advanced/live-20260910T174242220376Z/cadagent_flange.step) |
| Joint study | [F3D](../output/cadagent-advanced/live-20260910T174242220376Z/cadagent_joint.f3d) | [STEP](../output/cadagent-advanced/live-20260910T174242220376Z/cadagent_joint.step) |

To repeat the authored demonstration on a machine with the bridge running:

```sh
server/.venv/bin/python benchmarks/run_a79_cadagent_lessons.py
```

The harness creates its own three documents, records every attempt in a new
output directory, closes its archive verification copies, and leaves successful
source demonstrations visible. It refuses to mutate a different active document.
On failure it closes only documents created by that invocation.

The default guide index costs an estimated 272 tokens; a requested lesson costs
1,338–1,872. A fresh stdio connection still exposes 17 core tools / 2,129 estimated
schema tokens. All 331 affected tests passed. These measure authored workflow
and interface behavior, not independent AI success or a token saving against
an unmeasured alternative. Existing TEE servers must restart to load the new
source; the earlier Desktop bundle is unchanged.


The next three studies are [the Formula One lessons](cadagent-f1-fusion.md):
an articulated two-element wing, staggered radial brake passages and a driven
suspension wishbone. They add staged assembly, continuous geometric clearance,
curved-intersection volume checks and native-versus-STEP acceptance evidence.

The enclosure, flange and lever also have [native Blender lessons](blender-lessons.md),
alongside the F1 studies, house design, textures and fabric. They retain editable
mesh cutters and drivers, and explicitly measure their polygon approximation
rather than reusing the Fusion BRep accuracy claim.
