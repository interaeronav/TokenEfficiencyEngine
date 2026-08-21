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

## Run (Phase 1: fake adapter)

```bash
uv run tee serve --adapter fake   # stdio MCP server
uv run tee doctor                 # environment diagnostics
```
