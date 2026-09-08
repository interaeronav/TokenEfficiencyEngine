# Installing the flight-dynamics lane

```bash
cd server && uv pip install --python .venv/bin/python jsbsim
```

That is the whole install: one wheel, **8.8 MB**, pure PyPI, no system package
and nothing to build. It brings `numpy` with it, which the lane imports in
exactly one module (the worker child) and nowhere else.

The lane registers its tools **unconditionally**, so `fd_probe` answers on a
machine that cannot fly and names what is missing. Only the flying tools need
the wheel.

## Platform

| target | wheel |
|---|---|
| macOS (Intel and Apple Silicon) | `universal2`, native |
| Linux x86_64 | `manylinux2014` |
| Windows | `win_amd64` |
| **Linux aarch64** | **none — builds from the sdist, needs a compiler and CMake** |

Python 3.10 or newer.

## Verifying

```bash
cd server && uv run --no-sync pytest -q -m fdm
```

Three live tests: a generated aircraft trims and its modes are physical, the
trim holds when flown, and the reply stays a digest. They skip cleanly without
the wheel.

## What it does NOT install

No FlightGear, no viewer, no aircraft. The wheel's own 60 bundled aircraft are
present on disk once installed but the lane never ships, copies or reads them —
it writes its own from your polar.
