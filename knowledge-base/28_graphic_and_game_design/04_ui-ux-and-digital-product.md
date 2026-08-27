---
id: gxgd.uiux
title: UI/UX and digital product design
domain: 28_graphic_and_game_design
tags: [ux, ui, user-research, personas, jobs-to-be-done, information-architecture, interaction-design, wireframing, prototyping, design-systems, design-tokens, material-design, apple-hig, fluent, figma, usability-testing, accessibility, motion, handoff, product-metrics]
jurisdiction: global
status: stable
confidence: high
updated: 2026-08-25
applies_to: "Practice as of August 2026. WCAG 2.2 as published. Platform guideline specifics change frequently — verify against the vendor doc."
unit_system: metric
sources:
  - {title: "10 Usability Heuristics for User Interface Design", url: "https://www.nngroup.com/articles/ten-usability-heuristics/", publisher: "Nielsen Norman Group", accessed: 2026-08-25}
  - {title: "Nielsen Norman Group", url: "https://en.wikipedia.org/wiki/Nielsen_Norman_Group", publisher: "Wikipedia", accessed: 2026-08-25}
  - {title: "Understanding SC 1.4.3 Contrast (Minimum)", url: "https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html", publisher: "W3C Web Accessibility Initiative", accessed: 2026-08-25}
  - {title: "Design tokens — Material Design 3", url: "https://m3.material.io/foundations/design-tokens/overview", publisher: "Google", accessed: 2026-08-25}
related: [gxgd.overview, gxgd.gd_fundamentals, gxgd.portfolio, gxgd.resources]
---

# UI/UX and digital product design

**Summary.** Product design is graphic design plus three things it does not have: a research obligation, a systems obligation, and a measurement obligation. You are expected to know what users actually do (not what they say), to express your work as reusable components and tokens rather than as compositions, and to be judged on numbers you can be shown at a quarterly review. This file covers the full loop — research, IA, interaction, prototyping, design systems, Figma workflow, testing, accessibility, motion, handoff — and closes with the metrics designers are actually held to.

## Key facts

| Item | Value |
|---|---|
| Nielsen's usability heuristics | **10**, formulated with Rolf Molich 1990, refined **1994** from analysis of 249 usability problems; unchanged since |
| Nielsen Norman Group | founded **28 August 1998** by Jakob Nielsen and Don Norman |
| Usability test sample | ~**5 users** per round finds the majority of issues; run more, smaller rounds rather than one big one |
| WCAG 2.2 AA text contrast | **4.5:1** normal, **3:1** large (≥18 pt / ≥14 pt bold) |
| WCAG 2.2 AA non-text contrast (1.4.11) | **3:1** for UI components and meaningful graphics |
| Minimum touch target | **44×44 pt** (Apple HIG) / **48×48 dp** (Material) |
| Base spacing unit | **8 px** grid with a 4 px half-step is the near-universal convention |
| Material Design current version | **Material Design 3** ("Material You") |
| Material token tiers | reference → system → component; the same tokens used in design, tools and code |
| Doherty threshold | system response under **400 ms** keeps attention engaged |
| Perceived-instant threshold | **100 ms** feels instantaneous; **1 s** keeps flow; **10 s** loses attention (Nielsen/Miller) |

> ⚠️ "The user" is not a person you can ask. Self-reported preference and observed behaviour diverge routinely and predictably. Anything a research participant *says* they would do is a hypothesis; anything you watch them do is evidence. Design the study so you get the second.

---

## 1. User research

### Why it exists

Research answers three questions in order: **who** is this for, **what** are they trying to accomplish, and **what is currently in the way**. Design without those answers is guessing with good typography.

### Methods, and when to use which

