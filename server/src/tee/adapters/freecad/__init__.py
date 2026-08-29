"""FreeCAD adapter (A37 P4): the fabrication lane's typed seam.

Built FROM docs/adapter-kit.md over the ONE bridge the P0 probe chose -
neka-nat/freecad-mcp's in-FreeCAD RPC addon (xmlrpc :9875 in the GUI
process). freecadcmd stays the headless vehicle for CI-adjacent work;
this adapter is the live parametric seam: typed sketch/pad/pocket ops
(sketches solved server-side by sketch_solve BEFORE they reach FreeCAD),
diffs, checkpoints via document save-copies, budgeted capture.
"""
