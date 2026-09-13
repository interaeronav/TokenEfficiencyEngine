"""Fixed, generated solver decks. Names supplied by users never become code."""

from __future__ import annotations

import json
from pathlib import Path

from .model import fail

OPENSEES_WORKER = """import json
from pathlib import Path
import openseespy.opensees as ops
job=json.loads(Path("solver-input.json").read_text())
m=job["model"]
ni={n["id"]:i+1 for i,n in enumerate(m["nodes"])}
ma={r["id"]:r for r in m["materials"]}
se={r["id"]:r for r in m["sections"]}
ops.wipe()
ops.model("basic", "-ndm", 2, "-ndf", 3)
for n in m["nodes"]: ops.node(ni[n["id"]], *n["xy_mm"])
for s in m["supports"]: ops.fix(ni[s["node"]], *[int(v) for v in s["fixed"]])
ops.geomTransf("Linear",1)
for i,e in enumerate(m["elements"],1):
    a,s=ma[e["material"]],se[e["section"]]
    ops.element("ElasticTimoshenkoBeam",i,*[ni[n] for n in e["nodes"]],
        a["E_mpa"],a["E_mpa"]/(2*(1+a["nu"])),
        s["area_mm2"],s["iz_mm4"],s["shear_area_mm2"],1)
ops.timeSeries("Linear",1)
ops.pattern("Plain",1,1)
for i,n in enumerate(m["nodes"]): ops.load(ni[n["id"]], *job["loads"][i*3:i*3+3])
ops.constraints("Plain")
ops.numberer("RCM")
ops.system("BandGeneral")
ops.algorithm("Linear")
ops.integrator("LoadControl",1.0)
ops.analysis("Static")
code=ops.analyze(1)
if code != 0: raise RuntimeError("OpenSees convergence code "+str(code))
ops.reactions()
out={"engine_version":ops.version(),"convergence_code":code,
"displacements":{n:ops.nodeDisp(i) for n,i in ni.items()},
"reactions":{n:ops.nodeReaction(i) for n,i in ni.items()},
"element_forces":{e["id"]:ops.eleResponse(i,"localForce") for i,e in enumerate(m["elements"],1)}}
Path("solver-result.json").write_text(json.dumps(out,allow_nan=False))
ops.wipe()
"""


def write_opensees(root: Path, m: dict, loads: dict) -> list[str]:
    (root / "solver-input.json").write_text(
        json.dumps({"model": m, "loads": loads["f"].tolist()}, allow_nan=False)
    )
    (root / "analysis.py").write_text(OPENSEES_WORKER)
    return ["solver-input.json", "analysis.py"]


def write_oofem(root: Path, m: dict, loads: dict) -> list[str]:
    # OOFEM beam2d lives in XZ: [u,w,Ry] = [ux,uy,-rz].
    ni = {n["id"]: i + 1 for i, n in enumerate(m["nodes"])}
    mats = {r["id"]: r for r in m["materials"]}
    secs = {r["id"]: r for r in m["sections"]}
    ns, ne = len(ni), len(m["elements"])
    bc = []
    sets = []
    for s in m["supports"]:
        ds = [d for d, v in zip((1, 3, 5), s["fixed"], strict=True) if v]
        i = len(bc) + 1
        bc.append(
            f"BoundaryCondition {i} loadTimeFunction 1 dofs {len(ds)} {' '.join(map(str, ds))} values {len(ds)} {' '.join('0' for _ in ds)} set {i}"  # noqa: E501 - generated solver record
        )
        sets.append(f"Set {i} nodes 1 {ni[s['node']]}")
    for i, _n in enumerate(m["nodes"]):
        f = loads["f"][3 * i : 3 * i + 3]
        if not any(f):
            continue
        j = len(bc) + 1
        bc.append(
            f"NodalLoad {j} loadTimeFunction 1 dofs 3 1 3 5 Components 3 {f[0]:.17g} {f[1]:.17g} {-f[2]:.17g} set {j}"  # noqa: E501 - generated solver record
        )
        sets.append(f"Set {j} nodes 1 {i + 1}")
    lines = [
        "analysis.out",
        "TEE generated planar Timoshenko frame",
        "LinearStatic nsteps 1",
        "domain 2dBeam",
        "OutputManager tstep_all dofman_all element_all",
        f"ndofman {ns} nelem {ne} ncrosssect {ne} nmat {ne} nbc {len(bc)} nic 0 nltf 1 nset {len(sets)}",  # noqa: E501 - generated solver record
    ]
    for i, n in enumerate(m["nodes"], 1):
        x, y = n["xy_mm"]
        lines.append(f"node {i} coords 3 {x:.17g} 0 {y:.17g}")
    for i, e in enumerate(m["elements"], 1):
        lines.append(
            f"Beam2d {i} nodes 2 {ni[e['nodes'][0]]} {ni[e['nodes'][1]]} crossSect {i} mat {i}"
        )
    for i, e in enumerate(m["elements"], 1):
        s = secs[e["section"]]
        lines.append(
            f"SimpleCS {i} area {s['area_mm2']:.17g} Iy {s['iz_mm4']:.17g} beamShearCoeff {s['shear_area_mm2'] / s['area_mm2']:.17g}"  # noqa: E501 - generated solver record
        )
    for i, e in enumerate(m["elements"], 1):
        a = mats[e["material"]]
        # Zero density/thermal expansion: no automatic gravity/inertia/thermal
        # loading. Explicit uniform thermal strain is already in nodal equivalents.
        lines.append(f"IsoLE {i} d 0 E {a['E_mpa']:.17g} n {a['nu']:.17g} tAlpha 0")
    lines += [*bc, "ConstantFunction 1 f(t) 1", *sets]
    (root / "analysis.in").write_text("\n".join(lines) + "\n")
    return ["analysis.in"]


