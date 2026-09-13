"""Bounded documentation staging and reviewed application, not an OS sandbox."""

from __future__ import annotations

import contextlib
import difflib
import hashlib
import json
import os
import re
import stat
import unicodedata
import uuid
from collections.abc import Callable
from functools import wraps
from pathlib import Path
from typing import Any, ParamSpec, TypeVar

from tee.kernel.errors import TeeError

MAX_FILES = 64
MAX_BYTES = 1024 * 1024
MAX_INSTRUCTION = 8192
_RUN = re.compile(r"doc_[0-9a-f]{32}\Z")
_SHA = re.compile(r"[0-9a-f]{64}\Z")
_DOC = frozenset({".md", ".rst", ".txt", ".adoc"})
_POLICY = frozenset({"agents.md", "claude.md", "skill.md"})
_SECRET = frozenset(
    {
        "credentials",
        "credential",
        "secrets",
        "secret",
        "passwords",
        "api_keys",
        "api_key",
        "apikeys",
        "token",
        "tokens",
        "auth",
        "id_rsa",
        "id_ed25519",
        "id_ecdsa",
        "id_dsa",
        "authorized_keys",
        "known_hosts",
    }
)
_P = ParamSpec("_P")
_T = TypeVar("_T")


def _fail(code: str, message: str, fix: str | None = None) -> TeeError:
    return TeeError("docagent_" + code, message, fix or "Use explicit ordinary project text files.")


def _filesystem_errors(function: Callable[_P, _T]) -> Callable[_P, _T]:
    @wraps(function)
    def guarded(*args: _P.args, **kwargs: _P.kwargs) -> _T:
        try:
            return function(*args, **kwargs)
        except OSError:
            raise _fail(
                "filesystem",
                "Workspace filesystem access failed.",
                "Check the project paths and permissions, then retry.",
            ) from None

    return guarded


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()


def _relative(value: Any, *, output: bool = False) -> str:
    if not isinstance(value, str) or not value or len(value) > 512:
        raise _fail("path", "A file path must be a bounded relative string.")
    parts = value.split("/")
    if (
        any(p in {"", ".", ".."} for p in parts)
        or "\\" in value
        or ":" in value
        or any(ord(c) < 32 or ord(c) == 127 or 0xD800 <= ord(c) <= 0xDFFF for c in value)
    ):
        raise _fail("path", "Absolute, traversing and nonportable paths are refused.")
    folded = [p.casefold() for p in parts]
    name = folded[-1]
    path = "/".join(folded)
    if (
        any(p.startswith(".") for p in parts)
        or any(p in _SECRET for p in folded)
        or name in _POLICY
        or name.endswith("script.md")
        or Path(name).stem in _SECRET
        or Path(name).suffix in {".pem", ".key", ".p12", ".pfx", ".keystore"}
        or name
        in {
            "cline_mcp_settings.json",
            "settings.json",
            "config.json",
            "config.toml",
            "cline.json",
            "mcp.json",
            "aider.yml",
            "aider.yaml",
        }
        or path == "docs/upgrade-coordination-protocol.md"
        or path == "docs/coordination"
        or path.startswith("docs/coordination/")
    ):
        raise _fail("protected_path", "Policy, credentials and agent configuration are excluded.")
    if output and Path(name).suffix not in _DOC:
        raise _fail("output_type", "Outputs must be .md, .rst, .txt or .adoc documentation.")
    return value


def _path(base: Path, relative: str) -> Path:
    """Check every existing component; an absent leaf is different from a link."""
    path = base
    for part in Path(relative).parts:
        path /= part
        try:
            mode = path.lstat().st_mode
        except FileNotFoundError:
            continue
        if stat.S_ISLNK(mode):
            raise _fail("unsafe_file", "Symbolic links are refused.")
        if path != base / relative and not stat.S_ISDIR(mode):
            raise _fail("unsafe_file", "A parent path is not an ordinary directory.")
    return path


