# Home Builder 5.1.0 × Blender 5.2: modifier-input API breakage (upstream report)

Ready-to-file material for `CreativeDesigner3D/home_builder_5`
(found 2026-08-29 by TEE's joinery lane, SI-B11; verified live on
Blender 5.2.0 LTS, hash fbe6228777e7).

## The breakage

Blender 5.2 removed IDProperty-style access to geometry-node modifier
inputs. `mod[socket_identifier]` (read or write) now raises:

```
TypeError: bpy_struct[key] = val: id properties not supported for this type
```

The replacement surface is typed:

```python
mod.properties.inputs.<identifier>.value          # read/write
'modifiers["<mod>"].properties.inputs.<identifier>.value'   # driver data path
```

Home Builder 5.1.0 uses the removed idiom in `hb_types.py`:

- `GeoNodeObject.set_input` / `get_input` (`mod[ident] = value`)
- `GeoNodeObject.var_input` (driver variable path `modifiers["X"]["Ident"]`)
- `GeoNodeObject.driver_input` (driver_add on the same path)
- `CabinetPartModifier.set_input` / `get_input` / `driver_input`

Consequences on 5.2 (all reproduced live): every prompt write fails;
`driver_add` on token modifiers raises (`property "modifiers["Notch"]
["Socket_3"]" not found`); driver *variables* with the old path fail
silently — they just never evaluate, so e.g. wall `obj_x` stops
tracking Length, and interior cages (Doors/Interior) keep their default
`Dim X/Y/Z = 1.0`, from which shelf parts derive oversize (a 994 mm
shelf in a 600 mm carcass, observed).

Array-modifier paths (`modifiers["X"].count`,
`.constant_offset_displace`) are RNA properties and remain fine.

## The fix (drop-in, old-idiom-first so pre-5.2 keeps working)

```python
def _write_input(mod, input_name, value):
    ident = mod.node_group.interface.items_tree[input_name].identifier
    try:
        mod[ident] = value                      # <= Blender 5.1
    except TypeError:                           # Blender 5.2+
        getattr(mod.properties.inputs, ident).value = value

def _read_input(mod, input_name):
    ident = mod.node_group.interface.items_tree[input_name].identifier
    try:
        return mod[ident]
    except TypeError:
        return getattr(mod.properties.inputs, ident).value

def _input_data_path(mod, input_name):
    ident = mod.node_group.interface.items_tree[input_name].identifier
    try:
        mod[ident]
        return 'modifiers["%s"]["%s"]' % (mod.name, ident)
    except TypeError:
        return 'modifiers["%s"].properties.inputs.%s.value' % (mod.name, ident)
```

Route the seven methods above through these three helpers (TEE ships
exactly this as a session monkey-patch in
`server/src/tee/adapters/blender/homebuilder.py::_COMPAT`, proven by a
full wall/cabinet/cut-list/layout run on 5.2). The deeper interior-cage
dim chain should come right once `var_input`/`driver_input` build valid
paths at creation time; TEE's shim fixed walls, cabinet carcasses,
doors and layouts, while pre-existing scenes and any code binding
drivers outside these methods still need a look upstream.