| Method | Question it answers | Sample | Cost |
|---|---|---|---|
| Contextual inquiry / field study | What do people actually do, in situ? | 5–12 | High |
| Semi-structured interview | What are the goals, mental models, workarounds? | 6–12 per segment | Medium |
| Diary study | What happens over time and between sessions? | 8–20 | Medium-high |
| Usability test (moderated) | Can they complete this task with this design? | ~5 per round per segment | Low-medium |
| Unmoderated remote test | Same, at scale, cheaper, less depth | 15–50 | Low |
| Survey | How common is a thing we already know exists? | 100+ for any inference | Low |
| Card sort (open/closed) | How do users group and name concepts? | 15–30 | Low |
| Tree test | Can they find things in a proposed IA? | 30+ | Low |
| Analytics / funnel analysis | Where do people actually drop out? | all users | Low |
| A/B test | Which variant performs better on a chosen metric? | statistically powered | Medium |

**Generative research** (interviews, field studies, diaries) happens *before* design and changes what you build. **Evaluative research** (usability tests, A/B) happens *during and after* and changes how you build it. Teams that only do evaluative research build the wrong thing efficiently.

### Personas and jobs-to-be-done

**Personas** are a communication artefact: a named, archetypal user with goals, context, constraints and behaviours, synthesised from actual research. They fail in two specific ways — when they are invented rather than researched (demographic fiction), and when they describe *who someone is* rather than *what they are trying to do*.

**Jobs-to-be-Done** (Clayton Christensen's framing, and Bob Moesta's practice) fixes the second failure by shifting the unit of analysis from the person to the **job**: "When \_\_\_ [situation], I want to \_\_\_ [motivation], so I can \_\_\_ [expected outcome]." The canonical illustration is the milkshake study — people "hire" a morning milkshake to make a boring commute tolerable and to stay full until lunch, a job that has nothing to do with milkshake-ness. JTBD is better than personas for *prioritisation*; personas are better for *empathy and communication*. Most mature teams use both.

**Adjacent artefacts worth producing:** a **journey map** (stages, actions, thoughts, emotions, pain points, opportunities across a whole end-to-end experience), a **service blueprint** (the journey map plus the backstage systems and staff actions that make each step possible), and an **empathy map**. Produce them only if a decision depends on them.

---

## 2. Information architecture

IA is the structure and naming of content and function. It determines whether people can find things, and it is almost impossible to fix later without breaking URLs, muscle memory and search rankings.

**Core moves:**
- **Inventory** what exists — every page, feature, content type.
- **Card sort** to learn users' own groupings and vocabulary (open sort for discovery, closed sort to validate a proposed structure).
- **Tree test** the proposed hierarchy before designing any screens. A structure that fails a tree test will fail as an interface no matter how it is styled.
- **Name things in the users' words, not the organisation's.** The single most common IA failure is an org chart rendered as a navigation bar.
- **Depth vs breadth** — broad-and-shallow generally beats narrow-and-deep for findability; three levels is a good target for most consumer products.
- **Navigation systems** — global (persistent), local (contextual), utility (account, help), contextual (in-content links), and supplemental (search, sitemap, index). Search is not a substitute for structure; it is a parallel path.
- **Labelling and taxonomy** — a controlled vocabulary, applied consistently, plus a decision about whether categories are exclusive or facets.

**Book:** Rosenfeld, Morville and Arango, *Information Architecture* (the "polar bear book").

---

## 3. Interaction design and patterns

Interaction design specifies behaviour: what happens, when, in response to what, and what the user is told about it.

### Nielsen's 10 usability heuristics (1994)

Still the best checklist in the discipline. Run any interface against all ten:

1. **Visibility of system status** — always tell the user what is happening, promptly.
2. **Match between the system and the real world** — speak the user's language, follow real-world conventions.
3. **User control and freedom** — an obvious "emergency exit"; undo and redo.
4. **Consistency and standards** — within the product, and with platform conventions.
5. **Error prevention** — better than good error messages; use constraints, confirmations and sensible defaults.
6. **Recognition rather than recall** — make options and information visible; don't force memory across steps.
7. **Flexibility and efficiency of use** — accelerators for experts that don't burden novices.
8. **Aesthetic and minimalist design** — every extra unit of information competes with the relevant ones.
9. **Help users recognise, diagnose and recover from errors** — plain language, precise problem, constructive next step.
10. **Help and documentation** — ideally unnecessary, but findable and task-focused when needed.

### Patterns that carry most products

