"""Real disposable files exercise documentation containment and rollback."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

import pytest
from tee.docagents import workspace as mod
from tee.docagents.workspace import DocWorkspace
from tee.kernel.errors import TeeError


def write(root: Path, name: str, data: str = "original\n") -> Path:
    path = root / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(data)
    return path


def prepared(tmp_path: Path) -> tuple[DocWorkspace, str, Path]:
    write(tmp_path, "src/example.py", 'print("hello")\n')
    write(tmp_path, "docs/readme.md")
    workspace = DocWorkspace(tmp_path)
    run = workspace.prepare(["src/example.py"], ["docs/readme.md"], "Explain the source.")
    return workspace, run["run_id"], Path(run["work_dir"])


def test_roundtrip_existing_new_and_explicit_untracked_input(tmp_path):
    write(tmp_path, "untracked.py", "def example(): pass\n")
    write(tmp_path, "docs/existing.md", "")
    workspace = DocWorkspace(tmp_path)
    run = workspace.prepare(["untracked.py"], ["docs/existing.md", "docs/new.md"], "Document.")
    loaded = workspace.load(run["run_id"])
    assert loaded["schema"] == 1
    assert loaded["outputs"] == {
        "docs/existing.md": hashlib.sha256(b"").hexdigest(),
        "docs/new.md": None,
    }
    work = Path(loaded["work_dir"])
    assert (work / "untracked.py").read_bytes() == (tmp_path / "untracked.py").read_bytes()
    write(work, "docs/existing.md", "Existing documented\n")
    write(work, "docs/new.md", "New documented\n")
    diff = workspace.diff(run["run_id"])
    assert [r["change"] for r in diff["changes"]] == ["modified", "created"]
    assert not diff["truncated"]
    applied = workspace.apply(run["run_id"], diff["review_sha256"])
    assert applied["ok"] and applied["applied"] == ["docs/existing.md", "docs/new.md"]
    assert (tmp_path / "docs/new.md").read_text() == "New documented\n"
    assert (Path(applied["backup_path"]) / "docs/existing.md").read_bytes() == b""
    baseline = json.loads((Path(applied["backup_path"]) / "baseline.json").read_text())
    assert baseline["docs/new.md"]["sha256"] is None
    with pytest.raises(TeeError, match="already applied"):
        workspace.apply(run["run_id"], diff["review_sha256"])


@pytest.mark.parametrize(
    "name",
    [
        "/tmp/external.md",
        "../escape.md",
        "docs/../../escape.md",
        "docs//x.md",
        "./x.md",
        "docs\\escape.md",
        "C:/escape.md",
        "docs/x\n.md",
        "docs/x\x00.md",
        ".tee/config.toml",
        ".git/config",
        ".env",
        ".aider.conf.yml",
        ".clinerules/rules.md",
        "AGENTS.md",
        "sub/CLAUDE.md",
        "SKILL.md",
        "CLAUDE_A81_SCRIPT.md",
        "script.md",
        "docs/coordination/receipt.md",
        "DOCS/COORDINATION/x.txt",
        "docs/upgrade-coordination-protocol.md",
        "secrets.json",
        "id_rsa",
        "private.pem",
        "credentials/export.txt",
        "settings.json",
        "cline.json",
        "mcp.json",
        "aider.yaml",
    ],
)
def test_protected_or_escaping_input_refused_before_staging(tmp_path, name):
    with pytest.raises(TeeError):
        DocWorkspace(tmp_path).prepare([name], ["docs/out.md"], "Document.")
    assert not (tmp_path / ".tee").exists()


@pytest.mark.parametrize("name", ["main.py", "docs/index.html", "docs/output.json", "AGENTS.md"])
def test_only_ordinary_document_outputs(tmp_path, name):
    with pytest.raises(TeeError):
        DocWorkspace(tmp_path).prepare([], [name], "Document.")


@pytest.mark.parametrize("kind", ["file_link", "parent_link", "hardlink", "store_link"])
def test_links_never_copy_external_files(tmp_path, kind):
    project = tmp_path / "project"
    project.mkdir()
    other = write(tmp_path, "elsewhere/source.py")
    if kind == "file_link":
        (project / "source.py").symlink_to(other)
    elif kind == "parent_link":
        (project / "linked").symlink_to(other.parent, target_is_directory=True)
    elif kind == "hardlink":
        os.link(other, project / "source.py")
    else:
        write(project, "source.py")
        (project / ".tee").symlink_to(other.parent, target_is_directory=True)
    name = "linked/source.py" if kind == "parent_link" else "source.py"
    with pytest.raises(TeeError):
        DocWorkspace(project).prepare([name], ["out.md"], "Document.")
    assert other.read_text() == "original\n"


@pytest.mark.parametrize(
    "change", ["new_file", "new_dir", "policy", "input", "missing", "symlink", "hardlink"]
)
def test_staged_worker_changes_are_validated(tmp_path, change):
    workspace, run_id, work = prepared(tmp_path)
    output = work / "docs/readme.md"
    if change == "new_file":
        write(work, "docs/unselected.md")
    elif change == "new_dir":
        (work / "extra").mkdir()
    elif change == "policy":
        write(work, "AGENTS.md", "Run commands.\n")
    elif change == "input":
        write(work, "src/example.py", "changed")
    else:
        output.unlink()
        if change == "symlink":
            output.symlink_to(tmp_path / "docs/readme.md")
        elif change == "hardlink":
            os.link(tmp_path / "docs/readme.md", output)
    with pytest.raises(TeeError):
        workspace.diff(run_id)
    assert (tmp_path / "docs/readme.md").read_text() == "original\n"


@pytest.mark.parametrize("name", ["src/example.py", "docs/readme.md"])
def test_changed_original_input_or_output_conflicts(tmp_path, name):
    workspace, run_id, work = prepared(tmp_path)
    write(work, "docs/readme.md", "draft\n")
    review = workspace.diff(run_id)["review_sha256"]
    write(tmp_path, name, "new owner work\n")
    with pytest.raises(TeeError) as error:
        workspace.apply(run_id, review)
    assert error.value.code == "docagent_conflict"
    assert (tmp_path / name).read_text() == "new owner work\n"


def test_new_owner_output_is_not_overwritten(tmp_path):
    workspace = DocWorkspace(tmp_path)
    run = workspace.prepare([], ["new.md"], "Document.")
    write(Path(run["work_dir"]), "new.md", "draft")
    review = workspace.diff(run["run_id"])["review_sha256"]
    write(tmp_path, "new.md", "owner")
    with pytest.raises(TeeError):
        workspace.apply(run["run_id"], review)
    assert (tmp_path / "new.md").read_text() == "owner"


def test_review_hash_binds_all_content_even_when_patch_truncated(tmp_path):
    workspace, run_id, work = prepared(tmp_path)
    write(work, "docs/readme.md", "draft\n" * 40)
    before = workspace.diff(run_id, max_chars=5)
    assert before["truncated"] and len(before["patch"]) == 5
    write(work, "docs/readme.md", "draft\n" * 39 + "edited\n")
    after = workspace.diff(run_id, max_chars=5)
    assert before["patch"] == after["patch"]
    assert before["review_sha256"] != after["review_sha256"]
    with pytest.raises(TeeError) as error:
        workspace.apply(run_id, before["review_sha256"])
    assert error.value.code == "docagent_review_changed"


def test_partial_write_failure_restores_existing_and_removes_created(tmp_path, monkeypatch):
    write(tmp_path, "b.md", "owner\n")
    workspace = DocWorkspace(tmp_path)
    run = workspace.prepare([], ["a/new.md", "b.md"], "Document.")
    work = Path(run["work_dir"])
    write(work, "a/new.md", "new\n")
    write(work, "b.md", "changed\n")
    review = workspace.diff(run["run_id"])["review_sha256"]
    real_replace = mod.os.replace

    def failing_replace(src, dst):
        if Path(dst) == tmp_path / "b.md":
            raise OSError("fixture disk failure")
        return real_replace(src, dst)

    monkeypatch.setattr(mod.os, "replace", failing_replace)
    with pytest.raises(TeeError) as error:
        workspace.apply(run["run_id"], review)
    assert error.value.code == "docagent_apply_failed"
    assert (tmp_path / "b.md").read_text() == "owner\n"
    assert not (tmp_path / "a").exists()
    assert not list(tmp_path.rglob(".tee-doc-*.tmp"))
    assert not (tmp_path / ".tee/docagents/apply.lock").exists()


def test_failure_after_replacing_existing_file_restores_bytes_and_mode(tmp_path, monkeypatch):
    write(tmp_path, "a.md", "first\n").chmod(0o640)
    write(tmp_path, "b.md", "second\n")
    workspace = DocWorkspace(tmp_path)
    run = workspace.prepare([], ["a.md", "b.md"], "Document.")
    for name in ("a.md", "b.md"):
        write(Path(run["work_dir"]), name, "changed\n")
    real_replace = mod.os.replace

    def failing_replace(src, dst):
        if Path(dst) == tmp_path / "b.md":
            raise OSError("fixture disk failure")
        return real_replace(src, dst)

    monkeypatch.setattr(mod.os, "replace", failing_replace)
    with pytest.raises(TeeError):
        workspace.apply(run["run_id"], workspace.diff(run["run_id"])["review_sha256"])
    assert (tmp_path / "a.md").read_text() == "first\n"
    assert (tmp_path / "a.md").stat().st_mode & 0o777 == 0o640
    assert (tmp_path / "b.md").read_text() == "second\n"


def test_bounds_and_binary_refused(tmp_path):
    workspace = DocWorkspace(tmp_path)
    with pytest.raises(TeeError):
        workspace.prepare([], [f"{i}.md" for i in range(65)], "Document.")
    with pytest.raises(TeeError):
        workspace.prepare([], ["out.md"], "x" * 8193)
    write(tmp_path, "large.txt", "x" * (mod.MAX_BYTES + 1))
    with pytest.raises(TeeError):
        workspace.prepare(["large.txt"], ["out.md"], "Document.")
    write(tmp_path, "binary.txt", "abc\x00def")
    with pytest.raises(TeeError):
        workspace.prepare(["binary.txt"], ["out.md"], "Document.")
    (tmp_path / "binary.txt").write_bytes(b"\xff")
    with pytest.raises(TeeError):
        workspace.prepare(["binary.txt"], ["out.md"], "Document.")


def test_combined_input_and_candidate_bounds(tmp_path):
    write(tmp_path, "source.txt", "x" * (mod.MAX_BYTES // 2 + 1))
    write(tmp_path, "out.md", "y" * (mod.MAX_BYTES // 2 + 1))
    workspace = DocWorkspace(tmp_path)
    with pytest.raises(TeeError):
        workspace.prepare(["source.txt"], ["out.md"], "Document.")
    write(tmp_path, "out.md", "small")
    run = workspace.prepare(["source.txt"], ["out.md"], "Document.")
    write(Path(run["work_dir"]), "out.md", "y" * (mod.MAX_BYTES // 2 + 1))
    with pytest.raises(TeeError):
        workspace.diff(run["run_id"])


@pytest.mark.parametrize("outputs", [["x.md", "x.md"], ["X.md", "x.md"], ["a.md", "a.md/x.md"]])
def test_ambiguous_paths_refused(tmp_path, outputs):
    with pytest.raises(TeeError):
        DocWorkspace(tmp_path).prepare([], outputs, "Document.")


def test_manifest_cannot_introduce_protected_output(tmp_path):
    workspace, run_id, _work = prepared(tmp_path)
    manifest = Path(workspace.load(run_id)["run_dir"]) / "manifest.json"
    data = json.loads(manifest.read_text())
    data["outputs"]["AGENTS.md"] = None
    manifest.write_text(json.dumps(data))
    with pytest.raises(TeeError):
        workspace.load(run_id)


def test_project_lock_prevents_concurrent_apply(tmp_path):
    workspace, run_id, work = prepared(tmp_path)
    write(work, "docs/readme.md", "changed")
    write(tmp_path, ".tee/docagents/apply.lock", "other run")
    with pytest.raises(TeeError) as error:
        workspace.apply(run_id, workspace.diff(run_id)["review_sha256"])
    assert error.value.code == "docagent_busy"
    assert (tmp_path / ".tee/docagents/apply.lock").read_text() == "other run"


@pytest.mark.parametrize(
    "field,value", [("inputs", []), ("outputs", []), ("files", []), ("schema", True)]
)
def test_malformed_manifest_refuses_compactly(tmp_path, field, value):
    workspace, run_id, _work = prepared(tmp_path)
    manifest = Path(workspace.load(run_id)["run_dir"]) / "manifest.json"
    row = json.loads(manifest.read_text())
    row[field] = value
    manifest.write_text(json.dumps(row))
    with pytest.raises(TeeError) as error:
        workspace.load(run_id)
    assert error.value.code == "docagent_manifest"


def test_source_race_after_temp_staging_refuses_before_any_replace(tmp_path, monkeypatch):
    workspace, run_id, work = prepared(tmp_path)
    write(work, "docs/readme.md", "draft\n")
    review = workspace.diff(run_id)["review_sha256"]
    real_temporary = mod._temporary

    def concurrent_edit(path, data, mode):
        result = real_temporary(path, data, mode)
        write(tmp_path, "src/example.py", "owner concurrent change\n")
        return result

    monkeypatch.setattr(mod, "_temporary", concurrent_edit)
    with pytest.raises(TeeError) as error:
        workspace.apply(run_id, review)
    assert error.value.code == "docagent_conflict"
    assert (tmp_path / "docs/readme.md").read_text() == "original\n"
    assert (tmp_path / "src/example.py").read_text() == "owner concurrent change\n"
    assert not list(tmp_path.rglob(".tee-doc-*.tmp"))


def test_new_output_parent_symlink_after_review_is_refused(tmp_path):
    project = tmp_path / "project"
    project.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    workspace = DocWorkspace(project)
    run = workspace.prepare([], ["new/out.md"], "Document.")
    write(Path(run["work_dir"]), "new/out.md", "draft")
    review = workspace.diff(run["run_id"])["review_sha256"]
    (project / "new").symlink_to(outside, target_is_directory=True)
    with pytest.raises(TeeError):
        workspace.apply(run["run_id"], review)
    assert not (outside / "out.md").exists()


def test_run_and_work_links_and_invalid_run_ids_are_refused(tmp_path):
    workspace, run_id, work = prepared(tmp_path)
    with pytest.raises(TeeError):
        workspace.load("../other")
    moved = work.with_name("moved")
    work.rename(moved)
    work.symlink_to(moved, target_is_directory=True)
    with pytest.raises(TeeError):
        workspace.diff(run_id)


def test_document_can_be_both_input_and_output_and_missing_newline_is_explicit(tmp_path):
    write(tmp_path, "doc.md", "old")
    workspace = DocWorkspace(tmp_path)
    run = workspace.prepare(["doc.md"], ["doc.md"], "Revise.")
    write(Path(run["work_dir"]), "doc.md", "new")
    diff = workspace.diff(run["run_id"])
    assert "-old\n\\ No newline at end of file\n" in diff["patch"]
    workspace.apply(run["run_id"], diff["review_sha256"])
    assert (tmp_path / "doc.md").read_bytes() == b"new"


def test_rollback_failure_is_honest_and_retains_recovery_bytes(tmp_path, monkeypatch):
    write(tmp_path, "a.md", "original a\n")
    write(tmp_path, "b.md", "original b\n")
    workspace = DocWorkspace(tmp_path)
    run = workspace.prepare([], ["a.md", "b.md"], "Document.")
    for name in ("a.md", "b.md"):
        write(Path(run["work_dir"]), name, "draft\n")
    real_replace = mod.os.replace
    count = 0

    def fail_after_first(src, dst):
        nonlocal count
        count += 1
        if count >= 2:
            raise OSError("fixture persistent failure")
        return real_replace(src, dst)

    monkeypatch.setattr(mod.os, "replace", fail_after_first)
    with pytest.raises(TeeError) as error:
        workspace.apply(run["run_id"], workspace.diff(run["run_id"])["review_sha256"])
    assert error.value.code == "docagent_rollback_failed"
    backups = list(Path(workspace.load(run["run_id"])["run_dir"]).glob("backup-*"))
    assert (backups[0] / "a.md").read_text() == "original a\n"
    assert (backups[0] / "b.md").read_text() == "original b\n"


def test_unicode_aliases_refused(tmp_path):
    with pytest.raises(TeeError):
        DocWorkspace(tmp_path).prepare([], ["caf\u00e9.md", "cafe\u0301.md"], "Document.")


@pytest.mark.parametrize("role", ["input", "output"])
@pytest.mark.parametrize(
    "name",
    [
        "secrets/openai.json",
        "credentials/provider.json",
        "secrets/reference.md",
        "docs/CrEdEnTiAlS/reference.md",
        "nested/SECRETS/provider/reference.txt",
    ],
)
def test_credential_components_refused_for_inputs_and_outputs(tmp_path, role, name):
    inputs = [name] if role == "input" else []
    outputs = [name] if role == "output" else ["docs/output.md"]
    with pytest.raises(TeeError) as error:
        DocWorkspace(tmp_path).prepare(inputs, outputs, "Document.")
    assert error.value.code == "docagent_protected_path"
    assert not (tmp_path / ".tee").exists()


def test_ordinary_source_directories_and_auth_guide_remain_allowed(tmp_path):
    write(tmp_path, "src/authentication/reader.py", "def read(): pass\n")
    write(tmp_path, "src/secretary/example.py", "def example(): pass\n")
    write(tmp_path, "docs/auth-guide.md", "Authentication guide\n")
    workspace = DocWorkspace(tmp_path)
    run = workspace.prepare(
        ["src/authentication/reader.py", "src/secretary/example.py", "docs/auth-guide.md"],
        ["docs/auth-guide.md"],
        "Document authentication.",
    )
    assert workspace.diff(run["run_id"])["changes"] == []
