# Blender setup

TEE talks to Blender over a localhost socket bridge (null-delimited JSON
execute protocol, port 9876). Two interchangeable bridge flavors serve
it; the TEE adapter runs against both, and the live test suite proves it
on each.

## Option A — official Blender MCP add-on (zero-install for its users)

If you already run the official Blender Lab MCP add-on, TEE connects to
its socket as another client. Enable the add-on, note its port, and:

```bash
tee serve --adapter blender --blender-port 9876
```

## Option B — TEE bridge extension (GUI sessions)

Install `dist/tee_bridge-0.1.2.zip` (built with
`make -C server dist`, or `blender --command extension build
--source-dir adapters/blender/tee_bridge`):

Blender → Edit → Preferences → Get Extensions → Install from Disk →
pick the zip → enable "TEE Bridge". The bridge listens on
127.0.0.1:9876 (change it in the add-on preferences and pass
`--blender-port`).

Requires Blender 5.1+ (5.2 LTS is the primary target; 4.2 is EOL and
unsupported).

## Option C — headless (CI, servers, background jobs)

No GUI, no install:

```bash
blender --background --python adapters/blender/tee_bridge/boot_background.py -- --port 9876
```

## Verify

```bash
tee doctor
```

checks the binary and version, the bridge socket, a full protocol
round-trip, and the bpy-wheel ABI match, each failure with its one-line
fix.

## Notes

- One bridge, one TEE server is the normal shape. Two servers on one
  project work but share `.tee/` state (doctor warns).
- The bridge socket has NO authentication — it executes Python. It must
  never be exposed beyond localhost; see [security.md](security.md).
- GUI-session behaviors (undo pushes, depsgraph timing under user
  edits) get their final validation on a physical machine —
  headless coverage is what CI runs.
