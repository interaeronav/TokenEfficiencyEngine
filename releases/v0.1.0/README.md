# TEE v0.1.0 release files

- `tee_bridge-0.1.2.zip` — the Blender bridge extension (built and
  validated with Blender 5.2). Install: Blender → Settings →
  Get Extensions → dropdown arrow (top right) → **Install from Disk…**
  → pick this zip → enable **TEE Bridge**. Needs Blender 5.1+.
- `TeeToolset-0.1.0.zip` — TEE's Unreal **content-only** plugin (no C++
  module, nothing to compile). Install: unzip into
  `<YourProject>/Plugins/`, enable **TeeToolset** and
  **PythonScriptPlugin** in the `.uproject`, restart the editor. Needs
  UE 5.8+ with `ModelContextProtocol` and `AllToolsets` enabled. It adds
  ONE capability Epic's toolsets lack — unsandboxed editor Python inside
  an undo transaction — and TEE only calls it when code exec is allowed.
  Everything else in the Unreal adapter works without it.
- The server wheel is not committed (build it with `make -C server
  dist`; any TEE session does this automatically during setup).

Committed binaries are limited to these two small plugin zips so that
non-technical installs work straight from a repo pull, given that this
repo currently has no GitHub Releases. When Releases exist, these files
move there.
