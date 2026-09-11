# Formula One design lessons for CADAgent in Fusion

TEE's CADAgent guidance now includes three difficult, executable Fusion studies:
an articulated two-element wing, a disc with radial cooling passages, and a
lightened suspension wishbone with integral bearing bosses. Each teaches a
dependency graph, a meaningful revision and checks against actual geometry.
The recipes use TEE's existing typed Fusion operations and load only when the
client asks for the particular lesson.

All dimensions and layouts are original teaching choices. These models establish
CAD and kinematic behavior, without claiming a team's design, FIA compliance,
structural capacity, braking performance or aerodynamic performance. They are
authored instructions a client AI can replay; they do not train a model or
measure an independent CADAgent model's success. See the
[integration guide](cadagent-integration.md) for the local integration and
[earlier advanced lessons](cadagent-advanced-fusion.md) for simpler examples.

**Verified live on Fusion 2705.1.15, 2026-09-10:** all three native lessons passed
creation, revision and F3D reopening checks. The wing and wishbone STEP exports
matched their geometry targets. The brake's original Fusion STEP **failed the
0.1 mm³ volume gate**, measuring 12.8021875 mm³ above its authored oracle. An
independently constructed OCCT reference STEP passed that same gate; the
original Fusion export remains preserved and unrepaired.

The recorded three-lesson run took **16.053 seconds** and preserved the existing
documents. These figures describe the authored replay, not independent AI
performance. [Live evidence](../output/cadagent-f1/live-20260910T181655120798Z/evidence.json),
[brake STEP audit](../output/cadagent-f1/step-audit/README.md),
[independent reference evidence](../output/cadagent-f1/reference-portability/evidence.json).

## Find and prepare a lesson

```text
tee_search_tools(query="cadagent")
tee_call(name="lane_guide", args={"adapter":"fusion"})
tee_call(name="lane_guide", args={"adapter":"fusion","topic":"cadagent_f1_wing"})
```

| Topic | Composition taught | Executable recipe |
|---|---|---|
| `cadagent_f1_wing` | Airfoil profiles, shared span driver, staged component assembly, articulated flap and clearance sweep. | [Wing](../server/src/tee/adapters/fusion/recipes/cadagent_f1_wing.json) |
| `cadagent_f1_brake` | Radial cut seeds on different planes, two feature patterns, independent diameter drivers and centre-of-mass change. | [Brake](../server/src/tee/adapters/fusion/recipes/cadagent_f1_brake.json) |
| `cadagent_f1_wishbone` | Through lightening cut, three profiles joined into one solid, counterbored bearing seats and coordinated revisions. | [Wishbone](../server/src/tee/adapters/fusion/recipes/cadagent_f1_wishbone.json) |

Open a separate empty parametric Fusion design for each lesson and retain any
existing documents. Check the active document with `fu_probe`. The named
parameters in the recipe must be unused. A running TEE server must load the new
source from this checkout; see [the Fusion lane](fusion-lane.md) for its bridge.

For each stage, send its `ops` array to
`tee_call(name="lane_preflight", args={"adapter":"fusion","ops":...})`, then
execute the same array through `tee_batch(adapter="fusion", ops=...)`.
Preflight validates the instructions without contacting Fusion. After execution,
retain returned entity IDs and measure the resulting bodies or occurrences with
`fu_measure`. This tool now requests Fusion's `VeryHighCalculationAccuracy`
physical properties and precise bounding boxes by default, so its compact
measurement agrees with the accuracy required by these lessons. Use `fu_params`,
`fu_timeline`, `fu_design_stats` and a refreshed
`tee_scene_summary` to inspect parameters, feature health and entity ownership.
Stop on an error and resolve it before proceeding to the next stage.

## Articulated Active Aero wing

