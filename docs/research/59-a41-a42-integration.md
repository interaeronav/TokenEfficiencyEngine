# 59 — Integrating the merged campaign (A41) with the kernel scheduler (A42) (2026-08-29)

Verification basis: research 55/56/57 (the A41 designs) and 58 (the
scheduler design); TEE project memory verified current this session
(a41 key intact, neither campaign started — clean merge); open-web
methodology grounding 2026-08-29: trace-driven evaluation is the
canonical way schedulers are judged — Google's Borg traces, the
Omega paper's trace-based comparisons, Firmament's evaluation on a
12,500-machine Google trace (sources at foot). This doc adds no
feature scope; it is the composition map.

## Why one script beats "A42 after A41" — the trace prize

Research 58 sequenced the scheduler AFTER A41 because the router and
load ledger are its organs. Merging does not break that ordering —
it exploits it: **if the scheduler's shadow recorder lands the
moment the ledger exists (right after R1), then the entire remainder
of the campaign — reconstructions, routed chores, gateway calls, dry
run, benchmarks — is recorded as REAL WORKLOAD TRACES.** By the time
the dispatch policy goes live, it is validated against weeks of the
owner's actual mixed load, replayed Borg-style, not synthetic
fixtures. The campaign builds the scheduler's evidence base as a
side effect of building everything else. That is the merge's prize,
and it only exists inside one campaign.

## The seams (each shipped once instead of twice)

1. **Registry-form descriptors from day one**: R1 writes its engine
   facts (profiles, job classes, footprints) directly in the K-layer
   registry schema — no later migration.
2. **One meter schema**: R2 designs the merged meter with the
   scheduler's columns (queue age, dispatch reason, shadow delta)
   reserved from the start.
3. **QoS as annotations first, law later**: every T/R work item
   carries its class tag (interactive/standard/batch/maintenance)
   from R1 on — cheap labels; K1 turns them into admission and
   preemption law without retrofitting.
4. **The shadow recorder instruments its own campaign** (the prize
   above); K2's go-live gate is agreement-with-or-improvement-over
   the recorded reality, measured by replay.
5. **The deadline still rules**: nothing K touches the critical path
   to the site visit — T1's protocol and T6's dry run land on the
   A41 schedule regardless of scheduler progress.

## Release shape

One campaign, two release gates: **Gate A** after T6+R4 (trip-ready:
capture pipeline proven on the dry run, router benchmarked) —
recommend 0.6.0, owner tags; **final close** after K4 — recommend
0.7.0. If the site visit arrives mid-campaign, Gate A is the state
that travels.

## Laws

The A41 union stands unrelaxed, plus research 58's scheduler laws:
degrade-to-static always (no TEE feature may require the scheduler),
shadow before live, greedy before clever, win-or-revert at K4,
decisions logged as data, server-side work only, surface LAW
2,028/17 (the scheduler is internal machinery — zero new tools).

Sources: Omega (Schwarzkopf et al., EuroSys 2013 — trace-based
scheduler comparison), Firmament (Gog et al., OSDI 2016 — evaluated
on the 12,500-machine Google trace), Google Borg cluster traces
(2019 8-cluster release), ACM Queue "Cluster Scheduling for Data
Centers"; research 55–58 for everything internal.
