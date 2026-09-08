.PHONY: check lint test format dist mcpb

check: lint test

BLENDER ?= $(shell command -v blender 2>/dev/null || echo /home/user/blender-5.2.0-linux-x64/blender)
TEE_PLUGIN_VERSION ?= 0.1.0
# server/.mcpb version; TEE_PLUGIN_VERSION tracks the UE TeeToolset .uplugin
TEE_SERVER_VERSION ?= 0.30.0

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
	@echo ""
	@echo "  REMINDER: installing this wipes the fleet extras from the Desktop"
	@echo "  venv - Desktop provisions with 'uv sync', which rebuilds from the"
	@echo "  lock and drops anything installed on top. Restore afterwards:"
	@echo ""
	@echo "    uv pip install --python \"$$HOME/Library/Application Support/Claude/Claude Extensions/local.mcpb.interaeronav.token-efficiency-engine/.venv/bin/python\" \\"
	@echo "      'tee-engine[medimg]' 'tee-engine[quant]' 'tee-engine[solve]' 'tee-engine[extract]' \\"
	@echo "      'tee-engine[pdf]' 'tee-engine[windtunnel]' 'tee-engine[flightdyn]' \\"
	@echo "      'tee-engine[pointcloud]' 'tee-engine[assets]'"
	@echo ""
	@echo "  See docs/setup-fleet.md. 'cad' is excluded on purpose (sidecar)."
	@echo "  windtunnel is wt_export format=vtu only; flightdyn and pointcloud are"
	@echo "  what fd_* and pc_* need to run at all - all three were missing from"
	@echo "  this line until A75/A77."

# SI-B20: ../benchmarks was NOT in this list, and `ruff check .` run from
# server/ cannot reach it - so the code that produces the numbers this
# project is judged by went unlinted for its whole life, accumulating 30
# errors including unreachable code referencing an undefined name.
# `--no-sync` on every one of these, and it is load-bearing rather than tidy:
# a bare `uv run` SYNCS the venv to the lock first, and this project's engine
# extras (medimg, quant, solve, extract, pdf, and OCP/jsbsim/meshio) are
# installed ON TOP of the locked set with `uv pip install` - see the reminder
# the mcpb target below prints. A sync drops them. `make test` was the worst
# of the four: it would remove the extras and then the suites that need them
# would SKIP rather than fail, so the only trace is a skip count nobody reads.
lint:
	uv run --no-sync ruff check src tests ../benchmarks
	uv run --no-sync ruff format --check src tests

format:
	uv run --no-sync ruff format src tests

test:
	uv run --no-sync pytest
