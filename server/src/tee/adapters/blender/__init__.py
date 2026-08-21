"""Blender adapter (decision A3).

Speaks the official Blender Lab MCP add-on wire protocol as a client
(localhost:9876, null-delimited JSON execute requests), so it works unchanged
against either the official extension or TEE's own bridge add-on.
"""
