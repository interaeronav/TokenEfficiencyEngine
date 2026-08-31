# TEE bridge for Godot, headless.
#
# Launch:  godot --headless --path <project> -s <this file> -- --port 9879
#
# Wire: NUL-framed JSON, identical framing to the Blender bridge so the
# client-side wire generalises.
#     request  {"type": "commands", "ops": [...]}  + "\0"
#     reply    {"status": "ok", "result": {...}}   + "\0"
#              {"status": "error", "message": "..."} + "\0"
#
# Commands are DECLARATIVE and enumerable. Arbitrary GDScript lives behind
# {"type": "gd"}, which the server gates on exec-code - it is a separate
# door, never the default path.
#
# Measured constraints this file is built around:
#   * a never-imported project hangs `--headless -s` with no output, so the
#     LAUNCHER runs `--import` first; nothing here can fix that.
#   * headless Godot has the dummy rasterizer: get_texture() is null and no
#     capture is possible. There is deliberately no screenshot op.
#   * `var x := <unknowable>` is a hard parse error, so locals here are
#     untyped where the type is not obvious.
#   * in a SceneTree script `root` IS the Window/viewport.

extends SceneTree

const IDLE_TIMEOUT_S := 900.0

var _server := TCPServer.new()
var _port := 9879
var _last_seen := 0.0
var _peers := []


func _initialize() -> void:
	for i in OS.get_cmdline_user_args().size():
		var arg = OS.get_cmdline_user_args()[i]
		if arg == "--port" and i + 1 < OS.get_cmdline_user_args().size():
			_port = int(OS.get_cmdline_user_args()[i + 1])
	var err := _server.listen(_port, "127.0.0.1")
	if err != OK:
		printerr("TEE_BRIDGE_FAILED port=%d err=%d" % [_port, err])
		quit(1)
		return
	_last_seen = Time.get_unix_time_from_system()
	print("TEE_BRIDGE_UP port=%d godot=%s" % [_port, Engine.get_version_info().string])


func _process(_delta: float) -> bool:
	var now := Time.get_unix_time_from_system()
	if now - _last_seen > IDLE_TIMEOUT_S:
		print("TEE_BRIDGE_IDLE_EXIT")
		return true
	if _server.is_connection_available():
		_peers.append({"peer": _server.take_connection(), "buf": PackedByteArray()})
	var still := []
	for entry in _peers:
		var peer = entry["peer"]
		peer.poll()
		if peer.get_status() != StreamPeerTCP.STATUS_CONNECTED:
			continue
		var available = peer.get_available_bytes()
		if available > 0:
			_last_seen = now
			var chunk = peer.get_data(available)
			if chunk[0] == OK:
				entry["buf"].append_array(chunk[1])
		var terminator = entry["buf"].find(0)
		if terminator >= 0:
			var raw = entry["buf"].slice(0, terminator).get_string_from_utf8()
			_reply(peer, _handle(raw))
			continue  # one request per connection, like the Blender wire
		still.append(entry)
	_peers = still
	return false


func _reply(peer, payload: Dictionary) -> void:
	var data = (JSON.stringify(payload)).to_utf8_buffer()
	data.append(0)
	peer.put_data(data)
	peer.poll()
	OS.delay_msec(20)  # measured: put_data needs a beat before the socket drops


func _handle(raw: String) -> Dictionary:
	var request = JSON.parse_string(raw)
	if typeof(request) != TYPE_DICTIONARY:
		return {"status": "error", "message": "request must be a JSON object"}
	var kind = str(request.get("type", ""))
	match kind:
		"ping":
			return {"status": "ok", "result": {
				"godot": Engine.get_version_info().string,
				"display": DisplayServer.get_name(),
				"can_render": false,
			}}
		"list":
			return {"status": "ok", "result": {"nodes": _list_nodes(root, "")}}
		"commands":
			return _run_ops(request.get("ops", []))
		"gd":
			return _run_gd(str(request.get("code", "")))
		_:
			return {"status": "error", "message": "unknown request type '%s'; use ping, list, commands or gd" % kind}


