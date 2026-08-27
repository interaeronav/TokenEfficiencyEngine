---
id: vision.deployment
title: Deployment and hardware — edge inference, camera interfaces and industrial integration
domain: 21_machine_vision
tags: [edge-ai, jetson, coral, openvino, raspberry-pi, onnx, tensorrt, quantisation, pruning, latency, gige-vision, usb3-vision, camera-link, coaxpress, genicam, plc, opc-ua, ip-rating, ruggedising]
jurisdiction: global
status: stable
confidence: high
updated: 2026-08-25
sources:
  - {title: "Jetson Modules", url: "https://developer.nvidia.com/embedded/jetson-modules", publisher: "NVIDIA", accessed: 2026-08-25}
  - {title: "OpenVINO Documentation 2025", url: "https://docs.openvino.ai/2025/index.html", publisher: "Intel", accessed: 2026-08-25}
  - {title: "ONNX", url: "https://onnx.ai/", publisher: "ONNX / LF AI & Data", accessed: 2026-08-25}
  - {title: "GigE Vision", url: "https://en.wikipedia.org/wiki/GigE_Vision", publisher: "Wikipedia", accessed: 2026-08-25}
  - {title: "CoaXPress", url: "https://en.wikipedia.org/wiki/CoaXPress", publisher: "Wikipedia", accessed: 2026-08-25}
  - {title: "Vision Standards", url: "https://www.automate.org/vision/vision-standards/vision-standards", publisher: "A3", accessed: 2026-08-25}
related: [vision.deep_learning, vision.training, vision.platforms, vision.projects]
---

# Deployment and hardware — edge inference, camera interfaces and industrial integration

**Summary.** A model that works in a notebook is roughly 30 % of a delivered system. This file covers the decision between edge and cloud inference, the edge hardware families that matter (NVIDIA Jetson, Google Coral, Intel OpenVINO targets, Raspberry Pi plus accelerators), the ONNX → TensorRT/OpenVINO export path, quantisation and pruning, how to build a defensible latency and throughput budget, the industrial camera interface standards and GenICam, integration with PLCs and factory networks, and the physical business of surviving dust, vibration, heat and a Namibian summer in an uninsulated shed.

## Key facts

| Item | Value | Source |
|---|---|---|
| Jetson Orin Nano (8/4 GB) | up to 67 TOPS, 7–25 W | NVIDIA |
| Jetson Orin NX (16/8 GB) | up to 157 TOPS | NVIDIA |
| Jetson AGX Orin (64/32 GB) | up to 275 TOPS | NVIDIA |
| Jetson Thor (T5000/T4000) | up to 2070 FP4 TFLOPS, 128 GB, 40–130 W | NVIDIA |
| OpenVINO current release | 2025.4; CPU/GPU/NPU, IR format, NNCF quantisation | Intel |
| GigE Vision | introduced 2006; GVCP (control) + GVSP (stream) over UDP; XML per GenICam schema; A3-administered; licensed | Wikipedia / A3 |
| CoaXPress | CXP 1.0/1.1 to 6.25 Gbit/s per cable; CXP 2.0 to 12.5 Gbit/s; CXP 3.0 at 25 Gbit/s; 24 V, up to 13 W over the coax; JIIA | Wikipedia |
| Camera Link HS | released May 2012 | A3 |
| USB3 Vision | released January 2013 | A3 |
| GenICam | EMVA standard; the XML feature-description layer under all of the above | Wikipedia / EMVA |

## Edge versus cloud

| Factor | Edge | Cloud |
|---|---|---|
| Latency | 5–50 ms, deterministic | 200 ms–2 s, variable |
| Connectivity | Works with none | Requires reliable uplink |
| Data cost | Zero egress | Substantial for continuous video |
| Privacy | Images never leave site | Contractual and regulatory exposure |
| Model size | Constrained | Unconstrained |
| Update | Fleet management problem | Trivial |
| Unit cost | Capex per site | Opex per inference |

**The honest decision rule.** If the system must act on the result within one machine cycle, or the site has poor connectivity, or the imagery is sensitive — go to the edge. If the work is batch analysis of imagery already being uploaded (progress photos, drone flights, 360° walkthroughs) — go to the cloud, because you get bigger models, easier updates and no fleet to maintain.

**Hybrid is usually correct for construction.** Edge does cheap triage (motion, person present, sharpness check) and uploads only interesting frames; cloud does the heavy model. This cuts bandwidth by one to two orders of magnitude and keeps the expensive model centrally updatable.