def _read(path: Path, *, absent: bool = False) -> tuple[bytes | None, int | None]:
    try:
        fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    except FileNotFoundError:
        if absent:
            return None, None
        raise _fail("missing_file", "A declared file is missing.") from None
    except OSError:
        raise _fail("unsafe_file", "A declared file cannot be read safely.") from None
    with os.fdopen(fd, "rb") as handle:
        info = os.fstat(handle.fileno())
        if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
            raise _fail("unsafe_file", "Only regular files with one hard link are accepted.")
        if info.st_size > MAX_BYTES:
            raise _fail("bounds", "A selected file exceeds the 1 MiB workspace limit.")
        data = handle.read(MAX_BYTES + 1)
    if len(data) > MAX_BYTES:
        raise _fail("bounds", "A selected file exceeds the 1 MiB workspace limit.")
    try:
        data.decode("utf-8")
    except UnicodeDecodeError:
        raise _fail("text", "Selected files must be UTF-8 text.") from None
    if b"\x00" in data:
        raise _fail("text", "Binary data is refused.")
    return data, stat.S_IMODE(info.st_mode)


def _mkdir(path: Path, created: list[Path] | None = None) -> None:
    if path.exists():
        if path.is_symlink() or not path.is_dir():
            raise _fail("unsafe_file", "A workspace directory is not an ordinary directory.")
        return
    _mkdir(path.parent, created)
    path.mkdir()
    if created is not None:
        created.append(path)


def _new_file(path: Path, data: bytes, mode: int = 0o600) -> None:
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, mode)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
            os.fchmod(handle.fileno(), mode)
    except BaseException:
        with contextlib.suppress(OSError):
            path.unlink()
        raise


def _temporary(path: Path, data: bytes, mode: int) -> Path:
    tmp = path.parent / (".tee-doc-" + uuid.uuid4().hex + ".tmp")
    try:
        _new_file(tmp, data, mode)
    except BaseException:
        tmp.unlink(missing_ok=True)
        raise
    return tmp


def _atomic(path: Path, data: bytes, mode: int = 0o600) -> None:
    tmp = _temporary(path, data, mode)
    try:
        os.replace(tmp, path)
    finally:
        with contextlib.suppress(OSError):
            tmp.unlink(missing_ok=True)


