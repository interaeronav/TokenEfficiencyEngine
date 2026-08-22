"""The one editor capability Epic's shipped toolsets genuinely do not cover.

Epic's `ProgrammaticToolset.execute_tool_script` runs a SANDBOXED script: it
can call registered tools and import exactly {json, math, datetime, copy, re,
time}, with no access to the `unreal` module itself. That covers orchestration
but not the long tail - anything needing unreal.EditorLevelLibrary,
unreal.AssetRegistryHelpers, custom asset types, or a transaction.

This toolset is the escape hatch: real editor Python with the full `unreal`
module, wrapped in a named undo transaction so the user can Ctrl+Z whatever
it did. It is opt-in twice over - the plugin ships disabled and must be
enabled per project, and TEE itself refuses to call it unless the server was
started with code execution allowed.

Everything else TEE needs on 5.8 is already shipped by Epic (PIE start/stop,
viewport capture, frustum queries, Blueprint graph DSL), and the execution
script's rule is not to re-port what Epic ships.
"""

import json
import traceback

import unreal

import toolset_registry


@unreal.uclass()
class TeeEditorTools(unreal.ToolsetDefinition):
    """TEE's escape hatch: unsandboxed editor Python inside an undo transaction."""

    @toolset_registry.tool_call
    @staticmethod
    def execute_editor_python(code: str, transaction_label: str) -> str:
        """Runs Python inside the editor with the full `unreal` module available.

        Unlike ProgrammaticToolset.execute_tool_script this is NOT sandboxed:
        use it only for what the registered toolsets cannot express. Assign a
        JSON-serialisable dict to a variable named `result` to return data.
        The whole run is wrapped in one undo transaction.

        Args:
            code: Python source to execute. Assign to `result` to return data.
            transaction_label: Undo-stack label, e.g. "TEE: retarget rig".
        Returns:
            A JSON string: {"ok": true, "result": {...}} or
            {"ok": false, "error": "..."} with the traceback.
        """
        namespace = {"unreal": unreal, "result": {}}
        label = transaction_label or "TEE: editor python"
        try:
            with unreal.ScopedEditorTransaction(label):
                exec(code, namespace)
            payload = namespace.get("result")
            if not isinstance(payload, dict):
                return json.dumps(
                    {
                        "ok": False,
                        "error": "the `result` variable must be a dict, not %s"
                        % type(payload).__name__,
                    }
                )
            try:
                return json.dumps({"ok": True, "result": payload})
            except (TypeError, ValueError):
                return json.dumps(
                    {"ok": True, "result": json.loads(json.dumps(payload, default=repr))}
                )
        except Exception:
            return json.dumps({"ok": False, "error": traceback.format_exc()[-1500:]})