## Edge hardware families

### NVIDIA Jetson

The default for serious edge vision, because it runs the same CUDA/TensorRT/PyTorch stack as your workstation.

- **Orin Nano 4 GB / 8 GB** — up to 67 TOPS at 7–25 W. The entry point and the right choice for a single-camera YOLO11n/s pipeline at 30 FPS. The "Super" firmware update materially raised clocks on this module.
- **Orin NX 8 GB / 16 GB** — up to 157 TOPS. Multiple camera streams, or one stream with a larger model.
- **AGX Orin 32 GB / 64 GB** — up to 275 TOPS. Multi-camera, multi-model, 3D processing, or a mobile robot's whole perception stack.
- **Thor T4000 / T5000** — up to 2070 FP4 TFLOPS, 128 GB, 40–130 W. Aimed at humanoid/physical-AI workloads; a datacentre-class part in an embedded envelope.

Practical notes: buy modules on **carrier boards from Connect Tech, Auvidea, Seeed reComputer or AverMedia** rather than the devkit for production; budget for the **JetPack** version lock (TensorRT engines are not portable across JetPack versions or across module types — you must build the engine on the target); and use `nvpmodel`/`jetson_clocks` to pin a power mode, because the default DVFS makes latency measurements meaningless.

### Google Coral / Edge TPU

An ASIC for int8 TensorFlow Lite inference, available as a USB accelerator, M.2 A+E and Mini PCIe modules, a Dev Board with an SoM, and the microcontroller-class Dev Board Micro. Extremely power-efficient for its class, but the constraints are severe: **int8-quantised TFLite only, compiled with the Edge TPU compiler, with a restricted operator set** — anything unsupported falls back to CPU and destroys the performance. It suits fixed, simple models (MobileNet-SSD class) on a tight power budget, and it does not suit a modern transformer detector. Treat it as a specialist tool, and check current product availability before designing it in.

### Intel OpenVINO

Not hardware but the toolkit that makes Intel hardware viable: CPU, integrated and discrete GPU, and the NPU in recent Core Ultra parts. Current release **2025.4**. Workflow: convert from PyTorch/TensorFlow/ONNX/PaddlePaddle/JAX to the **IR** (Intermediate Representation) format, run on the OpenVINO Runtime with auto device selection, and optimise with **NNCF** (post-training quantisation with accuracy control, quantisation-aware training, filter pruning, and 4-bit weight compression for LLMs).

**This is the right answer for a factory or workshop PC.** A mini-PC with a Core Ultra runs a YOLO11s at usable frame rates with no GPU, no CUDA, no driver drama, and hardware you can replace from any supplier — which matters a great deal for a small joinery shop with no IT department.

### Raspberry Pi and accelerators

Pi 5 alone manages small classifiers and classical CV comfortably; it is not a detector platform at resolution. Add-ons that change that:

- **Raspberry Pi AI Kit / AI HAT+** — Hailo-8L (13 TOPS) or Hailo-8 (26 TOPS) over PCIe. Excellent performance per watt and per rand; the toolchain (Hailo Dataflow Compiler) is a real learning curve.
- **Coral USB accelerator** — as above.
- **Pi Global Shutter Camera** — a genuinely useful part: a Sony IMX296 global-shutter sensor with a C/CS mount, which makes a Pi into a legitimate low-end machine-vision head for a fixtured inspection.

For a joinery workshop pilot, a Pi 5 + AI HAT+ + Global Shutter Camera is a defensible sub-€400 platform to prove a concept before committing to industrial hardware.

## ONNX, TensorRT and the export path

**ONNX** is an open format defining a common operator set and file format so a model trained in one framework runs in another. The practical pipeline:

```
PyTorch  ──torch.onnx.export──►  model.onnx  ──┬──► ONNX Runtime (CPU/CUDA/DirectML/CoreML)
                                                ├──► TensorRT  (NVIDIA)
                                                ├──► OpenVINO IR (Intel)
                                                └──► TFLite / Edge TPU (via converters)
```

```python
from ultralytics import YOLO
m = YOLO("runs/ppe/v3_960px/weights/best.pt")

m.export(format="onnx", imgsz=960, opset=17, simplify=True, dynamic=False)
m.export(format="engine", imgsz=960, half=True, workspace=4)   # TensorRT, on target
m.export(format="openvino", imgsz=960, int8=True, data="ppe.yaml")
```

