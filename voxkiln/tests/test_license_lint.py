from pathlib import Path

from voxkiln.license_lint import lint_tree

SRC = Path(__file__).resolve().parent.parent / "src" / "voxkiln"
VENDOR = Path(__file__).resolve().parent.parent / "vendor"


def test_product_and_vendor_trees_are_clean():
    violations = lint_tree(SRC, VENDOR)
    assert violations == [], f"license violations: {violations}"


def test_lint_catches_banned_import(tmp_path):
    bad = tmp_path / "bad.py"
    bad.write_text("import nvdiffrast\nfrom easydict import EasyDict\n")
    violations = lint_tree(tmp_path)
    assert {v["module"] for v in violations} == {"nvdiffrast", "easydict"}


def test_lint_requires_guard_on_accelerators(tmp_path):
    unguarded = tmp_path / "unguarded.py"
    unguarded.write_text("import cumesh\n")
    assert lint_tree(tmp_path)[0]["module"] == "cumesh"

    guarded = tmp_path / "guarded.py"
    guarded.write_text("try:\n    import cumesh\nexcept ImportError:\n    cumesh = None\n")
    unguarded.unlink()
    assert lint_tree(tmp_path) == []
