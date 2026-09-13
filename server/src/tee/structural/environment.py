"""Sourced exposure investigation catalogue. No inferred degradation factors or lifespan."""

from __future__ import annotations

from .model import fail, keys, source
from .service import page

FHWA = "https://www.fhwa.dot.gov/bridge/preservation/docs/hif22052.pdf"
ACI = "https://www.concrete.org/Portals/0/Files/PDF/Previews/305R-20_preview.pdf"
NIST = "https://www.nist.gov/publications/real-world-considerations-predicting-service-life-steel-reinforced-concrete-exposed"

MECHANISMS = [
    {
        "id": "hot_weather_curing",
        "subject": (
            "Fresh cementitious material: hydration, evaporation, plastic shrinkage and curing"
        ),
        "needed": [
            "mix proportions and binder chemistry",
            "measured concrete and air temperatures, humidity and wind at placement",
            "placement, curing and test-specimen records",
            "cracking and strength/transport measurements",
        ],
        "source": ACI,
    },
    {
        "id": "chloride_corrosion",
        "subject": "Chloride ingress and corrosion of reinforcement",
        "needed": [
            "depth-resolved chloride profiles with mass basis",
            "cover-depth survey and cracking",
            "wetting/drying and marine or saline-water exposure",
            "resistivity, corrosion measurements and reinforcement section loss",
            "calibrated transport parameters and corrosion threshold uncertainty",
        ],
        "source": NIST,
    },
    {
        "id": "sulfate_attack",
        "subject": "External sulfate reaction and cement-paste damage",
        "needed": [
            "soil and groundwater sulfate chemistry, pH and exposure history",
            "binder composition and mix records",
            "petrography and expansion/damage measurements",
            "transport and reaction calibration; chloride diffusion is not sulfate diffusion",
        ],
        "source": "https://www.fhwa.dot.gov/publications/research/infrastructure/structures/ltbp/16007/051.cfm",
    },
    {
        "id": "carbonation",
        "subject": "Carbonation and reinforcement depassivation",
        "needed": [
            "carbonation-depth survey and cover variability",
            "humidity, wetting, CO2 exposure and curing history",
            "crack survey and steel condition",
            "binder-specific calibration; no generic years-to-failure coefficient",
        ],
        "source": FHWA,
    },
    {
        "id": "thermal_movement",
        "subject": "Temperature gradients, restraint and thermal cycles",
        "needed": [
            "member temperature history and through-section gradients",
            "material expansion and temperature-dependent stiffness",
            "restraints, joints, interfaces and fatigue/creep evidence",
        ],
        "available": (
            "st_solve supports explicit uniform temperature increments in linear "
            "frames; not gradients or damage accumulation"
        ),
        "source": "https://www.calculix.de/",
    },
    {
        "id": "abrasion_cover_loss",
        "subject": "Surface abrasion and erosion reduce protective cover",
        "needed": [
            "particle-size, shape, concentration, velocity and angle distributions",
            "surface hardness and controlled erosion tests",
            "measured surface and cover loss",
            (
                "calibrated material erosion law; CFD particle tracks alone do not "
                "predict concrete life"
            ),
        ],
        "source": "https://api.openfoam.com/2412/classFoam_1_1ParticleErosion.html",
    },
    {
        "id": "salt_wetting",
        "subject": "Saline groundwater, evaporation and wetting/drying chemistry",
        "needed": [
            "groundwater level and seasonal chemistry",
            "moisture and evaporation boundary conditions",
            "mineral phases and thermodynamic database provenance",
            "observed salt accumulation and damage; equilibrium is not a cracking law",
        ],
        "source": "https://water.usgs.gov/water-resources/software/PHREEQC/documentation/phreeqc3-html/phreeqc3-2.htm",
    },
    {
        "id": "sand_foundations",
        "subject": "Foundation settlement and soil-structure response",
        "needed": [
            "site investigation with soil strata, density and groundwater",
            "CPT/SPT and appropriate laboratory calibration",
            "foundation loads and geometry",
            "wetting-collapse and cyclic response where the site evidence warrants them",
        ],
        "source": "https://www.opengeosys.org/stable/",
    },
    {
        "id": "alkali_aggregate",
        "subject": "Aggregate reactivity and internal expansion",
        "needed": [
            "aggregate petrography and applicable reactivity tests",
            "binder alkali content and mitigation mix evidence",
            "moisture exposure, temperature and field expansion/cracking",
            "calibrated expansion and mechanical-damage model",
        ],
        "source": "https://www.fhwa.dot.gov/publications/research/infrastructure/pavements/pccp/01163/app.cfm",
    },
    {
        "id": "sealant_coating_weathering",
        "subject": "Sealants, roofing polymers and coatings: UV, heat, moisture and movement",
        "needed": [
            "product-specific weathering and adhesion tests",
            "UV, temperature, humidity and joint-movement histories",
            "observed cracking, debonding and coating defects",
            "validated acceleration model; chamber hours are not automatically years outdoors",
        ],
        "source": "https://www.nist.gov/publications/systematic-approach-study-accelerated-weathering-building-joint-sealants",
    },
    {
        "id": "glazing_thermal_stress",
        "subject": "Glazing thermal gradients, shading and edge/support condition",
        "needed": [
            "actual glass makeup and heat treatment",
            "absorptance, shading and temperature distribution",
            "edge condition, framing and manufacturer analysis",
        ],
        "source": "https://glassed.vitroglazings.com/managing-thermal-stress-breakage",
    },
]

