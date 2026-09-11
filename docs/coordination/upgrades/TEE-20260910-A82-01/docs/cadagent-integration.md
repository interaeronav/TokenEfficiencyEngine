# CADAgent modelling in TEE

TEE integrates CADAgent's shell and feature-pattern operations into the existing
Fusion lane. Use the same Fusion bridge and `tee_batch`; no additional add-in,
backend, API key or Python dependency is required. The original MIT licence and
source revision are preserved alongside the implementation.

Start a fresh TEE server from this checkout to load the integration. A client
already running TEE must reconnect/restart its server. The downloadable Desktop
package built before A79 does not contain these changes.

```text
tee_search_tools(query="cadagent")
tee_call(name="lane_guide", args={"adapter":"fusion","topic":"cadagent"})
```

The guide returns a complete three-operation example: create a 60 × 40 × 20 mm
box, then remove its top and shell inward by 2 mm. Run `lane_preflight` on its
`ops`, then pass those operations to `tee_batch(adapter="fusion", ops=...)`.
The measured result is 11,712 mm³ with the original external dimensions.

## Operations

All operations use `op: "create"`. Dimensions are millimetres; angles are degrees.

| Kind | Required properties | Optional properties |
|---|---|---|
| `shell` | `body`, positive `inside` and/or `outside` thickness | `remove_faces` directional labels such as `["+z"]`; default `[]` makes a closed shell. `tangent` defaults true; `shell_type` is `sharp` or `rounded`. |
| `rectangular_pattern` | `features`, `axis`, `count`, signed `spacing` | Second direction: `axis2`, `count2`, `spacing2` together. |
| `circular_pattern` | `features`, `axis`, `count` | `angle` defaults 360; accepted range `(0,360]`. |

`features` holds 1–32 feature IDs, such as `["f2"]`, or earlier batch aliases
such as `["@bore.feature"]`. Counts include the seed and must be integers
2–1000; two-direction patterns are capped at 1000 total instances. Axes are
`x`, `y` or `z`. Negative rectangular spacing reverses direction. Circular axes
pass through the root-component origin; arbitrary anchors are unsupported.

Targets must be native bodies/features in the root component. Occurrence
proxies and nested-component targets are refused. Shell openings select the
outermost planar face facing the given direction, using the existing Fusion
face selector. They are not arbitrary face-token selections.

A shell alias addresses its one resulting body; `@alias.feature` addresses the
shell feature. A pattern can affect several bodies: **both `@alias` and
`@alias.feature` address its feature**. Use the returned body IDs for subsequent
body operations. Names are labels, not IDs, and aliases last only one batch.

## Verification and rollback

The integration inherits TEE's preflight, checkpoints and diffs. Malformed input
fails before connection/checkpoint. A failed native operation rolls its batch
back. New Fusion checkpoints carry the document creation ID and refuse to
restore into another document. Historical checkpoints without that field retain
their previous behavior; take a new checkpoint before changing documents.

Six live cases passed on Fusion **2705.1.15**: open/closed/outside shells,
six holes in a rectangular grid, four holes in a circle, and three separate
cubes with negative spacing. Volumes and actual hole centres were read from
Fusion geometry. All six STEP files were independently measured by OCCT 7.9.3;
all six F3D archives reopened with their bodies and feature counts intact.
Rollback and foreign-document refusal were checked. Detailed evidence lives in
[`research/80-evidence/live.json`](research/80-evidence/live.json).

## Integration scope

CADAgent's official repository says its hosted service has shut down. Its
standalone chat UI and self-hosted backend form a separate application whose
backend calls model providers. TEE uses the local modelling sequences; the
client AI continues to own the conversation and cloud calls. No provider keys,
Supabase sessions, arbitrary-code WebSocket or bundled libraries are imported.

TEE already covers many overlapping functions (sketches, extrusions, holes,
fillets, chamfers, parameter changes, suppression, measurement and exports).
CADAgent's threads/tapped holes, detailed topology lists, arbitrary face tools
and standalone agent loop are not added by this integration.

Research and upstream citations: [`research/80-cadagent-integration.md`](research/80-cadagent-integration.md).


## Advanced Fusion lessons

Three complete, live-verified examples now teach how to combine these features
with parametric sketches, revolves and assemblies. Request the Fusion guide
index, then choose `cadagent_enclosure`, `cadagent_flange` or `cadagent_joint`.
Each contains creation, revision, geometry checks and export calls. The
[advanced lesson guide](cadagent-advanced-fusion.md) links the measured native
examples and explains the face-relative hole movement and joint flip that live
replay revealed. These are reusable instructions for the client AI, not model
training or an independent CADAgent performance result.


For difficult F1-inspired examples, see [the Formula One lessons](cadagent-f1-fusion.md):
an articulated wing, a disc with sixty radial cooling passages and a suspension
wishbone. The complete recipes are `cadagent_f1_wing`, `cadagent_f1_brake` and
`cadagent_f1_wishbone`, through the same `lane_guide` interface.

## Blender lessons

The [Blender lesson library](blender-lessons.md) carries the same six mechanical
studies into native editable Blender workflows, with a compact modern house,
texture workshop and dedicated fabric study. Each exposes build, revise and
inspect stages through Blender's existing guarded Python tool; mesh and material
acceptance are recorded separately from the Fusion BRep checks.

The [local continuous-learning loop](continuous-learning.md) now includes
CADAgent lesson execution through TEE's shared tool boundary. It fits numerical
reliability and cost models and accepts separate reported-quality feedback;
it does not fine-tune CADAgent or autonomously rewrite its lessons.
