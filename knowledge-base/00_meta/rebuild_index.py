import os, re, json, yaml, hashlib, datetime, collections

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REQUIRED = ["id","title","domain","tags","jurisdiction","status","confidence","updated","sources"]

DOMAIN_TITLES = {
 "00_meta":"Repository meta, schema and navigation",
 "01_architecture":"Architecture — formation, design craft and professional practice",
 "02_building_construction":"Building construction — the competent builder's trade knowledge",
 "03_codes_standards":"Codes and standards — Namibian and South African building regulation",
 "04_masters_and_practice":"Masters and practice — award-winning architects and builders",
 "05_companies_and_industry":"Companies and industry — contractors and project delivery",
 "06_joinery_and_woodwork":"Joinery and woodwork — cabinetmaking, timber and fitted furniture",
 "07_materials_and_suppliers":"Materials and suppliers — material science and the regional supply chain",
 "08_glass_and_facades":"Glass and facades — glazing technology, standards and projects",
 "09_equipment_manufacturers":"Equipment manufacturers — plant, tools and the manual library",
 "10_media_awards_competitions":"Media, awards and competitions — the industry's editorial ecosystem",
 "11_logistics_remote_areas":"Logistics in remote areas — supply chain for isolated sites",
 "12_hr_construction":"HR in construction — labour law, people processes and templates",
 "13_software_unreal_engine":"Unreal Engine — archviz, automation and the Python API",
 "14_software_blender":"Blender — modelling, geometry nodes and bpy automation",
 "15_software_autodesk_fusion":"Autodesk Fusion — parametric CAD, CAM and the Fusion API",
 "16_walls_and_boundaries":"Walls and boundaries — design, history, craft and precedent",
 "17_paving_and_roads":"Paving and roads — pavement engineering, manufacture and laying",
 "18_namibia_context":"Namibia context — history, architecture, climate, geology and geography",
 "19_interior_design":"Interior design — the discipline, its people, process and literature",
 "20_furnishing_industry":"Furnishing industry — materials, manufacturers and sourcing",
 "21_machine_vision":"Machine vision — imaging, deep learning and construction applications",
 "22_psychology_and_education":"Psychology and education — training, assessment and the reading list",
 "23_cartography_and_mapping":"Cartography and mapping — geodesy, GIS, remote sensing and design",
 "24_hydrology_arid":"Hydrology in arid regions — theory, instrumentation and the Cuvelai case",
 "25_environmental_asset_creation":"Environmental asset creation — photoreal 3D across Unreal, Blender and Fusion",
 "26_computer_engineering":"Computer engineering — curriculum, machine code and programming languages",
 "27_semiconductors_and_chip_design":"Semiconductors and chip design — from physics to 2 nm manufacturing",
 "28_graphic_and_game_design":"Graphic and game design — education, craft and the studio landscape",
 "29_aerospace_engineering":"Aerospace engineering — curriculum, design, materials and manufacturing",
 "30_space_science_and_propulsion":"Space science and propulsion — astrodynamics, engines and missions",
 "31_aviation_industry":"Aviation industry — law, economics, operations, training and simulation",
 "32_aviation_weather":"Aviation weather — meteorology for professional flight operations",
 "33_social_engineering_defence":"Social engineering defence — recognising and resisting human-vector attack",
 "34_medical_field":"Medical field — training, evidence and how medicines are made",
 "35_health_and_fitness":"Health and fitness — evidence-based training, nutrition and recovery",
 "36_finance_careers":"Finance careers — the quiet operators and what they studied",
 "37_alibaba_and_qwen":"Alibaba and Qwen — the company, the models and running them locally",
}

def parse(path):
    raw = open(path, encoding="utf-8", errors="replace").read()
    fm, body = {}, raw
    if raw.startswith("---"):
        end = raw.find("\n---", 3)
        if end != -1:
            try:
                fm = yaml.safe_load(raw[3:end]) or {}
            except Exception as e:
                fm = {"_parse_error": str(e)}
            body = raw[end+4:]
    return fm, body, raw

entries, problems = [], []
domain_counts = collections.Counter()
all_sources = []

for dom in sorted(os.listdir(ROOT)):
    dpath = os.path.join(ROOT, dom)
    if not os.path.isdir(dpath) or dom.startswith("_"):
        continue
    for fn in sorted(os.listdir(dpath)):
        if not fn.endswith(".md"):
            continue
        p = os.path.join(dpath, fn)
        fm, body, raw = parse(p)
        rel = f"{dom}/{fn}"
        missing = [k for k in REQUIRED if k not in fm]
        if missing:
            problems.append((rel, "missing frontmatter: " + ",".join(missing)))
        words = len(body.split())
        srcs = fm.get("sources") or []
        if isinstance(srcs, list):
            for s in srcs:
                if isinstance(s, dict) and s.get("url"):
                    all_sources.append((s.get("title") or "", s["url"], s.get("publisher") or "", rel))
        # summary = first paragraph after H1
        m = re.search(r"^#\s+.*?\n+(.+?)(?:\n\n|\n#)", body, re.S | re.M)
        summary = " ".join(m.group(1).split())[:400] if m else ""
        entries.append({
            "path": rel,
            "id": fm.get("id", ""),
            "title": fm.get("title", fn),
            "domain": dom,
            "tags": fm.get("tags", []),
            "jurisdiction": fm.get("jurisdiction", ""),
            "status": fm.get("status", ""),
            "confidence": fm.get("confidence", ""),
            "updated": str(fm.get("updated", "")),
            "words": words,
            "bytes": len(raw.encode()),
            "sha256": hashlib.sha256(raw.encode()).hexdigest()[:16],
            "source_count": len(srcs) if isinstance(srcs, list) else 0,
            "summary": summary,
        })
        domain_counts[dom] += 1

