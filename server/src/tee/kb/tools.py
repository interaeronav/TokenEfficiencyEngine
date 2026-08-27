"""TEE KB virtual tools (kb_*) - read-only, budgeted, flags verbatim (16.3).

Four registry tools behind progressive disclosure; nothing lands on the
always-loaded surface. Every response that carries corpus content carries
the corpus's own confidence and jurisdiction markers, and content marked
needs-verification or low-confidence is labelled, never served bare (A30).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from tee.kb import search as kb_search_mod
from tee.kb.index import KbIndex, resolve_root
from tee.kernel.budget import estimate_tokens
from tee.kernel.registry import VirtualTool

DEFAULT_READ_TOKENS = 800
DEFAULT_FACTS_TOKENS = 1500
MAX_READ_TOKENS = 4000
FACTS_FILES_CAP = 10

A30_NOTE = (
    "imported reference (A30): grounds nothing until re-checked against "
    "the source its frontmatter cites"
)


def _flags(record: dict[str, Any]) -> dict[str, Any]:
    flags = {
        "confidence": record["confidence"],
        "jurisdiction": record["jurisdiction"],
        "status": record["status"],
    }
    return flags


def _warning(record: dict[str, Any]) -> str | None:
    marks = []
    if record.get("status") == "needs-verification":
        marks.append("status=needs-verification")
    if record.get("confidence") == "low":
        marks.append("confidence=low")
    if marks:
        return f"UNVERIFIED ({', '.join(marks)}): {A30_NOTE}"
    return None


def _fit(text: str, budget: int, *, what: str) -> tuple[str, str | None]:
    """Trim at line boundaries to fit the token budget, with one notice."""
    if estimate_tokens(text) <= budget:
        return text, None
    lines = text.splitlines()
    kept: list[str] = []
    used = 0
    for line in lines:
        cost = estimate_tokens(line) + 1
        if used + cost > budget:
            break
        kept.append(line)
        used += cost
    dropped = len(lines) - len(kept)
    return (
        "\n".join(kept),
        f"{what} truncated to ~{budget} tokens ({dropped} lines dropped) - "
        "raise max_tokens (cap 4000) or ask for a narrower section",
    )


def register_kb_tools(app, project_root: Path | str, *, root: str | None = None) -> KbIndex | None:
    """Attach kb_* when a corpus root resolves; stay silent otherwise (an
    explicitly configured root is attached even if broken, so calls fail
    loud with the fix instead of the module quietly vanishing)."""
    configured = root
    if configured is None:
        configured = getattr(getattr(app, "config", None), "kb", {}).get("root")
    resolved = resolve_root(project_root, configured)
    if resolved is None:
        # SI-B1: the module must never vanish silently - a lone kb_status
        # stays registered and answers inactive with the exact fix
        app.registry.register(
            VirtualTool(
                name="kb_status",
                description=(
                    "Expert Knowledge Base: INACTIVE for this project - no "
                    "corpus root resolves. Activate with [kb] root = "
                    '"/path/to/knowledge-base" in .tee/config.toml '
                    "(docs/setup-kb.md); kb_search/kb_read/kb_facts register "
                    "once a corpus resolves."
                ),
                schema={"type": "object", "properties": {}},
                handler=lambda args: {
                    "ok": False,
                    "error": {
                        "code": "kb_inactive",
                        "message": "No Knowledge Base corpus root resolves for this project.",
                        "fix": (
                            'Add [kb] root = "/path/to/knowledge-base" to '
                            ".tee/config.toml (docs/setup-kb.md)."
                        ),
                    },
                },
                tags=["kb", "knowledge"],
            )
        )
        return None
    index = KbIndex(resolved, project_root)
    kb_conf = getattr(getattr(app, "config", None), "kb", {}) or {}
    default_read = int(kb_conf.get("max_tokens", DEFAULT_READ_TOKENS))
    reg = app.registry

    def _budget(args: dict[str, Any], default: int) -> int:
        raw = args.get("max_tokens", default)
        return max(50, min(int(raw), MAX_READ_TOKENS))

    def kb_status(args):
        data = index.load(rebuild=bool(args.get("rebuild")))
        drift = index.recheck_drift() if not args.get("rebuild") else data["drift"]
        domains = [[d["slug"], d["files"], d["words"]] for d in data.get("domains", [])]
        return {
            "ok": True,
            "root": data["root"],
            "corpus": data.get("name", ""),
            "generated": data.get("generated"),
            "totals": data.get("totals", {}),
            "domains": {"cols": ["slug", "files", "words"], "rows": domains},
            "drift": drift,
            "note": A30_NOTE,
        }

    def kb_search(args):
        return kb_search_mod.search(
            index,
            str(args.get("query", "")),
            domain=args.get("domain"),
            jurisdiction=args.get("jurisdiction"),
            confidence=args.get("confidence"),
            status=args.get("status"),
            limit=args.get("limit", kb_search_mod.DEFAULT_LIMIT),
        )

    def kb_read(args):
        record = index.record(str(args["id"]))
        out: dict[str, Any] = {
            "id": record["id"],
            "title": record["title"],
            "path": record["path"],
            "flags": _flags(record),
        }
        warning = _warning(record)
        if warning:
            out["warning"] = warning
        section = args.get("section")
        if not section:
            out["sections"] = index.sections(record)
            out["hint"] = "call again with section=<title> for its text"
            return out
        budget = _budget(args, default_read)
        text = index.section_text(record, str(section))
        # the file's Sources block rides along so the citation is never lost
        sources = ""
        if str(section).strip().lower() != "sources":
            try:
                sources = index.section_text(record, "Sources")
            except Exception:
                sources = ""
        text, notice = _fit(text, budget, what=f"section '{section}'")
        out["section"] = section
        out["text"] = text
        if notice:
            out["truncated"] = notice
        if sources:
            room = max(100, budget // 4)
            sources, src_notice = _fit(sources, room, what="sources")
            out["sources"] = sources
            if src_notice:
                out["sources_truncated"] = src_notice
        return out

    def kb_facts(args):
        ids = args.get("ids") or []
        if ids:
            records = [index.record(str(i)) for i in ids[:FACTS_FILES_CAP]]
        else:
            found = kb_search_mod.search(
                index, str(args.get("query", "")), limit=int(args.get("limit", 5))
            )
            records = [index.record(hit["id"]) for hit in found["hits"]]
        budget = _budget(args, DEFAULT_FACTS_TOKENS)
        per_file = max(120, budget // max(1, len(records))) if records else budget
        blocks = []
        for record in records:
            block: dict[str, Any] = {"id": record["id"], "flags": _flags(record)}
            warning = _warning(record)
            if warning:
                block["warning"] = warning
            try:
                text = index.section_text(record, "Key facts")
            except Exception:
                block["facts"] = "no '## Key facts' section in this file"
                blocks.append(block)
                continue
            text, notice = _fit(text, per_file, what="facts")
            block["facts"] = text
            if notice:
                block["truncated"] = notice
            blocks.append(block)
        out: dict[str, Any] = {"blocks": blocks}
        drift = index.load().get("drift", {})
        if drift.get("stale"):
            out["stale"] = drift.get("fix", "index is stale - see kb_status")
        return out

    filter_props = {
        "domain": {"type": "string"},
        "jurisdiction": {"type": "string"},
        "confidence": {"type": "string"},
        "status": {"type": "string"},
    }
    for tool in [
        VirtualTool(
            "kb_status",
            "Expert Knowledge Base health: corpus totals, domain table, "
            "index freshness and drift against its manifest. "
            "rebuild=true re-reads the manifest and re-hashes the corpus.",
            {"type": "object", "properties": {"rebuild": {"type": "boolean"}}},
            kb_status,
            tags=["kb", "knowledge", "corpus", "status", "domains"],
        ),
        VirtualTool(
            "kb_search",
            "Search the Expert Knowledge Base (38 domains, 401 files) by "
            "keyword with optional exact filters. Returns ranked hits only "
            "(id, title, domain, confidence, one-line summary) - read a hit "
            "with kb_read. Content is imported reference: flags are the "
            "corpus's own, and low/needs-verification content is labelled.",
            {
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "limit": {"type": "integer"},
                    **filter_props,
                },
                "required": ["query"],
            },
            kb_search,
            tags=["kb", "knowledge", "search", "reference", "namibia", "construction"],
        ),
        VirtualTool(
            "kb_read",
            "Read one Knowledge Base file by id. Without section: the "
            "section list and the file's flags. With section: that section's "
            "text, token-budgeted (max_tokens, default 800, cap 4000), with "
            "the file's Sources block riding along so the citation is kept.",
            {
                "type": "object",
                "properties": {
                    "id": {"type": "string"},
                    "section": {"type": "string"},
                    "max_tokens": {"type": "integer"},
                },
                "required": ["id"],
            },
            kb_read,
            tags=["kb", "knowledge", "read", "section", "cite"],
        ),
        VirtualTool(
            "kb_facts",
            "The '## Key facts' blocks of matched Knowledge Base files - the "
            "metrics lane. Query or explicit ids; every block carries the "
            "file's confidence and jurisdiction flags verbatim.",
            {
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "ids": {"type": "array", "items": {"type": "string"}},
                    "limit": {"type": "integer"},
                    "max_tokens": {"type": "integer"},
                },
            },
            kb_facts,
            tags=["kb", "knowledge", "facts", "metrics", "numbers"],
        ),
    ]:
        reg.register(tool)
    return index
