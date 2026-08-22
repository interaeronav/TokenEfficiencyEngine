# Skill evals

Three scenarios, authored before the skill was polished (R21). The
machine-checkable core of each is enforced by the server test suite
(`server/tests/test_assets_selection.py`, `test_assets_lanes_context.py`,
`test_assets_verify.py`); these descriptions are the full agent-level
scenarios for end-to-end runs on a live setup.

## 1. Furnish the fixture bedroom

Given the fixture plan's 3.2 × 3.0 m bedroom (walls, one 0.86 m door,
one window) and the site style brief:
- plan bed (anchored to the wall opposite the door), wardrobe, nightstand;
- `as_place` validates clean on the FIRST apply attempt (no door-swing or
  passage violations);
- every asset accepted or snapped by the scale policy — zero rejects kept
  in the plan;
- `as_verify` ends with `no geometric conflicts`; ≤ 1 render used;
- `as_credits` lists every non-CC0 asset.

Pass = clean verify + credits + no license_blocked answers ignored.

## 2. The kitchen work-triangle trap

A kitchen plan places the refrigerator in the far corner: the
sink-stove-refrigerator triangle has a 4.1 m leg (limit 2.7) — seeded
deliberately.
- The validator MUST flag `work_triangle` (guideline severity) on the
  first `as_place` call;
- the agent moves the refrigerator (not the sink plumbing wall) and
  re-validates clean;
- aisle clearances (1067 mm US) hold after the move.

Pass = trap caught by the table, not by the agent's intuition; fix keeps
plumbing-wall anchors.

## 3. Reject the 0.4 m "sofa"

A search shortlist deliberately contains a miniature sofa model
(0.4 × 0.18 × 0.15 m, a scale-toy scan).
- `as_import(asset_class="sofa")` answers `asset_rejected` with the
  one-line envelope reason;
- the agent picks the next shortlist row instead of retrying with a
  manual scale factor;
- the accepted sofa lands within the envelope and against a wall.

Pass = no manual scale override attempted; second candidate placed and
verified.
