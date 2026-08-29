# 58 — The TEE kernel scheduler: an M5-inspired coordinator over heterogeneous engines (2026-08-29)

Verification basis: open-web grounding 2026-08-29 (Apple M5-family
architecture from Apple's own releases; Ray's core abstractions read
live through `tee_web_lookup` — during which docs.ray.io's robots.txt
refusal fired and TEE honored it, the A34 etiquette gate working in
the wild); TEE's own shipped anatomy (A37/A38/A41 designs, measured
rows); the owner's directive verbatim: a "CPU" that coordinates all
TEE tasks "much like a neural network and nodes," inspired by the M5,
"dynamically integrating and managing tasks more efficiently than a
modular system."

## The metaphor, decoded honestly

What the M5 actually is: **modular engines under one scheduler and
one memory.** Six super cores + twelve performance cores (M5
Pro/Max), a Neural Accelerator in every GPU core, unified memory at
up to 614 GB/s (M5 Max), dies fused by UltraFusion — and macOS
dispatching work across all of it by quality-of-service class (Grand
Central Dispatch's user-interactive → background ladder). The chip's
genius is NOT the absence of modules; it is that modules never talk
past a shared memory and never sit idle when the scheduler can place
work on them. So the owner's ask lands as: **keep TEE's modules;
give them a nervous system.** "Neural network and nodes" maps to the
computer-science object that actually does this: a **task graph**
(nodes = tasks with declared inputs/outputs, edges = data
dependencies) dispatched by a cost-aware scheduler — the discipline
the literature calls heterogeneous DAG scheduling (HEFT-family
earliest-finish placement; work-stealing for balance; exact
citations verified at build per house rules).

## The precedent stack

- **Apple silicon + GCD**: heterogeneous cores + QoS classes +
  unified memory — the inspiration, and also the proof that the
  pattern is scheduler-over-modules.
- **Ray** (read live): Tasks (stateless functions), **Objects
  ("immutable values accessible across the cluster")** — the
  zero-copy substrate — actors for stateful engines, resource-aware
  dispatch; its "Ownership" futures paper is the reference for
  fine-grained task graphs. Ray is the existence proof that one
  runtime can schedule wildly heterogeneous AI work well.
- **TEE itself**: the A41 router is a scheduler for ONE task class
  (chores) over ONE engine axis (local models + client). The
  machine-load ledger is the arbiter. This research generalizes
  those two organs to everything TEE runs.

## The key insight TEE already owns: its unified memory exists

The M5's unified memory means engines exchange POINTERS, never
copies. TEE's dogma has been exactly this since Phase 1: content-
addressed facts, scene ids, extract-store hashes, provenance stamps —
**internal edges pass ids, never payloads. And internally, ids are
free: tokens are only spent at the CLIENT boundary.** The scheduler's
deepest efficiency law follows immediately: *maximize internal edges,
minimize boundary crossings* — route intermediate results engine-to-
engine by id, and cross into the conversation only with verified,
budgeted finals. That is the M5 keeping data on-chip, translated.

## What exists vs what is missing

Already shipped: the engine pool (adapters, llm profiles, VLM,
whisper, voxkiln, reconstruction jobs, gateway backends), async jobs,
the machine-load ledger (A41), the router seed (A41), measured cost
tables for nearly every operation (the benchmark corpus), the meter,
provenance, and an implicit QoS split (the <2 s chore bar vs batch
jobs). Missing — the unifying layer, four pieces:

1. **Task descriptors + the graph**: every unit of work declares
   inputs/outputs by id, its verifier, its QoS class, its cost
   estimate (from the measured tables). Today's implicit call chains
   become explicit nodes and edges.
2. **One engine registry**: capability + cost + residency + footprint
   per engine, in one place (today spread across profiles, adapters,
   and the ledger).
3. **QoS classes made law**: interactive (chores, client-facing) /
   standard / batch (reconstructions, batteries, LoRA) / maintenance
   (cache sweeps) — with admission control (never accept work the
   ledger cannot place) and preemption rules (interactive never
   queues behind batch; batch yields at its checkpoints, which the
   jobs pattern already has).
4. **The dispatch policy**: start embarrassingly simple — greedy
   cost-aware earliest-finish using the measured tables — and adopt
   HEFT-class sophistication ONLY if a benchmark row shows the greedy
   policy losing (the router's earn-your-complexity law, inherited).

## The honest efficiency claim

"More efficient than a modular system" is measurable ONLY under
mixed load. Under a single task, a scheduler adds overhead and zero
value — say it plainly. The benchmark shape (research-48 style): a
concurrent mixed workload (interactive chores + a reconstruction +
a gateway call + a generation) measured for makespan, interactive
p95 latency, engine utilization, and client tokens; arms = today's
static behavior vs scheduled. Expected wins come from three named
mechanisms: no head-of-line blocking (QoS), cost-aware placement
(the tables), and boundary-crossing minimization (the id law). If
the row does not win, the scheduler reverts — the A39 precedent.

## Risks and their gates

- **Complexity creep** → ship shadow-first (below), greedy-first;
  every mechanism must win a row to stay.
- **Single point of failure** → the kernel scheduler is OPTIONAL by
  construction: a supervised component whose death (or config-off)
  degrades to today's static behavior, always. No TEE feature may
  ever REQUIRE the scheduler to function.
- **Starvation** → aging on queued batch work; the meter shows queue
  ages.
- **Debuggability** → every dispatch decision logged with its reason
  and cost estimate vs actual (the meter pattern; decisions are data).
- **Scope** → server-side work only. The client's conversation is
  never scheduled, and the owner's pins (TEE/Q) outrank placement.

## The build shape (A42 when directed — sequenced AFTER A41)

The router and the load ledger are this scheduler's first two organs;
building the kernel before A41 lands would be roof-before-floor.
Phases, sketched: **K0** descriptors + graph substrate + SHADOW MODE
(the scheduler runs beside reality, recording what it WOULD have done
— the delta between shadow and actual is free evidence before any
behavior changes); **K1** QoS + admission; **K2** greedy dispatch
live behind config, shadow-validated; **K3** preemption +
backpressure; **K4** the mixed-load benchmark — win or revert; **K5**
close. Surface LAW throughout: the scheduler is internal machinery —
zero new always-loaded tools.

## Verdict

The metaphor survives contact with the evidence, with one correction
that strengthens it: the M5 is modules-plus-coordination, and so is
this. TEE already owns the unified memory (ids over payloads), the
arbiter (the ledger), the first dispatcher (the router), and the cost
tables the scheduler needs. What remains is the task graph, the QoS
law, one registry, and a shadow-validated dispatch loop — buildable,
measurable, revertible. Recommendation: adopt as campaign A42 after
A41 lands, with the mixed-load row as its judge.

Sources: Apple M5 Pro/Max release (apple.com/newsroom 2026-03), M5
Ultra/M6 release (apple.com/newsroom 2026-08), MacRumors/PetaPixel
coverage for the Ultra fusion details; github.com/ray-project/ray
(read via tee_web_lookup; the Ray whitepaper and Ownership paper
referenced therein); GCD QoS classes as Apple's software scheduling
precedent; HEFT-family DAG scheduling literature (citation verified
at build).
