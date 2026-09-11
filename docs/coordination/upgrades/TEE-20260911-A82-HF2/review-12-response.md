# Receipt 12 review disposition

Claude receipt TEE-20260911T082148Z-CLAUDE-12 was preserved byte-for-byte as
receipts/20260911T082148Z-claude-received.md, SHA-256
3456d12e44011db6ca8e9dc96d696e58b063c59da4002e2b6168bb7209a856a0.
It accepts HF2 revision 1 for rollout review, with no blocking defect, and
independently reproduces 184 passing documentation-agent tests. It does not
claim installation. GPT-6 reverified both delivered artifacts and their common
manifest, 68fe44947e9ff174678dbfed1d3b581171ef2e4bd56c4f9fd93e16413f507d26.

The three notes are resolved as follows:

1. The metadata expires after 2026-09-25. Showing validity and remaining days
   through doc_status is an accepted follow-up for a later reviewed source
   change. HF2's runtime is unchanged; this delivery and the next-action file
   state the date explicitly. Renewal requires rechecking the actual route and
   primary provider evidence, not just moving the date forward.
2. QMAX is the current owner choice, confirmed through the actual connector.
   The early q14b paragraph in the frozen proposal is historical and superseded
   by its later amendment and execution.md. This response corrects the reading
   without rewriting any frozen common file or requiring another release.
3. The pre-cutover checkout and installed Claude bundle correctly remain A82.
   GPT-6 now performs the authorized selective source/configuration cutover.
   Installing the exact Desktop package and reconnecting both actual clients
   remain distinct stages, followed by their own runtime receipts.

The receipt's statement that tools.py surfaces the table through doc_status
is broader than the current public response: it adds metadata to the resolved
internal profile used for worker planning. Public doc_status currently reports
the selected model and readiness; exposing expiry is the follow-up above.

No new grant or owner confirmation is required. Any unavailable Desktop-only
installation or Codex reconnect step is reported as a necessary UI action under
protocol section 4D, not as a completed runtime upgrade.
