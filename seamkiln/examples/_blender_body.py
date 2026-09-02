"""Loading the figure into Blender without the ribs. Runs INSIDE Blender.

The figure exports as triangles, and a Catmull-Clark subdivision on a
triangulated cylinder puts a ridge along every diagonal - the limbs rendered
as if pleated. The side triangles pair back into the quads they came from,
so they are joined first and the surface subdivided after.
"""

import os

import bmesh
import bpy
import numpy as np


def load_figure(path, materials, offset, name="Figure"):
    """Import the PLY, assign the six part materials by rank of the red
    channel, join the triangles into quads, smooth, subdivide."""
    before = set(bpy.data.objects)
    bpy.ops.wm.ply_import(filepath=str(path))
    obj = next(iter(set(bpy.data.objects) - before))
    obj.name = name
    obj.rotation_euler = (np.radians(90.0), 0.0, 0.0)  # seamkiln Y-up -> Blender Z-up
    obj.location = (offset[0], offset[2], offset[1])
    obj.data.materials.clear()
    for m in materials:
        obj.data.materials.append(m)
    me = obj.data
    attr = me.color_attributes[0]
    raw = np.zeros((len(attr.data), 4), dtype=np.float32)
    attr.data.foreach_get("color", raw.ravel())
    # the part tag rides in RED, sRGB-decoded on import: stretched but in
    # ORDER, so faces match slots by rank, never by float equality
    reds = raw[:, 0].astype(np.float64)
    order = np.asarray(sorted(set(reds.tolist())))
    edges = (order[:-1] + order[1:]) / 2.0
    per_vertex = np.searchsorted(edges, reds)
    first = np.asarray([p.vertices[0] for p in me.polygons], dtype=np.int64)
    me.polygons.foreach_set("material_index", per_vertex[first].astype(np.int32))
    me.update()

    # bmesh rather than the edit-mode operator: it needs no selection or
    # context, which a background Blender does not have to give
    bm = bmesh.new()
    bm.from_mesh(me)
    bmesh.ops.join_triangles(
        bm,
        faces=bm.faces[:],
        # generous: the limbs taper, so their quads are trapezoids, and the
        # shins kept their ribs at 40 degrees
        angle_face_threshold=np.radians(70.0),
        angle_shape_threshold=np.radians(70.0),
    )
    bm.to_mesh(me)
    bm.free()
    me.update()
    for poly in me.polygons:
        poly.use_smooth = True
    # No subdivision by default: forty-section frustums and icosphere joints
    # shade smooth as they are, and a Catmull-Clark pass left ridges on the
    # shins even after the triangles were joined. SEAMKILN_FIGURE_SUBSURF=1
    # puts it back for comparison.
    levels = int(os.environ.get("SEAMKILN_FIGURE_SUBSURF", "0"))
    if levels > 0:
        obj.modifiers.new("smooth", "SUBSURF").levels = levels
    return obj