class DocWorkspace:
    def __init__(self, project_root: Path | str) -> None:
        self.root = Path(project_root).resolve()
        if not self.root.is_dir():
            raise _fail("project", "The project directory does not exist.")

    def _store(self) -> Path:
        return _path(self.root, ".tee/docagents")

    def _run_dir(self, run_id: str) -> Path:
        if not isinstance(run_id, str) or not _RUN.fullmatch(run_id):
            raise _fail("run_id", "Invalid documentation run ID.", "Use the ID from preparation.")
        return _path(self._store(), run_id)

    @staticmethod
    def _names(inputs: Any, outputs: Any) -> tuple[list[str], list[str]]:
        for items in (inputs, outputs):
            if not isinstance(items, list) or len(items) > MAX_FILES:
                raise _fail("bounds", "Use lists containing at most 64 files in total.")
        if not outputs:
            raise _fail("outputs", "Declare at least one documentation output.")
        ins = [_relative(p) for p in inputs]
        outs = [_relative(p, output=True) for p in outputs]
        if len(set(ins)) != len(ins) or len(set(outs)) != len(outs):
            raise _fail("path", "Duplicate paths are refused.")
        union = set(ins) | set(outs)
        if len(union) > MAX_FILES:
            raise _fail("bounds", "Use at most 64 distinct files in total.")
        if len({unicodedata.normalize("NFC", p.casefold()) for p in union}) != len(union):
            raise _fail(
                "path", "Paths differing only in case or Unicode normalization are refused."
            )
        for name in union:
            if any(p in union for p in (str(a) for a in Path(name).parents if str(a) != ".")):
                raise _fail("path", "A selected file cannot also be a parent directory.")
        return ins, outs

    @_filesystem_errors
    def prepare(self, inputs: list[str], outputs: list[str], instruction: str) -> dict[str, Any]:
        ins, outs = self._names(inputs, outputs)
        if (
            not isinstance(instruction, str)
            or not instruction.strip()
            or any(0xD800 <= ord(c) <= 0xDFFF for c in instruction)
            or len(instruction.encode("utf-8")) > MAX_INSTRUCTION
            or "\x00" in instruction
        ):
            raise _fail("instruction", "Supply a nonempty instruction of at most 8 KiB.")
        files: dict[str, dict[str, Any]] = {}
        content: dict[str, bytes] = {}
        for name in sorted(set(ins) | set(outs)):
            data, mode = _read(_path(self.root, name), absent=name not in ins)
            files[name] = {
                "sha256": _sha(data) if data is not None else None,
                "bytes": len(data) if data is not None else None,
                "mode": mode,
            }
            content[name] = data if data is not None else b""
        if sum(map(len, content.values())) > MAX_BYTES:
            raise _fail("bounds", "Selected files exceed the 1 MiB workspace limit.")
        run_id = "doc_" + uuid.uuid4().hex
        run_dir = self._run_dir(run_id)
        work = run_dir / "work"
        _mkdir(work)
        for name, data in content.items():
            target = work / name
            _mkdir(target.parent)
            _new_file(target, data)
        manifest = {
            "schema": 1,
            "run_id": run_id,
            "status": "prepared",
            "instruction": instruction,
            "inputs": {p: files[p]["sha256"] for p in ins},
            "outputs": {p: files[p]["sha256"] for p in outs},
            "files": files,
        }
        _new_file(run_dir / "manifest.json", _canonical(manifest))
        return {
            "ok": True,
            "run_id": run_id,
            "inputs": len(ins),
            "outputs": outs,
            "bytes": sum(map(len, content.values())),
            "work_dir": str(work),
            "note": "Staging is not an OS sandbox. Review the diff before application.",
        }

    @_filesystem_errors
    def load(self, run_id: str) -> dict[str, Any]:
        run_dir = self._run_dir(run_id)
        try:
            data, _ = _read(_path(run_dir, "manifest.json"))
            row = json.loads(data or b"")
            if (
                not isinstance(row, dict)
                or type(row.get("schema")) is not int
                or row["schema"] != 1
                or row.get("run_id") != run_id
                or not all(isinstance(row.get(key), dict) for key in ("inputs", "outputs", "files"))
            ):
                raise ValueError
            ins, outs = self._names(list(row["inputs"]), list(row["outputs"]))
            files = row["files"]
            if set(files) != set(ins) | set(outs) or row["status"] not in {"prepared", "applied"}:
                raise ValueError
            if not isinstance(row["instruction"], str) or len(row["instruction"].encode()) > 8192:
                raise ValueError
            for name, item in files.items():
                if not isinstance(item, dict):
                    raise ValueError
                digest = item["sha256"]
                if digest is not None and (
                    not isinstance(digest, str) or not _SHA.fullmatch(digest)
                ):
                    raise ValueError
                if digest is None and (
                    name in ins or item["bytes"] is not None or item["mode"] is not None
                ):
                    raise ValueError
                if digest is not None and (
                    type(item["bytes"]) is not int
                    or not 0 <= item["bytes"] <= MAX_BYTES
                    or type(item["mode"]) is not int
                    or not 0 <= item["mode"] <= 0o7777
                ):
                    raise ValueError
                if any(
                    mapping.get(name, digest) != digest
                    for mapping in (row["inputs"], row["outputs"])
                ):
                    raise ValueError
            if sum(v["bytes"] or 0 for v in files.values()) > MAX_BYTES:
                raise ValueError
        except (KeyError, TypeError, ValueError):
            raise _fail(
                "manifest", "The documentation manifest is invalid.", "Prepare a new run."
            ) from None
        return {**row, "run_dir": str(run_dir), "work_dir": str(_path(run_dir, "work"))}

    def _candidate(self, row: dict[str, Any]) -> dict[str, bytes]:
        work = Path(row["work_dir"])
        if not work.is_dir():
            raise _fail("missing_file", "The staged workspace is missing.")
        expected = set(row["files"])
        directories = {str(a) for p in expected for a in Path(p).parents if str(a) != "."}
        found: dict[str, bytes] = {}
        pending = [work]
        while pending:
            # Stream directory entries: an unexpected log flood cannot first
            # allocate an unbounded os.walk filename list.
            with os.scandir(pending.pop()) as entries:
                for entry in entries:
                    path = Path(entry.path)
                    relative = path.relative_to(work).as_posix()
                    if entry.is_symlink():
                        raise _fail("unsafe_file", "Symbolic links are refused.")
                    if entry.is_dir(follow_symlinks=False):
                        if relative not in directories:
                            raise _fail(
                                "unexpected_file", "The worker created an undeclared directory."
                            )
                        pending.append(path)
                        continue
                    if relative not in expected:
                        raise _fail("unexpected_file", "The worker created an undeclared file.")
                    data, _ = _read(_path(work, relative))
                    found[relative] = data or b""
                    if sum(map(len, found.values())) > MAX_BYTES:
                        raise _fail("bounds", "Staged files exceed the 1 MiB workspace limit.")
        if set(found) != expected:
            raise _fail("missing_file", "A declared staged input or output is missing.")
        if any(
            _sha(found[p]) != digest
            for p, digest in row["inputs"].items()
            if p not in row["outputs"]
        ):
            raise _fail("input_modified", "The worker modified an input-only file.")
        return found

    def _originals(self, row: dict[str, Any]) -> dict[str, tuple[bytes | None, int | None]]:
        originals = {}
        for name, item in row["files"].items():
            data, mode = _read(_path(self.root, name), absent=True)
            if (_sha(data) if data is not None else None) != item["sha256"]:
                raise _fail(
                    "conflict",
                    "Project files changed after preparation.",
                    "Prepare a new run from the current files; no changes were applied.",
                )
            originals[name] = (data, mode)
        return originals

    @staticmethod
    def _review(row: dict[str, Any], candidate: dict[str, bytes]) -> str:
        return _sha(
            _canonical(
                {
                    "schema": 1,
                    "run_id": row["run_id"],
                    "baseline": row["files"],
                    "outputs": {p: _sha(candidate[p]) for p in row["outputs"]},
                }
            )
        )

    @_filesystem_errors
    def diff(self, run_id: str, max_chars: int = 4000) -> dict[str, Any]:
        if type(max_chars) is not int or not 0 <= max_chars <= 64000:
            raise _fail("bounds", "max_chars must be between 0 and 64000.")
        row = self.load(run_id)
        candidate = self._candidate(row)
        originals = self._originals(row)
        changes, patches = [], []
        for name in sorted(row["outputs"]):
            data = candidate[name]
            before = originals[name][0]
            if before is not None and data == before:
                continue
            changes.append(
                {
                    "path": name,
                    "change": "created" if before is None else "modified",
                    "before_sha256": row["outputs"][name],
                    "sha256": _sha(data),
                    "bytes": len(data),
                }
            )
            lines = difflib.unified_diff(
                (before or b"").decode().splitlines(keepends=True),
                data.decode().splitlines(keepends=True),
                fromfile=name if before is not None else "/dev/null",
                tofile=name,
            )
            patch = "".join(
                line if line.endswith("\n") else line + "\n\\ No newline at end of file\n"
                for line in lines
            )
            patches.append(patch or f"--- /dev/null\n+++ {name}\n(empty file created)\n")
        patch = "\n".join(patches)
        return {
            "ok": True,
            "run_id": run_id,
            "changes": changes,
            "review_sha256": self._review(row, candidate),
            "patch": patch[:max_chars],
            "truncated": len(patch) > max_chars,
        }

    @_filesystem_errors
    def apply(self, run_id: str, review_sha256: str) -> dict[str, Any]:
        row = self.load(run_id)
        if row["status"] == "applied":
            raise _fail("already_applied", "This documentation run was already applied.")
        if not isinstance(review_sha256, str) or not _SHA.fullmatch(review_sha256):
            raise _fail("review", "Supply the SHA-256 from the reviewed diff.")
        lock = _path(self._store(), "apply.lock")
        try:
            _new_file(lock, run_id.encode())
        except FileExistsError:
            raise _fail(
                "busy",
                "Another documentation application holds the project lock.",
                "Wait for it to finish; inspect a stale lock before removing it.",
            ) from None
        try:
            return self._apply(row, review_sha256)
        finally:
            with contextlib.suppress(OSError):
                lock.unlink(missing_ok=True)

    def _apply(self, row: dict[str, Any], review: str) -> dict[str, Any]:
        candidate = self._candidate(row)
        if self._review(row, candidate) != review:
            raise _fail(
                "review_changed",
                "The staged changes no longer match the reviewed diff.",
                "Review the current diff and use its new SHA-256.",
            )
        originals = self._originals(row)
        changed = [p for p in sorted(row["outputs"]) if originals[p][0] != candidate[p]]
        backup = Path(row["run_dir"]) / ("backup-" + uuid.uuid4().hex)
        backup.mkdir()
        temps: dict[str, Path] = {}
        applied: list[str] = []
        created_dirs: list[Path] = []
        try:
            for name in changed:
                before, mode = originals[name]
                if before is not None:
                    saved = backup / name
                    _mkdir(saved.parent)
                    _new_file(saved, before, mode if mode is not None else 0o600)
            _new_file(backup / "baseline.json", _canonical({p: row["files"][p] for p in changed}))
            for name in changed:
                target = _path(self.root, name)
                _mkdir(target.parent, created_dirs)
                mode = originals[name][1]
                temps[name] = _temporary(
                    target, candidate[name], mode if mode is not None else 0o644
                )
            self._originals(row)
            for name in changed:
                target = _path(self.root, name)
                data, _ = _read(target, absent=True)
                if data != originals[name][0]:
                    raise _fail("conflict", "An output changed during application.")
                os.replace(temps[name], target)
                applied.append(name)
            saved_row = {k: v for k, v in row.items() if k not in {"run_dir", "work_dir"}}
            saved_row.update(status="applied", review_sha256=review, backup_path=str(backup))
            _atomic(Path(row["run_dir"]) / "manifest.json", _canonical(saved_row))
        except Exception as exc:
            rollback_failed = False
            for name in reversed(applied):
                try:
                    target = _path(self.root, name)
                    current, _ = _read(target)
                    if current != candidate[name]:
                        raise _fail("conflict", "An applied output changed during rollback.")
                    before, mode = originals[name]
                    if before is None:
                        target.unlink()
                    else:
                        _atomic(target, before, mode if mode is not None else 0o600)
                except Exception:
                    rollback_failed = True
            if rollback_failed:
                raise _fail(
                    "rollback_failed",
                    "Application failed; a rollback also failed.",
                    f"Preserved originals are in {backup}; inspect before restoring.",
                ) from exc
            if isinstance(exc, TeeError):
                raise
            raise _fail(
                "apply_failed",
                "Application failed; original outputs were restored.",
                "Resolve the filesystem error, then review and retry.",
            ) from exc
        finally:
            for tmp in temps.values():
                with contextlib.suppress(OSError):
                    tmp.unlink(missing_ok=True)
            for directory in reversed(created_dirs):
                with contextlib.suppress(OSError):
                    directory.rmdir()
        return {
            "ok": True,
            "run_id": row["run_id"],
            "applied": applied,
            "backup_path": str(backup),
            "review_sha256": review,
        }
