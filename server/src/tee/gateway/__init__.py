"""TEE Gateway (A37 P1, research 51 F1): front ANY MCP server with TEE's
progressive disclosure, budgets, and drift firewall.

The fronted backend's tools register as prefixed virtual tools
(`fs.read_file`), so discovery/describe/call ride the EXISTING meta-tools
and the always-loaded surface does not grow. Everything a backend says -
names, descriptions, schemas, results - is untrusted data: capped,
summarized, budgeted, never instructions (the research-49 posture).
"""
