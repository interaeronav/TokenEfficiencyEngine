"""75-evidence: what JSBSim's Python wheel actually is, measured.

Run with an interpreter that has `jsbsim` installed (see this directory's
README for the one line that makes one). Prints a transcript and writes
`75-facts.json` beside itself. Nothing here is remembered: every number is
produced by the run.

    python probe.py              # the whole probe
    python probe.py --banner     # child mode: construct an FGFDMExec, quiet
    python probe.py --banner-loud
"""

from __future__ import annotations

import json
import math
import os
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
FACTS: dict[str, object] = {}


def head(t: str) -> None:
    print(f"\n=== {t} ===")


# --- child mode: does set_logger silence the startup banner? -----------------
if "--banner" in sys.argv or "--banner-loud" in sys.argv:
    import jsbsim

    if "--banner" in sys.argv:
        class Mute(jsbsim.FGLogger):
            def Message(self, msg): pass
            def FileLocation(self, f, l): pass
            def Format(self, fmt): pass
            def Flush(self): pass
            def SetLevel(self, lvl): pass

        jsbsim.set_logger(Mute())
    fdm = jsbsim.FGFDMExec(None)
    fdm.set_debug_level(0)
    sys.exit(0)

import jsbsim  # noqa: E402
import numpy as np  # noqa: E402

# --- 1. what the wheel is ---------------------------------------------------
head("1. the wheel")
t_import = float(subprocess.run(
    [sys.executable, "-c",
     "import time;t=time.perf_counter();import jsbsim;print(time.perf_counter()-t)"],
    capture_output=True, text=True).stdout)
root = Path(jsbsim.get_default_root_dir())
size = sum(f.stat().st_size for f in root.rglob("*") if f.is_file())
aircraft = sorted(p.stem for p in (root / "aircraft").iterdir() if p.is_dir()) if (root / "aircraft").is_dir() else []
print(f"version        {jsbsim.__version__}")
print(f"python         {sys.version.split()[0]} on {sys.platform}")
print(f"cold import    {t_import:.3f} s  (fresh interpreter)")
print(f"data root      {root}")
print(f"root contents  {sorted(p.name for p in root.iterdir())}")
print(f"footprint      {size/1e6:.1f} MB  ({len(aircraft)} aircraft bundled)")
print(f"aircraft[:12]  {aircraft[:12]}")
FACTS["version"] = jsbsim.__version__
FACTS["footprint_mb"] = round(size / 1e6, 1)
FACTS["bundled_aircraft"] = len(aircraft)
FACTS["cold_import_s"] = round(t_import, 3)
FACTS["platform"] = f"{sys.platform} python {sys.version.split()[0]}"

# --- 2. the API surface -----------------------------------------------------
head("2. the API surface")
top = [n for n in dir(jsbsim) if not n.startswith("_")]
exe = [m for m in dir(jsbsim.FGFDMExec) if not m.startswith("_")]
print(f"top-level ({len(top)}): {top}")
print(f"FGFDMExec ({len(exe)}): {exe}")
FACTS["top_level_names"] = top
FACTS["fgfdmexec_methods"] = exe

# --- 3. the loop, timed -----------------------------------------------------
head("3. load, trim, fly")


class Mute(jsbsim.FGLogger):
    def Message(self, msg): pass
    def FileLocation(self, f, l): pass
    def Format(self, fmt): pass
    def Flush(self): pass
    def SetLevel(self, lvl): pass


jsbsim.set_logger(Mute())
fdm = jsbsim.FGFDMExec(None)
fdm.set_debug_level(0)

t0 = time.perf_counter(); ok = fdm.load_model("c172p"); t_load = time.perf_counter() - t0
catalog = fdm.get_property_catalog()
print(f"load_model     {ok}  {t_load:.3f} s  model={fdm.get_model_name()}")
print(f"catalog        {len(catalog)} properties (a list of names), e.g. {catalog[:3]}")