SOFTWARE = [
    {
        "id": "oofem",
        "role": "Structural mechanics and concrete constitutive research",
        "licence": "v3.0 LGPL-2.1-or-later; pinned source headers checked",
        "tee_status": "planar elastic frame backend; concrete damage laws not yet exposed",
        "source": "https://github.com/oofem/oofem/tree/v3.0",
    },
    {
        "id": "openseespy",
        "role": (
            "Structural and soil constitutive models; PM4Sand is a calibrated "
            "plane-strain sand model"
        ),
        "licence": "UC terms restrict commercial redistribution; internal owner installation",
        "tee_status": "planar elastic frame backend; soil material models not yet exposed",
        "source": "https://opensees.github.io/OpenSeesDocumentation/user/manual/material/ndMaterials/PM4Sand.html",
    },
    {
        "id": "code_aster",
        "role": "Structural and thermomechanical finite elements",
        "licence": "GPLv3 source; separately installed executable",
        "tee_status": (
            "as_run/run_aster generated-deck adapter; native solver not available on this Mac"
        ),
        "source": "https://codeaster.gitlab.io/doc/docaster/manuals/man_u/u1/u1.04.00/utilisation_variants_run.html",
    },
    {
        "id": "calculix",
        "role": "Alternative headless structural, thermal and nonlinear solver",
        "licence": "GPL-2.0-or-later upstream",
        "tee_status": "researched alternative; not an A84 backend",
        "source": "https://www.calculix.de/",
    },
    {
        "id": "xc",
        "role": (
            "Civil structural analysis and design-code implementations, each needing verification"
        ),
        "licence": "GPL-3.0 repository",
        "tee_status": "researched alternative; not installed/integrated",
        "source": "https://github.com/xcfem/xc",
    },
    {
        "id": "opengeosys",
        "role": "Coupled heat, water, mechanics and chemistry in porous ground",
        "licence": "inspect pinned release and dependencies before integration",
        "tee_status": "researched candidate; no geotechnical analysis integrated",
        "source": "https://www.opengeosys.org/stable/",
    },
    {
        "id": "phreeqc",
        "role": (
            "Solution/mineral reactions, temperature-dependent transport, salinity "
            "and cement chemistry research with suitable database"
        ),
        "licence": (
            "USGS source available; audit selected distribution and databases before integration"
        ),
        "tee_status": "researched candidate; not a structural damage or service-life model",
        "source": "https://www.usgs.gov/software/phreeqc-version-3",
    },
    {
        "id": "vcctl",
        "role": "Cement hydration/curing and evolving thermal, mechanical and transport properties",
        "licence": "NIST public-domain statement; dependency/package review still required",
        "tee_status": (
            "legacy research candidate; published installer Windows/JDK7-8, not a "
            "verified native Mac route"
        ),
        "source": "https://www.nist.gov/services-resources/software/vcctl-software",
    },
    {
        "id": "energyplus",
        "role": (
            "Whole-building heat balance and energy simulation using site weather "
            "and envelope inputs"
        ),
        "licence": "BSD-3-like upstream, version-specific third-party inventory",
        "tee_status": (
            "researched for future dynamic analysis; current A83 thermal tool is "
            "steady-state selected surfaces only"
        ),
        "source": "https://github.com/NatLabRockies/EnergyPlus",
    },
    {
        "id": "honeybee",
        "role": "Headless EnergyPlus/Radiance workflows for energy, solar and daylight",
        "licence": "honeybee-energy AGPL-3.0; not an MIT dependency",
        "tee_status": "researched optional separate environment; not installed",
        "source": "https://github.com/ladybug-tools/honeybee-energy",
    },
    {
        "id": "openfoam",
        "role": "Airflow and particle erosion investigations with calibrated material parameters",
        "licence": "GPL external executable",
        "tee_status": "existing TEE wind-tunnel lane; desert erosion workflow not yet validated",
        "source": "https://api.openfoam.com/2412/classFoam_1_1ParticleErosion.html",
    },
]


def assess(
    collection: str = "mechanisms", exposures: list | None = None, offset: int = 0, limit: int = 5
) -> dict:
    if collection not in ("mechanisms", "software"):
        fail("Choose mechanisms or software.")
    observations = {}
    if exposures is not None:
        if not isinstance(exposures, list) or len(exposures) > len(MECHANISMS):
            fail("Use at most one observation per mechanism.")
        for e in exposures:
            keys(e, "mechanism status source")
            source(e)
            if (
                e["mechanism"] not in {r["id"] for r in MECHANISMS}
                or e["mechanism"] in observations
            ):
                fail("Use distinct named mechanisms.")
            if e["status"] not in ("present", "absent", "unknown"):
                fail("Exposure status must be present, absent or unknown.")
            observations[e["mechanism"]] = e
    data = []
    for r in MECHANISMS if collection == "mechanisms" else SOFTWARE:
        row = dict(r)
        if collection == "mechanisms":
            row["reported_exposure"] = observations.get(
                r["id"], {"status": "unknown", "source": None}
            )
            row["damage_status"] = "not_assessed"
        data.append(row)
    return {
        "collection": collection,
        **page(data, offset, limit),
        "assessment": "investigation guidance, not engineering acceptance",
        "service_life_years": None,
        "strength_reduction_factor": None,
        "regional_design_code": "not_selected",
        "note": (
            "Desert location alone does not establish salt exposure, soil strength "
            "or damage. Retain site, material, test and inspection provenance."
        ),
    }
