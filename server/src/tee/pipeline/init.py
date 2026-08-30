"""The draft route (A43 P4): read a project's scripts, propose steps.

The other two authoring routes need the owner to already know what they
want declared - hand-writing needs the whole shape, and adopt-after-ad-hoc
needs the command to have been run once. This one starts from what is
already in the project: entry points with a command-line interface, their
own docstrings, and the arguments they insist on.

What it will NOT do is write a runnable step. Every drafted block is
emitted COMMENTED OUT, so the file copied verbatim into
`.tee/pipeline.toml` declares exactly zero steps; the owner uncomments
what they actually want and fills the values a scan cannot know. That is
structural rather than a promise - a scan of somebody's build scripts is
a guess about intent, and a guess must not become an execution grant just
because it was formatted as TOML.

The scan is deliberately shallow: an entry point, its first docstring
line, its required flags. Everything else - which paths are inputs, which
are outputs, what a parameter may legally be - is domain knowledge that
belongs to the owner. TEE writes no domain knowledge.
"""

from __future__ import annotations

import ast
import os
from dataclasses import dataclass, field
from pathlib import Path

SKIP_DIRS = {
    ".git",
    ".tee",
    "__pycache__",
    ".venv",
    "venv",
    "node_modules",
    ".mypy_cache",
    "build",
    "dist",
    "archives",
    "backups",
    "checkpoints",
}
MAX_FILES = 4000
MAX_CANDIDATES = 30
# Entry points whose names suggest they answer rather than build. A guess,
# and labelled as one in the draft - the owner sets `kind`.
QUERY_HINTS = ("stats", "check", "report", "analysis", "count", "probe", "measure", "diff")


@dataclass
class Candidate:
    path: str
    summary: str = ""
    required: list[str] = field(default_factory=list)
    optional: list[str] = field(default_factory=list)
    kind_guess: str = "produce"
    # "flags" (argparse) or "positional" (bare sys.argv). Found by running
    # this against a real project: plenty of working scripts never import
    # argparse, and a draft tool that only sees argparse would quietly
    # report a project has fewer steps than it has.
    argv_style: str = "flags"

    @property
    def name(self) -> str:
        return Path(self.path).stem.replace("-", "_").lower()


def _first_line(text: str | None) -> str:
    if not text:
        return ""
    for line in text.strip().splitlines():
        stripped = line.strip()
        if stripped:
            # module docstrings here often open "name.py - what it does"
            for separator in (" — ", " - "):
                if separator in stripped:
                    stripped = stripped.split(separator, 1)[1]
                    break
            return stripped[:160]
    return ""


def _flag_of(call: ast.Call) -> str | None:
    for arg in call.args:
        if isinstance(arg, ast.Constant) and isinstance(arg.value, str) and arg.value[:1] == "-":
            return arg.value
    return None


def _scan_python(path: Path) -> Candidate | None:
    try:
        source = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None
    if "argparse" not in source and "__main__" not in source:
        return None
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return None
    candidate = Candidate(path="", summary=_first_line(ast.get_docstring(tree)))
    found_parser = False
    reads_argv = False
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Attribute)
            and node.attr == "argv"
            and isinstance(node.value, ast.Name)
            and node.value.id == "sys"
        ):
            reads_argv = True
        if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
            continue
        if node.func.attr == "ArgumentParser":
            found_parser = True
            continue
        if node.func.attr != "add_argument":
            continue
        flag = _flag_of(node)
        if flag is None:
            continue
        keywords = {kw.arg for kw in node.keywords}
        required = any(
            kw.arg == "required" and isinstance(kw.value, ast.Constant) and kw.value.value is True
            for kw in node.keywords
        )
        # `action=` supplies its own default (store_true is False, count is
        # 0), so an action flag is never one the caller must pass. Only a
        # bare flag with no default is treated as something the script
        # cannot run without.
        has_default = "default" in keywords or "action" in keywords
        if required or (flag not in candidate.optional and not has_default):
            if flag not in candidate.required:
                candidate.required.append(flag)
        elif flag not in candidate.optional:
            candidate.optional.append(flag)
    if not found_parser:
        if not (reads_argv and "__main__" in source):
            return None
        candidate.argv_style = "positional"
    return candidate