**Navigation:** tab bar (3–5 top-level destinations, mobile), navigation rail / sidebar (desktop, 5–15), breadcrumbs (deep hierarchies), hub-and-spoke, wizard/stepper for linear multi-step tasks.

**Data entry:** single-column forms (multi-column forms measurably slow completion), top-aligned labels, inline validation *after* the field loses focus rather than on every keystroke, sensible input types and keyboards on mobile, never placeholder-as-label (it disappears and fails contrast).

**Data display:** tables with sticky headers, sortable columns and a stated default sort; lists with a clear primary/secondary hierarchy; cards for heterogeneous items only; empty states that teach rather than apologise.

**Feedback and state:** the five states every component needs — **default, hover/focus, active/pressed, disabled, loading** — plus at the screen level **empty, loading, partial, error, ideal**. Skeleton screens over spinners for content-shaped waits; optimistic UI where the operation almost always succeeds and is reversible.

**Destructive actions:** confirm only when the action is irreversible; otherwise prefer undo. A confirmation dialog that appears every time is trained away within a week.

**Progressive disclosure:** show the common 80% path; put the rest behind an explicit "advanced" affordance.

**Timing thresholds:** under **100 ms** feels instant, so no feedback is needed; **100 ms–1 s** perceptible but flow is preserved, use a subtle indicator; **1–10 s** requires a determinate progress indicator; over **10 s** requires the ability to do something else. The **Doherty threshold** (~400 ms) is the point below which a system feels like it is keeping up with the user rather than the reverse.

---

## 4. Wireframing and prototyping

**Fidelity is a communication choice, not a stage of maturity.** Choose the lowest fidelity that answers the question you have.

| Fidelity | Answers | Time |
|---|---|---|
| Sketch (paper/whiteboard) | Is the concept right? Are there other concepts? | Minutes |
| Wireframe (grey boxes) | Is the structure and hierarchy right? | Hours |
| Clickable low-fi prototype | Does the flow work? | Hours |
| High-fidelity mockup | Does the visual system hold? | Days |
| Interactive high-fi prototype | Does the interaction and motion feel right? | Days |
| Coded prototype | Does it work with real data, at real speed, on a real device? | Days–weeks |

Two failure modes: **premature polish** (a beautiful mockup makes stakeholders discuss colour when the flow is broken) and **eternal greyness** (a wireframe cannot answer questions about density, contrast or emotional register, and shipping wireframe-thinking produces grey products).

**Crazy 8s** (eight sketches in eight minutes) and the Google Ventures **Design Sprint** structure remain the most reliable ways to generate divergent options fast. The instinct to converge on the first workable idea is the most expensive habit in the discipline.

---

## 5. Design systems

A design system is three things layered: **tokens** (the values), **components** (the reusable behaviour-bearing pieces), and **documentation** (the rules of use). It is a product with users — the designers and engineers of your organisation — and it fails when treated as a library dump.

### Tokens

Design tokens are named values that replace hard-coded numbers, and the essential property is that **the same tokens are used in designs, tools and code**. Material Design 3 formalises three tiers, which is the model most in-house systems copy:

1. **Reference tokens** — the raw palette. `md.ref.palette.primary40`. No semantics; just "this is the colour". Never used directly in a component.
2. **System tokens** — semantic roles. `md.sys.color.surface`, `md.sys.color.on-primary`, `md.sys.typescale.body-large`. These carry *meaning* and are what designers and engineers reference. Theming (light/dark, brand variants, density) works by re-pointing system tokens at different reference values without touching a single component.
3. **Component tokens** — per-component overrides where a component genuinely needs its own value. `md.comp.filled-button.container-color`. Use sparingly; a system where every component has its own tokens has no system.

**Token categories to define:** colour (with a full neutral ramp plus semantic roles and their `on-` foreground pairs), typography (family, size, line-height, weight, letter-spacing as a single named scale step), spacing (multiples of 4/8), sizing, border radius, border width, elevation/shadow, opacity, motion duration, motion easing, z-index, and breakpoints.

