"""Blueprint graph authoring with a verification pass Epic does not provide.

The gap this closes, found by execution on UE 5.8.1 (2026-08-22):

`write_graph_dsl` **silently drops statements it cannot resolve**. Writing

    (fn Broken ()
      (return (NoSuch|Node|Here :A 1)))

returns success; reading the graph back yields `(fn Broken ())` - the body is
gone - and `compile_blueprint(warnings_as_errors=True)` reports the Blueprint
**clean**. A hallucinated node type therefore produces an empty function that
looks like a successful authoring round-trip from every signal Epic exposes.

That is the exact failure this project exists to remove (CLAUDE.md: drifting
APIs and hallucinated calls are the #1 friction point). So TEE writes the
graph, reads it back, and compares structure: fewer statements out than in
means the engine dropped something, and the caller is told which forms went
missing instead of being congratulated.

The comparison is structural, not textual, because the engine normalizes as
it writes: `(Utilities|Operators|Add :A A :B B)` reads back as `(+ A B)`.
"""

from __future__ import annotations

from typing import Any

Node = list[Any]  # a parsed s-expression: nested lists of str


class DslSyntaxError(ValueError):
    pass


def parse_sexpr(text: str) -> Node:
    """Parse the graph DSL into nested lists. Quoted strings stay single
    atoms so pin names with spaces do not split."""
    tokens: list[str] = []
    i, n = 0, len(text)
    while i < n:
        ch = text[i]
        if ch in "()":
            tokens.append(ch)
            i += 1
        elif ch == '"':
            j = i + 1
            while j < n and text[j] != '"':
                j += 2 if text[j] == "\\" else 1
            tokens.append(text[i : j + 1])
            i = j + 1
        elif ch.isspace():
            i += 1
        elif ch == ";":  # line comment
            while i < n and text[i] != "\n":
                i += 1
        else:
            j = i
            while j < n and not text[j].isspace() and text[j] not in '()";':
                j += 1
            # `(:"Pin Name" ...)` is ONE atom: the DSL uses the quoted form for
            # exec-pin names containing spaces, and splitting it loses the pin.
            if j < n and text[j] == '"':
                k = j + 1
                while k < n and text[k] != '"':
                    k += 2 if text[k] == "\\" else 1
                tokens.append(text[i : k + 1])
                i = k + 1
            else:
                tokens.append(text[i:j])
                i = j

    pos = 0

    def read() -> Any:
        nonlocal pos
        if pos >= len(tokens):
            raise DslSyntaxError("unexpected end of DSL - unbalanced '('")
        token = tokens[pos]
        pos += 1
        if token == "(":
            out: Node = []
            while pos < len(tokens) and tokens[pos] != ")":
                out.append(read())
            if pos >= len(tokens):
                raise DslSyntaxError("unbalanced '(' in DSL")
            pos += 1  # ')'
            return out
        if token == ")":
            raise DslSyntaxError("unexpected ')' in DSL")
        return token

    forms: Node = []
    while pos < len(tokens):
        forms.append(read())
    return forms


def statement_heads(node: Any) -> list[str]:
    """Head symbol of every nested list form, depth-first - the fingerprint
    used to tell what survived the write."""
    heads: list[str] = []
    if isinstance(node, list):
        if node and isinstance(node[0], str):
            heads.append(node[0])
        for child in node:
            heads.extend(statement_heads(child))
    return heads


def count_forms(node: Any) -> int:
    if not isinstance(node, list):
        return 0
    return 1 + sum(count_forms(child) for child in node)


def verify_written(requested: str, readback: str) -> dict[str, Any]:
    """Compare what was asked for against what the graph actually holds."""
    want = parse_sexpr(requested)
    got = parse_sexpr(readback)
    want_forms, got_forms = count_forms(want), count_forms(got)
    want_heads, got_heads = statement_heads(want), statement_heads(got)

    remaining = list(got_heads)
    missing: list[str] = []
    for head in want_heads:
        if head in remaining:
            remaining.remove(head)
        else:
            missing.append(head)

    complete = got_forms >= want_forms
    report: dict[str, Any] = {
        "ok": complete,
        "forms_requested": want_forms,
        "forms_written": got_forms,
        "readback": readback.strip(),
    }
    if not complete:
        report["dropped_forms"] = want_forms - got_forms
        # Normalization renames some heads (Utilities|Operators|Add -> +), so
        # these are candidates, not a verdict - the count is the hard signal.
        report["likely_unresolved"] = [h for h in missing if "|" in h][:10] or missing[:10]
    return report
