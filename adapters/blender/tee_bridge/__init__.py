# SPDX-License-Identifier: GPL-3.0-or-later
"""TEE Bridge add-on: registers preferences and starts/stops the bridge
socket server inside a GUI Blender session. Background sessions use
boot_background.py instead (no add-on registration required)."""

from __future__ import annotations

import bpy

from . import bridge_server


class TeeBridgePreferences(bpy.types.AddonPreferences):
    bl_idname = __package__

    port: bpy.props.IntProperty(
        name="Port",
        description="Localhost port for the TEE bridge socket",
        default=bridge_server.DEFAULT_PORT,
        min=1024,
        max=65535,
    )
    auto_start: bpy.props.BoolProperty(
        name="Start automatically",
        description="Start the bridge when the add-on loads",
        default=True,
    )

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "port")
        layout.prop(self, "auto_start")
        running = bool(bridge_server._gui_state)
        layout.label(text=f"Bridge: {'running' if running else 'stopped'}")
        if _last_error["message"] and not running:
            box = layout.box()
            box.alert = True
            for line in _wrap(_last_error["message"], 60):
                box.label(text=line)
        row = layout.row()
        row.operator(TEE_OT_bridge_start.bl_idname)
        row.operator(TEE_OT_bridge_stop.bl_idname)


_last_error = {"message": ""}


def _wrap(text: str, width: int) -> list[str]:
    words, lines, line = text.split(), [], ""
    for word in words:
        if line and len(line) + len(word) + 1 > width:
            lines.append(line)
            line = word
        else:
            line = f"{line} {word}".strip()
    if line:
        lines.append(line)
    return lines


class TEE_OT_bridge_start(bpy.types.Operator):
    bl_idname = "tee.bridge_start"
    bl_label = "Start TEE Bridge"

    def execute(self, context):
        if bridge_server._gui_state:
            self.report({"INFO"}, "TEE bridge already running")
            return {"CANCELLED"}
        prefs = context.preferences.addons[__package__].preferences
        try:
            port = bridge_server.start_gui(port=prefs.port)
        except RuntimeError as exc:
            _last_error["message"] = str(exc)
            self.report({"ERROR"}, f"TEE bridge: {exc}")
            return {"CANCELLED"}
        _last_error["message"] = ""
        self.report({"INFO"}, f"TEE bridge listening on 127.0.0.1:{port}")
        return {"FINISHED"}


class TEE_OT_bridge_stop(bpy.types.Operator):
    bl_idname = "tee.bridge_stop"
    bl_label = "Stop TEE Bridge"

    def execute(self, context):
        bridge_server.stop_gui()
        self.report({"INFO"}, "TEE bridge stopped")
        return {"FINISHED"}


_CLASSES = (TeeBridgePreferences, TEE_OT_bridge_start, TEE_OT_bridge_stop)


def register() -> None:
    for cls in _CLASSES:
        bpy.utils.register_class(cls)
    prefs = bpy.context.preferences.addons[__package__].preferences
    if prefs.auto_start and not bpy.app.background:
        # a busy port must never break add-on enable: record the error,
        # show it in preferences, let the user fix the port and press Start
        try:
            bridge_server.start_gui(port=prefs.port)
            _last_error["message"] = ""
        except RuntimeError as exc:
            _last_error["message"] = str(exc)
            print(f"TEE bridge did not start: {exc}")


def unregister() -> None:
    bridge_server.stop_gui()
    for cls in reversed(_CLASSES):
        bpy.utils.unregister_class(cls)
