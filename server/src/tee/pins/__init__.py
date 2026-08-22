"""TEE Pins: introspectable marker actors whose data lives in actor tags.

A pin is a small editor-only marker standing where something should
eventually go. Everything about it - id, display name, category, notes, and
the wishlist of what should stand there - is written into the DCC's own actor
tags, so the pin survives level reloads, is readable by any tool that can see
tags, and needs no sidecar database that could drift from the level.
"""