Formula 1's 2026 Active Aero changes the position of front and rear wing elements
between Corner Mode and Straight Mode. That mechanism motivates this lesson;
the example's sections and angles are chosen for CAD practice.
[Formula 1's aerodynamics explanation](https://www.formula1.com/en/latest/article/2026-regulations-explained-all-you-need-to-know-about-f1s-new-aerodynamics.7IAt0auc32UkCEFE5ypkTB.7IAt0auc32UkCEFE5ypkTB)

The fixed mainplane has a 360 mm chord; the flap has a 160 mm chord. Both use
symmetric 12%-thickness reference sections generated from the standard
four-digit thickness equation in NASA TM 4741, printed page 3. The standard
trailing coefficient leaves finite trailing-edge thickness, which the sketch
closes explicitly. [NASA TM 4741](https://ntrs.nasa.gov/api/citations/19970008124/downloads/19970008124.pdf)

Each section contains **49 straight edges**, with 24 cosine-spaced intervals
per surface and a trailing-edge closure. The model therefore has explicit
planar facets. Coordinates use a **0.00001 mm grid**, matching the typed lane's
six-decimal-place centimetre conversion. Acceptance areas are computed from
those same coordinates, so the volume comparison tests the geometry actually
sent to Fusion. Chord is x, section height is y, and span is z.

Replay the stages in order:

1. Run `ops`. This creates `F1 fixed mainplane` and `F1 active flap` in separate
   components and binds both extrusion spans to `F1W_span=1000 mm`.
2. Refresh `tee_scene_summary` and identify each named body's actual parent
   component ID. Substitute those IDs for `{{main_component}}` and
   `{{flap_component}}` in `assembly.ops`. A body ID cannot replace its parent
   occurrence ID.
3. Preflight and execute the bound `assembly.ops`. Its origin joint places the
   hinge at `[0,0,0]`, one quarter of the way along the flap chord. Retain the
   actual ID of `F1 active flap hinge` as `wing_joint`.
4. Replace `{{wing_joint}}` in `revision.ops` with that returned ID, preflight,
   then execute. This changes `F1W_span` to 1200 mm and joint rotation to +25°.
5. Drive that same joint through the recipe's samples
   0°, 5°, 10°, 15°, 20°, 25°, 0°, 25°. Check actual relative vertices, solid
   volumes and clearance at every sample. Returning to zero must recover the
   original section arrangement at the revised span.

An alias such as `@flap` expires with its creation batch. Names identify the
objects to resolve; neither names nor guessed IDs are valid substitutions.
Neither occurrence is grounded, so compare vertices in the mainplane's frame.
On the measured component-origin joint, **+25° joint rotation produces −25°
rotation in the mainplane's XY frame**. The recipe records that sign explicitly;
the joint value alone cannot establish the flap's placement.

| Acceptance target | Initial | Revised |
|---|---:|---:|
| Common span | 1000 mm | 1200 mm |
| Joint rotation | 0° | +25° |
| Mainplane volume | 10,624,486.954542 mm³ | 12,749,384.345451 mm³ |
| Flap volume | 2,098,663.850351 mm³ | 2,518,396.620421 mm³ |
| Total solid volume | 12,723,150.804893 mm³ | 15,267,780.965872 mm³ |
| Mainplane bounds in its own frame | 360 × 43.199900 × 1000 mm | 360 × 43.199900 × 1200 mm |
| Flap bounds in mainplane frame | 160 × 19.199960 × 1000 mm | 145.239855 × 69.825825 × 1200 mm |

The measured lower bound on clearance throughout the 0°–25° joint sweep was
**16.5347105496 mm**, exceeding the 10 mm requirement. The check considers all
polygon edge pairs and containment, then subtracts a conservative rotational
displacement bound between samples and the vertex-matching allowance. Actual
Fusion vertices matched the expected sections in the mainplane's frame. This
proves the stated rigid geometric clearance; it does not calculate downforce,
drag or deflection. Actuators, endplates and composite construction are outside
this model.

## Ventilated brake disc

Brembo describes internal radial ventilation channels and their development
into multiple rows as a thermal-management mechanism. This lesson models that
radial passage arrangement with a deliberately small, replayable count.
[Brembo's ventilation explanation](https://www.brembo.com/en/motorsport/formula1/ventilation-holes)

Run the complete `ops` batch in its own empty design. It makes a Ø280 mm disc,
28 mm thick, with a Ø180 mm central opening. One radial cut seed lies at z=7 mm
and another at z=21 mm. Each seed is patterned 30 times, including the original,
creating **60 radial channels in two staggered rows**. The 12° pitch and
orthogonal seed directions produce a 6° stagger. These are internal passages
connecting the inner and outer rims; the friction faces are not axially
perforated.

The two sketch diameter dimensions drive the cut features and their patterns.
After checking the initial solid, execute `revision.ops` as a separate batch:

| Driver or acceptance target | Initial | Revised |
|---|---:|---:|
| `A79B_channel_A`, lower row diameter | 6 mm | 7 mm |
| `A79B_channel_B`, upper row diameter | 6 mm | 8 mm |
| Overall bounds | 280 × 280 × 28 mm | 280 × 280 × 28 mm |
| Solid volume | 926,762.257163 mm³ | 878,448.853574 mm³ |
| Centre-of-mass z coordinate | 14 mm | 13.859144 mm |

Verify 30 inward cylindrical passage surfaces at each row height, with the
specified radius and angular directions. Each passage must open onto both the
90 mm inner-radius rim and the 140 mm outer-radius rim. Opposite passages share
an infinite cylinder axis, so the direction of a face's actual position matters
when counting distinct channels. The upper row loses more material after the
revision, moving the centre of mass downward.

The curved rims trim each passage obliquely. The volume oracle integrates that
intersection instead of using a straight cylinder's area times 50 mm. Tight
comparisons require the harness's high-accuracy Fusion properties and adaptive
OCCT integration. Overall volume supplements the individual mouth, axis and
radius checks. The example omits material, caliper, pads, bell, mounting hardware
and thermal analysis.

The native brake and reopened F3D met their geometry checks. Its original STEP
preserves one valid solid, all 60 cylindrical passages and the two annular rims,
but its translated passage boundaries introduce a measurable volume difference:

| Revised brake representation | Volume (mm³) | Difference from oracle (mm³) | 0.1 mm³ volume gate |
|---|---:|---:|---|
| Authored curved-intersection oracle | 878,448.853573634 | 0 | Target |
| Original Fusion STEP, adaptive OCCT readback | 878,461.655761130 | +12.802187497 | **Fail** |
| Independently authored OCCT reference STEP | 878,448.853525248 | −0.000048386 | Pass |

The audit identified approximated trimmed boundaries in the Fusion translation;
tighter integration of that STEP does not recover the pre-export volume. No
acceptance tolerance was widened. The additional reference was rebuilt from the
recipe's annulus and radial cylinders and never read or repaired the Fusion
STEP. Its native and exported checks include both-rim adjacency for every
channel, radius, height, axis, centre of mass and volume.
[Translation audit](../output/cadagent-f1/step-audit/README.md),
[reference readback](../output/cadagent-f1/reference-portability/evidence.json).

## Three-pickup suspension wishbone

F1 suspension uses upper and lower wishbones to establish wheel geometry;
the members also influence airflow. This lesson isolates a planar part's
dependency graph from those vehicle-level relationships.
[Formula 1's suspension explanation](https://www.formula1.com/en/latest/article/explainer-whats-the-difference-between-pull-rod-and-push-rod-suspension.1I3wL4LEL0nQZbKZbx1Dhz)

Run `ops` to extrude a triangular web, cut a triangular lightening aperture and
join three bearing-boss profiles into the same solid. Drill the three
counterbores from the shared underside, the −z face. This common datum avoids
ambiguity among the separate coplanar boss tops.

The 30,000 mm² outer triangle contains a 7,500 mm² aperture. Pickup centres are
`[30,-70]`, `[30,70]` and `[250,0]` mm. The first two bosses are Ø32 mm; the
outboard boss is Ø28 mm. Their hole axes are parallel to z. These authored
coordinates remain fixed during the revision.

Execute `revision.ops` using its four named parameters:

| Driver or acceptance target | Initial | Revised |
|---|---:|---:|
| `A79W_plate`, web thickness | 6 mm | 8 mm |
| `A79W_boss_height`, total height from XY datum | 20 mm | 24 mm |
| `A79W_inboard_bore`, both inboard through diameters | 12 mm | 14 mm |
| `A79W_outboard_bore`, outboard through diameter | 16 mm | 18 mm |
| Overall bounds | 300 × 200 × 20 mm | 300 × 200 × 24 mm |
| Solid volume | 154,477.874452 mm³ | 199,622.387714 mm³ |

**Both the web extrusion and aperture cut depend on `A79W_plate`.** Check that
the aperture remains through the full revised 8 mm web; changing the stock
alone would leave a membrane. The boss join's distance specifies total height
from the sketch plane, so its contribution above the web is height minus web
thickness.

The inboard counterbores remain Ø20 × 4 mm deep; the outboard counterbore remains
Ø24 × 6 mm deep. Only the through diameters change. Check one solid, all three
boss locations, six inward bore/counterbore cylinders, their axial intervals and
the through aperture. Preserve the driving expressions as well as the resulting
dimensions. The planar profiles are coordinate-defined and are not claimed
fully constrained; bearing fit, spherical joints, composite layup, loads and
vehicle suspension motion are outside this part study.

## Export and repeat

Choose existing local output directories and export each whole design:

```text
tee_call(name="fu_export", args={"format":"step","out":"/absolute/output/cadagent_f1_wing.step"})
tee_call(name="fu_export", args={"format":"f3d","out":"/absolute/output/cadagent_f1_wing.f3d"})
```

Replace the example paths for each lesson and omit `of`. Read STEP independently
to verify solid count, volume, bounds, component placement and centre of mass.
Reopen F3D in a separate document and check its geometry, joint and parameter
expressions. Rediscover all entity IDs in that document. A picture or an existing
file is insufficient evidence of a correct export.

The revised editable examples and their exchange files are available below.
The brake reference is labelled separately so its acceptance is not credited to
Fusion's export.

| Lesson | Editable native design | Original Fusion STEP | STEP result |
|---|---|---|---|
| Active Aero wing | [F3D](../output/cadagent-f1/live-20260910T181655120798Z/cadagent_f1_wing.f3d) | [STEP](../output/cadagent-f1/live-20260910T181655120798Z/cadagent_f1_wing.step) | Geometry checks passed |
| Ventilated brake | [F3D](../output/cadagent-f1/live-20260910T181655120798Z/cadagent_f1_brake.f3d) | [Original STEP](../output/cadagent-f1/live-20260910T181655120798Z/cadagent_f1_brake.step) | Volume gate failed; original preserved |
| Suspension wishbone | [F3D](../output/cadagent-f1/live-20260910T181655120798Z/cadagent_f1_wishbone.f3d) | [STEP](../output/cadagent-f1/live-20260910T181655120798Z/cadagent_f1_wishbone.step) | Geometry checks passed |

**Additional brake artifact:**
[independently authored ideal-reference STEP](../output/cadagent-f1/live-20260910T181655120798Z/cadagent_f1_brake_ideal_reference.step).
This reference passes the unchanged numerical gates and is not a repaired
Fusion export.

With the Fusion bridge running, the authored harness executes all three studies:

```sh
server/.venv/bin/python benchmarks/run_a79_cadagent_f1.py
```

It writes each attempt under `output/cadagent-f1/live-<timestamp>/`, preserves
existing documents, checks archive copies, and retains successful source
demonstrations for inspection. Failed attempts remain recorded. The pure
generators in `benchmarks/fixtures/generate_f1_*.py` regenerate the packaged
recipe JSON without contacting Fusion.

To regenerate and verify the independent brake reference from the current
recipe, run [the portable reference builder](../benchmarks/fixtures/build_f1_brake_reference.py)
with the partkiln sidecar's Python, which supplies OCP:

```sh
/path/to/partkiln/bin/python benchmarks/fixtures/build_f1_brake_reference.py \
  --recipe server/src/tee/adapters/fusion/recipes/cadagent_f1_brake.json \
  --out /absolute/new-reference-directory
```

Replace the interpreter path with the installed sidecar Python and choose a
new output directory. The builder writes `reference.step` and `evidence.json`,
including recipe/file hashes, origin, measurement method and separate native
and STEP acceptance results. It refuses to replace an existing directory. The
portable regeneration was measured with OCP 7.9.3.1 and passed all its stated
checks. [Portable-run evidence](../output/cadagent-f1/reference-portability/evidence.json).

Plan: [A79 P5](../CLAUDE_A79_SCRIPT.md). API facts:
[research 71](research/71-fusion-lane.md). Integration and measured findings:
[research 80](research/80-cadagent-integration.md).

The currently connected TEE server still has the earlier in-memory topic index.
Restart/reconnect TEE to load these topics and the measurement correction. A
fresh source server has returned all three complete lessons and preflighted
their creation batches; the Desktop MCPB was not replaced.

For the same wing, brake and wishbone studies as native editable meshes, see
[the Blender lesson library](blender-lessons.md). It also includes the earlier
mechanical examples, compact house, texture workshop and dedicated fabric study,
with separate geometry and appearance checks.
