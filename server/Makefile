.PHONY: check lint test format dist mcpb

check: lint test

BLENDER ?= $(shell command -v blender 2>/dev/null || echo /home/user/blender-5.2.0-linux-x64/blender)
TEE_PLUGIN_VERSION ?= 0.1.0
# server/.mcpb version; TEE_PLUGIN_VERSION tracks the UE TeeToolset .uplugin
TEE_SERVER_VERSION ?= 0.3.1

dist:
	uv build
	$(BLENDER) --command extension build \
		--source-dir ../adapters/blender/tee_bridge --output-dir dist
	cd ../adapters/unreal && zip -qr ../../server/dist/TeeToolset-$(TEE_PLUGIN_VERSION).zip \
		TeeToolset -x '*/__pycache__/*' -x '*.pyc'
	$(MAKE) mcpb
	@ls -la dist/

# .mcpb (MCP Bundle) for drag-and-drop install into Claude Desktop. Schema
# mirrors a real installed bundle (manifest_version 0.4, server.type "uv"),
# not a guessed one.
mcpb:
	@rm -rf build/mcpb && mkdir -p build/mcpb dist
	cp ../packaging/mcpb_manifest.json build/mcpb/manifest.json
	cp ../packaging/icon.png build/mcpb/
	cp pyproject.toml uv.lock build/mcpb/
	# Claude Desktop provisions the bundle venv with a PLAIN uv sync at
	# install time, which includes the default dev group (measured: +58 MB
	# of ruff/pytest/fpdf2 the server never runs, A35 P0/P1). The bundle's
	# copy of pyproject opts out; the dev tree keeps its defaults.
	printf '\n[tool.uv]\ndefault-groups = []\n' >> build/mcpb/pyproject.toml
	cp ../README.md build/mcpb/
	cp -R src build/mcpb/src
	find build/mcpb -name '__pycache__' -type d -exec rm -rf {} + 2>/dev/null || true
	find build/mcpb -name '*.pyc' -delete
	cd build/mcpb && zip -qr ../../dist/tee-engine-$(TEE_SERVER_VERSION).mcpb .
	@echo "built dist/tee-engine-$(TEE_SERVER_VERSION).mcpb"

lint:
	uv run ruff check src tests
	uv run ruff format --check src tests

format:
	uv run ruff format src tests

test:
	uv run pytest
