#!/usr/bin/env bash
# 75-evidence: where JSBSim's licence is actually stated. Needs network.
# The three sources disagree in detail, which is the point of asking all three.
set -u
echo "=== the grant, from a source-file header (the operative text) ==="
curl -sL --max-time 25 https://raw.githubusercontent.com/JSBSim-Team/jsbsim/master/src/FGFDMExec.cpp \
  | sed -n '8,16p'

echo
echo "=== the SAME repo, the Python CLI that the wheel installs as \`jsbsim\` ==="
echo "    (packaged into the wheel as jsbsim/script.py -- read its grant, not COPYING)"
curl -sL --max-time 25 https://raw.githubusercontent.com/JSBSim-Team/jsbsim/master/python/JSBSim.py \
  | sed -n '9,14p'

echo
echo "=== and the C++ standalone binary, for contrast ==="
curl -sL --max-time 25 https://raw.githubusercontent.com/JSBSim-Team/jsbsim/master/src/JSBSim.cpp \
  | sed -n '/free software/,/later version/p' | head -5

echo
echo "=== the licence file the repo ships ==="
for f in COPYING LICENSE.txt LICENSE; do
  code=$(curl -sL --max-time 20 -o /tmp/jsb.$$ -w '%{http_code}' \
    "https://raw.githubusercontent.com/JSBSim-Team/jsbsim/master/$f")
  printf '%-12s HTTP %s  %s\n' "$f" "$code" \
    "$( [ "$code" = 200 ] && sed -n '2,3p' /tmp/jsb.$$ | tr -s ' \n' ' ' || echo '-' )"
  rm -f /tmp/jsb.$$
done

echo
echo "=== what PyPI declares, and the wheel matrix ==="
curl -s --max-time 25 https://pypi.org/pypi/jsbsim/json | python3 -c '
import json,sys,re,collections
d=json.load(sys.stdin); i=d["info"]
print("version           ", i["version"])
print("license field     ", repr(i.get("license")))
print("license_expression", repr(i.get("license_expression")))
print("requires_python   ", i.get("requires_python"), "|", i.get("requires_dist"))
for c in i["classifiers"]:
    if "License" in c: print("classifier        ", c)
tags=collections.Counter()
for f in d["urls"]:
    m=re.search(r"-(cp\d+|pp\d+|py3)[^-]*-[^-]*-(.+)\.whl$", f["filename"])
    if m: tags[m.group(2)]+=1
    elif f["filename"].endswith(".tar.gz"): tags["sdist"]+=1
print("wheel platforms   ")
for t,n in sorted(tags.items()): print(f"   {t:<52} x{n}")
'
