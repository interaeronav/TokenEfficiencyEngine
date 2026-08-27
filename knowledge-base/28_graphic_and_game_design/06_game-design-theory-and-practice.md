---
id: gxgd.game_theory
title: Game design theory and practice
domain: 28_graphic_and_game_design
tags: [game-design, core-loop, mda, elemental-tetrad, systems-design, economy-design, progression, difficulty, flow, game-feel, juice, level-design, pacing, environmental-storytelling, narrative-design, multiplayer, monetisation, playtesting, prototyping, gdd, metrics]
jurisdiction: global
status: stable
confidence: high
updated: 2026-08-25
applies_to: "Design theory is stable; the monetisation and live-ops sections reflect practice and regulation as of August 2026."
unit_system: metric
sources:
  - {title: "MDA framework", url: "https://en.wikipedia.org/wiki/MDA_framework", publisher: "Wikipedia", accessed: 2026-08-25}
  - {title: "Level design", url: "https://en.wikipedia.org/wiki/Level_design", publisher: "Wikipedia", accessed: 2026-08-25}
  - {title: "Valve Corporation", url: "https://en.wikipedia.org/wiki/Valve_Corporation", publisher: "Wikipedia", accessed: 2026-08-25}
  - {title: "DigiPen Institute of Technology", url: "https://en.wikipedia.org/wiki/DigiPen_Institute_of_Technology", publisher: "Wikipedia", accessed: 2026-08-25}
  - {title: "Supergiant Games", url: "https://en.wikipedia.org/wiki/Supergiant_Games", publisher: "Wikipedia", accessed: 2026-08-25}
  - {title: "Hollow Knight: Silksong", url: "https://en.wikipedia.org/wiki/Hollow_Knight:_Silksong", publisher: "Wikipedia", accessed: 2026-08-25}
  - {title: "FromSoftware", url: "https://en.wikipedia.org/wiki/FromSoftware", publisher: "Wikipedia", accessed: 2026-08-25}
related: [gxgd.overview, gxgd.game_education, gxgd.game_disciplines, gxgd.engines_tools, gxgd.resources, envasset.principles]
---

# Game design theory and practice

**Summary.** Game design is the design of *rules that generate experience*. The designer never authors the moment directly; they build a system, and the player produces the moment by acting inside it. This file covers the working apparatus: the core loop, MDA, the elemental tetrad, systems and economy design, difficulty and flow, game feel, level design principles with the *Half-Life 2* and *Portal* lessons stated concretely, narrative design and environmental storytelling, multiplayer and social design, monetisation and its ethics, playtesting method, prototyping, what replaced the design document, and metrics-driven design. Real games are used as cases throughout.

## Key facts

| Item | Value |
|---|---|
| MDA framework | Robin Hunicke, Marc LeBlanc, Robert Zubek — **M**echanics → **D**ynamics → **A**esthetics |
| MDA's eight kinds of fun | Sensation, Fantasy, Narrative, Challenge, Fellowship, Discovery, Expression, Submission (Competition sometimes added as a ninth) |
| Designer/player asymmetry in MDA | Designer works M→D→A; player experiences A→D→M |
| Elemental tetrad (Jesse Schell) | **Mechanics, Story, Aesthetics, Technology** — all four, equally weighted |
| Level design as a profession | Did not exist as a discipline in the 1970s–2000s; a single programmer laid out maps |
| Early shipped level editors | *Lode Runner* (1983), *Dandy* (1983) |
| Prototyping rule of thumb | The question determines the fidelity; paper before code before art |
| Playtest sample per round | ~5 for usability-style issues; far more for balance and telemetry |
| Portal's origin | *Narbacular Drop* (DigiPen student game, 2005) — Valve hired the team |
| Portal 2's paint mechanic origin | *Tag: The Power of Paint* (DigiPen student game, 2008) |

> ⚠️ Every framework on this page is a *lens*, not a procedure. MDA, the tetrad, flow channels and the rest are useful for diagnosing why a game is not working and for arguing about it with colleagues. None of them will generate a good game, and treating any of them as a checklist produces competent, forgettable design.

---

## 1. The core loop