def write_aster(root: Path, m: dict, loads: dict, launcher: str) -> list[str]:
    # Only fixed local serial export jobs. Neither user code nor remote export fields.
    ni = {n["id"]: i + 1 for i, n in enumerate(m["nodes"])}
    mats = {r["id"]: r for r in m["materials"]}
    secs = {r["id"]: r for r in m["sections"]}
    for s in secs.values():
        missing = {"iy_mm4", "torsion_j_mm4", "shear_area_z_mm2"} - s.keys()
        if missing:
            fail(
                "Code_Aster 3D beam section needs explicit "
                + ", ".join(sorted(missing))
                + "; out-of-plane motion is restrained, properties are not invented."
            )
    mesh = ["TITRE", "TEE planar analysis", "FINSF", "COOR_3D"]
    for i, n in enumerate(m["nodes"], 1):
        mesh.append(f"N{i} {n['xy_mm'][0]:.17g} {n['xy_mm'][1]:.17g} 0")
    mesh += ["FINSF", "SEG2"]
    for i, e in enumerate(m["elements"], 1):
        mesh.append(f"M{i} N{ni[e['nodes'][0]]} N{ni[e['nodes'][1]]}")
    mesh += ["FINSF"]
    for i in range(1, len(ni) + 1):
        mesh += ["GROUP_NO", f"G{i}", f"N{i}", "FINSF"]
    for i in range(1, len(m["elements"]) + 1):
        mesh += ["GROUP_MA", f"E{i}", f"M{i}", "FINSF"]
    mesh += ["FIN"]
    (root / "analysis.mail").write_text("\n".join(mesh) + "\n")
    cmd = [
        "import json",
        "from code_aster.Commands import *",
        "DEBUT()",
        "mesh=LIRE_MAILLAGE(UNITE=20,FORMAT='ASTER')",
        "model=AFFE_MODELE(MAILLAGE=mesh,AFFE=_F(TOUT='OUI',PHENOMENE='MECANIQUE',MODELISATION='POU_D_T'))",
    ]
    for i, e in enumerate(m["elements"], 1):
        a = mats[e["material"]]
        cmd.append(f"mat{i}=DEFI_MATERIAU(ELAS=_F(E={a['E_mpa']!r},NU={a['nu']!r}))")
    cmd.append(
        "materials=AFFE_MATERIAU(MAILLAGE=mesh,AFFE=("
        + ",".join(f"_F(GROUP_MA='E{i}',MATER=mat{i})" for i in range(1, len(m["elements"]) + 1))
        + ",))"
    )
    sections = []
    orientation = []
    for i, e in enumerate(m["elements"], 1):
        s = secs[e["section"]]
        vals = (
            s["area_mm2"],
            s["iy_mm4"],
            s["iz_mm4"],
            s["torsion_j_mm4"],
            s["area_mm2"] / s["shear_area_mm2"],
            s["area_mm2"] / s["shear_area_z_mm2"],
        )
        sections.append(
            f"_F(GROUP_MA='E{i}',SECTION='GENERALE',CARA=('A','IY','IZ','JX','AY','AZ'),VALE={vals!r})"
        )
        a, b = (m["nodes"][ni[n] - 1]["xy_mm"] for n in e["nodes"])
        orientation.append(
            f"_F(GROUP_MA='E{i}',CARA='VECT_Y',VALE={(-(b[1] - a[1]), b[0] - a[0], 0)!r})"
        )
    cmd.append(
        "section=AFFE_CARA_ELEM(MODELE=model,POUTRE=("
        + ",".join(sections)
        + ",),ORIENTATION=("
        + ",".join(orientation)
        + ",))"
    )
    fix = ["_F(TOUT='OUI',DZ=0.,DRX=0.,DRY=0.)"]
    for s in m["supports"]:
        fixed = ",".join(
            k + "=0." for k, v in zip(("DX", "DY", "DRZ"), s["fixed"], strict=True) if v
        )
        fix.append(f"_F(GROUP_NO='G{ni[s['node']]}',{fixed})")
    nodal = []
    for i in range(len(ni)):
        f = loads["f"][3 * i : 3 * i + 3]
        nodal.append(
            f"_F(GROUP_NO='G{i + 1}',FX={float(f[0])!r},FY={float(f[1])!r},MZ={float(f[2])!r})"
        )
    cmd += [
        "bc=AFFE_CHAR_MECA(MODELE=model,DDL_IMPO=("
        + ",".join(fix)
        + ",),FORCE_NODALE=("
        + ",".join(nodal)
        + ",))",
        "result=MECA_STATIQUE(MODELE=model,CHAM_MATER=materials,CARA_ELEM=section,EXCIT=_F(CHARGE=bc))",
        "result=CALC_CHAMP(reuse=result,RESULTAT=result,FORCE='REAC_NODA',CONTRAINTE='SIEF_ELNO')",
    ]
    # Tables are native solver results, exported as JSON by fixed generated code.
    cmd += [
        (
            "out={'displacements':{},'reactions':{},'element_forces':{},'convergence_code':0,'engine_version':'see analysis.mess'}"  # noqa: E501 - generated solver record
        )
    ]
    for i, n in enumerate(m["nodes"], 1):
        for key, field, components in [
            ("displacements", "DEPL", ("DX", "DY", "DRZ")),
            ("reactions", "REAC_NODA", ("DX", "DY", "DRZ")),
        ]:
            cmd += [
                f"tab=POST_RELEVE_T(ACTION=_F(OPERATION='EXTRACTION',INTITULE='values',RESULTAT=result,NOM_CHAM={field!r},GROUP_NO='G{i}',NOM_CMP={components!r})).EXTR_TABLE().values()",
                f"out[{key!r}][{n['id']!r}]=[float(tab[c][0]) for c in {components!r}]",
            ]
    for i, e in enumerate(m["elements"], 1):
        cmd.append("vals=[]")
        for end, n in enumerate(e["nodes"]):
            cmd += [
                f"tab=POST_RELEVE_T(ACTION=_F(OPERATION='EXTRACTION',INTITULE='forces',RESULTAT=result,NOM_CHAM='SIEF_ELNO',GROUP_MA='E{i}',GROUP_NO='G{ni[n]}',NOM_CMP=('N','VY','MFZ'))).EXTR_TABLE().values()",
                f"vals.extend([{(-1 if end == 0 else 1)}*float(tab[c][0]) for c in ('N','VY','MFZ')])",  # noqa: E501 - generated solver record
            ]
        cmd.append(f"out['element_forces'][{e['id']!r}]=vals")
    cmd += ["with open('fort.80','w') as stream: json.dump(out,stream,allow_nan=False)", "FIN()"]
    (root / "analysis.comm").write_text("\n".join(cmd) + "\n")
    exp = [
        "P actions make_etude",
        "P mode interactif",
        "P time_limit 120",
        "P memory_limit 1024",
        "P ncpus 1",
        "P mpi_nbcpu 1",
    ]
    if launcher == "as_run":
        exp += ["P memjob 1048576", "P tpsjob 2"]
    for kind, name, dr, unit in [
        ("comm", "analysis.comm", "D", 1),
        ("mail", "analysis.mail", "D", 20),
        ("mess", "analysis.mess", "R", 6),
        ("libr", "solver-result.json", "R", 80),
    ]:
        path = str(root / name)
        if any(c.isspace() for c in path):
            fail(
                "Code_Aster export paths must not contain whitespace; choose a project "
                "path without spaces."
            )
        exp.append(f"F {kind} {path} {dr} {unit}")
    (root / "analysis.export").write_text("\n".join(exp) + "\n")
    return ["analysis.mail", "analysis.comm", "analysis.export"]
