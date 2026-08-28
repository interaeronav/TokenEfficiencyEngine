"""The TEE-native model's chore layer (A34 M2, research 50 rung 0).

Server-side jobs for a local code-expert model - traceback triage, script
repair drafts, lint explanation, extract refinement, fact structuring,
recap compression, kb rerank. Every chore answers in a schema-validated
shape with a provenance stamp, degrades to the deterministic path when no
endpoint runs, and never sits in the client's token path. The A30
boundary is part of every template: reasoning over in-context evidence
yes, API facts from weights never.
"""
