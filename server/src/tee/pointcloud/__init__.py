"""TEE point-cloud scan prep (A67, `pc_*`).

Turns a raw scan into a scale-verified, axis-aligned tracing template while
the model never sees a single point. Design of record: research doc 69.

This lane is the FRONT half of reality capture. The back half already exists
(`capture_*`, A42) and is not rebuilt here: registration stays
`tee.capture.align.register_icp`, which already carries a refusing RMS gate
and a 7-DOF degeneracy guard.
"""
