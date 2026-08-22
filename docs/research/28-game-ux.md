# 28 — Game experience & UX: validated practice (2026-08-22)

## Instruments and methods

**PXI** (5 validation studies, 529 participants + independent CHI 2024
validation; 11-item miniPXI) = the default open instrument. **GEQ was
never formally validated — its 7-factor structure is unsupported (CHI
PLAY 2018): do not treat GEQ scores as validated.** PENS proprietary
(Immersyve); UPEQ (Ubisoft FDG 2018) has the strongest published
survey→behavior link (subscales predict playtime/spend/group play).
Methods: 5-user qualitative rule per iteration (~40 users for quant);
RITE fix-between-participants (AoE2 tutorial: >90% of issues fixed =
canonical case); Valve = weekly playtests from week one, 100+ testers
per HL2 level; cadence norm: weekly-biweekly small-n, large-n at
milestones. Biometrics = triangulation only.

## Frameworks with evidence

Swink game feel: input feedback within ~100 ms preserves direct control.
**Juice is inverted-U** (Kao 2020: medium beats none AND extreme — cap
it). Flow (Chen): embed difficulty choice inside play (player-controlled
DDA); covert DDA must never be provable mid-session nor tied to
monetization. Hodent: usability + engage-ability (motivation, emotion,
game flow); consistent signs & feedback. HEP/PLAY heuristics for early
prototypes. Difficulty data: 70-80% of players use the easiest
difficulty (Bandai telemetry); AoW4: 48% on easy; **defaults dominate**
(AC Odyssey subtitles default-on: 95% kept them; Division 2 default-off:
50% sampled-on). Celeste assist-mode is the model (and its de-moralized
reframing is the documented lesson). Minimize failure cost: sub-second
respawn, <30 s retry loops.

## Onboarding patterns (validated)

Teach by doing in a safe space; blend the tutorial into the game; spaced
mechanic introduction (PvZ withholds the meta ~10 levels); isolate then
combine (Portal chambers); kishōtenketsu level grammar (introduce →
develop → twist → conclude); RITE the tutorial.

## Enforce vs judge (the module's split)

**Enforce (parameter table, sources in reference files):** console text
≥26 px@1080p (PC 18 px), 200% scaling, ≤80 chars/line, 1.5× line
spacing; contrast 4.5:1 / 3:1; subtitles ≥46 px@1080p, ≤38 chars × ≤2
lines, 15-20 chars/sec, on by default; no color-only information (1 in
12 men colorblind); ≤3 flashes/sec, avoid 5-30 Hz flicker; input
feedback <100 ms (aiming degrades from 41 ms local latency); FOV 60° TV
/ 90° monitor defaults + PC slider; motion blur/shake/bob toggles; VR
<20 ms motion-to-photon, ≥90 Hz, no artificial acceleration; remapping;
0.5 s input-cooldown option; sub-second respawn in failure-heavy loops;
one-mechanic-at-a-time with safe practice; CVAA compliance whenever
player-to-player comms exist (fines to ~$1.16M/violation; EAA
enforceable since June 2025 via storefronts/chat).

**Judge:** juice quantity; DDA visibility/tuning; difficulty curve
shape; HUD diegesis level vs genre convention (diegetic / non-diegetic /
spatial / meta); instrument choice; assist-mode depth.

Market case: ~46M US gamers with disabilities (AbleGamers); TLOU2
shipped ~60 accessibility options, 7 of the 10 most-used were
subtitle-related.