def _scan_shell(path: Path) -> Candidate | None:
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()[:20]
    except OSError:
        return None
    comments = [line.lstrip("# ").strip() for line in lines if line.startswith("#")]
    summary = next((c for c in comments if c and not c.startswith("!")), "")
    return Candidate(path="", summary=summary[:160])


def scan(root: Path | str) -> list[Candidate]:
    """Entry points with a command-line interface, cheapest scan first."""
    root = Path(root)
    found: list[Candidate] = []
    seen = 0
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(d for d in dirnames if d not in SKIP_DIRS and not d.startswith("."))
        for filename in sorted(filenames):
            seen += 1
            if seen > MAX_FILES:
                return found[:MAX_CANDIDATES]
            path = Path(dirpath) / filename
            if filename.endswith(".py"):
                candidate = _scan_python(path)
            elif filename.endswith(".sh"):
                candidate = _scan_shell(path)
            else:
                continue
            if candidate is None:
                continue
            candidate.path = str(path.relative_to(root))
            stem = candidate.name
            if any(hint in stem for hint in QUERY_HINTS):
                candidate.kind_guess = "query"
            found.append(candidate)
            if len(found) >= MAX_CANDIDATES:
                return found
    return found


def _argv_line(candidate: Candidate) -> str:
    parts = ["python3" if candidate.path.endswith(".py") else "bash", candidate.path]
    if candidate.argv_style == "positional":
        parts.append("<FILL>")
    else:
        for flag in candidate.required[:8]:
            parts += [flag, "<FILL>"]
    return "argv = [" + ", ".join(f'"{p}"' for p in parts) + "]"


def draft(root: Path | str, candidates: list[Candidate] | None = None) -> str:
    """The candidate file's text. Every step COMMENTED OUT, by law."""
    root = Path(root)
    candidates = scan(root) if candidates is None else candidates
    out = [
        f"# TEE draft for {root.name} - NOT A DECLARATION YET.",
        "#",
        "# Every block below is commented out on purpose: this file copied",
        "# as-is into .tee/pipeline.toml declares zero steps. A scan of your",
        "# scripts is a guess about your intent, and a guess must not become",
        "# permission to run something just because it is valid TOML.",
        "#",
        "# To adopt one: uncomment it, replace every <FILL>, state the inputs",
        "# and outputs it really touches, and bound any params. Then approve",
        "# the file. TEE never writes .tee/pipeline.toml.",
    ]
    if not candidates:
        out += [
            "#",
            "# Nothing with a command-line interface was found to draft from.",
            "# Hand-write the first step, or run it once with pipeline_adhoc",
            "# and adopt what it actually did.",
        ]
        return "\n".join(out) + "\n"
    for candidate in candidates:
        out.append("")
        if candidate.summary:
            out.append(f"# {candidate.summary}")
        out.append(f"# kind below is a GUESS from the name - {candidate.path}")
        if candidate.argv_style == "positional":
            out.append("# reads sys.argv directly: the <FILL> below is positional")
        out.append("# [[step]]")
        out.append(f'# name = "{candidate.name}"')
        out.append(f'# kind = "{candidate.kind_guess}"')
        out.append(f"# {_argv_line(candidate)}")
        out.append("# inputs = []   # <FILL: paths this reads, for staleness")
        if candidate.kind_guess == "produce":
            out.append("# outputs = []  # <FILL: paths this writes, for the diff")
        else:
            out.append('# answer = { format = "text", max_tokens = 400 }')
        if candidate.optional:
            shown = ", ".join(candidate.optional[:8])
            out.append(f"# other flags it accepts: {shown}")
    return "\n".join(out) + "\n"