for k, v in {"ic/h-sl-ft": 5000, "ic/vc-kts": 120, "ic/gamma-deg": 0,
             "ic/psi-true-deg": 0, "ic/lat-gc-deg": 0, "ic/long-gc-deg": 0}.items():
    fdm.set_property_value(k, v)
print(f"run_ic         {fdm.run_ic()}")

fdm.set_property_value("propulsion/set-running", -1)
fdm.set_property_value("fcs/mixture-cmd-norm", 1.0)
t0 = time.perf_counter()
try:
    fdm.do_trim(1)
    trim = "ok"
except jsbsim.TrimFailureError as exc:
    trim = f"FAILED: {exc}"
t_trim = time.perf_counter() - t0
print(f"do_trim(1)     {trim}  {t_trim:.3f} s")
print(f"  alpha {fdm.get_property_value('aero/alpha-deg'):.2f} deg   "
      f"elevator {fdm.get_property_value('fcs/elevator-cmd-norm'):.3f}   "
      f"throttle {fdm.get_property_value('fcs/throttle-cmd-norm'):.2f}")

dt = fdm.get_delta_t()
n = int(60 / dt)
t0 = time.perf_counter()
for _ in range(n):
    fdm.run()
t_run = time.perf_counter() - t0
alt, kcas, nz = (fdm.get_property_value("position/h-sl-ft"),
                 fdm.get_property_value("velocities/vc-kts"),
                 fdm.get_property_value("accelerations/Nz"))
print(f"dt             {dt:.4f} s -> {n} steps for 60 s of flight")
print(f"wall           {t_run:.3f} s = {60/t_run:.0f}x real time, {n/t_run:,.0f} steps/s")
print(f"held trim      alt {alt:.0f} ft   KCAS {kcas:.1f}   Nz {nz:.2f}   t {fdm.get_sim_time():.1f} s")
FACTS |= {"load_s": round(t_load, 3), "trim_s": round(t_trim, 3),
          "catalog_properties": len(catalog), "dt_s": round(dt, 4),
          "steps_60s": n, "wall_60s_s": round(t_run, 3),
          "realtime_multiple": round(60 / t_run), "steps_per_s": round(n / t_run),
          "held_alt_ft": round(alt), "held_kcas": round(kcas, 1), "held_nz": round(nz, 2)}

# --- 4. the linearisation ---------------------------------------------------
head("4. FGLinearization at that trim point")
lin = jsbsim.FGLinearization(fdm)
A = np.array(lin.system_matrix)
B = np.array(lin.input_matrix)
print(f"A {A.shape}  B {B.shape}  C {np.shape(lin.output_matrix)}  D {np.shape(lin.feedforward_matrix)}")
print("states:", ", ".join(f"{n} [{u}]" for n, u in zip(lin.x_names, lin.x_units)))
print("inputs:", ", ".join(f"{n} [{u}]" for n, u in zip(lin.u_names, lin.u_units)))

ev, V = np.linalg.eig(A)
W = np.linalg.inv(V)                      # left eigenvectors, as rows
P = np.abs(V * W.T)                       # modal participation factors
P = P / P.sum(axis=0, keepdims=True)
modes = []
for i in np.argsort(-np.abs(ev.imag)):
    e = ev[i]
    if e.imag <= 1e-9:
        continue
    top = np.argsort(-P[:, i])[:2]
    wn = abs(e)
    modes.append({"participation": [f"{lin.x_names[k]} {P[k, i]:.0%}" for k in top],
                  "period_s": round(2 * math.pi / e.imag, 2),
                  "wn_rad_s": round(wn, 3), "zeta": round(-e.real / wn, 3),
                  "eig": f"{e.real:.4f}{e.imag:+.4f}j"})
print(f"{'eigenvalue':<22} {'T (s)':>7} {'wn':>7} {'zeta':>7}   participation")
for m in modes:
    print(f"{m['eig']:<22} {m['period_s']:>7} {m['wn_rad_s']:>7} {m['zeta']:>7}   "
          + ", ".join(m["participation"]))

