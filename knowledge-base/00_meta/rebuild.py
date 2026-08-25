#!/usr/bin/env python3
"""Regenerate INDEX.md, manifest.json, source-register.md and VERIFICATION.md.
Run from anywhere:  python3 00_meta/rebuild.py
Edit ROOT in the two rebuild_*.py scripts if the repository is moved."""
import subprocess, sys, os
here = os.path.dirname(os.path.abspath(__file__))
for script in ("rebuild_index.py", "rebuild_verification.py"):
    print(f"--- {script} ---")
    subprocess.run([sys.executable, os.path.join(here, script)], check=True)
print("done")

