"""Godot adapter (A49): headless game-scene work through the TEE kernel."""

from tee.adapters.godot.adapter import GodotAdapter
from tee.adapters.godot.wire import GodotWire

__all__ = ["GodotAdapter", "GodotWire"]