The core loop is the smallest repeating unit of activity the player performs, and it is the first thing to design and the last thing to compromise. Format: **input → action → outcome → feedback → new opportunity**, cycling.

- *Vampire Survivors*: move → auto-attack fires → enemies die → gems drop → level up → choose an upgrade → the space is more survivable → move.
- *Slay the Spire*: draw hand → play cards against enemy intent → resolve turn → win combat → choose a card/relic reward → deck is stronger and more specific → next node.
- *Dark Souls*: approach → observe enemy tell → commit to an attack or dodge within a stamina budget → succeed and progress or die and lose souls → return to the same fight with better knowledge.
- *Stardew Valley*: wake → allocate a finite day of energy across farming, mining, fishing, relationships → sleep → the farm and relationships have advanced → wake.

**Design tests for a core loop:**
1. **Can you state it in one sentence?** If it takes a paragraph, it isn't a loop, it's a list of features.
2. **Is it fun on the tenth repetition with no rewards attached?** Strip the XP, the loot, the story. If what remains is boring, you have a Skinner box, not a game.
3. **Does the loop's output feed its own input?** Loops that terminate need an outer loop to restart them.
4. **How long is one cycle?** Seconds (a shooter's engage-kill-reload), minutes (a roguelike combat), hours (a strategy turn), days (a live-service daily). Games typically nest three loops at different timescales.

**Nested loops.** A durable game usually has: a **moment-to-moment loop** (seconds), a **session loop** (10–60 minutes, ending in a resolvable state), and a **progression loop** (hours to weeks). *Destiny* and *Monster Hunter* are the textbook cases; *Hades* nests run → meta-progression → narrative advancement with unusual elegance, which is why Supergiant's seven-person team produced a game that won Game of the Year at BAFTA and D.I.C.E. and sold over a million copies.

---

## 2. MDA and the elemental tetrad

### MDA

**Mechanics** are "the base components of the game — its rules, every basic action the player can take". **Dynamics** are "the run-time behaviour of the mechanics acting on player input". **Aesthetics** are "the emotional responses evoked in the player".

The framework's real contribution is the **asymmetry**: the designer builds mechanics and can only *hope* for aesthetics; the player encounters aesthetics and only ever infers mechanics. This means your intent is not transmitted — it is reconstructed. Every design decision should be tested against what a player will infer, not what you meant.

**The eight kinds of fun** replace the useless word "fun" with a target you can design toward: **Sensation** (sensory pleasure), **Fantasy** (make-believe), **Narrative** (drama), **Challenge** (obstacle course), **Fellowship** (social framework), **Discovery** (uncharted territory), **Expression** (self-discovery and creation), **Submission** (pastime); competition is often added as a ninth. State which two or three your game is targeting in its first design document, and cut features that serve a fourth.

Worked example: *Minecraft* targets Discovery, Expression and Fantasy. *Counter-Strike* targets Challenge, Fellowship and Competition. *Animal Crossing* targets Expression, Submission and Fellowship. Games that fail often target none clearly, or all nine.

### The elemental tetrad

Jesse Schell's framing in *The Art of Game Design*: every game is made of **Mechanics** (rules and procedures), **Story** (the sequence of events), **Aesthetics** (how it looks, sounds and feels), and **Technology** (the materials that make it possible). The tetrad's argument is that all four are equally essential and that they constrain each other — technology enables mechanics, mechanics enable story, aesthetics communicate mechanics. Its practical use is as a completeness check: for any design problem, ask what each of the four is contributing, and which one you have neglected.

**Other lenses worth having:** **Bartle's player types** (Achievers, Explorers, Socialisers, Killers — designed for MUDs, over-applied since, still useful for multiplayer); **Costikyan's** framing of games as decision-making under uncertainty; **Salen and Zimmerman's** three schemas (Rules, Play, Culture) from *Rules of Play*; **Koster's** thesis in *A Theory of Fun* that fun is the sensation of a brain successfully learning a pattern — which predicts, usefully, that a game stops being fun exactly when the player has fully learned it.

---

## 3. Systems design

Systems design is the discipline of the numbers and their relationships. It is spreadsheet work before it is anything else.

**The vocabulary:**
- **Resource** — anything countable that the player accumulates or spends: health, ammo, gold, time, action points, attention.
- **Source** and **sink** — where a resource enters the economy and where it leaves. Every resource needs both. An economy with sources and no sinks inflates; the reverse starves.
- **Converter** — a mechanism that turns one resource into another (a crafting bench, a shop, a skill tree).
- **Feedback loop** — **positive** loops amplify a lead (getting richer lets you get richer: *Monopoly*, snowballing MOBA lanes); **negative** loops compress differences (rubber-banding in *Mario Kart*, comeback mechanics, catch-up XP). Positive loops shorten games and create decisive moments; negative loops extend games and preserve tension. Most well-designed competitive games use both — a positive loop within a round, a negative loop across rounds.
- **Emergence** — behaviour the designer did not encode, arising from simple rules interacting. *Dwarf Fortress*, *Breath of the Wild*'s chemistry system, *Minecraft* redstone, *Deus Ex*'s solution space. Emergence is bought with *orthogonality*: mechanics that each do one thing and interact with everything.
- **Orthogonality** — two mechanics are orthogonal if neither can substitute for the other. Non-orthogonal mechanics (three guns that do the same thing at different numbers) add content but not depth.
- **Depth vs complexity** — depth is the number of *meaningfully different* strategies; complexity is the number of rules. *Go* has near-zero complexity and enormous depth. The design goal is always maximum depth per unit of complexity.
- **Dominant strategy** — an option that is always correct. Its existence collapses the decision space and is the primary failure mode of systems design.

**Balance is not fairness.** It is the property that no option is either always correct or never correct. The practical method: define what each option is *for* (a role, a situation, a playstyle), then tune so each option wins in its intended situation and loses outside it. A rock-paper-scissors skeleton underneath a complex system is usually what makes it comprehensible.

**Case: *Elden Ring*** (FromSoftware, 2022). Its systems design succeeds by making almost every build viable and almost nothing mandatory: stat allocation, weapon scaling, ashes of war, spirit summons, and the open structure that lets a stuck player go elsewhere. The difficulty is high but the *system* is permissive — the design absorbs player disagreement rather than forcing compliance.

---

## 4. Economy and progression design

**The progression question is: what changes, and does the player feel it?**

Three progression types, usually combined:
1. **Player skill** — nothing in the game changes; the player gets better. *Counter-Strike*, *Super Meat Boy*, *Tetris*. The purest form and the hardest to sustain commercially.
2. **Character power** — numbers go up. Levels, gear, stats. Easy to author, easy to over-serve; produces the "treadmill" complaint when the world scales with the player and nothing actually changes.
3. **Player capability** — the verb set expands. A new traversal ability, a new tool, a new mechanic. *Metroid*, *Hollow Knight*, *Portal*. The most satisfying and the most expensive, because every new verb must be supported by every subsequent piece of content.

**Progression curves.** Linear costs with linear rewards feel flat. The standard shape is **exponential cost against linear-to-sublinear reward**, which produces a natural taper and lets the designer decide where the game ends. Publish the curve as a chart, not a table; the shape is the design.

**Economy design checklist:**
- Every resource has at least one source and one sink, and you can state both.
- The *rate* of each faucet and drain is written down, per unit of play time.
- There is a designed answer to "what does a player with too much of this do?" — if the answer is nothing, you have inflation.
- Currency count is minimal. Every additional currency is a partition that makes the player's mental model harder and the designer's balancing job combinatorially worse. Free-to-play games routinely run five and it is almost always a monetisation decision, not a design one.
- Time is a resource. Anything gated by real time is spending the player's attention budget.

**Case: *Diablo* series.** The loot economy is the reference implementation: a source (drops with a designed rarity curve), a sink (crafting, gambling, repair), a positive feedback loop (better gear kills faster, killing faster yields more gear) held in check by rising difficulty tiers, and a periodic reset (seasons) that restores scarcity. Every live-service loot game since is a variation on it.

---

## 5. Difficulty and flow

**Flow** (Csíkszentmihályi) describes the band between anxiety (challenge exceeds skill) and boredom (skill exceeds challenge). Player skill rises during play, so a *fixed* challenge level slides out of the band; difficulty must rise with it. The "flow channel" diagram is a design tool: plot intended challenge over time, plot expected player skill over it, and look for where they diverge.

But flow is not the only target. Deliberate excursions matter:
- **Below the channel** (easy stretches) provide recovery and let the player feel mastery of something previously hard. *Doom Eternal*'s brief lulls; *Half-Life 2*'s downtime between engagements.
- **Above the channel** (spike difficulty) creates memorable moments. FromSoftware's entire design thesis is a controlled excursion above the channel with an exceptionally cheap retry.

**Difficulty is multi-dimensional.** Separate them and tune independently:
- **Execution difficulty** — reaction time, precision, timing.
- **Cognitive difficulty** — understanding what to do.
- **Strategic difficulty** — planning several steps ahead.
- **Knowledge difficulty** — knowing a thing you can only learn by dying to it.
- **Punishment severity** — what you lose when you fail, and how long it takes to retry.

FromSoftware's games are high on execution and knowledge, moderate on strategic, and — critically — very cheap on *retry time*. *Celeste* is extremely high on execution and near-zero on punishment (instant respawn at screen start), which is why it is brutal and beloved simultaneously. The single most reliable difficulty improvement in any game is **reducing the time between failure and the next attempt.**

**Accessibility and difficulty options** are now standard practice: separate assist options (aim assist, slowdown, invincibility) from difficulty tiers, and let players mix. *Celeste*'s Assist Mode is the reference implementation — it explains what each toggle does, states that the game was designed to be challenging, and then gets out of the way.

---

## 6. Feedback, game feel and juice

**Game feel** is the tactile quality of real-time interaction: the sense that your input has weight and consequence. Steve Swink's book decomposes it into **real-time control**, **simulated space**, and **polish**. It is where a technically correct game becomes a good one, and it is almost entirely invisible in a design document.

**The components:**
- **Input responsiveness** — frames between button and visible response. Under ~100 ms feels immediate. Buffering (accepting an input slightly before it can be executed) and coyote time (allowing a jump a few frames after leaving a ledge) are lies the game tells that make it feel *more* fair, not less.
- **Animation** — anticipation, follow-through, and the willingness to cancel animation for responsiveness. A perfectly animated 400 ms attack wind-up feels worse than an ugly 120 ms one.
- **Camera** — screen shake scaled to impact, subtle punch-in on hit, follow lag and lead, and a deadzone so small movements don't move the world.
- **Hit feedback** — hitstop/hitlag (freezing both parties for 2–6 frames on impact), flash, knockback, particles, decals.
- **Audio** — layered impact sounds with pitch variation to avoid machine-gun repetition; a distinct sound for every state change.
- **Haptics** — controller rumble mapped to event weight.
- **UI feedback** — numbers popping, bars draining with easing rather than snapping, resources animating to their destination.

**"Juice"** is the term for stacking these. The canonical demonstration is Martin Jonasson and Petri Purho's talk *Juice It or Lose It* (2012), which takes a bare Breakout clone and adds twenty layers of feedback without changing a single rule. The lesson is that a large share of what players call "feel" is polish that costs days, not months.

**A discipline worth adopting:** for every player action, list the feedback channels it fires — visual, audio, haptic, UI, camera, world. Actions that fire only one channel feel thin.

---

## 7. Level design

Level design did not exist as a separate profession through the 1970s–2000s; a single programmer laid out the maps. It emerged as environments grew and now typically requires **both visual-artist and game-designer skills**. Early shipped level editors — *Lode Runner* (1983) and *Dandy* (1983) — began the tradition of players making levels that eventually produced the entire modding pipeline.

### The process

Concept sketch → **blockout / whitebox** (grey geometry, correct scale and metrics, playable) → gameplay pass (enemies, items, spawn points, scripted events) → **art pass** → lighting → optimisation and streaming setup → bug pass. Blockout must be playtested and approved *before* any art is made; art on an unfun level is money burned. Scale metrics — character height, jump distance, cover height, door width, corridor width — must be locked before blockout begins and published to the whole team.

### Principles

**Readability.** A player should understand at a glance where they can go, where they cannot, what is dangerous and what is interactive. Achieved through consistent material language (this metal means "climbable"), silhouette, lighting contrast and colour. The much-mocked "yellow paint" convention is a crude solution to a real problem; the sophisticated version does the same work with light and composition.

**Sightlines and composition.** Frame the objective. The player should see where they are going before they can reach it. Use leading lines, framing geometry, and a lit landmark at the vanishing point. *Half-Life 2* does this relentlessly — the Citadel is visible from almost everywhere in City 17, which orients the player across a dozen hours without a single map screen.

**Affordances.** Shape communicates function. A ledge that can be climbed should look climbable in a way that no un-climbable ledge does. Establish the vocabulary early and never violate it.

**Pacing.** A level is a sequence of intensity. The standard shape is a sawtooth: tension → engagement → resolution → recovery → higher tension. Flat intensity, high or low, exhausts or bores. Plot the intended curve before building.

**Teaching without tutorials.** The canonical sequence, from *Portal*:
1. **Introduce the mechanic in a safe room** where the player cannot fail and cannot proceed without using it.
2. **Combine it** with a mechanic they already have.
3. **Complicate it** — the same idea under time pressure, at range, or with an obstruction.
4. **Test it** — a chamber that requires full understanding, with no hand-holding.
5. **Subvert it** — break the rule the player has learned, which is only possible because you taught it properly (*Portal*'s escape from the test chambers is exactly this).

*Portal*'s lineage is instructive: it originated as *Narbacular Drop*, a **2005 DigiPen student project** whose team Valve hired; *Portal 2*'s paint mechanic came from *Tag: The Power of Paint*, another **2008 DigiPen student game**.

**The *Half-Life 2* lessons**, stated concretely:
- **Never take control away** unless you have to. HL2's commentary tracks describe designing for a player who is never cut away from.
- **Lead the eye with light.** Valve's playtests showed players walk toward the brightest point in a scene; level designers used it as a navigation system.
- **Use the physics gun as a teacher.** The gravity gun is introduced through a dog-and-ball fetch sequence with no text, teaching pickup, aim and launch in ninety seconds.
- **Playtest with people who have never played it, and watch where they get stuck.** Valve's design culture — the studio has run a **flat organisation** with open allocation since its founding in 1996 — is built around iterating on observed player behaviour rather than argument.
- **Repeat a space with a changed meaning.** Ravenholm, the coast, Nova Prospekt — each returns to earlier vocabulary with new stakes.

**Multiplayer level design** adds: symmetry vs asymmetry (competitive maps are usually mirrored to remove spawn advantage), flow and choke points, sightline length distribution (a map that is all long lanes favours one weapon class), verticality, cover density, spawn safety and rotation timings, and the "three-lane" convention that most MOBA and arena shooter maps ultimately reduce to.

**Open-world level design** replaces linear pacing with **points of interest density**, sightline landmarks, traversal cost, and "compass" design — *Breath of the Wild*'s method of placing a visible curiosity in every direction so any wandering choice is rewarded within about a minute.

---

## 8. Narrative design and environmental storytelling

**Narrative design ≠ writing.** A writer produces dialogue and prose; a narrative designer produces the *structure that delivers it*: quest architecture, branching and its costs, pacing against gameplay, barks and ambient dialogue systems, codex and lore delivery, cutscene budget, and the alignment between what the mechanics say and what the story says.

**Ludonarrative dissonance** is the term for that alignment failing — a protagonist characterised as reluctant who kills three hundred people in the first hour. The fix is rarely more writing; it is usually changing the mechanic or changing the character.

**Delivery methods, ranked by how well they respect player agency:**
1. **Environmental storytelling** — the space tells the story. Two skeletons, a locked door and a note. *Dark Souls*' entire narrative method; *Gone Home*; *What Remains of Edith Finch*; *BioShock*'s Rapture. Cheapest per unit of impact and the most reliably praised.
2. **Systemic/emergent narrative** — the story is produced by systems interacting. *Dwarf Fortress*, *Crusader Kings*, *RimWorld*. Players tell each other these stories, which is free marketing.
3. **Barks and ambient dialogue** — characters commenting on player state. *Hades* runs thousands of context-specific lines that respond to run history, weapon, boons and deaths; it is the reason a repetitive roguelike sustains dozens of hours of narrative interest.
4. **In-world text and audio logs** — cheap, skippable, easy to overuse.
5. **Playable narrative sequences** — story delivered while the player retains control. *Half-Life*'s entire method.
6. **Cutscenes** — highest control, lowest agency. Use for what only they can do.

**Branching structure.** Full branching is combinatorially unaffordable. The workable patterns are: the **gauntlet** (choices that change flavour and immediate outcome but reconverge), the **branch-and-bottleneck** (real divergence that reconverges at act boundaries, with state carried forward as flags), and the **quest web** (parallel content with a state-tracking system rather than a branching tree). *Baldur's Gate 3* is the current high-water mark for genuinely divergent state tracking, and the reason it took Larian — founded 1996, headquartered in Ghent with six further studios — three years of early access and a very large team.

---

## 9. Multiplayer and social design

**Design the social experience, not just the mechanics.** The questions:
- **Synchronous or asynchronous?** Asynchronous social features (*Dark Souls*' messages and bloodstains, *Death Stranding*'s shared structures) deliver a sense of other people at a fraction of the technical and moderation cost.
- **Cooperative or competitive?** And within co-op, *interdependent* (each player has a distinct necessary role) or *parallel* (everyone does the same thing near each other)?
- **What does a player do to another player?** Every affordance you give will be used to grief. Design the grief case explicitly.
- **Matchmaking and skill.** MMR/Elo/TrueSkill systems, the tension between match quality and queue time, and the ethical question of engagement-optimised matchmaking (EOMM) — matchmaking tuned to retention rather than fairness.
- **Toxicity is a design problem, not a moderation problem.** Riot's published work on *League of Legends* behaviour systems is the most-studied case: reporting, the (now-retired) Tribunal, chat restrictions and honour systems. Design decisions that reduce toxicity include limiting negative communication channels, removing information that enables blame, and making punishment visible.
- **Onboarding a live game.** A multiplayer game with a five-year-old player base is unenterable without deliberate design — bot matches, restricted starting modes, mentor systems.
- **Retention through social debt.** Guilds, clans and scheduled group content retain players far more strongly than any content cadence, because the obligation is to people.

---

## 10. Monetisation models and their ethics

**The models:**

| Model | Mechanism | Design consequence |
|---|---|---|
| Premium (buy once) | Single upfront price | Design serves the experience; revenue depends on reviews and word of mouth |
| Premium + DLC/expansion | Paid content additions | Encourages content that is separable and post-launch resourcing |
| Season pass / battle pass | Time-limited tiered rewards for play | Encourages daily/weekly engagement design; creates obligation |
| Cosmetic-only F2P | Free game, paid appearance items | Cleanest F2P ethics; requires a huge audience and strong character/identity design |
| F2P with progression sales | Pay to skip or accelerate | Directly incentivises making unpaid progression worse |
| Loot boxes / gacha | Randomised paid rewards | Regulated or banned in several jurisdictions; strongest revenue, weakest ethics |
| Subscription | Recurring access | Encourages steady content cadence; punishes gaps |
| Ad-supported | Interstitial/rewarded video | Almost exclusively mobile; shapes session length directly |

**The mechanisms that raise ethical questions**, named plainly because they are named in design documents:
- **Premium currency with non-matching denominations** — you buy 500 gems, the item costs 480, leaving a residue that only another purchase resolves.
- **Artificial scarcity and FOMO** — limited-time offers, rotating shops, expiring passes.
- **Energy/stamina gates** — the game stops until you wait or pay.
- **Pay-to-win** in competitive contexts.
- **Loss aversion framing** — "your streak will end", "your crops will wither".
- **Gacha pity systems** — a guaranteed drop after N pulls; simultaneously a consumer protection and a mechanism that makes spending feel rational.
- **Targeting whales** — a small percentage of spenders providing the majority of revenue, which turns "optimise revenue" into "optimise for the most vulnerable spenders".

**Where the line is.** A workable professional test: *would you be comfortable explaining this mechanic, in full, to the player who spends the most on it?* Regulatory pressure has tightened materially — several jurisdictions have restricted or banned loot boxes, disclosure of drop rates is mandatory on major platforms and in several countries, and consumer-protection authorities have pursued dark patterns in games. The 2023–26 contraction has also made the pure engagement-maximising live-service model look considerably less safe commercially than it did in 2021: several very large live-service bets failed outright, including studio-ending failures.

**The counter-case:** premium, finite, well-made games sold extremely well through the contraction. *Stardew Valley* passed **50 million copies by February 2026**. *Hollow Knight: Silksong* sold **over 7 million copies by mid-December 2025** with over 5 million players in three days. *Hades II* (Supergiant, seven original staff still with the studio) released to acclaim in September 2025. None of these monetise beyond a single purchase.

---

## 11. Playtesting methodology

**Types, by what they answer:**

| Type | Question | Who | When |
|---|---|---|---|
| Kleenex / first-time-user test | Can a new player understand and start? | 5–8 fresh players, never reused | Every milestone |
| Usability test | Can they complete this specific task? | ~5 per round | Continuously |
| Focus / fun test | Is it enjoyable, and where does interest drop? | 8–15 | Vertical slice onward |
| Balance test | Are the numbers right? | Many, or telemetry | Alpha onward |
| Longitudinal test | Does it hold up over 20 hours? | Small panel over weeks | Beta |
| Telemetry / analytics | What are thousands of players actually doing? | All players | Beta and live |

**Method.** Recruit players who match the target audience and who have not seen the build. Give a starting condition, not instructions. **Do not help.** Do not explain. Watch hands and face as much as the screen. Note *where they stop*, *where they look*, and *what they say aloud* — but weight what they do far above what they say. Debrief with open questions after, never during.

**The cardinal rules:**
1. **Players are excellent at identifying problems and terrible at proposing solutions.** "The boss is too hard" may mean the boss is too hard, or the tutorial failed, or the camera obscures the tell, or the previous room drained resources.
2. **Never argue with a playtester.** If you have to explain it, it does not work.
3. **The designer must not moderate their own test** if it can be avoided; you will lead.
4. **One change at a time between tests**, or you cannot attribute the difference.
5. **Fresh eyes are a depleting resource.** Every person who plays your game becomes useless for first-time testing forever. Budget them.

---

## 12. Prototyping

**Match fidelity to the question.**

- **Paper prototype** — for systems, economy and turn structure. A card game version of your RPG combat can be balanced in a week for the cost of a printer. *Civilization*, *XCOM* and countless others were designed this way first.
- **Grey-box digital prototype** — for game feel, movement, camera and moment-to-moment mechanics. No art. Programmer-art capsules and cubes. If the prototype is fun with cubes, the game will be fun with art; the reverse is never true.
- **Vertical slice** — one small section at final quality, used to prove the whole and to sell it internally or to a publisher. Expensive; do not build one before the grey-box prototype is fun.
- **Horizontal slice** — the whole game at low quality, used to prove structure and pacing.
- **Throwaway vs evolutionary** — decide up front. A prototype you intend to keep will be built more slowly and will still probably need rewriting. Prefer throwaway.

**The rule:** a prototype exists to answer one question and should be abandoned the moment it has. Prototypes that acquire features are projects, and projects that began as prototypes carry their shortcuts into shipping code.

---

## 13. The design document and its modern replacements

**The 200-page GDD is dead**, and deserved to be. It was obsolete the day it was finished, nobody read past page 20, and its comprehensiveness created a false confidence that the design was settled.

**What replaced it:**

- **A one-page pitch.** Elevator line, pillars, target aesthetics (in MDA terms), reference games, target platform and audience, and what makes it different. If this page is not compelling, nothing downstream will be.
- **Design pillars** — three to five sentences that every subsequent decision is tested against. Pillars must be *exclusionary*: "immersive and fun" is not a pillar because nothing fails it. "The player is always vulnerable" is, because it kills your invincibility power-up.
- **A living wiki** (Confluence, Notion, an in-repo markdown tree) with one page per system, versioned, owned by a named person, and updated as the system changes.
- **The macro chart / beat chart** — a spreadsheet of the whole game: every level or region, the mechanics introduced, the intended intensity, the narrative beat, the estimated play time, and the assets required. This is the single most useful document in production; it is what makes scope visible.
- **Feature briefs / one-pagers** — a short document per feature: the problem, the proposed mechanic, how it is taught, how it is tested, what it costs, and how you will know it worked.
- **The build itself** — increasingly the primary design document. A playable answer beats a written argument.
- **Recorded playtests and telemetry dashboards** — the evidence layer.

**What still needs writing down:** anything that must be consistent across many people (metrics, naming conventions, UI rules, narrative canon, the tuning philosophy) and anything that must survive staff turnover.

---

## 14. Metrics-driven design

**What telemetry is genuinely good at:** locating problems. Heatmaps of player deaths reveal which corner of which level is broken. Funnel drop-off shows which tutorial step loses people. Session length distributions show whether the session loop resolves. Completion rates per level show pacing failures. Retention curves show whether the game has a reason to return.

**What telemetry is bad at:** telling you *why*, and telling you what to build. It measures what exists. It cannot indicate a game you have not made. Every metric optimisation converges on a local maximum, which is why metric-led design produces a genre of games that are individually well-tuned and collectively identical.

**Core metrics by category:**
- **Acquisition** — installs, store conversion rate, CPI.
- **Activation** — tutorial completion, time to first meaningful action.
- **Retention** — D1/D7/D30 (mobile benchmarks commonly cited around 40/20/10% for a healthy game, though this varies enormously by genre; treat any specific benchmark as `needs-verification`).
- **Engagement** — DAU/MAU, session length, sessions per day, core-action frequency.
- **Progression** — completion rate per level or chapter, average attempts per encounter, drop-off point distribution.
- **Monetisation** — conversion to payer, ARPDAU, ARPPU, LTV.
- **Health** — crash-free session rate, frame time percentiles, load times.

**The discipline that makes it safe:** pair every optimisation metric with a **guardrail** — refund rate, complaint volume, long-run (D180) retention, review sentiment. And keep at least one qualitative channel open permanently, because the day your telemetry says everything is fine and your community says the game is dying, the community is right.

---

## Sources

- [MDA framework](https://en.wikipedia.org/wiki/MDA_framework) — Wikipedia
- [Level design](https://en.wikipedia.org/wiki/Level_design) — Wikipedia
- [Valve Corporation](https://en.wikipedia.org/wiki/Valve_Corporation) — Wikipedia
- [DigiPen Institute of Technology](https://en.wikipedia.org/wiki/DigiPen_Institute_of_Technology) — Wikipedia (Narbacular Drop / Tag lineage)
- [Supergiant Games](https://en.wikipedia.org/wiki/Supergiant_Games) — Wikipedia
- [Hollow Knight: Silksong](https://en.wikipedia.org/wiki/Hollow_Knight:_Silksong) — Wikipedia
- [Stardew Valley](https://en.wikipedia.org/wiki/Stardew_Valley) — Wikipedia
- [FromSoftware](https://en.wikipedia.org/wiki/FromSoftware) — Wikipedia
- [Larian Studios](https://en.wikipedia.org/wiki/Larian_Studios) — Wikipedia

## Open questions

- The MDA framework's publication year and venue (commonly cited as the AAAI Workshop on Challenges in Game AI, 2004) were **not** stated on the page fetched; treat the date as `needs-verification`.
- Specific *Half-Life 2* design claims (lighting-as-navigation, the gravity-gun teaching sequence) are drawn from Valve's published developer commentary and widely circulated GDC material, but were not source-fetched here.
- Mobile retention benchmarks (D1/D7/D30 ≈ 40/20/10%) are practitioner rules of thumb and are explicitly unverified.
- Jesse Schell's elemental tetrad, Koster's theory of fun, Bartle's taxonomy, Swink's *Game Feel* decomposition and Csíkszentmihályi's flow model are described from the primary books, which were not fetched in this pass.
- The specific regulatory status of loot boxes by jurisdiction was not verified and changes frequently; do not rely on the general statement above for compliance purposes.