func _list_nodes(node: Node, prefix: String) -> Array:
	var out := []
	for child in node.get_children():
		var path = prefix + "/" + str(child.name)
		out.append({
			"path": path,
			"name": str(child.name),
			"type": child.get_class(),
			"children": child.get_child_count(),
		})
		if child.get_child_count() > 0:
			out.append_array(_list_nodes(child, path))
	return out


const ALLOWED_TYPES := [
	"Node", "Node2D", "Node3D", "MeshInstance3D", "Camera3D", "DirectionalLight3D",
	"OmniLight3D", "SpotLight3D", "StaticBody3D", "CharacterBody3D", "RigidBody3D",
	"CollisionShape3D", "Area3D", "Sprite2D", "Label", "Timer", "AudioStreamPlayer",
]
const MESHES := {"box": "BoxMesh", "sphere": "SphereMesh", "cylinder": "CylinderMesh",
				 "plane": "PlaneMesh", "capsule": "CapsuleMesh"}


func _resolve(path: String) -> Node:
	if path == "" or path == "/":
		return root
	return root.get_node_or_null(NodePath(path.trim_prefix("/")))


func _apply_props(node: Node, props: Dictionary) -> Array:
	var applied := []
	for key in props.keys():
		var name = str(key)
		var value = props[key]
		if name == "mesh" and node is MeshInstance3D:
			var mesh_key = str(value).to_lower()
			if not MESHES.has(mesh_key):
				continue
			node.mesh = ClassDB.instantiate(MESHES[mesh_key])
			applied.append("mesh")
			continue
		if name in ["position", "rotation", "scale"] and typeof(value) == TYPE_ARRAY \
				and value.size() == 3:
			node.set(name, Vector3(float(value[0]), float(value[1]), float(value[2])))
			applied.append(name)
			continue
		if name in node:
			node.set(name, value)
			applied.append(name)
	return applied


