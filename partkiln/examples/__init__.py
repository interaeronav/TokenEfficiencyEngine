"""Three runnable pipelines that drive the kernel the way a session would.

    cd partkiln
    PYTHONPATH=src python -m examples.bracket       all --out /tmp/bracket
    PYTHONPATH=src python -m examples.shaft_housing all --out /tmp/shaft
    PYTHONPATH=src python -m examples.sheet_bracket all --out /tmp/sheet

Each example is a package of stages plus `all`, and each stage is a separate
process-worth of work that hands the next one a **script**, not a B-rep:
`model` writes `script.json`, every later stage replays it. That is Law 16
made runnable - the checkpoint is the script and the solid is a cache - and
it is why `drawing` can be re-run against an edited model without anyone
having to remember what `model` did.

`--probe` is the short mode. It builds the same feature tree but tessellates
coarsely, skips the STEP round-trip read-back and skips the PDF, so it proves
the pipeline runs and nothing else. Every manifest it writes says so in
words, because a coarse run is a different answer, not a rougher one.
"""
