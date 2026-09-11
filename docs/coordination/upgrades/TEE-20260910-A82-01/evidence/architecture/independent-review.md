# A82 internal architecture review

**Outcome: PASS within the reviewed first-slice scope; no unresolved material finding.**
This is an internal Codex review, not Claude's actual-client receipt, an external
security audit, live Unreal acceptance, or legal/fabrication certification.
The reviewer authored imports/rules and reviewed those modules with additional
negative tests; service/model/GUI integration was reviewed independently of its
implementers. Exchange review here covers the shared wall-policy validator and
its integration, not a duplicate of the separate IFC/drawing review.

## Findings resolved

1. **Wrong-model GUI mutation risk.** Delayed state/preview responses could mix
   a previous document's draft/revision with the current selector. The GUI now
   pins model ID, document UUID, revision and request generation, clears pending
   drafts/candidates on selection changes, and discards stale state, preview,
   schedule, candidate, check/export and index responses. The independent rerun
   of both actual isolated headless Chrome cases passed, including the controlled
   wrong-model mutation attempt that must issue no POST.
2. **Invalid opted-in wall policy committed before derived geometry failed.**
   An owned compact-house edit setting partition.height=2700 previously committed
   revision 2 while preview refused and ak_check omitted geometry. The shared
   dependency-light geometry-policy validator now runs before core commit.
   Independently repeated: edit refuses ak_join_unsupported, the complete state
   is unchanged at revision 1, and check reports six supported joints while
   global geometric/structural/regulatory verification stays not_verified.
3. **Import boundary and numerical refusals.** Trimesh resolver=None created an
   ambient filesystem resolver from the file handle name. An explicit empty
   resolver now prevents that path, covered by a regression. Primary/dependency
   symlinks and hard links refuse; malformed manifests, extreme finite values and
   LAS scale/offset metadata are checked before unsafe arithmetic.
4. **Incomplete promoted provenance.** Promoted walls now retain reviewed fit
   residuals, tolerance, sample support, observed bounds/plane, sampling/precision
   and uncertainty alongside primary/dependency hashes. Source identities are
   rechecked at promotion, and source geometry remains unchanged.
5. **Rule validation and uncertainty.** Malformed JSON field types now produce
   bounded validation refusals/not_verified rather than runtime crashes. Review
   names, primary/adoption URLs and dates are checked for required types. Declared
   measurement uncertainty is converted with units and evaluated as an interval;
   crossing a threshold is not_verified, and uncertain equality never passes
   solely because its center equals the threshold.
6. **Cancellation publication.** Root added cooperative cancellation events:
   native steps may finish, but import publication and final export success
   manifests are gated. Partial owned export files can remain. Model authoring
   is a separate explicit action. The guide records this precise limit.

## Verification

- Imports/rules focused suite: **95 passed in 0.49 s**, warnings treated as errors.
- Independent actual headless Chrome rerun: **2 passed, 17 deselected in 3.83 s**
  with TEE_GUI_BROWSER_SMOKE=1; it used isolated owned browser profiles.
- Ruff passed for modified imports/rules/helper and their focused tests.
- Root's model/service join regression was repeated with an owned temporary
  project; refusal preserved the complete prior document.
- GUI implementer's retained evidence: output/architecture/gui-evidence/result.json.
- No paid inference, external messages, owner design edits or dependency changes
  were used for this review.

## Scope retained in delivery

The worldwide framework selects explicit jurisdictions and evaluates supplied
reviewed subsets; no verified worldwide law corpus or complete law inventory is
bundled. Schema/IDS, geometry, supplied rule results and legal approval remain
separate. Initial architecture/cabinet primitives and supported orthogonal wall
joins do not imply complete professional construction documents, arbitrary wall
junctions, hidden construction knowledge or CNC readiness. Unreal export has
source-reviewed API contracts and a stub-to-real-OBJ regression, but actual live
Editor calibration/acceptance remains pending. Actual-client installation still
requires the shared upgrade protocol's receipts.

## Reviewed source identities

Recorded UTC: 2026-09-10T23:23:00.790843+00:00

| File | SHA-256 |
|---|---|
| server/src/tee/architecture/model.py | 8fe2550bd9bad19d61339859625d7c874fac78418f1559b7a9b326333693141f |
| server/src/tee/architecture/service.py | f8af83d732225196400d7bc5bc45a4fb9444db6f80a7e2501f2bef6add4cd792 |
| server/src/tee/architecture/tools.py | 53dfb68ab30227fb0c547c125600c628d3666385af892ee651fad0153a7560db |
| server/src/tee/architecture/imports.py | edd68145b1a3477588b6f8c92523df7c61128b06dd4df5c13b231694dfd81c3b |
| server/src/tee/architecture/rules.py | 153bffed23d0108befbbbe7191afb4ccaf7c44618338d1fcab2651ada4c17720 |
| server/src/tee/architecture/gui.py | 8d1dd0dae30c7946870a33c8bad0304976db031bd0cdc3e41c7f51b644b5980f |
| server/src/tee/architecture/gui.html | 94db4274cc101642a1ccecbf3e6cb052198eeb06395b8f2b845e70fe30c0ed0c |
| server/src/tee/architecture/unreal_export.py | 9f351cf6863c7930ad7644ece36b14288c0f57411ca1a8110c62748ff5a9915d |
