---
id: sedef.psychology
title: The psychology of influence — why social engineering works
domain: 33_social_engineering_defence
tags: [psychology, influence, cialdini, milgram, asch, heuristics, cognitive-bias, truth-default-theory, replication-crisis, decision-fatigue, security-awareness]
jurisdiction: global
status: stable
confidence: medium
updated: 2026-08-25
sources:
  - {title: "Robert Cialdini", url: "https://en.wikipedia.org/wiki/Robert_Cialdini", publisher: "Wikipedia", accessed: 2026-08-25}
  - {title: "Milgram experiment", url: "https://en.wikipedia.org/wiki/Milgram_experiment", publisher: "Wikipedia", accessed: 2026-08-25}
  - {title: "Asch conformity experiments", url: "https://en.wikipedia.org/wiki/Asch_conformity_experiments", publisher: "Wikipedia", accessed: 2026-08-25}
  - {title: "Truth-default theory", url: "https://en.wikipedia.org/wiki/Truth-default_theory", publisher: "Wikipedia", accessed: 2026-08-25}
  - {title: "Confidence trick", url: "https://en.wikipedia.org/wiki/Confidence_trick", publisher: "Wikipedia", accessed: 2026-08-25}
  - {title: "Phishing in Organizations: Findings from a Large-Scale and Long-Term Study", url: "https://arxiv.org/abs/2112.07498", publisher: "Lain, Kostiainen & Čapkun, IEEE S&P 2022", accessed: 2026-08-25}
  - {title: "Telling users to avoid clicking bad links still isn't working", url: "https://www.ncsc.gov.uk/blog-post/telling-users-to-avoid-clicking-bad-links-still-isnt-working", publisher: "UK NCSC", accessed: 2026-08-25}
related: [sedef.overview, sedef.taxonomy, sedef.human_controls]
---

# The psychology of influence — why social engineering works

**Summary.** Social engineering is applied social psychology used against the target's interest. The mechanisms are not exotic: they are the ordinary heuristics that let people cooperate at scale — deference to authority, conformity to a group, reciprocation of favours, consistency with prior commitments, liking, perceived scarcity, and above all a default assumption that other people are telling the truth. Understanding these mechanisms matters for defenders for two practical reasons: it lets you build training that explains *why* rather than listing red flags, and it tells you which controls to build, because a control that depends on a person overriding a deep heuristic under time pressure is a control that will fail. This file also states honestly which of the classic findings have survived replication and which have not — an awareness programme built on discredited psychology loses credibility the moment a curious employee looks it up.

> ⚠️ This file describes influence mechanisms so that defenders can recognise and blunt them. It is not a persuasion manual, and it deliberately gives no scripts, wordings or sequencing advice.

## Key facts

| Finding | Headline result | Replication status |
|---|---|---|
| Cialdini's principles of influence | Six principles (reciprocity, commitment/consistency, social proof, authority, liking, scarcity), *Influence* 1984; a seventh, **unity**, added in *Pre-Suasion* (2016) | Framework is a synthesis, not a single experiment; individual underlying studies vary widely in robustness |
| Milgram obedience studies (1961, Yale) | 65% of participants administered the maximum 450 V; all continued to at least 300 V | Burger's 2009 ethically-modified partial replication (stopping at 150 V) found obedience rates "virtually identical". Gina Perry's 2012 archival work argues only about half of participants fully believed the setup, and of those, 66% disobeyed |
| Asch conformity (1950s) | 74% of participants conformed to an obviously wrong majority at least once; about one-third of critical-trial responses conformed; 26% never conformed | Robust paradigm; Bond & Smith's 1996 meta-analysis established cross-cultural variation while confirming the effect |
| A single dissenting ally | Conformity fell to about 5% | Replicated; the practical basis for "two-person verification" |
| Truth-default theory (Levine) | People default to believing others are honest; human deception-detection accuracy sits around 50–60% | The ~54% mean accuracy result is one of the better-replicated findings in the deception literature |
| Employees as a detection sensor | Practical at scale over 15 months with 14,000+ employees | Lain, Kostiainen & Čapkun, IEEE S&P 2022 |
| Embedded training delivered at the moment of a simulated failure | Did **not** make employees more resilient; may increase susceptibility | Same study; see file `05` for the fuller evidence picture |

