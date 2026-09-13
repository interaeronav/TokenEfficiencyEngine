"""Independent Timoshenko stiffness/equilibrium critic; never a substitute engine result."""

from __future__ import annotations

import math

from .model import fail


def system(m: dict) -> dict:
    import numpy as np

    ni = {n["id"]: i for i, n in enumerate(m["nodes"])}
    mats = {r["id"]: r for r in m["materials"]}
    secs = {r["id"]: r for r in m["sections"]}
    k = np.zeros((3 * len(ni), 3 * len(ni)))
    elems = {}
    for e in m["elements"]:
        a, b = (ni[n] for n in e["nodes"])
        xy1, xy2 = (m["nodes"][n]["xy_mm"] for n in (a, b))
        length = math.dist(xy1, xy2)
        c, s = (v / length for v in (xy2[0] - xy1[0], xy2[1] - xy1[1]))
        mat, sec = mats[e["material"]], secs[e["section"]]
        ea, ei = mat["E_mpa"] * sec["area_mm2"], mat["E_mpa"] * sec["iz_mm4"]
        ga = mat["E_mpa"] / (2 * (1 + mat["nu"])) * sec["shear_area_mm2"]
        phi = 12 * ei / (ga * length**2)
        aa, bb, cc = (
            ea / length,
            12 * ei / ((1 + phi) * length**3),
            6 * ei / ((1 + phi) * length**2),
        )
        dd, ee = (4 + phi) * ei / ((1 + phi) * length), (2 - phi) * ei / ((1 + phi) * length)
        kl = np.array(
            [
                [aa, 0, 0, -aa, 0, 0],
                [0, bb, cc, 0, -bb, cc],
                [0, cc, dd, 0, -cc, ee],
                [-aa, 0, 0, aa, 0, 0],
                [0, -bb, -cc, 0, bb, -cc],
                [0, cc, ee, 0, -cc, dd],
            ]
        )
        t = np.zeros((6, 6))
        for i in (0, 3):
            t[i : i + 3, i : i + 3] = [[c, s, 0], [-s, c, 0], [0, 0, 1]]
        dofs = [3 * a, 3 * a + 1, 3 * a + 2, 3 * b, 3 * b + 1, 3 * b + 2]
        k[np.ix_(dofs, dofs)] += t.T @ kl @ t
        elems[e["id"]] = {
            "k": kl,
            "t": t,
            "dofs": dofs,
            "L": length,
            "EA": ea,
            "alpha": mat.get("alpha_per_c"),
        }
    fixed = [3 * ni[s["node"]] + j for s in m["supports"] for j, f in enumerate(s["fixed"]) if f]
    free = [i for i in range(len(k)) if i not in fixed]
    if free:
        kf = k[np.ix_(free, free)]
        diag = np.diag(kf)
        if np.any(diag <= 0):
            fail("Unstable frame: a free degree of freedom has zero stiffness.")
        scaled = kf / np.sqrt(diag[:, None] * diag[None, :])
        ev = np.linalg.eigvalsh(scaled)
        if ev[0] <= ev[-1] * 1e-12:
            fail(
                "Unstable or excessively ill-conditioned frame; review connectivity, "
                "restraints and stiffness contrast."
            )
        condition = float(ev[-1] / ev[0])
    else:
        condition = 1.0
    return {
        "nodes": ni,
        "k": k,
        "fixed": fixed,
        "free": free,
        "elements": elems,
        "scaled_condition": condition,
    }


def loading(m: dict, sys: dict, case_id: str) -> dict:
    import numpy as np

    cases = {c["id"]: c for c in m["cases"]}
    combos = {c["id"]: c for c in m["combinations"]}
    factors = {case_id: 1.0} if case_id in cases else combos.get(case_id, {}).get("factors")
    if factors is None:
        fail("Select an existing case or combination ID.")
    f = np.zeros(len(sys["k"]))
    f0 = {e: np.zeros(6) for e in sys["elements"]}
    for cid, factor in factors.items():
        c = cases[cid]
        for load in c["nodal"]:
            i = 3 * sys["nodes"][load["node"]]
            f[i : i + 3] += factor * np.array([load["fx_n"], load["fy_n"], load["mz_nmm"]])
        for load in c.get("uniform", []):
            length = sys["elements"][load["element"]]["L"]
            qx, qy = factor * load["qx_n_mm"], factor * load["qy_n_mm"]
            f0[load["element"]] += [
                qx * length / 2,
                qy * length / 2,
                qy * length**2 / 12,
                qx * length / 2,
                qy * length / 2,
                -qy * length**2 / 12,
            ]
        for load in c.get("thermal", []):
            e = sys["elements"][load["element"]]
            p = factor * e["EA"] * e["alpha"] * load["delta_c"]
            f0[load["element"]] += [-p, 0, 0, p, 0, 0]
    for eid, e in sys["elements"].items():
        f[e["dofs"]] += e["t"].T @ f0[eid]
    return {"f": f, "fixed_end_equivalent_local": f0, "factors": factors}


