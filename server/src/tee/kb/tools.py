"""TEE KB virtual tools (kb_*) - read-only, budgeted, flags verbatim (16.3).

Four registry tools behind progressive disclosure; nothing lands on the
always-loaded surface. Every response that carries corpus content carries
the corpus's own confidence and jurisdiction markers, and content marked
needs-verification or low-confidence is labelled, never served bare (A30).
"""

from __future__ import annotations

import json
import re
from datetime import date
from pathlib import Path
from typing import Any

from tee.kb import search as kb_search_mod
from tee.kb.index import KbIndex, resolve_root
from tee.kernel.budget import estimate_tokens
from tee.kernel.errors import TeeError
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
            records = [index.record(hit["id"]) for hit in found["items"]]
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

    # -- kb_propose (A37 P5.2 = A36 G6): gated authoring, A31-preserving ---
    # "The KB joins TEE as a read-only query module ... never written to by
    # TEE" (DECISIONS A31, 2026-08-26). Proposals therefore land ONLY in the
    # project's .tee/kb-staging/; the mirror stays untouchable by
    # construction, and a draft grounds nothing until the owner re-verifies
    # it at its cited sources and moves it in per docs/setup-kb.md.

    _JURISDICTIONS = ("global", "namibia", "south-africa", "southern-africa", "eu", "us", "uk")
    _ID_SHAPE = re.compile(r"^[a-z0-9]+(\.[a-z0-9_]+)+$")
    staging_root = (Path(project_root) / ".tee" / "kb-staging").resolve()

    def kb_propose(args: dict[str, Any]) -> dict[str, Any]:
        draft_id = str(args.get("id") or "").strip()
        if not _ID_SHAPE.fullmatch(draft_id):
            raise TeeError(
                "kb_bad_id",
                f"'{draft_id}' is not a corpus id.",
                fix="Use dotted lowercase like 'joinery.euro_hinges' - letters, "
                "digits, dots, underscores only (no slashes).",
            )
        data = index.load()
        domains = [d["slug"] for d in data.get("domains", [])]
        domain = str(args.get("domain") or "")
        if domain not in domains:
            raise TeeError(
                "kb_bad_domain",
                f"'{domain}' is not a corpus domain.",
                fix=f"One of: {', '.join(domains)}.",
            )
        jurisdiction = str(args.get("jurisdiction") or "global")
        if jurisdiction not in _JURISDICTIONS:
            raise TeeError(
                "kb_bad_jurisdiction",
                f"'{jurisdiction}' is not in the corpus schema.",
                fix=f"One of: {', '.join(_JURISDICTIONS)} (00_meta/SCHEMA.md).",
            )
        title = str(args.get("title") or "").strip()
        summary = str(args.get("summary") or "").strip()
        if not title or not summary:
            raise TeeError(
                "kb_bad_draft",
                "A proposal needs title and summary.",
                fix="Give a sentence-case title and a 2-5 sentence summary.",
            )
        sources = [s for s in (args.get("sources") or []) if isinstance(s, dict) and s.get("url")]
        if not sources:
            raise TeeError(
                "kb_uncited",
                "A proposal without sources cannot be reviewed.",
                fix="Give sources as [{title, url, publisher?, accessed?}] - "
                "cited material in, cited draft out (tee_web_lookup answers "
                "carry their citation).",
            )
        today = date.today().isoformat()
        source_lines = []
        for s in sources:
            entry = {
                "title": str(s.get("title") or s["url"]),
                "url": str(s["url"]),
                "publisher": str(s.get("publisher") or ""),
                "accessed": str(s.get("accessed") or today),
            }
            quoted = {k: json.dumps(v) for k, v in entry.items()}
            source_lines.append(
                f"  - {{title: {quoted['title']}, url: {quoted['url']}, "
                f"publisher: {quoted['publisher']}, accessed: {quoted['accessed']}}}"
            )
        tags = [str(t).strip().lower() for t in (args.get("tags") or []) if str(t).strip()]
        facts = [str(f).strip() for f in (args.get("key_facts") or []) if str(f).strip()]
        body_extra = str(args.get("body") or "").strip()
        front = [
            "---",
            f"id: {draft_id}",
            f"title: {json.dumps(title)}",
            f"domain: {domain}",
            f"tags: [{', '.join(tags)}]",
            f"jurisdiction: {jurisdiction}",
            "status: proposed",
            f"confidence: {args.get('confidence') or 'low'!s}",
            f"updated: {today}",
            "sources:",
            *source_lines,
            "proposed_by: tee kb_propose",
            "---",
        ]
        body = [
            f"# {title}",
            "",
            "> ⚠️ UNVERIFIED PROPOSAL (kb_propose): grounds nothing until the",
            "> owner re-verifies every fact at its cited source and accepts it",
            "> per docs/setup-kb.md (A30/A31).",
            "",
            summary,
        ]
        if facts:
            body += ["", "## Key facts", "", *[f"- {f}" for f in facts]]
        if body_extra:
            body += ["", body_extra]
        body += [
            "",
            "## Sources",
            "",
            *[f"- [{s.get('title') or s['url']!s}]({s['url']})" for s in sources],
            "",
            "## Open questions",
            "",
            "- Every fact above awaits re-verification at its cited source.",
        ]
        path = (staging_root / f"{draft_id}.md").resolve()
        if not path.is_relative_to(staging_root):  # belt over the id regex
            raise TeeError(
                "kb_bad_id", "The id escapes the staging folder.", fix="No path parts in ids."
            )
        replaced = path.exists()
        staging_root.mkdir(parents=True, exist_ok=True)
        path.write_text("\n".join([*front, "", *body]) + "\n", encoding="utf-8")
        out = {
            "ok": True,
            "id": draft_id,
            "path": str(path),
            "status": "proposed",
            "note": "UNVERIFIED draft staged OUTSIDE the corpus (A31: TEE never "
            "writes the mirror). Owner accepts per docs/setup-kb.md.",
        }
        if replaced:
            out["replaced"] = "a previous draft of this id was overwritten"
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
            "keyword with optional exact filters. Returns ranked rows only "
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
            "kb_propose",
            "Draft a NEW Knowledge Base entry for owner review. Writes a "
            "complete schema-shaped candidate (frontmatter with cited "
            "sources, status=proposed, UNVERIFIED banner) into "
            ".tee/kb-staging/ ONLY - the corpus mirror is never written by "
            "TEE (decision A31: 'a read-only query module ... never written "
            "to by TEE'). Pair with tee_web_lookup: cited material in, "
            "cited draft out. The owner accepts per docs/setup-kb.md.",
            {
                "type": "object",
                "properties": {
                    "id": {"type": "string"},
                    "title": {"type": "string"},
                    "domain": {"type": "string"},
                    "summary": {"type": "string"},
                    "key_facts": {"type": "array", "items": {"type": "string"}},
                    "body": {"type": "string"},
                    "tags": {"type": "array", "items": {"type": "string"}},
                    "jurisdiction": {"type": "string"},
                    "confidence": {"type": "string"},
                    "sources": {"type": "array", "items": {"type": "object"}},
                },
                "required": ["id", "title", "domain", "summary", "sources"],
            },
            kb_propose,
            tags=["kb", "knowledge", "propose", "draft", "staging", "author"],
            examples=[
                {
                    "id": "joinery.euro_hinges",
                    "title": "Euro (cup) hinges - boring, mounting, adjustment",
                    "domain": "06_joinery_and_woodwork",
                    "summary": "Cup hinges bore 35 mm...",
                    "sources": [{"title": "Blum catalogue", "url": "https://example/blum"}],
                }
            ],
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