**Build TensorRT engines on the machine that will run them.** An engine is specialised to the GPU architecture, the TensorRT version and the CUDA version. Ship the ONNX file and build on first boot, caching the engine.

Raw TensorRT from ONNX:

```bash
trtexec --onnx=model.onnx --saveEngine=model.engine \
        --fp16 --workspace=4096 \
        --minShapes=images:1x3x960x960 \
        --optShapes=images:1x3x960x960 \
        --maxShapes=images:4x3x960x960
```

## Quantisation and pruning

**Quantisation** reduces numeric precision. FP32 → FP16 is nearly free and roughly doubles throughput on any modern accelerator; **do it always**. FP32 → INT8 gives another ~2× and cuts memory 4×, at a typical cost of 0.5–2 mAP points.

- **Post-training quantisation (PTQ)** — calibrate scales on 100–500 representative images. Fast, no retraining. This is the default. *Use images from the real deployment, not from COCO.*
- **Quantisation-aware training (QAT)** — simulate quantisation during fine-tuning. Recovers most of the lost accuracy; costs a training run.
- **FP8 / FP4** on Ada/Blackwell/Thor-class hardware is increasingly the sweet spot for large models.

**Pruning** removes weights or whole channels. *Unstructured* pruning gives high sparsity but needs sparse-kernel support to translate into speed; *structured* (channel/filter) pruning gives real speedup on any hardware at a larger accuracy cost. In practice, for vision, **choosing a smaller model variant beats pruning a larger one** — YOLO11n is a better-engineered small model than a pruned YOLO11m. Pruning earns its place when you must keep a specific trained architecture.

**Knowledge distillation** — train the small model to match the large model's outputs on unlabelled in-domain data. Often the highest-value compression technique, and it exploits the mountain of unlabelled site imagery you already have.

> ⚠️ Every compression step must be re-validated on the quarantined test set with the *deployed preprocessing*. A quantised model that lost 4 mAP because the calibration set was unrepresentative will look fine on a demo image and fail on a rainy Tuesday.

## Latency and throughput budgeting

Budget the whole path, not the model. For a 30 FPS single-camera pipeline the frame budget is 33.3 ms:

| Stage | Typical | Notes |
|---|---|---|
| Sensor exposure + readout | 5–15 ms | Overlappable with processing |
| Transfer (GigE/USB3/CSI) | 2–10 ms | Zero-copy on CSI/Jetson |
| Decode (if compressed) | 1–5 ms | Use NVDEC/VAAPI, not CPU |
| Preprocess (resize, normalise, HWC→CHW) | 1–8 ms | **Do it on GPU.** A CPU resize of a 4K frame can exceed the model time |
| Inference | 2–20 ms | The number everyone quotes |
| Postprocess (NMS, decode) | 1–10 ms | NMS on CPU for 8,400 anchors is slow — use the GPU NMS plugin, or an NMS-free model such as YOLO26 or RT-DETR |
| Tracking / business logic | 1–5 ms | |
| Output (I/O, network, DB) | 1–20 ms | Must be asynchronous |

**Rules that matter:**
1. **Measure end-to-end, at the 99th percentile, under thermal load.** Mean latency on a cold device is marketing.
2. **Pipeline, do not serialise.** Capture, preprocess, infer and postprocess in separate threads/CUDA streams with bounded queues. This converts a 40 ms serial path into a 20 ms-throughput pipeline at the cost of one frame of extra latency.
3. **Batching raises throughput and raises latency.** Correct for offline analysis of a photo set, wrong for a real-time reject actuator.
4. **Drop frames deliberately.** A bounded queue with a drop-oldest policy degrades gracefully; an unbounded queue turns a transient slowdown into an ever-growing delay and then an out-of-memory kill.
5. **Thermal throttling is the silent killer.** A Jetson in a sealed enclosure in a Namibian summer will clock down. Design the enclosure thermals, then re-measure.

## Industrial cameras and interfaces

