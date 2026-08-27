---
id: equipment.survey
title: Survey and measurement instruments — GNSS, total stations, levels and scanners
domain: 09_equipment_manufacturers
tags: [survey, total-station, gnss, rtk, automatic-level, rotating-laser, laser-scanner, photogrammetry, leica, trimble, topcon, sokkia, hexagon, disto, accuracy, calibration, two-peg-test]
jurisdiction: southern-africa
status: stable
confidence: medium
updated: 2026-08-25
sources:
  - {title: "Leica Geosystems — total stations", url: "https://leica-geosystems.com/products/total-stations", publisher: "Leica Geosystems (Hexagon)", accessed: 2026-08-25}
  - {title: "Leica Geosystems — GNSS systems", url: "https://leica-geosystems.com/products/gnss-systems", publisher: "Leica Geosystems", accessed: 2026-08-25}
  - {title: "Leica Geosystems — laser scanners", url: "https://leica-geosystems.com/products/laser-scanners", publisher: "Leica Geosystems", accessed: 2026-08-25}
  - {title: "Leica Geosystems — levels", url: "https://leica-geosystems.com/products/levels", publisher: "Leica Geosystems", accessed: 2026-08-25}
  - {title: "myWorld customer portal (Leica)", url: "https://myworld.leica-geosystems.com/", publisher: "Leica Geosystems", accessed: 2026-08-25}
  - {title: "Trimble Construction", url: "https://construction.trimble.com/", publisher: "Trimble Inc.", accessed: 2026-08-25}
  - {title: "Trimble Geospatial help portal", url: "https://help.trimblegeospatial.com/", publisher: "Trimble Inc.", accessed: 2026-08-25}
  - {title: "myTopcon NOW! support", url: "https://mytopcon.topconpositioning.com/support", publisher: "Topcon Positioning Systems", accessed: 2026-08-25}
  - {title: "Sokkia", url: "https://sokkia.com/", publisher: "Sokkia (Topcon Positioning Group)", accessed: 2026-08-25}
related: [equipment.overview, equipment.manual_library, equipment.earthmoving, equipment.power_tools]
unit_system: SI
---

# Survey and measurement instruments — GNSS, total stations, levels and scanners

**Summary.** Setting out is where a design becomes a building, and the instrument class must match the tolerance being controlled. This file maps the manufacturers, states the accuracy classes for each instrument type, gives the decision rule for when each is appropriate, and sets out the setup and calibration procedures — the two-peg test, collimation checks, GNSS base setup and scanner registration — that separate a reliable survey from a confidently wrong one.

## Key facts

| Instrument | Typical accuracy | Range | Appropriate for |
|---|---|---|---|
| **Laser distance meter** (DISTO) | ±1.0–1.5 mm | 0.05–200 m | Room dimensions, quantities, quick checks |
| **Builder's automatic level** | 2.0–2.5 mm double-run per km | 60–100 m | General site levels, drainage, slabs |
| **Precise automatic level** | 0.7–1.5 mm/km | 100 m | Structural levelling, settlement monitoring |
| **Digital level with bar-coded staff** | 0.3–0.9 mm/km | 100 m | Deformation monitoring, precise benchmarks |
| **Rotating laser (construction)** | ±1.0–1.5 mm at 30 m (≈ ±10 arcsec) | 300–600 m dia. with detector | Formwork, floors, falls, machine control reference |
| **Rotating laser (grade)** | dual-slope, ±0.005% | — | Drainage falls, car park grading |
| **Total station (construction, 5″)** | angle 5″; distance 2 mm + 2 ppm (prism) | 3 000–5 000 m prism; 500 m reflectorless | General setting out, as-builts |
| **Total station (survey, 1–2″)** | angle 1″; distance 1 mm + 1.5 ppm | 3 500 m+ | Control networks, precise structures, monitoring |
| **Robotic total station** | as above, plus one-person operation and auto-lock | — | Setting out at production rate |
| **GNSS RTK rover** | **8–10 mm + 1 ppm horizontal**, **15–20 mm + 1 ppm vertical** | 10–40 km from base; unlimited on network RTK | Topographic survey, earthworks stakeout, machine control |
| **GNSS static post-processed** | 3–5 mm + 0.5 ppm | — | Control point establishment |
| **Terrestrial laser scanner** | 1–3 mm range noise at 10 m; 2–6 mm 3D position | 0.4–350 m (typical), to 1 000 m+ | As-built capture, clash detection, heritage, volumes |
| **Handheld/SLAM scanner** | 10–30 mm | walk-through | Fast interior as-builts where mm accuracy is not needed |
| **UAV photogrammetry** | 20–50 mm with good GCPs; 10–30 mm with RTK/PPK | — | Volumes, progress, topo over large areas |