## 1. Cialdini's principles, and what they rest on

Robert Cialdini's *Influence: The Psychology of Persuasion* (1984) synthesised three years of participant observation inside sales, fundraising and telemarketing organisations with the experimental literature of the day. He identified six "weapons of influence"; a seventh, **unity**, was added in *Pre-Suasion* (2016) and is glossed as: the more we identify ourselves with others, the more we are influenced by them.

For defenders the value of the framework is diagnostic. After an incident, ask: *which lever was pulled?* The answer usually tells you which control was missing.

**Reciprocity.** People feel obliged to return favours, including unrequested ones. In an attack this appears as an unsolicited gift, a piece of "helpful" information, a favour done for the target before anything is asked. The victim experience is a vague sense of owing something. *Defensive read:* an unsolicited benefit arriving immediately before a request is a structural indicator, independent of content.

**Commitment and consistency.** Once a person has taken a small step, they experience pressure to remain consistent with it. Attacks exploit this by beginning with a request so small it is unreasonable to refuse — confirming a name, acknowledging an email — and escalating. *Defensive read:* the fact that you have already engaged with a party is not evidence that the party is legitimate. Verification must be independent of the conversation so far.

**Social proof.** In uncertainty, people look to what others are doing. Attacks manufacture it: "the rest of the finance team has already signed off", forged colleague endorsements, fabricated review counts, or in the Arup deepfake case (file `07`) an entire video call full of apparently-real colleagues. *Defensive read:* social proof presented *by the requester* is worthless. Only independently observed consensus counts.

**Authority.** People comply with perceived legitimate authority, and with its symbols — titles, uniforms, letterheads, domain names, badge lanyards. This is the single most-used lever in BEC and in helpdesk attacks.

**Liking.** People say yes to people they like, and liking is generated cheaply by similarity, compliments, cooperation toward a shared goal, and physical attractiveness. Romance fraud is liking industrialised.

**Scarcity.** Opportunities appear more valuable as they become less available. Combined with time pressure, scarcity is what removes deliberation. Loss framing is stronger than gain framing — Kahneman and Tversky's prospect theory establishes that losses loom roughly twice as large as equivalent gains, which is why "your account will be suspended" outperforms "claim your reward."

**Unity.** Shared identity — same team, same nationality, same alma mater, same faith — converts an outsider into an insider. Recruitment and insider-solicitation attacks lean on it heavily.

**Honest caveat on the framework.** Cialdini's six principles are a *taxonomy synthesised from* the mid-century social psychology literature, not a single validated instrument. Some of the underlying studies are strong (Asch, the door-in-the-face and foot-in-the-door literatures have been replicated many times); others come from an era with small samples and flexible analysis. Use the framework as a diagnostic vocabulary, which is what it is good for, and do not present it in training as though each principle carried a single decisive experiment behind it.

## 2. Authority: the Milgram work and what it actually shows

Milgram's 1961 Yale studies had participants deliver what they believed were escalating electric shocks to a "learner" at the instruction of an experimenter in a lab coat. Sixty-five per cent went to the maximum 450 volts; every participant continued to at least 300 volts.

The findings are among the most cited and most contested in psychology. Two lines of criticism matter for anyone using them in training:

- **Gina Perry's 2012 archival investigation** found substantial discrepancies between Milgram's published accounts and the recorded sessions, and concluded that only about half of participants fully believed the shocks were real — and that of those who did believe, 66% disobeyed. That is close to an inversion of the headline number.
- **Ethics and after-effects.** A 1973–74 replication at La Trobe University found participants suffered long-lasting psychological effects, attributed partly to inadequate debriefing.

Against that, **Jerry Burger's 2009 partial replication** — ethically constrained to stop at 150 volts, with immediate debriefing — found obedience rates virtually identical to Milgram's, with no meaningful gender difference. The defensible summary for a security audience is therefore:

> Ordinary people comply with instructions from an apparent authority far more readily than they predict they will, even when the instruction is uncomfortable. The precise percentage is contested and the original study has serious methodological and ethical problems. The robust part is the gap between *predicted* and *actual* compliance.

That gap is the useful part, because it is exactly the gap an attacker exploits and exactly what a phishing simulation reveals. It also explains why the correct control is procedural rather than dispositional: you do not train people out of deference to authority, you build a process in which a deferential person still cannot wire the money alone.

## 3. Social proof and conformity: Asch

Asch's line-judgement experiments put a naive participant in a group of confederates who unanimously gave an obviously wrong answer. Seventy-four per cent of participants conformed at least once across the twelve critical trials; about one-third of all critical-trial responses matched the wrong majority; 26% never conformed; about 12% conformed almost always.

The finding that matters most operationally is the **ally effect**: introducing a single confederate who gave the correct answer dropped conformity to roughly 5%. Bond and Smith's 1996 meta-analysis confirmed the paradigm holds across cultures with variation in magnitude.

*Defensive read:* this is the empirical case for **two-person rules on high-consequence actions**, and for a security culture in which visible dissent is normal. One person willing to say "this looks wrong" collapses the effect for everyone else in the room. Organisations that punish the person who questioned the CEO's urgent request are removing their own ally.

## 4. Scarcity, loss aversion and time pressure

Prospect theory (Kahneman & Tversky, 1979) established that people evaluate outcomes as gains and losses from a reference point and weight losses considerably more heavily than equivalent gains. Practically every urgent-action lure is loss-framed: an account will be closed, a payment will be missed, a penalty will be applied, a delivery will be returned.

Time pressure does something separate and additive. It reduces the resources available for the deliberate, effortful checking that would expose the deception. The relevant mechanism is not a single named bias but the well-established finding that **accuracy in judgement degrades under cognitive load and deadline**. Every serious social-engineering attack manufactures a deadline; the deadline is the tell.

*Defensive read:* build a **mandatory cooling-off period** into irreversible actions. A payment above a threshold that cannot execute for thirty minutes, and requires an out-of-band callback in that window, defeats a very large fraction of BEC regardless of how convincing the lure was. Urgency is the attacker's only perishable asset.

## 5. Affect, cognitive load and decision fatigue

**The affect heuristic** (Slovic and colleagues) describes how a rapid emotional evaluation of a stimulus drives subsequent judgements of its risks and benefits. A message that produces fear, excitement or affection shifts risk judgement before any reasoning occurs. This is why romance fraud and investment fraud are so resistant to warnings: by the time a warning arrives, the affective evaluation is already established and contradicting evidence is processed defensively.

**Cognitive load.** Attention is finite. An employee processing 120 emails while in a meeting is not the same cognitive agent as the same employee reviewing one email carefully. Lain et al.'s field data is consistent with what practitioners observe: susceptibility is strongly situational.

**Decision fatigue.** The claim that the quality of decisions degrades over a sequence of decisions is intuitively appealing and widely repeated. Be careful here. The most-cited demonstration — Danziger, Levav and Avnaim-Pesso's 2011 study of Israeli parole decisions, reporting favourable rulings falling from roughly 65% to near zero across a session and resetting after breaks — has been seriously challenged on the grounds that case ordering was not random, and the broader **ego-depletion** literature it sits within has largely failed multi-lab replication. Mark this as **contested**. The defensible, weaker version — that people are less careful when tired, rushed and at the end of a long day, and that attacks timed for Friday afternoon and month-end exploit that — is well supported by ordinary vigilance and fatigue research and by operational experience, and is enough for training purposes. Do not present the parole study as established fact.

## 6. How people actually judge credibility

Formal credibility assessment is not what people do. In practice they use fast surface cues:

