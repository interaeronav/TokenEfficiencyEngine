"""Per-chore token demand with thinking on, from FIVE DIFFERENT inputs each.

A repeated prompt returns a repeated generation on this backend, so varying
the input is the only way to see the spread the cap has to cover.
"""
import json, statistics, time
from pathlib import Path
from tee.kernel import local_llm
from tee.llm import chores as C

URL, MODEL, BIG, N = "http://127.0.0.1:4000/v1", "claude-qwen-27b", 8000, 5
OUT = Path("/private/tmp/claude-501/-Users-john-TokenEfficiencyEngine/"
           "66bb34fa-ea68-4af7-9b78-9a82a2737fc4/scratchpad/cap_measure2.json")

SCENES = [
 {"objects": 160, "kinds": {"mesh": 147, "camera": 12}, "last_ops": ["wall x62", "canopy x11"]},
 {"objects": 12, "kinds": {"sketch": 8, "body": 4}, "last_ops": ["extrude 12mm", "fillet 2mm"]},
 {"objects": 1904, "kinds": {"mesh": 1900, "light": 4}, "last_ops": ["import ifc", "merge by material", "decimate 0.4"]},
 {"objects": 3, "kinds": {"panel": 3}, "last_ops": ["sew seam", "drape 240 frames", "export obj"]},
 {"objects": 47, "kinds": {"actor": 40, "blueprint": 7}, "last_ops": ["spawn grid", "bake lighting"]},
]
TEXTS = [
 "The slab is 150 mm thick, C25/30, on 250 mm compacted G5 fill. Cover is 40 mm bottom, 25 mm top.",
 "Roof trusses at 900 mm centres, 38x114 SA pine grade 5, span 7.2 m, tie-down straps every second truss.",
 "The duct run is 315 mm diameter, 22 m long, two 90 degree bends, design velocity 6 m/s, insulated 25 mm.",
 "Foundation: 600 wide x 300 deep strip, 10 MPa concrete, founded 900 below NGL on stiff residual granite.",
 "Glazing is 6.38 mm laminated, 1.8 m x 2.4 m panes, wind load 1.2 kPa, structural silicone to three edges.",
]
LINTS = ["E501 line too long (118 > 100 characters)", "F841 local variable 'tmp' is assigned to but never used",
 "B008 do not perform function call in argument defaults", "C901 'build' is too complex (14)",
 "S603 subprocess call: check for execution of untrusted input"]
CODES = [
 'rows = tee_call("bl_scene_summary", {})\ntotal = 0\nfor r in rows["items"]:\n    total = total + r["verts"]\n',
 'items = tee_call("pk_list", {})["items"]\nlast = items[len(items)]\n',
 'made = tee_call("bl_create", {"type": "cube"})\nident = made["id"]\n',
 'w = 2.4\nmade = tee_call("bl_create", {"kind": "cube", "size": w})\n',
 'ids = [r["id"] for r in tee_call("fu_list", {})["rows"]]\nfirst = ids[0]["name"]\n',
]
ERRS = ["KeyError: 'verts'. Rows carry 'vertex_count'.", "IndexError: list index out of range; last index is n-1.",
 "TypeError: unknown argument 'type'; bl_create takes 'kind'.",
 "ValueError: size is in millimetres; 2.4 metres must be scaled by 1000.",
 "TypeError: string indices must be integers; ids holds strings, not dicts."]
QUERIES = ["watertight wall with openings", "drape a garment on a body", "level a point cloud to the floor plane",
 "extrude a sketch to a solid", "run a wind tunnel sweep and read the polar"]

JOBS = {
 "repair_script":    (C._REPAIR_SYSTEM, [f"Failing script:\n```\n{CODES[i]}```\nValidation error:\n{ERRS[i]}" for i in range(N)], 500),
 "explain_lint":     (C._LINT_SYSTEM,   [f"Finding:\n{x}" for x in LINTS], 160),
 "refine_extract":   (C._EXTRACT_SYSTEM,[f"Text:\n{x}" for x in TEXTS], 500),
 "structure_facts":  (C._FACTS_SYSTEM,  [f"Text:\n{x}" for x in TEXTS], 500),
 "compress_recap":   (C._RECAP_SYSTEM,  [f"Recap JSON:\n{x}" for x in SCENES], 160),
 "rerank":           (C._RERANK_SYSTEM, [f"Query: {q}\nCandidates:\n1 wall_with_openings\n2 bl_create cube\n"
                                         f"3 sk_drape\n4 pc_level\n5 pk_extrude\n6 wt_sweep" for q in QUERIES], 200),
 "phrase_deviation": (C._DEVIATION_SYSTEM, [f"Text:\n{x}" for x in TEXTS], 400),
}

res = {}
for name, (sys_p, prompts, cur) in JOBS.items():
    used, walls, ok = [], [], 0
    for p in prompts:
        seen = {}
        t0 = time.monotonic()
        try:
            r = local_llm.complete_json(p, system=sys_p, url=URL, model=MODEL, max_tokens=BIG,
                    adapters=None, thinking=True, json_mode="auto",
                    on_usage=lambda pl, n, s, _s=seen: _s.update(u=pl.get("usage") or {}))
            ok += r is not None
        except Exception:
            pass
        used.append(int(seen.get("u", {}).get("completion_tokens") or 0))
        walls.append(time.monotonic() - t0)
    res[name] = {"current_cap": cur, "generated": sorted(used), "max": max(used),
                 "median": int(statistics.median(used)),
                 "median_wall_s": round(statistics.median(walls), 1),
                 "max_wall_s": round(max(walls), 1), "answered": f"{ok}/{len(prompts)}"}
    print(f"  {name:<18} cap={cur:<4} generated={sorted(used)}  max={max(used):<5} "
          f"wall med/max {round(statistics.median(walls),1)}/{round(max(walls),1)}s", flush=True)

OUT.write_text(json.dumps(res, indent=1))
print("saved")
