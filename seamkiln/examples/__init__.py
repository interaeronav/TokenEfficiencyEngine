"""The two delivered shots, as headless pipelines that run from the repo.

    cd seamkiln
    python -m examples.cape_shot all --out /tmp/cape      # sim, render, sound, encode
    python -m examples.fur_walk  sim --out /tmp/fur --probe

Each example is four stages - `sim` (seamkiln only), `render` and `encode`
(headless Blender, `--factory-startup`, never the owner's open file) and
`sound` (numpy) - plus `all`. `--probe` is a short, coarse run whose only
claim is that the pipeline runs; its manifest says so, and nothing measured
on a probe is evidence of anything but that.
"""