- **Familiarity of the sender's display name**, not the underlying address. Most mail clients show display name first; attackers know this.
- **Visual conformity** — logo, layout, signature block, footer disclaimers.
- **Contextual plausibility** — does this arrive when I would expect it? An invoice during a real project, a courier notice during a real delivery window, a password reset just after a real login attempt.
- **Channel trust transfer** — people trust a phone call more than an email, a video call more than a phone call, and an in-person interaction most of all. Deepfake video-call fraud (file `07`, `08`) attacks precisely this hierarchy, and it is the reason the hierarchy can no longer be relied upon.
- **Prior thread** — a reply within an existing conversation inherits the trust of that conversation. Thread hijacking after a mailbox compromise exploits this and is one of the hardest variants for a recipient to detect.

*Defensive read:* every one of these cues is cheap to forge. Verification must therefore rest on something the attacker cannot supply: a callback to a number obtained independently of the message, a cryptographic origin check (which is what FIDO2 does automatically — see file `04`), or a pre-agreed shared secret.

## 7. Truth-default theory: the deepest reason this works

Timothy Levine's **truth-default theory** proposes that human communication presumes honesty by default: people do not routinely entertain deception as a live possibility, and they abandon the truth-default only when a trigger crosses a threshold of suspicion. The associated empirical picture:

- Human accuracy at detecting deception in laboratory settings clusters around **50–60%**, barely above chance.
- The **veracity effect**: accuracy is well above chance for truthful messages and *below* chance for deceptive ones — because people say "true" most of the time.
- Conventional deception cues (gaze aversion, fidgeting) are unreliable and occur naturally in truthful speakers.
- Detection in the real world typically depends on confessions, physical evidence or prior knowledge, not on reading the person.

This has a hard implication that most awareness programmes refuse to state: **training people to "detect" deception is training them at a task humans are close to incapable of.** What people *can* do reliably is follow a procedure — "any payment change is verified by callback to the number on file" — which converts a detection problem into a process problem. This is why the NCSC's guidance argues that spotting phishing is not the user's job and that the burden belongs on technical and procedural controls.

## 8. Why intelligent and senior people are often *more* vulnerable

This is counter-intuitive and important, and it needs saying in every executive briefing.

**Greater exposure.** Senior people have more public surface — bios, conference talks, interviews, filings, LinkedIn — and are named in more externally-visible processes. They are worth researching. A generic phishing email is a numbers game; an attack on a CFO is bespoke.

**Delegated authority is the target.** The value of a compromise is proportional to what the account can *do*. Executives can approve payments, direct staff, and override process — which is precisely why "the CEO asked me to do this quietly" is the most reliable pretext in existence.

**Legitimate urgency.** Executive work genuinely is time-pressured, genuinely does involve confidential deals, and genuinely does include unusual requests routed around normal process. The attacker's pretext is indistinguishable from Tuesday.

**Process exemption.** Senior people are routinely excused from controls that annoy them — separate admin accounts, MFA prompts, gateway quarantines, mandatory training. The exemption is granted for convenience and harvested by attackers. In the 2020 Twitter compromise, the NY DFS report found over 1,000 employees had access to sensitive internal account-management tooling; broad, weakly-controlled privilege is the same disease at a different level.

**The bias blind spot.** Pronin and colleagues documented that people recognise cognitive biases in others far more readily than in themselves, and that this asymmetry does not diminish with intelligence or education. Confidence in one's own immunity is itself a risk factor. Related work on the "intelligence trap" — that cognitive ability predicts skill at *constructing arguments for a position already held* rather than at revising it — explains why a clever victim, once committed, can defend a fraud against the concerns of colleagues and family.

**Expertise in the wrong domain.** Deep expertise in law, medicine, engineering or finance produces well-founded confidence in judgement generally, which transfers badly to a domain (message provenance) where the expert's intuitions carry no information. Security professionals are not exempt: the RSA breach (file `07`) began with a spear-phishing attachment opened inside a security company.

**Practical consequence.** Role-based controls for executives and their assistants should be *stronger*, not weaker, than for general staff: hardware security keys, no MFA exemptions, a standing rule that the executive will never request a payment or credential change outside the documented process, and an explicit, pre-communicated licence for junior staff to refuse and verify without career risk. See file `05` §7 and file `06` §6.

