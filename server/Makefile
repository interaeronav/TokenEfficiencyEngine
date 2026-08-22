.PHONY: check lint test format dist

check: lint test

BLENDER ?= $(shell command -v blender 2>/dev/null || echo /home/user/blender-5.2.0-linux-x64/blender)
TEE_PLUGIN_VERSION ?= 0.1.0

dist:
	uv build
	$(BLENDER) --command extension build \
		--source-dir ../adapters/blender/tee_bridge --output-dir dist
	cd ../adapters/unreal && zip -qr ../../server/dist/TeeToolset-$(TEE_PLUGIN_VERSION).zip \
		TeeToolset -x '*/__pycache__/*' -x '*.pyc'
	@ls -la dist/

lint:
	uv run ruff check src tests
	uv run ruff format --check src tests

format:
	uv run ruff format src tests

test:
	uv run pytest
