"""Technical boards (A37 P7): templated pages from live artifacts.

`board_compose` lays renders, drawing sheets, tables and fact panels
into ONE styled SVG page - title block, grid, captions, footer stamp.
Pure stdlib (images embed as base64 data URIs), so it works on the base
install; SVG renders crisply in any host or browser.

Scope honesty (research 52 pain 3, by design): TEE supplies BOARDS -
the renders, sheets and facts a presentation embeds. Slide-deck polish
is a host-side job and deliberately out of scope; this module will not
grow transitions, themes or layout AI.

Budget: the response is a compact pointer (path, bytes, panel count) -
the board itself is a file, never inline content.
"""

from __future__ import annotations

import base64
import html
import time
from pathlib import Path
from typing import Any

from tee.kernel.errors import TeeError
from tee.kernel.registry import VirtualTool

_MIME = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".svg": "image/svg+xml"}
_STYLES = {
    "light": {
        "bg": "#f5f2ec",
        "panel": "#ffffff",
        "ink": "#1c1a17",
        "accent": "#b45309",
        "line": "#d6cfc2",
    },
    "dark": {
        "bg": "#14161a",
        "panel": "#1e2228",
        "ink": "#e8e4da",
        "accent": "#e8a33d",
        "line": "#333a44",
    },
}
PAGE_W, PAGE_H_MIN = 1600, 900
MARGIN, GUTTER, HEADER_H, FOOTER_H = 48, 24, 110, 44
MAX_PANELS = 8
MAX_EMBED_BYTES = 8_000_000


def _esc(text: Any) -> str:
    return html.escape(str(text), quote=True)


def _embed(path: Path) -> str:
    mime = _MIME.get(path.suffix.lower())
    if mime is None:
        raise TeeError(
            "board_bad_panel",
            f"'{path.name}' is not an embeddable image.",
            fix=f"Panels embed {', '.join(sorted(_MIME))} files.",
        )
    if not path.is_file():
        raise TeeError("board_bad_panel", f"No file at {path}.", fix="Render/export it first.")
    data = path.read_bytes()
    if len(data) > MAX_EMBED_BYTES:
        raise TeeError(
            "board_bad_panel",
            f"'{path.name}' is {len(data):,} bytes (cap {MAX_EMBED_BYTES:,}).",
            fix="Render a smaller resolution for the board panel.",
        )
    return f"data:{mime};base64,{base64.b64encode(data).decode()}"