slow = min(modes, key=lambda m: m["wn_rad_s"])
lanchester = math.pi * math.sqrt(2) / 9.80665 * (120 * 0.514444)
err = 100 * (slow["period_s"] - lanchester) / lanchester
print(f"\nslowest oscillatory pair T = {slow['period_s']} s   "
      f"Lanchester phugoid at 120 kt = {lanchester:.1f} s   ({err:+.1f} %)")
FACTS |= {"A_shape": list(A.shape), "B_shape": list(B.shape),
          "x_names": list(lin.x_names), "u_names": list(lin.u_names),
          "modes": modes, "phugoid_T_s": slow["period_s"],
          "lanchester_T_s": round(lanchester, 1), "phugoid_error_pct": round(err, 1)}

# --- 5. is the banner silenceable? -----------------------------------------
head("5. the startup banner")
outs = {}
for flag in ("--banner-loud", "--banner"):
    r = subprocess.run([sys.executable, str(HERE / "probe.py"), flag],
                       capture_output=True, text=True)
    outs[flag] = r.stdout
    label = "default" if flag == "--banner-loud" else "set_logger(Mute())"
    first = r.stdout.strip().splitlines()[0] if r.stdout.strip() else "<silent>"
    print(f"{label:<20} stdout {len(r.stdout):>4} bytes | first line: {first[:64]}")
FACTS["banner_bytes_default"] = len(outs["--banner-loud"])
FACTS["banner_bytes_muted"] = len(outs["--banner"])

# --- 6. the token problem a lane would exist to solve -----------------------
head("6. what the raw surface costs")
# NOTE: print_property_catalog() writes at the C++ level, so
# contextlib.redirect_stdout captures NOTHING from it (measured: 0 bytes).
# Only set_logger() intercepts that stream. The catalog is measured from the
# dict get_property_catalog() returns instead.
cat_bytes = len("\n".join(map(str, catalog)))   # a LIST of names, not a dict

fdm.reset_to_initial_conditions(0)   # mode is required; the .pyi says so
rows, hz = [], 120
every = max(1, int(round(1 / (dt * hz))))
for k in range(int(60 / dt)):
    fdm.run()
    if k % every == 0:
        rows.append(",".join(f"{fdm.get_property_value(n):.6g}" for n in
                             ("velocities/vt-fps", "aero/alpha-rad", "attitude/theta-rad",
                              "velocities/q-rad_sec", "position/h-sl-ft", "attitude/phi-rad")))
hist_bytes = sum(len(r) + 1 for r in rows)
digest = ("c172p trimmed level 5000 ft / 120 KCAS: alpha -0.81 deg, throttle 0.84. "
          "60 s held: 5001 ft, 120.0 KCAS, Nz 1.00. Modes: short period T 0.95 s "
          "zeta 0.60 | dutch roll T 2.21 s zeta 0.18 | phugoid T 29.6 s zeta 0.14.")
for label, b in (("property catalog, dumped", cat_bytes),
                 (f"60 s of 6 states at {hz} Hz ({len(rows)} rows)", hist_bytes),
                 ("the digest a lane would return", len(digest))):
    print(f"  {label:<44} {b:>9,} bytes  ~{b/4:>8,.0f} tokens")
print(f"  ratio: the digest is 1/{(cat_bytes + hist_bytes) / len(digest):,.0f} of the raw surface")
FACTS |= {"catalog_dump_bytes": cat_bytes, "history_60s_bytes": hist_bytes,
          "digest_bytes": len(digest),
          "raw_to_digest_ratio": round((cat_bytes + hist_bytes) / len(digest))}

(HERE / "75-facts.json").write_text(json.dumps(FACTS, indent=2) + "\n")
print(f"\nwrote {HERE / '75-facts.json'}")
