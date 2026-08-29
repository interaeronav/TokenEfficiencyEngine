import os, re, yaml, collections
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
today="2026-08-25"
rows=[]; openq=[]
for dom in sorted(os.listdir(ROOT)):
    dp=os.path.join(ROOT,dom)
    if not os.path.isdir(dp) or dom.startswith("_"): continue
    for fn in sorted(os.listdir(dp)):
        if not fn.endswith(".md"): continue
        raw=open(os.path.join(dp,fn),encoding="utf-8",errors="replace").read()
        fm={}; body=raw
        if raw.startswith("---"):
            e=raw.find("\n---",3)
            if e!=-1:
                try: fm=yaml.safe_load(raw[3:e]) or {}
                except Exception: fm={}
                body=raw[e+4:]
        st=fm.get("status",""); cf=fm.get("confidence","")
        rel=f"{dom}/{fn}"
        if st=="needs-verification" or cf in ("low","medium"):
            rows.append((rel, fm.get("title",fn), st, cf))
        m=re.search(r"^##\s+Open questions\s*\n(.+?)(?=\n##\s|\Z)", body, re.S|re.M)
        if m:
            txt=m.group(1).strip()
            if txt: openq.append((rel, fm.get("title",fn), txt))
counts=collections.Counter(r[0].split("/")[0] for r in rows)
with open(os.path.join(ROOT,"00_meta","VERIFICATION.md"),"w",encoding="utf-8") as f:
    f.write("---\n"+yaml.safe_dump({"id":"meta.verification","title":"Verification register",
      "domain":"00_meta","tags":["verification","confidence","gaps","provenance"],
      "jurisdiction":"global","status":"stable","confidence":"high","updated":today,"sources":[]},
      sort_keys=False,allow_unicode=True)+"---\n\n")
    f.write("# Verification register\n\n")
    f.write("This repository was built by research agents working from public sources. Where a fact could not be confirmed against a primary source it was **flagged rather than invented** — that discipline is what makes the rest of the corpus trustworthy, but it means an agent using this knowledge base must read the flags.\n\n")
    f.write("## How to use this file\n\n")
    f.write("1. Before relying on any number, clause reference, price or specification for a decision with real consequences, check whether its file appears below.\n")
    f.write("2. Treat `confidence: low` and `status: needs-verification` as **do not act on this without checking**.\n")
    f.write("3. Treat `confidence: medium` as **usable for orientation, verify before commitment**.\n")
    f.write("4. Every file carries its own `## Open questions` section; those are reproduced in full in the second half of this document.\n\n")
    f.write("> ⚠️ Three categories recur across the whole corpus and should be assumed unverified everywhere: **prices and rates** (almost no Namibian or South African price list is publicly retrievable), **paywalled standards text** (SANS clause values in particular), and **labour output rates** (trade convention, not published data).\n\n")
    f.write(f"## Files carrying a verification flag ({len(rows)})\n\n")
    f.write("| File | Title | Status | Confidence |\n|---|---|---|---|\n")
    for rel,t,st,cf in rows:
        f.write(f"| [`{rel}`](../{rel}) | {str(t)[:70]} | {st or '—'} | {cf or '—'} |\n")
    f.write("\n## Flag count by domain\n\n| Domain | Flagged files |\n|---|---|\n")
    for d,c in sorted(counts.items()): f.write(f"| `{d}` | {c} |\n")
    f.write(f"\n---\n\n## Open questions, by file ({len(openq)} files)\n\n")
    for rel,t,txt in openq:
        f.write(f"### [`{rel}`](../{rel}) — {t}\n\n{txt}\n\n")
print("flagged files:",len(rows)," files with open questions:",len(openq))