> ⚠️ **Vertical GNSS accuracy is roughly twice as poor as horizontal, always.** Never set floor levels or drainage invert levels from a GNSS rover without a check against a levelled benchmark. The geoid model is the usual culprit: GNSS measures ellipsoidal height, and the conversion to orthometric height depends on the geoid model loaded in the controller.

## The manufacturers

| Manufacturer | Position |
|---|---|
| **Leica Geosystems** (Hexagon AB) | The premium reference. TS/TM/MS total stations, GS GNSS, LS digital levels, RTC360/BLK/P-series scanners, iCON construction line, Captivate/iCON field software, and the **BLK** reality-capture family. Also owns the **DISTO** brand of hand lasers. |
| **Trimble** | The other giant. S/SX total stations and scanning total stations, R-series GNSS, X-series scanners, and the strongest ecosystem in **machine control** (Trimble Earthworks), construction software (Tekla, SketchUp, Trimble Connect, Business Center) and field data. |
| **Topcon Positioning Systems** | GT/GTL robotic total stations, HiPer GNSS, RL rotating lasers, and machine control. Strong price/performance; **myTopcon NOW!** self-service portal with manuals, firmware and e-learning. |
| **Sokkia** | Part of the Topcon Positioning Group. Value-positioned total stations (iM/FX), GNSS (GCX/GRX) and levels (B-series automatic levels are a workhorse). |
| **Hexagon AB** | Parent of Leica Geosystems; also owns Hexagon Manufacturing Intelligence, NovAtel (GNSS boards and correction services), and the GeoCloud/HxDR platforms. |
| **FARO** | Focus/Freestyle scanners; strong in AEC and forensic. |
| **Z+F (Zoller+Fröhlich)** | High-end phase-based scanners, best-in-class range noise. |
| **RIEGL** | Long-range and airborne LiDAR. |
| **NavVis**, **GeoSLAM/FARO**, **Emesent** | SLAM/mobile mapping. |
| **Bosch, Stabila, Hilti, Spectra Precision** | Construction-grade lasers, levels and detection tools. Spectra Precision (Trimble) supplies much of the rotating-laser market. |
| **South, Kolida, Ruide, Hi-Target, CHCNav, Stonex** | Chinese instruments increasingly common in SADC; capable hardware, weaker service and software ecosystems. |

## When each instrument is appropriate

**Use a laser distance meter** for anything where ±2 mm over a room is adequate — quantities, checks, fit-out. Not for setting out.

**Use an automatic level** for all vertical control on a normal building site: floor levels, formwork soffits, drainage invert levels, kerb levels, and the transfer of a benchmark. It is cheap, robust, has no batteries to fail and no software to be wrong. Every site should own one. The digital level with a bar-coded staff removes reading error and is worth the premium on any project with a monitoring requirement.

**Use a rotating laser** where a *plane* rather than a *point* is needed — screed levels, suspended ceiling grids, formwork soffits, large slab pours — and where a machine (grader, dozer, screed) is following a laser receiver. Dual-slope models set falls in two axes.

**Use a total station** for horizontal setting out: gridlines, column positions, wall lines, pile positions, and as-built verification. A **robotic** instrument lets one person set out at roughly double the rate of a two-person crew and is the right buy for a contractor doing continuous setting out. A 5″ instrument suffices for building work; 1–2″ is needed for long control traverses, precise steel, and monitoring.