**Practical rule:** generate colour ramps in **OKLCH** so lightness steps are perceptually even, and *contrast-test every semantic pair* at definition time, not at use time. A token system whose `on-surface-variant` fails 4.5:1 has shipped an accessibility bug into every screen simultaneously.

### Components

Define each component with: **anatomy** (named parts), **variants** (fill, outline, ghost…), **sizes**, **states** (default/hover/focus/active/disabled/loading/error), **content rules** (max characters, truncation behaviour, what happens with no content), **accessibility contract** (role, keyboard behaviour, ARIA, focus order), **do/don't examples**, and **when *not* to use it** — the last being the most valuable and most often omitted.

Structure components in tiers (an "atomic design"-style hierarchy is common, though the vocabulary matters less than the discipline): primitives → composed components → patterns → page templates.

### The three reference systems

| System | Owner | Platform | Character |
|---|---|---|---|
| **Material Design 3** | Google | Android, web, cross-platform | Fully specified, token-first, dynamic colour from a source colour, strong accessibility defaults. The most complete public system; also the most opinionated aesthetically. |
| **Apple Human Interface Guidelines (HIG)** | Apple | iOS, iPadOS, macOS, visionOS, watchOS | Guidance rather than a component library; assumes you use system controls. Strong on ergonomics (44 pt targets), platform idiom and typography (SF, Dynamic Type). |
| **Fluent (Fluent 2)** | Microsoft | Windows, Microsoft 365, web | Enterprise-oriented, dense-data-capable, strong theming and high-contrast support. |

Study all three even when building your own: they encode decades of platform usability testing you cannot afford to repeat.

### Building your own

Sequence that works:
1. **Audit** the existing product — screenshot every button, input and colour. The inventory is the argument for the system.
2. **Define tokens first**, not components. Colour ramp, type scale, spacing scale.
3. **Build the 10 components that cover 80% of screens**: button, input, select, checkbox/radio, link, card, modal, table row, nav item, toast.
4. **Document as you go**, in the same place engineers already look (Storybook, an internal site, or Figma with a linked code reference).
5. **Version and communicate.** Semantic versioning, changelog, deprecation policy.
6. **Measure adoption** — percentage of production UI using system components is the system's own primary metric.

**Governance is the hard part**, not the design. Decide who can add a component, how a contribution is reviewed, and how an exception is granted. Systems die of unmanaged forks, not of bad buttons.

---

## 6. Figma workflow

Figma is the default tool; the workflow matters more than the feature list.

