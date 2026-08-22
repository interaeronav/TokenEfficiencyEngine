# TEE v0.1.0 release files

- `tee_bridge-0.1.0.zip` — the Blender bridge extension (built and
  validated with Blender 5.2). Install: Blender → Settings →
  Get Extensions → dropdown arrow (top right) → **Install from Disk…**
  → pick this zip → enable **TEE Bridge**. Needs Blender 5.1+.
- The server wheel is not committed (build it with `make -C server
  dist`; any TEE session does this automatically during setup).

Committed binaries are limited to this small extension zip so that
non-technical installs work straight from a repo pull, given that this
repo currently has no GitHub Releases. When Releases exist, these files
move there.