**Use GNSS RTK** for open-sky work over area: topographic survey, earthworks stakeout, road centrelines, stockpile volumes, and machine control. It fails under canopy, next to tall buildings, and inside structures. **[NA] [ZA]** Both countries have CORS/network RTK infrastructure (South Africa's TrigNet, operated by the Chief Directorate: National Geospatial Information, and commercial networks); coverage in remote northern Namibia is patchy, so plan for a **local base station** with a known control point rather than relying on network corrections.

**Use a laser scanner** when the deliverable is geometry you cannot fully anticipate: as-built capture for refurbishment, clash detection against a model, complex facades, heritage recording, or accurate volume computation. The cost is in registration and processing, not in the field time.

**Use UAV photogrammetry** for periodic volumes and progress over large open sites, where 30–50 mm accuracy is sufficient and ground control can be laid. **[NA] [ZA]** Both require regulatory compliance for commercial UAV operation — an RPAS operating certificate and licensed pilot in South Africa (SACAA), and NCAA authorisation in Namibia. Do not assume a drone can simply be flown on a commercial site.

## Setup and calibration procedure

### Automatic level — setup
1. Set the tripod firm, legs pushed in, head roughly level; **on soft ground, tread the legs in and re-check**.
2. Level the circular bubble with the three footscrews.
3. Check the compensator: gently tap the instrument; the reading must return to the same value. If it does not, the compensator is stuck or damaged.
4. Read **backsight → intermediate sights → foresight**, keeping backsight and foresight distances **approximately equal** (this cancels collimation error and curvature/refraction).
5. Close the level run back onto the starting benchmark. **A level run that is not closed is not a level run.** Acceptable misclosure for general building work is often taken as **±12√K mm** (K in km); for precise work, ±5√K mm or tighter per specification.

### Automatic level — the two-peg test (collimation check)
Do this monthly, and always after transport or a knock.
1. Set two pegs, A and B, about **60 m apart** (or 2× the normal sight length).
2. Set the level **exactly midway** between them. Read A and B. The difference (a₁ − b₁) is the **true height difference** — collimation error cancels because the distances are equal.
3. Move the level to about **3 m beyond B** (or close to A, per your preferred variant). Read A and B again: (a₂ − b₂).
4. The **collimation error** is the difference between the two computed height differences, expressed over the distance AB. A common tolerance is **≤ 3 mm over 60 m (≈10 arcsec)**; outside that, the instrument needs adjustment by a service agent.

### Total station — setup
1. Set the tripod over the station point, head level by eye, legs firm.
2. **Centre** using the optical or laser plummet, and **level** with the circular bubble by adjusting tripod leg length — not the footscrews.
3. Fine-level with the footscrews using the electronic level, then **rotate 180°** and confirm the bubble stays centred; if it drifts, the plate level/electronic level needs adjustment.
4. Re-check the plummet, iterate until both centring and levelling hold.
5. Measure and record the **instrument height** to the trunnion axis mark, and the **target height** at every prism. Height blunders are the most common survey error.
6. **Orient** by backsighting a known control point and *checking* a second known point. Never orient from a single backsight without a check — an orientation error is undetectable and propagates through everything.
7. Record temperature and pressure for the **atmospheric (ppm) correction**; 10 °C error ≈ 1 ppm ≈ 1 mm per km.
8. Set the correct **prism constant** (−30 mm, −17 mm, 0 mm depending on the prism). A wrong prism constant is a systematic, invisible error.

### Total station — periodic checks
- **Two-face (face left / face right) observation** cancels horizontal collimation, trunnion axis tilt and vertical index error. Do it on control work as a matter of course.
- Run the instrument's built-in **calibration routine** (collimation, tilting axis, compensator index, ATR) monthly.
- **EDM check** against a calibrated baseline annually; **full workshop calibration** annually, or per the instrument's ISO 17123 verification regime.

### GNSS RTK — setup
1. Set the **base** over a known control point, or use an autonomous position and later transform — but never mix the two on one job.
2. Enter the **antenna height** correctly, and note whether it is a slant height to the antenna edge or a vertical height to the reference point; this is the second most common GNSS blunder after the geoid model.
3. Configure the **correction link** (radio, GSM/NTRIP to a CORS network) and confirm the rover reports a **fixed** solution, not float. Never record a float position as a survey point.
4. Load the correct **coordinate system, projection and geoid model**. **[ZA]** South African survey coordinates use the Hartebeesthoek94 datum on the **Lo. system** (Gauss Conform, southing-positive, 2°-wide belts on odd meridians — Lo15, Lo17, Lo19 etc.), which is *not* UTM and has negative-Y conventions that will silently corrupt data if mis-set. **[NA]** Namibia uses Schwarzeck datum / Namibian Lo. belts for cadastral work and WGS84/UTM for many engineering projects — confirm with the client which is required.
5. **Check into at least two known points** before starting, and check out at the end.
6. Observe with adequate satellite geometry: **PDOP < 4**, at least 6–8 satellites, and beware of multipath near metal, water and buildings.

### Laser scanner — workflow
1. Plan station positions so that consecutive scans overlap by **30–40%** and every scan sees at least three well-distributed targets, or has adequate geometry for cloud-to-cloud registration.
2. Control the scan to site coordinates by scanning **survey-controlled targets** (spheres or checkerboards) established by total station or GNSS.
3. Set resolution and quality to the deliverable: higher resolution costs time quadratically and file size linearly.
4. **Register**, then check the reported registration residuals — targets under 3 mm, cloud-to-cloud overlap error under 5 mm for building work.
5. Record the **registration report** with the deliverable. An unregistered or unchecked point cloud is not evidence of anything.

### Rotating laser — field check
Set the laser at one end of a 30 m run, read a receiver on a staff at both ends, then move the laser to the other end and repeat. The difference between the two computed height differences is twice the cone error. Tolerance for a construction-grade instrument is typically **±1.5 mm at 30 m**; outside that, return for calibration.

## Instrument management

- Keep a **calibration register** for every instrument: serial number, last calibration date, certificate number, next due, and the field checks performed between calibrations.
- Field checks (two-peg, two-face, laser check) should be logged in the site survey record, not just done.
- Transport in the case, always. A total station bounced in a bakkie bin is out of collimation whether or not it looks fine.
- **[NA]** Battery and charger availability on remote sites is a real constraint: carry spare batteries, a 12 V charging option, and a printed record of the control coordinates in case the controller fails.

## Sources

- [Leica Geosystems](https://leica-geosystems.com/), [total stations](https://leica-geosystems.com/products/total-stations), [GNSS systems](https://leica-geosystems.com/products/gnss-systems), [laser scanners](https://leica-geosystems.com/products/laser-scanners), [levels](https://leica-geosystems.com/products/levels) — Leica Geosystems (Hexagon), accessed 2026-08-25
- [Leica myWorld customer portal](https://myworld.leica-geosystems.com/) — Leica Geosystems, accessed 2026-08-25
- [Leica DISTO](https://www.disto.com/) — accessed 2026-08-25
- [Trimble](https://www.trimble.com/) and [Trimble Construction](https://construction.trimble.com/) — Trimble Inc., accessed 2026-08-25
- [Trimble Geospatial help portal](https://help.trimblegeospatial.com/) — Trimble Inc., accessed 2026-08-25
- [Topcon Positioning](https://www.topconpositioning.com/) and [Topcon support](https://www.topconpositioning.com/support) — Topcon, accessed 2026-08-25
- [myTopcon NOW!](https://mytopcon.topconpositioning.com/) and [support](https://mytopcon.topconpositioning.com/support) — Topcon, accessed 2026-08-25
- [Sokkia](https://sokkia.com/), [Sokkia US](https://us.sokkia.com/), [Sokkia EU](https://eu.sokkia.com/) — Topcon Positioning Group, accessed 2026-08-25
- [Hexagon GeoCloud](https://geocloud.hexagon.com/) — Hexagon AB, accessed 2026-08-25

## Open questions

- Accuracy figures above are typical class values for current instruments; the exact specification for a given model must be read from that model's data sheet (ISO 17123 test conditions apply). Status `needs-verification` for any figure used in a tolerance argument.
- **[NA]** Current Namibian CORS/network RTK coverage and the official Namibian geoid model should be confirmed with the Namibian Directorate of Survey and Mapping before planning GNSS-based vertical control.
- **[ZA]** TrigNet service status and the current South African geoid model version should be confirmed before relying on network RTK heights.
