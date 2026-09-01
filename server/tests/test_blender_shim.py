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


def test_a61_drift_faults_caught_in_a_real_headless_run() -> None:
    """Four Blender 5.x drift faults, each of which cost a live run before it
    was catalogued - which is the exact cost this firewall exists to remove.

    They came out of rendering an actual shot in Blender 5.2, not out of a
    changelog, so each pattern is the code that was really written and each
    hint is what really fixed it.
    """
    # the physical sky was renamed, and so was one of its inputs
    assert "sky_nishita_renamed" in codes('sky.sky_type = "NISHITA"', (5, 2, 0))
    assert "sky_nishita_renamed" in codes("sky.dust_density = 2.4", (5, 2, 0))
    assert "sky_nishita_renamed" not in codes('sky.sky_type = "NISHITA"', (4, 2, 0))

    # video output is behind a media_type switch on 5.x
    ffmpeg = 'scene.render.image_settings.file_format = "FFMPEG"'
    assert "ffmpeg_needs_video_media_type" in codes(ffmpeg, (5, 2, 0))
    assert "ffmpeg_needs_video_media_type" not in codes(ffmpeg, (4, 2, 0))

    # sequences -> strips, plus the falsy-empty-collection trap in the hint
    assert "sequence_editor_sequences_renamed" in codes(
        "book = scene.sequence_editor.sequences", (5, 2, 0)
    )
    hint = next(
        h["hint"]
        for h in firewall_check("scene.sequence_editor.sequences", (5, 2, 0))
        if h["code"] == "sequence_editor_sequences_renamed"
    )
    assert "is None" in hint and "falsy" in hint

    # probing the CLASS rna reports capability the instance does not have
    probe = 'bpy.types.ImageFormatSettings.bl_rna.properties["file_format"].enum_items'
    assert "class_rna_capability_probe" in codes(probe, (5, 2, 0))
    # and that one is not version-gated: it was never right on any version
    assert "class_rna_capability_probe" in codes(probe, (3, 6, 0))

    # none of them fire on code that is correct for the connected version
    assert codes('scene.render.engine = "BLENDER_EEVEE"', (5, 2, 0)) == set()
    assert codes('sky.sky_type = "MULTIPLE_SCATTERING"', (5, 2, 0)) == set()
