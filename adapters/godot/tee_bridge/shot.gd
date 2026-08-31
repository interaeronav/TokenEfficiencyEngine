# One-frame offscreen render for TEE's OPT-IN windowed capture (A49 P4).
#
# This runs WITHOUT --headless, because headless Godot cannot render at all:
# with --rendering-driver vulkan, opengl3 and dummy alike the viewport
# texture yields no image ("Parameter t is null"). Measured on 4.7.2, all
# three drivers, before this file existed.
#
# Consequence, stated plainly: running this opens a real window on the
# owner's display for a fraction of a second. That is why the adapter makes
# it opt-in and never the default - `capture()` refuses instead.
#
# Args:  -- --out <abs path> [--width N] [--height N] [--scene res://x.tscn]
extends SceneTree

func _initialize():
	var args = OS.get_cmdline_user_args()
	var out_path := ""
	var width := 640
	var height := 360
	var scene_res := ""
	for i in args.size():
		match args[i]:
			"--out":
				if i + 1 < args.size(): out_path = args[i + 1]
			"--width":
				if i + 1 < args.size(): width = int(args[i + 1])
			"--height":
				if i + 1 < args.size(): height = int(args[i + 1])
			"--scene":
				if i + 1 < args.size(): scene_res = args[i + 1]
	if out_path == "":
		printerr("SHOT_ERR no --out")
		quit(2)
		return
	DisplayServer.window_set_size(Vector2i(width, height))
	if scene_res != "":
		var packed = load(scene_res)
		if packed == null:
			printerr("SHOT_ERR cannot load ", scene_res)
			quit(3)
			return
		root.add_child(packed.instantiate())
	# A scene authored for gameplay often has no Camera3D - main.tscn here
	# does not - and Godot then renders an empty viewport quite correctly.
	# The first version of this file shipped that empty frame; TEE's own
	# vision model reported "0 objects", which was RIGHT and is how the gap
	# was found. Frame the visible meshes when nobody else has.
	await process_frame
	if _needs_camera():
		_add_framing_camera()
	# Two frames: one to build the tree, one to draw it.
	await process_frame
	await process_frame
	var tex = root.get_texture()
	if tex == null:
		printerr("SHOT_ERR no viewport texture")
		quit(4)
		return
	var img = tex.get_image()
	if img == null or img.is_empty():
		printerr("SHOT_ERR empty image (is this running headless?)")
		quit(5)
		return
	var err = img.save_jpg(out_path, 0.85)
	if err != OK:
		printerr("SHOT_ERR save failed ", err)
		quit(6)
		return
	print("SHOT_OK ", out_path, " ", img.get_width(), "x", img.get_height())
	quit()


func _needs_camera() -> bool:
	for node in _walk(root):
		if node is Camera3D:
			return false
	return true


func _walk(node: Node) -> Array:
	var out := [node]
	for child in node.get_children():
		out.append_array(_walk(child))
	return out


func _add_framing_camera() -> void:
	var points := []
	for node in _walk(root):
		if node is VisualInstance3D:
			var aabb = node.get_aabb()
			var origin = node.global_transform.origin
			points.append(origin + aabb.position)
			points.append(origin + aabb.position + aabb.size)
	var centre := Vector3.ZERO
	var radius := 3.0
	if points.size() > 0:
		var lo = points[0]
		var hi = points[0]
		for p in points:
			lo = Vector3(min(lo.x, p.x), min(lo.y, p.y), min(lo.z, p.z))
			hi = Vector3(max(hi.x, p.x), max(hi.y, p.y), max(hi.z, p.z))
		centre = (lo + hi) * 0.5
		radius = max((hi - lo).length() * 0.9, 2.0)
	var cam := Camera3D.new()
	cam.name = "TEEFramingCamera"
	root.add_child(cam)
	var eye = centre + Vector3(radius, radius * 0.7, radius)
	cam.look_at_from_position(eye, centre, Vector3.UP)
	print("SHOT_CAMERA framed centre=", centre, " radius=", radius)
