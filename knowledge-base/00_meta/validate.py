#!/usr/bin/env python3
"""Validate every file against 00_meta/SCHEMA.md. Exit 1 if anything fails."""
import os, sys, yaml, datetime
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REQUIRED = ["id","title","domain","tags","jurisdiction","status","confidence","updated","sources"]
STATUS = {"stable","draft","needs-verification"}
CONF = {"high","medium","low"}
fails, ids, n = [], {}, 0
for dom in sorted(os.listdir(ROOT)):
    dp = os.path.join(ROOT, dom)
    if not os.path.isdir(dp) or dom.startswith(("_", ".")): continue
    for fn in sorted(os.listdir(dp)):
        if not fn.endswith(".md"): continue
        rel = f"{dom}/{fn}"; n += 1
        raw = open(os.path.join(dp, fn), encoding="utf-8", errors="replace").read()
        if not raw.startswith("---"):
            fails.append((rel, "no frontmatter")); continue
        end = raw.find("\n---", 3)
        if end == -1:
            fails.append((rel, "unterminated frontmatter")); continue
        try:
            fm = yaml.safe_load(raw[3:end]) or {}
        except Exception as e:
            fails.append((rel, f"yaml error: {e}")); continue
        body = raw[end+4:]
        for k in REQUIRED:
            if k not in fm: fails.append((rel, f"missing key: {k}"))
        if fm.get("status") not in STATUS: fails.append((rel, f"bad status: {fm.get('status')}"))
        if fm.get("confidence") not in CONF: fails.append((rel, f"bad confidence: {fm.get('confidence')}"))
        if not isinstance(fm.get("tags"), list): fails.append((rel, "tags not a list"))
        i = fm.get("id")
        if i:
            if i in ids: fails.append((rel, f"duplicate id '{i}' (also {ids[i]})"))
            ids[i] = rel
        if "\n# " not in "\n" + body: fails.append((rel, "no H1"))
        if dom != "00_meta" and "## Sources" not in body: fails.append((rel, "no ## Sources section"))
for rel, msg in fails: print(f"FAIL {rel}: {msg}")
print(f"\n{n} files checked, {len(fails)} problems")
sys.exit(1 if fails else 0)