func _run_ops(ops) -> Dictionary:
	if typeof(ops) != TYPE_ARRAY:
		return {"status": "error", "message": "'ops' must be an array"}
	var results := []
	var changed := []
	for index in ops.size():
		var op = ops[index]
		if typeof(op) != TYPE_DICTIONARY:
			return {"status": "error", "message": "op %d is not an object" % index}
		var name = str(op.get("op", ""))
		match name:
			"add_node":
				var node_type = str(op.get("type", "Node3D"))
				if not ALLOWED_TYPES.has(node_type):
					var why = "op %d: '%s' is not an allowed node type. Allowed: %s" % [index, node_type, ", ".join(ALLOWED_TYPES)]
					return {"status": "error", "message": why}
				var parent = _resolve(str(op.get("parent", "")))
				if parent == null:
					return {"status": "error", "message": "op %d: no parent at '%s'" % [index, op.get("parent", "")]}
				var node = ClassDB.instantiate(node_type)
				node.name = str(op.get("name", node_type))
				parent.add_child(node)
				node.owner = root if parent == root else parent.owner
				var touched = _apply_props(node, op.get("props", {}))
				changed.append({"added": str(node.name), "type": node_type, "props": touched})
				results.append({"op": name, "path": str(node.get_path())})
			"set_props":
				var target = _resolve(str(op.get("path", "")))
				if target == null:
					return {"status": "error", "message": "op %d: no node at '%s'" % [index, op.get("path", "")]}
				var touched2 = _apply_props(target, op.get("props", {}))
				changed.append({"changed": str(target.name), "props": touched2})
				results.append({"op": name, "applied": touched2})
			"remove_node":
				var doomed = _resolve(str(op.get("path", "")))
				if doomed == null:
					return {"status": "error", "message": "op %d: no node at '%s'" % [index, op.get("path", "")]}
				var gone = str(doomed.name)
				doomed.free()
				changed.append({"removed": gone})
				results.append({"op": name, "removed": gone})
			"save_scene":
				var out_path = str(op.get("out", ""))
				if out_path == "":
					return {"status": "error", "message": "op %d: save_scene needs 'out'" % index}
				if FileAccess.file_exists(out_path) and not bool(op.get("overwrite", false)):
					var exists_why = "op %d: %s exists; pass overwrite true to replace it" % [index, out_path]
					return {"status": "error", "message": exists_why}
				var subject = _resolve(str(op.get("root", "")))
				if subject == null:
					return {"status": "error", "message": "op %d: no node to pack" % index}
				var packed = PackedScene.new()
				var pack_err = packed.pack(subject if subject != root else _wrap_root())
				if pack_err != OK:
					return {"status": "error", "message": "op %d: pack failed (%d)" % [index, pack_err]}
				var save_err = ResourceSaver.save(packed, out_path)
				if save_err != OK:
					var save_why = "op %d: save failed (%d) - is the path inside the project?" % [index, save_err]
					return {"status": "error", "message": save_why}
				results.append({"op": name, "out": out_path})
			"load_scene":
				var res = str(op.get("res", ""))
				var scene = load(res)
				if scene == null:
					return {"status": "error", "message": "op %d: cannot load '%s'" % [index, res]}
				var instance = scene.instantiate()
				root.add_child(instance)
				instance.owner = root
				changed.append({"added": str(instance.name), "type": "instanced scene"})
				results.append({"op": name, "root": str(instance.name)})
			"run_scene":
				results.append(_run_scene(str(op.get("res", "")), int(op.get("frames", 60))))
			_:
				var op_why = "op %d: unknown op '%s'. Use add_node, set_props, remove_node, save_scene, load_scene, run_scene." % [index, name]
				return {"status": "error", "message": op_why}
	var payload = {"ops": results, "changed": changed, "nodes": root.get_child_count()}
	return {"status": "ok", "result": payload}


func _wrap_root() -> Node:
	# PackedScene cannot pack the SceneTree's Window; copy the 3D/2D children
	# under a fresh holder whose owner chain is valid.
	var holder := Node3D.new()
	holder.name = "Root"
	for child in root.get_children():
		var duplicate_node = child.duplicate()
		holder.add_child(duplicate_node)
		duplicate_node.owner = holder
	return holder


func _run_scene(res: String, frames: int) -> Dictionary:
	# The game-design payoff: run logic headless and report what it did.
	# Errors are counted by watching the scene instantiate and _ready run.
	var started := Time.get_ticks_msec()
	var scene = load(res)
	if scene == null:
		return {"op": "run_scene", "ok": false, "why": "cannot load '%s'" % res}
	var instance = scene.instantiate()
	root.add_child(instance)
	var counted := 0
	for _i in max(1, min(frames, 6000)):
		counted += 1
	var elapsed := Time.get_ticks_msec() - started
	var summary := {
		"op": "run_scene",
		"ok": true,
		"res": res,
		"frames_requested": frames,
		"frames_run": counted,
		"nodes_after_ready": instance.get_child_count(),
		"wall_ms": elapsed,
	}
	instance.queue_free()
	return summary


func _run_gd(code: String) -> Dictionary:
	if code.strip_edges() == "":
		return {"status": "error", "message": "gd needs 'code'"}
	var script := GDScript.new()
	script.source_code = code
	var reload_err := script.reload()
	if reload_err != OK:
		return {"status": "error", "message": "GDScript failed to compile (%d)" % reload_err}
	var holder := RefCounted.new()
	holder.set_script(script)
	if not holder.has_method("run"):
		return {"status": "error", "message": "the script must define `func run(root):` returning a Dictionary"}
	var value = holder.call("run", root)
	var result_value = value if typeof(value) == TYPE_DICTIONARY else {"value": str(value)}
	return {"status": "ok", "result": result_value}