today = "2026-08-25"
manifest = {
    "name": "Expert Knowledge Base",
    "version": "1.0.0",
    "generated": today,
    "description": "A structured, machine-readable expert knowledge repository spanning architecture, construction, trades, materials, regional context for Namibia and South Africa, 3D and CAD software, and a set of adjacent technical and professional domains.",
    "schema": "00_meta/SCHEMA.md",
    "conventions": {
        "file_format": "Markdown with YAML frontmatter",
        "required_frontmatter": REQUIRED,
        "jurisdiction_markers": {"**[NA]**": "Namibia-specific", "**[ZA]**": "South Africa-specific"},
        "confidence": "high | medium | low — how strongly the content is source-backed",
        "status": "stable | draft | needs-verification",
    },
    "totals": {
        "domains": len(domain_counts),
        "files": len(entries),
        "words": sum(e["words"] for e in entries),
        "cited_sources": len(all_sources),
        "unique_source_urls": len({u for _, u, _, _ in all_sources}),
    },
    "domains": [
        {"slug": d, "title": DOMAIN_TITLES.get(d, d), "files": domain_counts[d],
         "words": sum(e["words"] for e in entries if e["domain"] == d)}
        for d in sorted(domain_counts)
    ],
    "files": entries,
}

with open(os.path.join(ROOT, "manifest.json"), "w", encoding="utf-8") as f:
    json.dump(manifest, f, indent=2, ensure_ascii=False)

# ---- source register ----
seen, rows = set(), []
for title, url, pub, rel in sorted(all_sources, key=lambda x: (x[2].lower(), x[1])):
    if url in seen:
        continue
    seen.add(url)
    rows.append((title, url, pub, rel))

with open(os.path.join(ROOT, "00_meta", "source-register.md"), "w", encoding="utf-8") as f:
    f.write("---\n")
    f.write(yaml.safe_dump({
        "id": "meta.source_register", "title": "Source register",
        "domain": "00_meta", "tags": ["sources", "citations", "provenance"],
        "jurisdiction": "global", "status": "stable", "confidence": "high",
        "updated": today, "sources": []}, sort_keys=False, allow_unicode=True))
    f.write("---\n\n# Source register\n\n")
    f.write(f"Every external source cited anywhere in this repository, deduplicated by URL. "
            f"{len(rows)} unique URLs drawn from {len(all_sources)} citations across {len(entries)} files. "
            f"Generated {today} from the frontmatter of every file.\n\n")
    f.write("| Publisher | Title | URL | First cited in |\n|---|---|---|---|\n")
    for title, url, pub, rel in rows:
        t = (title or "").replace("|", "\\|")[:110]
        p = (pub or "—").replace("|", "\\|")[:60]
        f.write(f"| {p} | {t} | <{url}> | `{rel}` |\n")

# ---- index ----
by_dom = collections.defaultdict(list)
for e in entries:
    by_dom[e["domain"]].append(e)

with open(os.path.join(ROOT, "INDEX.md"), "w", encoding="utf-8") as f:
    f.write("---\n")
    f.write(yaml.safe_dump({
        "id": "meta.index", "title": "Index",
        "domain": "00_meta", "tags": ["index", "navigation", "table-of-contents"],
        "jurisdiction": "global", "status": "stable", "confidence": "high",
        "updated": today, "sources": []}, sort_keys=False, allow_unicode=True))
    f.write("---\n\n# Index\n\n")
    f.write(f"Complete table of contents. **{manifest['totals']['domains']} domains, "
            f"{manifest['totals']['files']} files, ~{manifest['totals']['words']:,} words, "
            f"{manifest['totals']['unique_source_urls']:,} unique cited sources.** "
            f"Generated {today}.\n\n")
    f.write("## Domains at a glance\n\n| # | Domain | Files | Words |\n|---|---|---|---|\n")
    for d in sorted(by_dom):
        f.write(f"| {d.split('_')[0]} | [{DOMAIN_TITLES.get(d,d)}](./{d}/) | {len(by_dom[d])} | "
                f"{sum(e['words'] for e in by_dom[d]):,} |\n")
    f.write("\n---\n\n## Full file listing\n")
    for d in sorted(by_dom):
        f.write(f"\n### {d} — {DOMAIN_TITLES.get(d,d)}\n\n")
        for e in sorted(by_dom[d], key=lambda x: x["path"]):
            flag = ""
            if e["status"] == "needs-verification":
                flag = " ⚠️"
            elif e["confidence"] == "low":
                flag = " ⚠️"
            f.write(f"- [`{os.path.basename(e['path'])}`](./{e['path']}) — **{e['title']}**{flag}  \n")
            if e["summary"]:
                f.write(f"  {e['summary'][:260]}\n")
    f.write("\n---\n\n⚠️ marks a file whose status is `needs-verification` or whose confidence is `low`. "
            "See `00_meta/VERIFICATION.md` for the consolidated list of what still needs checking.\n")

print(json.dumps({"files": len(entries), "words": manifest["totals"]["words"],
                  "unique_sources": manifest["totals"]["unique_source_urls"],
                  "citations": len(all_sources), "problems": len(problems)}, indent=2))
for p in problems[:25]:
    print("  PROBLEM:", p[0], "-", p[1])

