"""Tier-2 modeling ops for the Blender batch interpreter (A21).

Each op compiles to the research-verified BMesh patterns:
- wall_with_openings / slab / profile_extrude: mathutils.geometry.
  tessellate_polygon (respects holes) -> faces -> recalc normals ->
  bmesh.ops.solidify - watertight by construction (verified headless,
  0 non-manifold edges).
- roof: explicit closed prisms (flat / shed / gable). Hip needs a
  straight-skeleton library (choice deliberately open per research 36) -
  it answers not_implemented with that exact note.
- opening_cut: object boolean modifier, solver MANIFOLD default with
  EXACT fallback; the legacy 'FAST' identifier is GONE in 5.x and is
  guarded here.
- param_set: geometry-node inputs addressed STRICTLY by socket
  identifier through one chokepoint (the 5.2 NodesModifier RNA break:
  ID-property subscripting raises; `md.properties.inputs.<id>.value` is
  the 5.2+ API; pre-5.2 falls back to ID properties).
"""

MODELING_LIB = '''
import mathutils

def _watertight_from_polys(name, polys, thickness, offset_dir):
    """tessellate_polygon (holes respected) -> bmesh faces -> solidify.
    polys: list of vertex loops in a local 2D plane as Vectors((u, v, 0));
    the mesh is built in the XZ plane (u = local x, v = local z)."""
    verts2d = [v for poly in polys for v in poly]
    tris = mathutils.geometry.tessellate_polygon(polys)
    mesh = bpy.data.meshes.new(name)
    bm = bmesh.new()
    bmv = [bm.verts.new((v.x, 0.0, v.y)) for v in verts2d]
    for tri in tris:
        try:
            bm.faces.new([bmv[i] for i in tri])
        except ValueError:
            pass  # duplicate face from degenerate tessellation input
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    bmesh.ops.solidify(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:],
                       thickness=thickness)
    bm.to_mesh(mesh)
    bm.free()
    return mesh

def _wall_with_openings(op):
    p = dict(op.get("props") or {})
    start = p.get("start", [0.0, 0.0])
    end = p.get("end", [float(p.get("length", 4.0)), 0.0])
    height = float(p.get("height", 2.7))
    thickness = float(p.get("thickness", 0.2))
    dx, dy = end[0] - start[0], end[1] - start[1]
    length = (dx * dx + dy * dy) ** 0.5
    if length <= 0:
        raise ValueError("wall start == end (zero length)")
    polys = [[mathutils.Vector((x, z, 0.0)) for x, z in
              ((0, 0), (length, 0), (length, height), (0, height))]]
    for o in p.get("openings") or []:
        x0 = float(o["offset"]); w = float(o["width"])
        s = float(o.get("sill", 0.0)); h = float(o.get("head", 2.03))
        if x0 < 0 or x0 + w > length:
            raise ValueError("opening at %.2f width %.2f exceeds wall length %.2f"
                             % (x0, w, length))
        if h > height:
            raise ValueError("opening head %.2f above wall height %.2f" % (h, height))
        polys.append([mathutils.Vector((x, z, 0.0)) for x, z in
                      ((x0, s), (x0 + w, s), (x0 + w, h), (x0, h))])
    mesh = _watertight_from_polys(op.get("name") or "Wall", polys, thickness, 1)
    obj = _link(bpy.data.objects.new(op.get("name") or "Wall", mesh))
    obj.location = (start[0], start[1], float(p.get("level_z", 0.0)))
    obj.rotation_euler = (0.0, 0.0, math.atan2(dy, dx))
    return obj

def _slab(op):
    p = dict(op.get("props") or {})
    polygon = p.get("polygon")
    if not polygon or len(polygon) < 3:
        raise ValueError("slab needs props.polygon with >= 3 [x, y] points")
    thickness = float(p.get("thickness", 0.2))
    polys = [[mathutils.Vector((pt[0], pt[1], 0.0)) for pt in polygon]]
    for hole in p.get("holes") or []:
        polys.append([mathutils.Vector((pt[0], pt[1], 0.0)) for pt in hole])
    # build in XY: reuse the helper by treating (x, y) as (u, v), then the
    # mesh built in XZ is rotated back onto XY
    mesh = _watertight_from_polys(op.get("name") or "Slab", polys, thickness, 1)
    obj = _link(bpy.data.objects.new(op.get("name") or "Slab", mesh))
    obj.rotation_euler = (math.pi / 2, 0.0, 0.0)  # XZ-built -> lie flat in XY
    obj.location = (0.0, 0.0, float(p.get("top_z", 0.0)))
    return obj

def _roof(op):
    p = dict(op.get("props") or {})
    kind = str(p.get("kind", "gable"))
    x0, y0, x1, y1 = (float(v) for v in p.get("footprint", [0, 0, 4, 3]))
    base = float(p.get("base_z", 2.7))
    pitch = math.radians(float(p.get("pitch_deg", 35.0)))
    name = op.get("name") or "Roof"
    mesh = bpy.data.meshes.new(name)
    bm = bmesh.new()
    if kind == "flat":
        rise = float(p.get("thickness", 0.25))
        v = [bm.verts.new(c) for c in (
            (x0, y0, base), (x1, y0, base), (x1, y1, base), (x0, y1, base),
            (x0, y0, base + rise), (x1, y0, base + rise),
            (x1, y1, base + rise), (x0, y1, base + rise))]
        faces = [(0, 1, 2, 3), (7, 6, 5, 4), (0, 4, 5, 1), (1, 5, 6, 2),
                 (2, 6, 7, 3), (3, 7, 4, 0)]
    elif kind == "shed":
        rise = (y1 - y0) * math.tan(pitch)
        v = [bm.verts.new(c) for c in (
            (x0, y0, base), (x1, y0, base), (x1, y1, base), (x0, y1, base),
            (x1, y1, base + rise), (x0, y1, base + rise))]
        faces = [(3, 2, 1, 0), (0, 1, 4, 5), (1, 2, 4), (3, 0, 5), (2, 3, 5, 4)]
    elif kind == "gable":
        axis = str(p.get("ridge_axis", "x"))
        if axis == "x":
            ridge_y = (y0 + y1) / 2
            rise = (y1 - y0) / 2 * math.tan(pitch)
            v = [bm.verts.new(c) for c in (
                (x0, y0, base), (x1, y0, base), (x1, y1, base), (x0, y1, base),
                (x0, ridge_y, base + rise), (x1, ridge_y, base + rise))]
            faces = [(3, 2, 1, 0), (0, 1, 5, 4), (2, 3, 4, 5), (1, 2, 5), (3, 0, 4)]
        else:
            ridge_x = (x0 + x1) / 2
            rise = (x1 - x0) / 2 * math.tan(pitch)
            v = [bm.verts.new(c) for c in (
                (x0, y0, base), (x1, y0, base), (x1, y1, base), (x0, y1, base),
                (ridge_x, y0, base + rise), (ridge_x, y1, base + rise))]
            faces = [(3, 2, 1, 0), (0, 4, 5, 3), (4, 1, 2, 5), (0, 1, 4), (2, 3, 5)]
    elif kind == "hip":
        raise ValueError("roof kind 'hip' pending a straight-skeleton library "
                         "choice (research 36) - use gable/shed/flat")
    else:
        raise ValueError("unknown roof kind %r (gable|shed|flat)" % kind)
    for f in faces:
        try:
            bm.faces.new([v[i] for i in f])
        except ValueError:
            pass
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    bm.to_mesh(mesh)
    bm.free()
    obj = _link(bpy.data.objects.new(name, mesh))
    obj["tee_pitch_deg"] = float(p.get("pitch_deg", 35.0))
    return obj

def _stairs(op):
    p = dict(op.get("props") or {})
    rise_total = float(p.get("rise_total", 2.7))
    riser_max = float(p.get("riser_max", 0.196))
    tread = float(p.get("tread", 0.28))
    width = float(p.get("width", 1.0))
    n = max(2, int(math.ceil(rise_total / riser_max)))
    riser = rise_total / n
    name = op.get("name") or "Stairs"
    mesh = bpy.data.meshes.new(name)
    bm = bmesh.new()
    for i in range(n):
        x0, x1 = i * tread, (i + 1) * tread
        z1 = (i + 1) * riser
        corners = [
            (x0, 0, 0), (x1, 0, 0), (x1, width, 0), (x0, width, 0),
            (x0, 0, z1), (x1, 0, z1), (x1, width, z1), (x0, width, z1)]
        v = [bm.verts.new(c) for c in corners]
        for f in ((3, 2, 1, 0), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5),
                  (2, 3, 7, 6), (3, 0, 4, 7)):
            bm.faces.new([v[i2] for i2 in f])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    bm.to_mesh(mesh)
    bm.free()
    obj = _link(bpy.data.objects.new(name, mesh))
    obj["tee_riser_mm"] = round(riser * 1000, 1)
    obj["tee_tread_mm"] = round(tread * 1000, 1)
    _apply_props(obj, p)
    return obj

_BOOL_SOLVERS = ("MANIFOLD", "EXACT", "FLOAT")

def _opening_cut(op):
    target = _find(op.get("id"))
    if target is None:
        raise ValueError("no entity %r for opening_cut" % op.get("id"))
    p = dict(op.get("props") or {})
    solver = str(p.get("solver", "MANIFOLD")).upper()
    if solver == "FAST":
        raise ValueError("boolean solver 'FAST' was removed in Blender 5.x - "
                         "use MANIFOLD (default) or EXACT")
    if solver not in _BOOL_SOLVERS:
        raise ValueError("unknown boolean solver %r (MANIFOLD|EXACT|FLOAT)" % solver)
    center = p.get("center") or [0, 0, 1]
    size = p.get("size") or [0.9, 1.0, 2.03]
    cutter_mesh = bpy.data.meshes.new("tee_cutter")
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bm.to_mesh(cutter_mesh)
    bm.free()
    cutter = _link(bpy.data.objects.new("tee_cutter", cutter_mesh))
    cutter.location = center
    cutter.scale = [float(s) for s in size]  # over-penetrating manifold box
    cutter.hide_viewport = True
    cutter.hide_render = True
    mod = target.modifiers.new(name="tee_opening", type="BOOLEAN")
    mod.operation = "DIFFERENCE"
    mod.object = cutter
    try:
        mod.solver = solver
    except TypeError:
        mod.solver = "EXACT"  # older enum set
    if p.get("apply"):
        with bpy.context.temp_override(object=target, active_object=target,
                                       selected_objects=[target]):
            bpy.ops.object.modifier_apply(modifier=mod.name)
        bpy.data.objects.remove(cutter, do_unlink=True)
        return target, None
    return target, cutter

def _array_along(op):
    src = _find(op.get("id"))
    if src is None:
        raise ValueError("no entity %r for array_along" % op.get("id"))
    p = dict(op.get("props") or {})
    count = int(p.get("count", 2))
    step = [float(v) for v in (p.get("step") or [1.0, 0.0, 0.0])]
    copies = []
    for i in range(1, count):
        dup = src.copy()  # linked duplicate: shares mesh data
        _link(dup)
        dup.location = (src.location[0] + step[0] * i,
                        src.location[1] + step[1] * i,
                        src.location[2] + step[2] * i)
        copies.append(dup)
    return copies

def _profile_extrude(op):
    p = dict(op.get("props") or {})
    profile = p.get("profile")
    if not profile or len(profile) < 3:
        raise ValueError("profile_extrude needs props.profile with >= 3 [x, y] points")
    depth = float(p.get("depth", 1.0))
    polys = [[mathutils.Vector((pt[0], pt[1], 0.0)) for pt in profile]]
    mesh = _watertight_from_polys(op.get("name") or "Profile", polys, depth, 1)
    obj = _link(bpy.data.objects.new(op.get("name") or "Profile", mesh))
    _apply_props(obj, p)
    return obj

def _set_gn_input(md, socket, value):
    """THE chokepoint for geometry-node inputs (A24): identifier-addressed,
    version-shimmed. 5.2+: md.properties.inputs.<identifier>.value;
    pre-5.2: ID-property subscript."""
    props = getattr(md, "properties", None)
    if props is not None and hasattr(props, "inputs"):
        sock = getattr(props.inputs, socket, None)
        if sock is None:
            names = [s for s in dir(props.inputs) if s.startswith("Socket")]
            raise ValueError("no socket %r on modifier %r; sockets: %s"
                             % (socket, md.name, names))
        sock.value = value
        return
    try:
        md[socket] = value  # pre-5.2 ID-property path
    except (KeyError, TypeError) as exc:
        raise ValueError("cannot set %r on modifier %r: %s" % (socket, md.name, exc))

def _param_set(op):
    obj = _find(op.get("id"))
    if obj is None:
        raise ValueError("no entity %r for param_set" % op.get("id"))
    p = dict(op.get("props") or {})
    modifier_name = p.get("modifier")
    md = obj.modifiers.get(modifier_name) if modifier_name else next(
        (m for m in obj.modifiers if m.type == "NODES"), None)
    if md is None or md.type != "NODES":
        raise ValueError("no geometry-nodes modifier %r on %r"
                         % (modifier_name, obj.name))
    for socket, value in (p.get("values") or {}).items():
        _set_gn_input(md, str(socket), value)
    return obj
'''

