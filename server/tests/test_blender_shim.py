from tee.adapters.blender.shim import compact_traceback, firewall_check

V52 = (5, 2, 0)
V45 = (4, 5, 3)


def codes(code, version):
    return {h["code"] for h in firewall_check(code, version)}


def test_stale_5x_idioms_flagged_on_52():
    assert "use_auto_smooth_removed" in codes("obj.data.use_auto_smooth = True", V52)
    assert "id_prop_dict_access" in codes("scene['cycles'].samples = 8", V52)
    assert "eevee_next_id_on_5x" in codes("scene.render.engine = 'BLENDER_EEVEE_NEXT'", V52)
    assert "scene_node_tree_removed" in codes("tree = scene.node_tree", V52)
    assert "bgl_removed" in codes("import bgl\nbgl.glClear(0)", V52)
    assert "legacy_action_fcurves" in codes("for f in action.fcurves: pass", V52)
    assert "sculpt_tool_renamed" in codes("brush.sculpt_tool = 'DRAW'", V52)
    assert "file_output_node_api" in codes("node.file_slots.new('x')", V52)
    assert "geonodes_socket_dict_access" in codes(
        "obj.modifiers['GeometryNodes']['Socket_2'] = 5.0", V52
    )
    assert "vse_strip_times_renamed" in codes("strip.frame_final_start = 10", V52)


def test_version_gating():
    # BLENDER_EEVEE is wrong on 4.x but right on 5.x
    code = "scene.render.engine = 'BLENDER_EEVEE'"
    assert "eevee_id_on_4x" in codes(code, V45)
    assert codes(code, V52) == set()
    # 5.2-only geometry nodes RNA change not flagged on 4.5
    gn = "obj.modifiers['GeometryNodes']['Socket_2'] = 5.0"
    assert codes(gn, V45) == set()
    # use_auto_smooth already wrong on 4.5 (removed in 4.1)
    assert "use_auto_smooth_removed" in codes("m.use_auto_smooth = True", V45)


def test_clean_modern_code_passes():
    code = (
        "import bpy\n"
        "scene = bpy.context.scene\n"
        "scene.cycles.samples = 16\n"
        "scene.render.engine = 'CYCLES'\n"
        "result = {'ok': True}\n"
    )
    assert codes(code, V52) == set()
    assert codes(code, V45) == set()


def test_compact_traceback_keeps_last_line_and_context():
    tb = (
        "Traceback (most recent call last):\n"
        '  File "<string>", line 3, in <module>\n'
        "    obj.data.use_auto_smooth = True\n"
        "AttributeError: 'Mesh' object has no attribute 'use_auto_smooth'\n"
    )
    out = compact_traceback(tb)
    assert out.startswith("AttributeError:")
    assert "use_auto_smooth = True" in out
    assert "Traceback" not in out
    assert len(out) <= 400


def test_firewall_ignores_comments():
    code = (
        "import bpy\n"
        "# use_auto_smooth was the old way; scene.node_tree too\n"
        "scene = bpy.context.scene\n"
        "result = {}\n"
    )
    assert codes(code, V52) == set()


def test_firewall_still_catches_string_engine_ids():
    assert "eevee_next_id_on_5x" in codes(
        "scene.render.engine = 'BLENDER_EEVEE_NEXT'  # set engine", V52
    )
