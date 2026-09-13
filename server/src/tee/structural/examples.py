"""Synthetic controls, never project material or site loading defaults."""


def cantilever() -> dict:
    s = "Synthetic analytic verification only; not a design specification."
    return {
        "name": "Synthetic 3 m cantilever",
        "units": "N-mm-MPa-rad",
        "analysis": "linear_static_frame2d",
        "nodes": [{"id": "base", "xy_mm": [0, 0]}, {"id": "tip", "xy_mm": [3000, 0]}],
        "materials": [
            {"id": "test", "E_mpa": 200000.0, "nu": 0.3, "alpha_per_c": 12e-6, "source": s}
        ],
        "sections": [
            {
                "id": "test",
                "area_mm2": 6000.0,
                "iz_mm4": 200e6,
                "shear_area_mm2": 5000.0,
                "iy_mm4": 50e6,
                "torsion_j_mm4": 20e6,
                "shear_area_z_mm2": 4000.0,
                "source": s,
            }
        ],
        "elements": [
            {
                "id": "beam",
                "nodes": ["base", "tip"],
                "material": "test",
                "section": "test",
                "source": s,
            }
        ],
        "supports": [{"node": "base", "fixed": [True, True, True], "source": s}],
        "cases": [
            {
                "id": "vertical",
                "source": s,
                "nodal": [
                    {"node": "tip", "fx_n": 0.0, "fy_n": -10000.0, "mz_nmm": 0.0, "source": s}
                ],
            },
            {
                "id": "axial",
                "source": s,
                "nodal": [
                    {"node": "tip", "fx_n": 10000.0, "fy_n": 0.0, "mz_nmm": 0.0, "source": s}
                ],
            },
            {
                "id": "heat",
                "source": s,
                "nodal": [],
                "thermal": [{"element": "beam", "delta_c": 40.0, "source": s}],
            },
            {
                "id": "udl",
                "source": s,
                "nodal": [],
                "uniform": [{"element": "beam", "qx_n_mm": 0.0, "qy_n_mm": -3.0, "source": s}],
            },
        ],
        "combinations": [
            {"id": "combined", "factors": {"vertical": 1.2, "axial": 1.5, "heat": 1.0}, "source": s}
        ],
    }
