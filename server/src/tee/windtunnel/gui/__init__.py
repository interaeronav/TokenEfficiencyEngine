"""A control surface for the wind-tunnel lane. Not a viewer, on purpose.

A67 ruled that TEE builds no viewer, and partkiln refused a 3-D pane on the
ground that a second-rate GL widget inside Qt would be a worse picture and a
whole new surface to maintain. Both stand here: this window lists cases,
starts and cancels runs, shows the verdict, and hands the picture to the
application that owns it. It renders nothing.

Three of the four modules are Qt-free and tested with PySide6 absent:
`actions` builds argument dicts for the lane's own tools, `shell` calls them
through the registry and formats what came back. `app` is the only module
that touches Qt, and it imports PySide6 inside its functions.

The window is a client of the same registry a model drives, so there is no
path through it that a tool call could not take, and no state of its own to
drift: what it shows is what `wt_case`, `wt_status` and `wt_result` answered.
"""