# dispatch branches appended into the batch interpreter
MODELING_DISPATCH = """
    elif _kind == "wall_with_openings":
        _obj = _wall_with_openings(_op)
        _eid = _uid(_obj)
        _created.append(_eid)
        _touched[_eid] = _obj
    elif _kind == "slab":
        _obj = _slab(_op)
        _eid = _uid(_obj)
        _created.append(_eid)
        _touched[_eid] = _obj
    elif _kind == "roof":
        _obj = _roof(_op)
        _eid = _uid(_obj)
        _created.append(_eid)
        _touched[_eid] = _obj
    elif _kind == "stairs":
        _obj = _stairs(_op)
        _eid = _uid(_obj)
        _created.append(_eid)
        _touched[_eid] = _obj
    elif _kind == "opening_cut":
        _target, _cutter = _opening_cut(_op)
        _eid = _uid(_target)
        if _eid not in _created and _eid not in _modified:
            _modified.append(_eid)
        _touched[_eid] = _target
        if _cutter is not None:
            _ceid = _uid(_cutter)
            _created.append(_ceid)
            _touched[_ceid] = _cutter
    elif _kind == "array_along":
        for _dup in _array_along(_op):
            _eid = _uid(_dup)
            _created.append(_eid)
            _touched[_eid] = _dup
    elif _kind == "profile_extrude":
        _obj = _profile_extrude(_op)
        _eid = _uid(_obj)
        _created.append(_eid)
        _touched[_eid] = _obj
    elif _kind == "param_set":
        _obj = _param_set(_op)
        _eid = _uid(_obj)
        if _eid not in _created and _eid not in _modified:
            _modified.append(_eid)
        _touched[_eid] = _obj
"""