def compose(
    title: str,
    panels: list[dict[str, Any]],
    out_path: Path,
    *,
    subtitle: str = "",
    style: str = "light",
) -> dict[str, Any]:
    if not title.strip():
        raise TeeError("board_bad_args", "A board needs a title.", fix="Give title.")
    if not panels:
        raise TeeError(
            "board_bad_args",
            "A board needs panels.",
            fix='Give panels: [{"image": path, "caption": ...} | '
            '{"table": {"cols": [...], "rows": [...]}, "caption": ...} | '
            '{"lines": [...], "caption": ...}].',
        )
    if len(panels) > MAX_PANELS:
        raise TeeError(
            "board_bad_args",
            f"{len(panels)} panels (cap {MAX_PANELS}).",
            fix="Split into more boards.",
        )
    colors = _STYLES.get(style)
    if colors is None:
        raise TeeError("board_bad_args", f"Unknown style '{style}'.", fix="Styles: light, dark.")

    columns = 1 if len(panels) == 1 else 2
    rows = (len(panels) + columns - 1) // columns
    panel_w = (PAGE_W - 2 * MARGIN - (columns - 1) * GUTTER) // columns
    panel_h = 380 if rows > 1 else 620
    page_h = max(PAGE_H_MIN, HEADER_H + MARGIN + rows * (panel_h + GUTTER) + FOOTER_H)

    parts: list[str] = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{PAGE_W}" '
        f'height="{page_h}" viewBox="0 0 {PAGE_W} {page_h}" '
        f'font-family="Helvetica, Arial, sans-serif">',
        f'<rect width="{PAGE_W}" height="{page_h}" fill="{colors["bg"]}"/>',
        f'<rect x="0" y="0" width="{PAGE_W}" height="6" fill="{colors["accent"]}"/>',
        f'<text x="{MARGIN}" y="{MARGIN + 22}" font-size="34" font-weight="bold" '
        f'fill="{colors["ink"]}">{_esc(title)}</text>',
    ]
    if subtitle:
        parts.append(
            f'<text x="{MARGIN}" y="{MARGIN + 52}" font-size="17" '
            f'fill="{colors["ink"]}" opacity="0.75">{_esc(subtitle)}</text>'
        )
    parts.append(
        f'<line x1="{MARGIN}" y1="{HEADER_H - 8}" x2="{PAGE_W - MARGIN}" '
        f'y2="{HEADER_H - 8}" stroke="{colors["line"]}" stroke-width="1.5"/>'
    )

    for index, panel in enumerate(panels):
        col, row = index % columns, index // columns
        x = MARGIN + col * (panel_w + GUTTER)
        y = HEADER_H + MARGIN // 2 + row * (panel_h + GUTTER)
        caption = str(panel.get("caption") or "")
        parts.append(
            f'<rect x="{x}" y="{y}" width="{panel_w}" height="{panel_h}" rx="8" '
            f'fill="{colors["panel"]}" stroke="{colors["line"]}"/>'
        )
        body_y, body_h = y + 10, panel_h - 52
        if panel.get("image"):
            href = _embed(Path(str(panel["image"])))
            parts.append(
                f'<image x="{x + 10}" y="{body_y}" width="{panel_w - 20}" '
                f'height="{body_h}" href="{href}" '
                f'preserveAspectRatio="xMidYMid meet"/>'
            )
        elif panel.get("table"):
            table = panel["table"]
            cols = [str(c) for c in table.get("cols") or []]
            data_rows = [list(r) for r in (table.get("rows") or [])][:14]
            col_w = (panel_w - 40) / max(1, len(cols))
            ty = body_y + 24
            for ci, name in enumerate(cols):
                parts.append(
                    f'<text x="{x + 24 + ci * col_w:.0f}" y="{ty}" font-size="14" '
                    f'font-weight="bold" fill="{colors["accent"]}">{_esc(name)}</text>'
                )
            for ri, data_row in enumerate(data_rows):
                ry = ty + 24 + ri * 22
                if ry > y + body_h:
                    break
                for ci, value in enumerate(data_row[: len(cols)]):
                    parts.append(
                        f'<text x="{x + 24 + ci * col_w:.0f}" y="{ry}" '
                        f'font-size="13" fill="{colors["ink"]}">{_esc(value)}</text>'
                    )
        elif panel.get("lines"):
            for li, line in enumerate([str(v) for v in panel["lines"]][:14]):
                ly = body_y + 26 + li * 24
                if ly > y + body_h:
                    break
                parts.append(
                    f'<text x="{x + 24}" y="{ly}" font-size="15" '
                    f'fill="{colors["ink"]}">{_esc(line)}</text>'
                )
        else:
            raise TeeError(
                "board_bad_panel",
                f"Panel {index} has no image, table, or lines.",
                fix="Each panel needs one content key.",
            )
        if caption:
            parts.append(
                f'<text x="{x + 16}" y="{y + panel_h - 16}" font-size="15" '
                f'font-weight="bold" fill="{colors["ink"]}" opacity="0.85">'
                f"{_esc(caption)}</text>"
            )

    stamp = time.strftime("%Y-%m-%d %H:%M")
    parts.append(
        f'<text x="{MARGIN}" y="{page_h - 16}" font-size="12" '
        f'fill="{colors["ink"]}" opacity="0.55">TEE board · {_esc(stamp)} · '
        "panels are live artifacts (renders, sheets, model facts) - deck "
        "polish is host-side by design</text>"
    )
    parts.append("</svg>")

    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("".join(parts), encoding="utf-8")
    return {
        "ok": True,
        "path": str(out_path),
        "bytes": out_path.stat().st_size,
        "panels": len(panels),
    }


def register_board_tools(app) -> None:
    def board_compose(args: dict[str, Any]) -> dict[str, Any]:
        return compose(
            str(args.get("title") or ""),
            list(args.get("panels") or []),
            Path(str(args.get("out") or (app.project_root / ".tee" / "boards" / "board.svg"))),
            subtitle=str(args.get("subtitle") or ""),
            style=str(args.get("style") or "light"),
        )

    app.registry.register(
        VirtualTool(
            "board_compose",
            "Compose ONE styled technical board (SVG page: title block, "
            "panel grid, captions, footer stamp) from live artifacts - "
            "renders/sheets as image panels (png/jpg/svg embedded), tables "
            "(cut lists, findings), fact lines. The response is a compact "
            "file pointer. Boards feed presentations; deck polish stays "
            "host-side by design.",
            {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "subtitle": {"type": "string"},
                    "panels": {"type": "array", "items": {"type": "object"}},
                    "out": {"type": "string"},
                    "style": {"type": "string"},
                },
                "required": ["title", "panels"],
            },
            board_compose,
            tags=["board", "present", "compose", "sheet", "render", "page", "svg"],
        )
    )