def check(m: dict, sys: dict, loads: dict, raw: dict, *, oofem_text: bool = False) -> dict:
    import numpy as np

    nodes = sys["nodes"]

    def vectors(field: str, ids: list, size: int) -> dict:
        data = raw.get(field)
        if not isinstance(data, dict) or set(data) != set(ids):
            fail(f"Solver {field} is incomplete or has unexpected entities.")
        for v in data.values():
            if (
                not isinstance(v, list)
                or len(v) != size
                or any(type(n) not in (int, float) or not math.isfinite(n) for n in v)
            ):
                fail(f"Solver {field} has invalid or nonfinite vectors.")
        return data

    disp = vectors("displacements", list(nodes), 3)
    reactions = vectors("reactions", list(nodes), 3)
    native_forces = vectors("element_forces", list(sys["elements"]), 6)
    u = np.array([n for i in nodes for n in disp[i]])
    r = np.array([n for i in nodes for n in reactions[i]])
    residual = sys["k"] @ u - loads["f"]
    # Scale force and moment DOFs individually by accumulated absolute stiffness
    # contributions, with absolute floors to make unloaded/zero checks meaningful.
    scale = np.maximum(1.0, np.abs(sys["k"]) @ np.abs(u) + np.abs(loads["f"]))
    # Native OOFEM prints nodal displacements with %.8e and forces with %.4e.
    # Propagate that measured decimal rounding through stiffness, especially
    # at nominally zero end moments. Never enlarge the mechanics tolerance.
    du = np.abs(u) * (5e-9 if oofem_text else 0.0)
    force_precision = 5e-5 if oofem_text else 0.0
    equation_rounding = np.abs(sys["k"]) @ du + force_precision * np.abs(r)
    equation_error = float(np.max(np.maximum(0, np.abs(residual - r) - equation_rounding) / scale))
    free_reaction = (
        float(np.max(np.abs(r[sys["free"]]) / scale[sys["free"]])) if sys["free"] else 0.0
    )
    fixed_error = max((abs(u[i]) for i in sys["fixed"]), default=0.0)
    forces = {}
    force_error = 0.0
    for eid, e in sys["elements"].items():
        expected = e["k"] @ e["t"] @ u[e["dofs"]]
        measured = np.array(native_forces[eid])
        rounding = np.abs(e["k"] @ e["t"]) @ du[e["dofs"]] + force_precision * np.abs(measured)
        error = np.maximum(0, np.abs(expected - measured) - rounding)
        force_error = max(force_error, float(np.max(error / np.maximum(1.0, np.abs(expected)))))
        forces[eid] = (measured - loads["fixed_end_equivalent_local"][eid]).tolist()
    total = loads["f"] + r
    origin = m["nodes"][0]["xy_mm"]
    fx = float(total[0::3].sum())
    fy = float(total[1::3].sum())
    moment = sum(
        float(total[3 * i + 2])
        + (n["xy_mm"][0] - origin[0]) * float(total[3 * i + 1])
        - (n["xy_mm"][1] - origin[1]) * float(total[3 * i])
        for i, n in enumerate(m["nodes"])
    )
    passed = max(equation_error, free_reaction, force_error) <= 2e-5 and fixed_error <= 1e-9
    if not passed:
        fail(
            f"Solver verification failed: residual={equation_error:.3g}, "
            f"free reaction={free_reaction:.3g}, member force={force_error:.3g}, "
            f"restrained displacement={fixed_error:.3g}."
        )
    return {
        "displacements": disp,
        "reactions": reactions,
        "element_forces": forces,
        "checks": {
            "passed": True,
            "native_text_rounding_propagated": oofem_text,
            "relative_equation_error": equation_error,
            "relative_member_force_error": force_error,
            "global_balance_n_n_nmm": [fx, fy, moment],
            "scaled_stiffness_condition": sys["scaled_condition"],
        },
        "internal_member_extrema": "not_evaluated",
        "max_nodal_translation_mm": max(math.hypot(*v[:2]) for v in disp.values()),
        "max_nodal_rotation_rad": max(abs(v[2]) for v in disp.values()),
    }