## 9. The stages of a confidence trick — the older literature

The con-artistry literature predates computing and describes the same arc. Edward H. Smith's model runs: foundation work, approach, build-up, pay-off or "convincer", "the hurrah" (a manufactured crisis forcing immediate action), and "the in-and-in" (an accomplice adding apparent legitimacy). David Maurer's *The Big Con* sets out a ten-stage sequence including "putting in the fix" to inhibit the victim going to the authorities.

Huang and Orbach's 2018 analysis in *Social Research* frames cons as **inducing judgement errors — chiefly errors arising from imperfect information and cognitive biases** — and identifies dishonesty, greed and gullibility as the recurring exploited traits. That framing is useful but incomplete for defenders, because most modern organisational victims are neither greedy nor dishonest: they are conscientious people trying to be helpful and fast. The "convincer" (a small, real payout or a small, real favour that validates the scheme) and "the hurrah" (the manufactured crisis) map directly onto modern investment fraud and BEC respectively, and are worth teaching by name.

## 10. What this means for defence — five design rules

1. **Never build a control whose last line of defence is a human noticing something.** Humans detect deception at near chance. Build controls that work on a deceived human.
2. **Attack the urgency, not the lure.** Mandatory delays and out-of-band verification neutralise the attacker's perishable advantage regardless of how good the pretext is.
3. **Guarantee an ally.** Two-person rules for irreversible actions; a culture where questioning is rewarded. Asch's 5% figure is the justification.
4. **Remove exemptions at the top.** The highest-privilege people need the strictest controls; process exemptions are the attack surface.
5. **Teach mechanisms, not indicator checklists.** Checklists date within months (see file `08` on the collapse of the bad-grammar tell); an employee who understands that urgency plus authority plus channel-switching is the signature can generalise to a lure they have never seen.

## Sources

- [Robert Cialdini](https://en.wikipedia.org/wiki/Robert_Cialdini) — Wikipedia (principles, publication dates, unity principle)
- [Milgram experiment](https://en.wikipedia.org/wiki/Milgram_experiment) — Wikipedia (original results, Perry critique, Burger 2009 replication)
- [Asch conformity experiments](https://en.wikipedia.org/wiki/Asch_conformity_experiments) — Wikipedia (conformity rates, ally effect, Bond & Smith 1996)
- [Truth-default theory](https://en.wikipedia.org/wiki/Truth-default_theory) — Wikipedia (Levine, veracity effect, detection accuracy)
- [Confidence trick](https://en.wikipedia.org/wiki/Confidence_trick) — Wikipedia (Smith and Maurer stage models; Huang & Orbach 2018)
- [Phishing in Organizations: Findings from a Large-Scale and Long-Term Study](https://arxiv.org/abs/2112.07498) — Lain, Kostiainen & Čapkun, IEEE S&P 2022
- [Telling users to "avoid clicking bad links" still isn't working](https://www.ncsc.gov.uk/blog-post/telling-users-to-avoid-clicking-bad-links-still-isnt-working) — UK NCSC, 20 December 2022
- [Twitter investigation report](https://www.dfs.ny.gov/Twitter_Report) — New York State Department of Financial Services

## Open questions

- **Prospect theory and the affect heuristic** are cited here from general knowledge of Kahneman & Tversky (1979) and Slovic et al.; the primary papers were not fetched during construction. The claims made are standard textbook content, but the specific loss-aversion coefficient (~2×) should be checked against the original before being quoted precisely. Marked `needs-verification` at the level of the numeric coefficient only.
- **Danziger et al. (2011) parole study** and the **ego-depletion replication failures** (Hagger et al. multi-lab RRR) are described from general knowledge; primary sources not fetched. The contested status is well established but citations should be added.
- **Pronin's bias blind spot** work and the "intelligence trap" literature are cited from general knowledge; primary sources not fetched.
- Cialdini's *Pre-Suasion* unity principle is verified; the experimental basis for unity specifically is thinner than for the original six and should be characterised cautiously.
