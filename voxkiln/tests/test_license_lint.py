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


# -- banned model WEIGHTS (strings in configs, invisible to the import lint) --


def test_banned_weight_repo_is_caught_in_a_config(tmp_path):
    """Weights are named as strings, so the AST import lint cannot see them: a
    non-commercial matting model can ride along in a vendored config with every
    import perfectly clean."""
    from voxkiln.license_lint import lint_weights

    (tmp_path / "pipeline.json").write_text('{"rembg_model": "briaai/RMBG-2.0"}')
    found = lint_weights(tmp_path)
    assert len(found) == 1
    assert found[0]["module"] == "briaai/RMBG-2.0"
    assert "non-commercial" in found[0]["why"]


def test_the_substitution_site_may_name_what_it_rejects(tmp_path):
    from voxkiln.license_lint import lint_weights

    (tmp_path / "BiRefNet.py").write_text('if "RMBG" in name: name = "briaai/RMBG-2.0"')
    assert lint_weights(tmp_path) == []


def test_runtime_tree_has_no_banned_weights():
    from pathlib import Path

    from voxkiln.license_lint import lint_weights

    here = Path(__file__).resolve().parents[1]
    assert lint_weights(here / "src" / "voxkiln", here / "vendor") == []
