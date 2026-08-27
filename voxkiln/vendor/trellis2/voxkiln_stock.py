"""Stock-parity switch, used ONLY by the benchmark harness.

`VOXKILN_STOCK=1` turns the vendored defect fixes OFF so the stock-vs-ours
battery (research 48) measures a real delta instead of asserting one. It is
read once per process; the product path never sets it, and nothing outside
`benchmarks/` should.

It covers the fixes that change GEOMETRY: the fp32 hard decode thresholds
(research 44 / upstream issue #169). The license surgery, the MPS backends
and the memory-leak fix stay on in both arms - "stock" here means
"upstream's numerics on this machine", not "upstream's unrunnable build".
"""

import os

STOCK = os.environ.get("VOXKILN_STOCK", "") not in ("", "0", "false", "False")
