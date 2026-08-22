# tee — Token Efficiency Engine server

MCP server + token-efficiency kernel between AI models and Unreal Engine /
Blender. See the repository root `README.md` and `CLAUDE_EXECUTION_SCRIPT.md`
for the project plan, and `docs/research/` for the grounding corpus.

## Develop

```bash
uv sync
uv run ruff check src tests
uv run pytest
```

## Run

```bash
uv run tee serve --adapter fake      # stdio MCP server, no DCC needed
uv run tee serve --adapter blender   # against a live bridge (:9876)
uv run tee doctor                    # environment diagnostics with fixes
uv run tee doctor --emit claude-code # MCP client config for this install
```

## Package

```bash
make dist   # wheel + sdist (tee-engine) + Blender extension zip -> dist/
```

User docs live in `../docs/` (quickstart, per-DCC setup, troubleshooting,
security).
