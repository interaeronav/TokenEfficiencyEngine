.PHONY: check lint test format dist

check: lint test

BLENDER ?= /home/user/blender-5.2.0-linux-x64/blender

dist:
	uv build
	$(BLENDER) --command extension build \
		--source-dir ../adapters/blender/tee_bridge --output-dir dist
	@ls -la dist/

lint:
	uv run ruff check src tests
	uv run ruff format --check src tests

format:
	uv run ruff format src tests

test:
	uv run pytest
