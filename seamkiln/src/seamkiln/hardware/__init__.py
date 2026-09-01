"""Hardware: the parts of a garment that are not cloth.

A zipper, a button, a rivet and a snap are all *trim*, and trim behaves in
ways cloth does not - it is denser, far stiffer, and it is attached at points
rather than woven through. Modelling it as more fabric gets every one of those
wrong, which is why it lives here and enters the solver through
`GarmentMesh.attach` rather than through the mesh.
"""

from seamkiln.hardware import buttons, trim, zipper

__all__ = ["buttons", "trim", "zipper"]