- **File structure:** separate the *library* file (published components and styles/variables) from *product* files. Never let a product file become a source of truth for a component.
- **Variables** (Figma's token primitive) with **modes** for light/dark, density and brand. Map variables to your token names so design and code share one vocabulary. Variables can be pulled into code via the REST API or a token pipeline (Style Dictionary, Tokens Studio).
- **Auto-layout everywhere.** A frame without auto-layout is a picture, not a design; it will not survive content change or translation.
- **Component properties** (boolean, instance swap, text, variant) collapse combinatorial variant explosions into a small property set.
- **Naming convention** — `Category/Component/Variant`, consistent, because the layer panel is the API.
- **Branching** (on paid tiers) for changes to shared libraries; otherwise a duplicate-and-review convention.
- **Dev Mode** for handoff: mark frames Ready for Dev, annotate, and let engineers read spacing, tokens and code snippets directly.
- **FigJam** for research synthesis, journey maps and workshops; keep it out of the design file.
- **Hygiene:** delete detached instances, run a periodic library audit, and keep a single "kitchen sink" page per component showing every state.

Adjacent tools worth knowing in 2026: **Penpot** (open-source alternative, SVG-native), **Framer** (design-to-production web), **Rive** (interactive runtime animation), **Storybook** (component documentation and visual regression), **Maze** / **UserTesting** / **Lookback** (remote testing), **Dovetail** (research repository), **Style Dictionary** (token transformation), **Axe DevTools** / **WAVE** (accessibility audit).

---

## 7. Usability testing

**The method.** Recruit 5 participants matching a defined segment. Give them **tasks**, not questions ("Buy a ticket to Cape Town for next Tuesday", not "What do you think of the booking flow?"). Ask them to think aloud. Do not help. Do not explain. Record screen and voice. Debrief with open questions at the end only.

**Why five.** Each additional participant in a homogeneous segment finds progressively fewer *new* problems; roughly five surfaces the large majority. The right response is not to test more people in one round but to **test five, fix, and test five more**. Test separately per distinct segment.

**What to measure.** Task success (binary or graded), time on task, error count, assists required, and a post-task ease rating (SEQ — Single Ease Question, 1–7). At study level, the **System Usability Scale** (SUS, 10 items, 0–100, ~68 is average) gives a comparable benchmark across rounds.

**Common invalidating mistakes:** leading tasks that name the button; moderator rescuing the participant; testing with colleagues; recruiting from your own power users; running one round at the end of the project when nothing can change; treating a preference statement as a finding.

**Other evaluative methods:** heuristic evaluation (2–3 evaluators independently against Nielsen's 10, then merged), cognitive walkthrough (step through a task asking whether the user would know what to do and whether they would know it worked), accessibility audit, and analytics-driven funnel analysis to locate *where* to test.

---

## 8. Accessibility

The numeric requirements are in `02 §7`. What is specific to product design:

- **Keyboard first.** Every interactive element reachable and operable by keyboard, in a logical order, with a visible focus indicator meeting 3:1 non-text contrast. If it works by keyboard it usually works with a screen reader; the reverse is not true.
- **Semantics before ARIA.** Use the native element. `<button>` beats `<div role="button">` in every respect. The first rule of ARIA is not to use ARIA.
- **Names, roles, values.** Every control must expose an accessible name (visible label, `aria-label`, or `aria-labelledby`), its role, and its current state.
- **Focus management** — moving focus into a modal on open, returning it on close, and announcing dynamic content with a live region.
- **Colour is never the sole signal** (WCAG 1.4.1). Pair colour with an icon, text or shape.
- **Text spacing resilience** (1.4.12) — the layout must survive line-height 1.5×, letter-spacing 0.12em, word-spacing 0.16em without clipping.
- **Motion** — respect `prefers-reduced-motion`; never use motion as the only way to convey a change.
- **Targets** — ≥44×44 pt (Apple) / ≥48×48 dp (Material); WCAG 2.2 SC 2.5.8 adds a 24×24 CSS px minimum at AA.
- **Test with real assistive technology** at least once per release — VoiceOver on iOS/macOS, NVDA or JAWS on Windows, TalkBack on Android. Automated tools catch roughly a third of issues.

Accessibility is also a design *constraint that improves outcomes*: the discipline of sufficient contrast, clear labels, generous targets and keyboard operability produces better interfaces for everyone.

---

## 9. Motion and micro-interaction

Motion in product has four legitimate jobs: **maintain spatial continuity** (where did that come from, where did it go), **direct attention**, **express causality** (this action produced that result), and **express brand character** — in that priority order.

**Durations:** 100–150 ms for small on-screen changes (hover, toggle), 200–300 ms for medium transitions (modal, drawer, page), 300–500 ms for large or full-screen transitions. Anything over 500 ms in a frequently-repeated interaction becomes an irritation by the fiftieth use.

**Easing:** `ease-out` for elements entering (fast start, gentle settle — feels responsive), `ease-in` for elements leaving, `ease-in-out` for elements moving within the view. Linear only for continuous indeterminate motion (spinners, progress). Spring physics for direct-manipulation gestures.

**Micro-interaction anatomy** (Dan Saffer's framing): **trigger** → **rules** → **feedback** → **loops and modes**. The design work is mostly in the feedback: what confirms that the toggle toggled, the message sent, the item saved.

**Choreography:** stagger related elements by 20–50 ms rather than animating everything at once; transform and opacity only (they are GPU-composited); avoid animating layout properties.

**Always** honour `prefers-reduced-motion` with a non-animated equivalent — usually a cross-fade or an instant change.

---

## 10. Handoff to engineering

Handoff is a smell when it is an event. In a working team it is continuous.

**What engineers actually need:**
1. **Tokens, not values.** "spacing-4" not "16px". If the token doesn't exist, that's the conversation.
2. **Every state**, drawn. Empty, loading, partial, error, ideal, plus per-component hover/focus/active/disabled.
3. **Responsive behaviour** — what happens at each breakpoint, what wraps, what truncates, what reorders. Show the breakpoints, not just two extremes.
4. **Content edge cases** — longest realistic string, shortest, zero items, 10,000 items, right-to-left, a name with diacritics.
5. **Interaction spec** — triggers, transitions, durations, easing, and what happens on failure.
6. **Accessibility contract** — keyboard behaviour, focus order, roles and names, announcements.
7. **A named decision owner** for the questions that will arise, because they will.

**Practices that work:** sit in on sprint planning; review the built UI in a staging environment against the design, not against a screenshot; keep a shared "design debt" backlog; and accept that a component built once in code and referenced everywhere beats a pixel-perfect mockup of it.

---

## 11. The metrics designers are actually judged on

This is the part design education omits and every product review depends on.

**Product-level (what leadership watches):**
- **Activation** — the proportion of new users reaching a defined first-value moment, and time to reach it.
- **Retention** — D1/D7/D30 or W1/W4 cohort retention curves; the shape (does it flatten?) matters more than any single number.
- **Engagement** — DAU/MAU ratio ("stickiness"), sessions per user, core-action frequency.
- **Conversion** — funnel step-through rates, and the drop-off you own.
- **Churn** and its inverse, **NRR** (net revenue retention) in B2B.
- **Task success rate** and **time on task** for workflow products.
- **Support contact rate** per 1,000 sessions for the flows you designed — a direct, unarguable design metric.
- **Performance** — Core Web Vitals (LCP, INP, CLS) on web; frame rate and cold-start time on native. Designers own CLS and a large share of LCP.

**Experience-level:**
- **SUS** (System Usability Scale, 0–100, ~68 average), **SEQ** (per-task, 1–7), **CSAT**, **NPS** (widely criticised as a diagnostic but widely used as a tracker).
- **HEART framework** (Google): **H**appiness, **E**ngagement, **A**doption, **R**etention, **T**ask success — each with Goals → Signals → Metrics. The most useful bridge between "design quality" and "a number in a dashboard".
- **Accessibility conformance** — automated violations per page, plus manual audit findings closed.

**Design-org-level:**
- **Design system adoption** — percentage of production UI built from system components.
- **Cycle time** from concept to ship.
- **Rework rate** — how often designs change after development starts.

**Two warnings.** First, a metric a designer cannot influence is not their metric; refuse ownership of revenue you don't touch. Second, metric-only design converges on dark patterns — the fastest way to raise a conversion rate is usually to make cancelling harder. Pair every optimisation metric with a **guardrail metric** (complaint rate, refund rate, unsubscribe rate, long-run retention) that catches the harm.

---

## Sources

- [10 Usability Heuristics for User Interface Design](https://www.nngroup.com/articles/ten-usability-heuristics/) — Nielsen Norman Group
- [Nielsen Norman Group](https://en.wikipedia.org/wiki/Nielsen_Norman_Group) — Wikipedia
- [Understanding SC 1.4.3 Contrast (Minimum)](https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html) — W3C Web Accessibility Initiative
- [Design tokens — Material Design 3](https://m3.material.io/foundations/design-tokens/overview) — Google

## Open questions

- The Material Design 3 tokens page returned only metadata to automated fetch; the three-tier structure and naming above is stated from the token model as documented publicly and should be re-verified against the live page.
- Apple HIG and Microsoft Fluent pages were not fetched in this pass; the 44 pt / 48 dp target figures and platform characterisations are from established convention and are `needs-verification`.
- The "5 users" figure and the SUS average of 68 are widely used practitioner benchmarks (Nielsen 2000; Sauro & Lewis) that were not verified against their primary sources here.
- Doherty threshold (400 ms) and the 100 ms / 1 s / 10 s response-time bands derive from Miller (1968) and Nielsen (1993) and were not re-verified.
- WCAG 2.2 SC 2.5.8 target-size minimum (24×24 CSS px at AA) was not fetched directly.
