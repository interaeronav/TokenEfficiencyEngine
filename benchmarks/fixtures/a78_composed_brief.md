# A78 composed transfer brief: original inspection-air module

Frozen before the guided microtask outputs were read. This is a composition
pilot, not a reproduction of the AETHER car and not a manufacturing release.

Create an original graphite, satin-silver and electric-blue inspection-air
module. Work inside separate task-owned Fusion and Blender scopes. Preserve
all existing user documents and unrelated scene content.

In Fusion, build a native mounting plate with a 125 x 90 mm rectangular
footprint, 6 mm thickness and four 6 mm diameter through-holes centered
100 mm apart in X and 65 mm apart in Y. The plate is centered on the origin,
with its bottom on Z=0. Make plate thickness a driving parameter named
module_plate_t. Export STEP and a native F3D. Import that actual plate into
Blender at its correct physical size. After the first geometry check, change
module_plate_t to 7.5 mm, recompute, and propagate the changed plate to the
presentation scene without duplicating the old plate.

Design a separate hollow intake housing above the plate. Its horizontal
centerline is parallel to X at Y=0 and Z=80 mm; total housing length is 94 mm;
inlet outside diameter is 90 mm and unobstructed inlet diameter is at least
58 mm. Use a visually coherent rim, a rear collar, a continuous outer housing
and two mounting supports. Give the user a clear view through the opening;
an opaque disk painted black does not qualify. Keep housing and supports
separate, named editable objects. Their exact curves and finishing details
are the model's design choice. Do not label the shape aerodynamically proven.

Use graphite for the main housing, satin silver for the mounting structure
and narrow electric-blue accents. Produce a clean studio product image and
a close-up that clearly shows the hollow inlet and mounting relationship.
Set the product camera to 63 mm focal length. Output both at 1600 x 1000 or
higher, with readable surfaces, no clipped parts and consistent materials.

Deliver the STEP, F3D, .blend, two renders and a one-page PDF showing measured
mounting dimensions, plate thickness after the revision, hole count and the
real Fusion-to-Blender scale check. Describe which parts are native solids
versus presentation geometry. Verify by reading the actual app geometry,
reopening the saved files and inspecting the actual render. Report anything
that remains incomplete.

## Independent reviewer gates (not instructions for constructing the answer)

- Before/after fingerprints of protected documents and scene entities match.
- Plate dimensions 125 x 90 x 7.5 mm; four actual through holes, diameter 6 mm,
  center spacing 100 x 65 mm; native solid; parameter still drives thickness.
- Plate volume equals (125*90 - 4*pi*3^2)*7.5 mm^3 within 0.1%; cross-kernel
  round-trip tolerance independently measured and stated if a broader band
  is required. Exactly one current imported plate in Blender.
- Export/import three-axis extents agree within 0.1%, including the late
  thickness change. .blend and F3D reopen with expected editable content.
- Housing length and inlet dimensions independently measured; centerline
  and optical opening verified geometrically and in the close-up. No
  intersection through the plate or protected geometry.
- At least two coherent renders, actual lens and image size read back; blind
  visual review grades material plausibility, lighting, framing and detail.
- PDF contains actual measured values and accurately describes native solids,
  visual geometry, late revision and unvalidated aerodynamic status.
- No strong-model rewrite or replay of a finished task script. Any intervention
  is recorded as assistance and disqualifies an unassisted-local success claim.
