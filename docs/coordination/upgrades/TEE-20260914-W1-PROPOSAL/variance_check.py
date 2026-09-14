"""Were those five reps five samples, or one cached answer five times?
Same chore, prompts perturbed by a trailing marker the task ignores."""
import time
from tee.kernel import local_llm
from tee.llm import chores as C
FACTS = ("The slab is 150 mm thick, C25/30, on 250 mm compacted G5 fill. Cover to "
         "reinforcement is 40 mm bottom, 25 mm top. The design imposed load is 1.5 kPa "
         "and the span is 4.2 m one-way. Deflection limit is span/250.")
for label, mk in (("identical prompt", lambda i: f"Text:\n{FACTS}"),
                  ("perturbed prompt", lambda i: f"Text:\n{FACTS}\n(record {i})")):
    used, walls = [], []
    for i in range(4):
        seen = {}
        t0 = time.monotonic()
        try:
            local_llm.complete_json(mk(i), system=C._FACTS_SYSTEM,
                url="http://127.0.0.1:4000/v1", model="claude-qwen-27b",
                max_tokens=8000, adapters=None, thinking=True, json_mode="auto",
                on_usage=lambda p, n, s, _s=seen: _s.update(u=p.get("usage") or {}))
        except Exception as e:
            seen["u"] = {}
        used.append(int(seen.get("u", {}).get("completion_tokens") or 0))
        walls.append(round(time.monotonic() - t0, 1))
    print(f"  {label:<18} tokens={used}  walls={walls}", flush=True)