| Standard | Body | Bandwidth | Cable | Power | Use |
|---|---|---|---|---|---|
| **GigE Vision** | A3 (2006) | 1 GbE ≈ 100–115 MB/s; 5/10/25 GigE variants | 100 m Cat 5e/6 | PoE (802.3af) | The default. Long cable runs, multi-camera, switched networks |
| **USB3 Vision** | A3 (Jan 2013) | ~350–400 MB/s usable | ~3–5 m passive | Bus-powered | Single camera to a nearby PC; cheapest per camera |
| **Camera Link** | A3 | Base/Medium/Full to ~850 MB/s | ~10 m | PoCL variants | Legacy high speed; needs a frame grabber |
| **Camera Link HS** | A3 (May 2012) | Multi-GB/s, fibre capable | Long over fibre | — | Very high speed line-scan |
| **CoaXPress** | JIIA | CXP-6: 6.25 Gbit/s per cable; CXP-12 (v2.0): 12.5 Gbit/s; v3.0: 25 Gbit/s; aggregate over multiple cables | Tens of metres of coax | 24 V, up to 13 W over the same coax | High-speed, long-cable, single-cable-power applications |
| **MIPI CSI-2** | MIPI Alliance | Very high, board-level | Centimetres | — | Embedded (Jetson, Pi); lowest latency, zero-copy |

**GigE Vision** in practice: it uses **GVCP** over UDP for control and **GVSP** over UDP for streaming, with an XML feature-description file conforming to the EMVA **GenICam** schema. Enable **jumbo frames (MTU 9000)**, raise the socket receive buffer, use a dedicated NIC with hardware timestamping, and expect packet loss and resend storms if you put cameras on a shared office network. It is a licensed standard — developing a compliant driver requires a licence.

**GenICam** is the layer that makes all of this tolerable: a generic programming interface where every camera publishes an XML description of its features (`ExposureTime`, `Gain`, `TriggerMode`, `Width`, `Height`…) with a standard naming convention (SFNC). Consequence: **you can swap a Basler for an Allied Vision for a Teledyne camera and change almost no application code**, if you go through a GenICam-based API. Open implementations: **Harvester** (Python, `genicam` bindings), **Aravis** (GObject/Linux, LGPL). Vendor SDKs: Basler **pylon**, Allied Vision **Vimba X**, Teledyne **Spinnaker**, IDS **peak**.

```python
# GenICam camera access with Harvester — vendor-neutral
from harvesters.core import Harvester
h = Harvester()
h.add_file("/opt/pylon/lib/gentl/ProducerU3V.cti")   # any GenTL producer
h.update()
ia = h.create(0)
ia.remote_device.node_map.PixelFormat.value  = "Mono8"
ia.remote_device.node_map.ExposureTime.value = 4000.0     # µs
ia.remote_device.node_map.TriggerMode.value  = "On"
ia.start()
with ia.fetch(timeout=5) as buf:
    comp = buf.payload.components[0]
    img  = comp.data.reshape(comp.height, comp.width)
ia.stop(); ia.destroy(); h.reset()
```

## PLC and factory integration

The vision system almost never acts directly; it tells a controller what to do.

- **Digital I/O** — the most robust and the most common. A 24 V opto-isolated input triggers the camera from a proximity sensor or encoder; a 24 V output fires a reject solenoid N milliseconds later. Deterministic, diagnosable with a multimeter, no network. **Prefer this for the actual reject decision.**
- **EtherNet/IP** (Rockwell), **PROFINET** (Siemens), **EtherCAT** (Beckhoff) — real-time industrial Ethernet. Most smart cameras (Cognex In-Sight, Keyence, Omron) speak these natively; a PC-based system needs a stack (e.g. a Hilscher netX card, or `SOEM`/`igh` for EtherCAT on Linux).
- **Modbus TCP** — simple, universal, ubiquitous on small PLCs. `pymodbus` in three lines. Good enough for pass/fail and a measurement register.
- **OPC UA** — the modern semantic layer for MES/SCADA integration. Use it for reporting and recipe management, not for the millisecond-critical path. **OPC UA Companion Specification for Machine Vision** exists precisely for this.
- **MQTT / REST** — for the IT side: dashboards, databases, cloud. Never in the safety or reject path.

```python
from pymodbus.client import ModbusTcpClient
plc = ModbusTcpClient("192.168.1.50", port=502)
plc.write_coil(address=0, value=bool(is_pass), slave=1)                 # pass/fail
plc.write_registers(address=100, values=[int(width_mm*100)], slave=1)   # 0.01 mm units
```

**Timing discipline:** the reject decision must reach the actuator within a known window relative to the trigger. Latch the trigger with a hardware counter, tag every image with it, and have the PLC — not the vision PC — own the timing. **Never rely on wall-clock time across a network for a physical actuation.**

> ⚠️ A vision system is not a safety device. Light curtains, e-stops, interlocks and guarding are safety functions and must be implemented with rated safety components to the applicable standard (ISO 13849 / IEC 62061 in machinery). A PPE-detection camera is a *management information* tool; it must never be presented, sold or relied upon as a substitute for physical safeguarding or a permit-to-work system.

