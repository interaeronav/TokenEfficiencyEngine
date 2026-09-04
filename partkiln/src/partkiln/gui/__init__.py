"""The partkiln shell: a window that writes the same batch a model would send.

Headless was the decision and stays the decision (A66 owner decision 2): this
package is a CLIENT of `partkiln.document`, added later, and the kernel does
not know it exists. Nothing here is imported by the kernel, and `import
partkiln` still loads neither Qt nor OCP - `tests/test_gui.py` asserts it.

Three of the four modules are Qt-free and fully tested with PySide6 absent:
`actions` builds command dicts, `shell` applies them through the kernel and
formats what came back, `preview` turns a sketch into SVG. `app` is the only
module that touches Qt, and it imports PySide6 inside its functions.
"""