## Ruggedising for dust, heat and vibration

**Ingress protection.** IP65 is the sensible minimum for a workshop; IP67 for a wet or wash-down area; IP66/IP69K for high-pressure cleaning. Enclosures for cameras are available off the shelf (autoVimation, Tempest, Videotec). **[NA]** In Namibian and inland South African conditions the dominant threats are fine dust and thermal cycling, not water — specify sealed enclosures with a Gore-type vent to equalise pressure without admitting dust, and avoid unfiltered forced-air cooling, which pumps abrasive dust across the optics.

**Heat.** Ambient inside an uninsulated workshop or a roof-mounted enclosure in Namibia can exceed 55 °C. Consequences: sensors get noisier (dark current roughly doubles per 6–8 °C), LEDs lose output and shift wavelength, and edge modules throttle. Mitigations: passive heatsinking to the enclosure wall, a sun shield with a ventilated air gap (far more effective than any fan), mounting on the shaded side, vortex coolers or Peltier units where compressed air or power allow, and specifying industrial-temperature-rated parts (−40 to +85 °C) rather than commercial.

**Vibration.** Mount the camera to the same rigid structure as the part, never to a separate frame. Every relative motion between the two is measurement error. Use vibration-damping mounts under the whole assembly rather than under the camera alone. On mobile plant, expect to re-check calibration far more often.

**Optical contamination.** A sacrificial front window is cheaper and faster to replace than a lens. Air knives or a positive-pressure purge across the window keep dust off. **In a joinery shop, fine MDF dust on the front element is the number one cause of drift** — schedule cleaning as a documented, logged operation, and include a periodic reference-target check in the software so drift is detected rather than discovered.

**Power.** 24 V DC industrial supplies with correct grounding; surge protection on any outdoor cable run; and a UPS with clean shutdown for anything with a filesystem. **[NA]** In areas subject to load-shedding or unstable supply, design for abrupt power loss: read-only root filesystem, journalled data partition, and no unsaved state.

**Fleet management.** Ten cameras across three sites is a fleet. Use containerised deployment (Docker/Balena/Fleet), remote SSH via a mesh VPN (Tailscale/WireGuard), OTA updates with automatic rollback on health-check failure, and centralised logs. Decide this before deployment, not after the first field visit.

## Sources

- [NVIDIA Jetson Modules](https://developer.nvidia.com/embedded/jetson-modules) — Orin Nano 67 TOPS / 7–25 W, Orin NX 157 TOPS, AGX Orin 275 TOPS, Thor T5000/T4000 up to 2070 FP4 TFLOPS / 128 GB / 40–130 W.
- [OpenVINO Documentation 2025](https://docs.openvino.ai/2025/index.html) — 2025.4; CPU/GPU/NPU; conversion from PyTorch/TF/ONNX/TFLite/PaddlePaddle/JAX to IR; NNCF PTQ, QAT and filter pruning.
- [ONNX](https://onnx.ai/) — open format, common operator set and file format.
- [Wikipedia — GigE Vision](https://en.wikipedia.org/wiki/GigE_Vision) — 2006, GVCP/GVSP over UDP, GenICam XML schema, A3 administration, licensing.
- [Wikipedia — CoaXPress](https://en.wikipedia.org/wiki/CoaXPress) — CXP 1.0/1.1 6.25 Gbit/s, 2.0 12.5 Gbit/s, 3.0 25 Gbit/s, 24 V / 13 W over coax, JIIA.
- [A3 Vision Standards](https://www.automate.org/vision/vision-standards/vision-standards) — Camera Link HS May 2012, USB3 Vision January 2013, GigE Vision 3.0.

## Open questions

- **Google Coral figures could not be verified in this pass** — both product pages redirected or returned only navigation. The commonly cited Edge TPU figure is 4 TOPS int8 at ~2 W, requiring int8 TFLite compiled by the Edge TPU compiler. Marked `needs-verification`, and current product availability should be confirmed before designing Coral in.
- Hailo-8/8L TOPS figures (26 / 13 TOPS) and Raspberry Pi AI HAT+ details are from familiarity, not fetched.
- GigE Vision practical bandwidth (~115 MB/s on 1 GbE) and USB3 Vision (~350–400 MB/s) are practitioner figures, not standard-specified.
- Dark-current doubling "per 6–8 °C" is a widely quoted silicon rule of thumb, not verified against a datasheet here.
