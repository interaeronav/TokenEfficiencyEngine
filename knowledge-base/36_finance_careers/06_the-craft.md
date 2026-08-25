---
id: finance.craft
title: The craft — financial statements, forensics, valuation, moats, sizing and thesis discipline
domain: 36_finance_careers
tags: [financial-statements, accounting, forensic-accounting, valuation, dcf, reverse-dcf, roic, capital-cycle, moats, kelly-criterion, position-sizing, portfolio-construction, base-rates, pre-mortem]
jurisdiction: global
status: stable
confidence: medium
updated: 2026-08-25
sources:
  - {title: "Aswath Damodaran homepage", url: "https://pages.stern.nyu.edu/~adamodar/", publisher: "NYU Stern", accessed: 2026-08-25}
  - {title: "Chuck Akre", url: "https://en.wikipedia.org/wiki/Chuck_Akre", publisher: "Wikipedia", accessed: 2026-08-25}
  - {title: "Terry Smith (businessman)", url: "https://en.wikipedia.org/wiki/Terry_Smith_(businessman)", publisher: "Wikipedia", accessed: 2026-08-25}
  - {title: "Edward O. Thorp", url: "https://en.wikipedia.org/wiki/Edward_O._Thorp", publisher: "Wikipedia", accessed: 2026-08-25}
  - {title: "Tweedy, Browne", url: "https://en.wikipedia.org/wiki/Tweedy,_Browne", publisher: "Wikipedia", accessed: 2026-08-25}
  - {title: "Joel Greenblatt", url: "https://en.wikipedia.org/wiki/Joel_Greenblatt", publisher: "Wikipedia", accessed: 2026-08-25}
  - {title: "SEC EDGAR", url: "https://www.sec.gov/edgar", publisher: "U.S. Securities and Exchange Commission", accessed: 2026-08-25}
related: [finance.canonical_reading, finance.quant, finance.lessons]
---

# The craft — financial statements, forensics, valuation, moats, sizing and thesis discipline

**Summary.** The actual analytical work of a discretionary investor, in the order it is performed: read the statements and understand how they articulate; check whether the numbers are honest; understand the business and whether its returns can persist; value it; decide how much to own; write down why, in a form that can later convict you of being wrong. Almost all of the value in this sequence sits in steps 1, 2 and 6, and almost all of the glamour sits in step 4.

> ⚠️ **Nothing in this file is investment advice.** The methods described are the standard analytical apparatus of the profession; their correct application does not produce good outcomes reliably, and the base rates in `00_overview.md` apply.

## Key facts

| Concept | The one-line version |
|---|---|
| Articulation | Net income → retained earnings on the balance sheet; cash flow reconciles opening and closing cash. If the three statements do not tie, the model is wrong. |
| Owner earnings (Buffett, 1986 letter) | Reported earnings + D&A + other non-cash charges − average annual maintenance capex |
| ROIC | NOPAT ÷ (net working capital + net fixed assets), i.e. return on capital actually employed |
| Value creation condition | ROIC > WACC. Growth below that condition destroys value. |
| Reverse DCF | Solve for the growth and margin the current price implies, then judge plausibility |
| Kelly fraction | f\* = edge ÷ odds; for a simple binary, f\* = (bp − q)/b |
| Practical Kelly | Half-Kelly or less, because the edge estimate is itself uncertain |
| Risk (this tradition) | Permanent loss of purchasing power, not standard deviation |

---

## 1. Reading financial statements properly

### The three statements and their articulation
The income statement is a period flow measured on accruals. The balance sheet is a point-in-time stock. The cash flow statement reconciles the two by removing the accruals. **The whole point of statement analysis is the gap between the first and the third.** Accounting earnings involve dozens of estimates — revenue recognition timing, bad-debt provisions, useful lives, impairment tests, pension assumptions, share-based compensation. Cash is comparatively hard to fake for long.

The mechanical checks that must always tie:
- Net income flows to retained earnings (adjusted for dividends and buybacks).
- Cash flow from operations begins at net income and reconciles, via non-cash charges and working-capital movements, to the change in cash.
- Depreciation on the cash flow statement matches the property, plant and equipment roll-forward in the notes.
- Every balance-sheet movement is explained by a flow somewhere.

If a model does not tie, you have not understood the business — you have understood a spreadsheet.

### Cash flow versus earnings
The two habitual questions:
1. **Is cash conversion (CFO ÷ net income) stable and close to or above 1 over a full cycle?** Persistently below 1 means earnings are being recognised ahead of cash — sometimes legitimately (a growing business funding receivables and inventory), sometimes not.
2. **Is free cash flow (CFO − capex) positive and growing, and how much of capex is maintenance versus growth?** Companies do not disclose this split. Estimating it is the analyst's job, and it is where "owner earnings" lives.

### Working capital
Days sales outstanding, days inventory, days payable, and the cash conversion cycle. Watch the *direction* and *relative to peers*, not the level. Rising DSO faster than revenue is the single most common early warning of revenue-recognition trouble — channel stuffing shows up here before it shows up anywhere else. Falling payables can signal a supplier losing confidence. A negative cash conversion cycle (customers pay before suppliers are paid — Amazon, Costco, Dell historically) is a source of free financing and a genuine competitive weapon.

### Capitalised costs
When a company capitalises a cost it moves an expense off the income statement onto the balance sheet, boosting current earnings and creating an asset that must later be amortised or impaired. Watch capitalised software development, capitalised interest, capitalised customer-acquisition cost, and capitalised exploration. The check: compare the capitalisation policy against close peers. Divergence is the signal.

The inverse adjustment matters too: **R&D and brand advertising are expensed under IFRS and US GAAP but are economically investment.** A company spending heavily on genuinely productive R&D looks *worse* on reported earnings than it is. Capitalising R&D notionally (Damodaran publishes the method and industry amortisable lives) changes both earnings and invested capital, and therefore ROIC. Do it consistently or not at all.

### Off-balance-sheet items
Post-IFRS 16 and ASC 842 most operating leases are on balance sheet, which closed the largest historical gap. What remains: unconsolidated joint ventures and associates (equity-method investments hide both assets and debt), securitisations and receivables factoring, pension deficits and their actuarial assumptions, contingent liabilities and litigation, purchase commitments, and guarantees. All of it lives in the notes, which is why the notes are longer than the statements and why almost nobody reads them.

### Segment reporting
Segment disclosure is where a diversified company is forced to reveal what is actually earning. Read it for: which segment's margins are carrying the group, whether corporate costs are being allocated in a way that flatters one segment, and whether the segments would be worth more separately (the sum-of-the-parts question). Changes in segment definitions between years are almost always defensive.

### Share count and dilution
Use fully diluted, and track the *trend* in share count over five to ten years alongside stock-based compensation. A company buying back shares at the same rate it issues them to employees is transferring value from owners to staff while reporting "returns to shareholders." Look at cash spent on buybacks against the actual reduction in share count.

---

## 2. Forensic techniques and red flags

The taxonomy below is the practical distillation of Schilit's *Financial Shenanigans*, O'glove's *Quality of Earnings* and Terry Smith's *Accounting for Growth* (1992) — the book that got its author suspended and sued by his employer.

**Revenue red flags.** Receivables growing materially faster than revenue; unbilled or contract-asset balances rising; revenue recognised on shipment to distributors rather than sell-through; large "bill and hold" arrangements; a spike in fourth-quarter revenue; a change in revenue-recognition policy; related-party revenue.

**Expense and margin red flags.** Capitalisation policy changes; extending depreciable lives; reducing bad-debt or warranty provisions as a percentage of revenue; "big bath" restructuring charges that create a cookie-jar reserve to be released later; recurring "one-off" items every year; gross margin that improves while peers' deteriorate without an explanation you can articulate.

**Cash flow red flags.** Operating cash flow persistently below net income; classifying operating outflows as investing; securitising or factoring receivables to flatter CFO; capitalising costs that peers expense; and — a personal favourite of forensic analysts — a company that reports growing profits while continually raising external finance.

**Balance sheet red flags.** Goodwill as a large and growing share of assets from serial acquisition; intangibles that never impair; inventory rising faster than cost of sales; deferred tax assets whose recoverability depends on future profits that have not materialised.

**Governance and behavioural red flags.** Auditor change, especially to a smaller firm; CFO departure without a named successor; late filings; restatements; complex holding structures in low-disclosure jurisdictions; aggressive non-GAAP measures with widening gaps to GAAP; management compensation tied to adjusted metrics they define; heavy insider selling; a dominant CEO with a compliant board; and hostility to specific questions in earnings calls. **Christopher Browne of Tweedy Browne reported irregularities in Conrad Black's management of Hollinger to the SEC in 2003** — a reminder that this work is occasionally consequential.

**Where to look.** **[FREE]** [SEC EDGAR](https://www.sec.gov/edgar): the 10-K (full-year, audited, with the notes), the proxy statement DEF 14A (compensation, incentives, related-party transactions, board composition — the most under-read document in finance), 8-K filings (auditor changes, executive departures, material events), and 13D/G filings. **[ZA]/[NA]** JSE SENS and NSX announcements are the regional equivalents for material disclosures.

---

## 3. Valuation

### DCF and why it is oversold
A discounted cash flow model is arithmetically correct and practically fragile. In a standard ten-year model with a terminal value, **the terminal value is typically 60–80% of the total**, and the terminal value is a function of two numbers — the perpetual growth rate and the discount rate — whose difference sits in a denominator. Move the discount rate by 100bp and the perpetuity growth by 50bp and the answer moves by 30–50%. A DCF is therefore not a measuring instrument. It is a device for making assumptions explicit.

Use it correctly by: running the model as a *range* with explicit scenarios rather than a point estimate; keeping the forecast period only as long as you can genuinely say something about; sanity-checking the implied terminal ROIC (a perpetual growth rate above GDP is a claim that the company eventually becomes the economy); and being honest that a discount rate is a hurdle you choose, not a fact you discover — many of the investors in `02` simply use a fixed required return (often 8–10%) rather than pretending to compute a CAPM cost of equity.

### Reverse DCF — the superior discipline
Instead of forecasting cash flows to derive a value, **take the current market price as given and solve for the growth rate, margin and reinvestment rate that would justify it.** Then ask a single question: *is that plausible?*

This inverts the psychology. A forward DCF invites you to generate assumptions that produce the answer you already want. A reverse DCF confronts you with the market's assumptions and forces you to disagree with something specific. It also produces a falsifiable statement — "the price implies 14% revenue growth for a decade at a 22% margin; the company has never exceeded 18% growth and the industry's best operator earns 19%" — which is what a thesis should look like. Rappaport and Mauboussin's *Expectations Investing* is the book-length treatment.

### Multiples and their misuse
P/E, EV/EBIT, EV/EBITDA, EV/Sales, P/B, FCF yield, EV/IC. Each is a shorthand for a DCF with embedded assumptions.

The standard errors: comparing a multiple across companies with different capital structures (P/E is contaminated by leverage; EV/EBIT is not); using EBITDA for capital-intensive businesses where depreciation is a genuine economic cost (Munger's line about "bullshit earnings" is directed exactly here); comparing multiples across different growth and return profiles without adjustment; using a peer-group median as a target price, which merely assumes the peer group is correctly valued; and mistaking a low multiple for cheapness when it reflects a business in structural decline — the value trap.

The one relationship worth memorising: **a justified multiple rises with growth and with ROIC, and falls with risk.** A business earning 30% on incremental capital and growing 10% deserves a very different multiple from one earning 6% and growing 10%, and the second is often *destroying* value while growing.

### Sum-of-the-parts
Value each segment on an appropriate basis, add, subtract net debt and a holding-company discount, and compare to the market price. Essential for conglomerates, holding companies (PSG, Investor AB, Berkshire) and businesses with a hidden crown jewel. The traps: double-counting corporate costs, ignoring the tax leakage on a hypothetical disposal, and assuming a discount will close when there is no catalyst. Joel Greenblatt's *You Can Be a Stock Market Genius* (1997) is essentially a book about the moment such discounts *do* close — spin-offs, restructurings and forced selling.

### Owner earnings
Buffett's 1986 definition: reported earnings, plus depreciation, amortisation and other non-cash charges, **minus the average annual capitalised expenditure required to maintain competitive position and unit volume**. The subtlety is entirely in that last clause, which is an estimate, not a disclosure. Practical approaches: use depreciation as a proxy for maintenance capex in a stable, non-inflationary business; look at capex in a no-growth year; or model capex per unit of capacity.

### ROIC and the capital cycle
ROIC = NOPAT ÷ invested capital. What matters is not the current level but:
- **Incremental ROIC** — the return on the capital deployed over the last five years, which is what determines future compounding: (change in NOPAT) ÷ (change in invested capital).
- **Persistence** — high ROIC attracts competition. The empirical regularity is mean reversion toward the cost of capital; the whole question in quality investing is which businesses resist it and why.
- **The capital cycle** (Marathon Asset Management, *Capital Returns*, 2015). High returns attract capital; capital expands supply; supply crushes returns; capital withdraws; supply contracts; returns recover. The framework's practical instruction is to **watch capital expenditure and industry capacity, not earnings** — buy where capex has been cut for years and consolidation is happening, sell where capacity is being built and everyone is optimistic. It applies with unusual reliability to shipping, semiconductors, mining, energy, airlines and homebuilding.

---

## 4. Competitive analysis and moat identification

The moat is what allows high ROIC to persist. There are only a handful of real sources, and most claimed moats are not moats:

1. **Intangible assets** — brands that support pricing power (not merely recognition), patents, regulatory licences. Test: can the company raise price above inflation without losing volume?
2. **Switching costs** — the customer's cost, in money, time, risk or retraining, of leaving. Enterprise software, banking relationships, medical devices with trained clinicians.
3. **Network effects** — the product is more valuable as more people use it. Exchanges, marketplaces, payment networks, some social platforms. The strongest and rarest.
4. **Cost advantage** — from scale, from process, from a uniquely located asset, or from **scale economics shared** (see `09`): passing scale benefits to customers as lower prices to grow volume and deepen the advantage. Costco, Amazon, GEICO, Nebraska Furniture Mart.
5. **Efficient scale** — a market only large enough to support one or two operators profitably. Pipelines, regional airports, rural utilities.

**What is not a moat:** being big; having good management; a first-mover advantage in a market with low switching costs; a superior current product; high current margins.

**The falsification test.** For each claimed moat, write down what you would observe if it were eroding — market share loss, price concessions, rising customer acquisition cost, falling gross margin, increasing capex to stand still — and then monitor those specific series. A moat thesis that cannot be falsified is a story.

**Chuck Akre's three-legged stool** is the practical version: an extraordinary business, talented management of high integrity, and *reinvestment opportunity and skill*. The third leg is the one that turns a good business into a compounder — 30% returns on capital are worth far less if only a fifth of earnings can be redeployed at that rate. **Thomas Russo's "capacity to suffer"** is the complement: a controlling owner willing to depress reported profits for a decade to build a position.

---

## 5. Management assessment and incentive analysis

Read the proxy statement before the annual report. Specifically:

- **What are they paid on?** If the long-term incentive plan vests on EPS growth, expect buybacks and acquisitions. If it vests on ROIC or economic profit, expect capital discipline. If it vests on "adjusted EBITDA," expect adjustments. Incentives predict behaviour better than strategy documents do.
- **How much do they own, and how did they get it?** Purchased shares are a stronger signal than granted shares. A CEO whose net worth is dominated by the stock behaves differently from one holding options struck at a low price.
- **Capital allocation history.** Trace every major use of cash over ten years — organic capex, acquisitions, buybacks, dividends, debt repayment — and score it against what the stock did. Most CEOs are promoted for operating skill and then judged on capital allocation, which they have never done. William Thorndike's *The Outsiders* (2012) is the case-study collection.
- **Language.** Compare what management said would happen three years ago against what happened. Read the same paragraph of the strategy section across five annual reports. Consistency and candour about mistakes are informative; François Rochon's practice of publishing his own annual error review is the investor-side version.
- **Ownership structure.** Family or foundation control, dual-class shares, a large anchor shareholder — these cut both ways. They enable long horizons (Russo's whole thesis) and they enable expropriation of minorities. Which one depends on the specific family.

---

## 6. Position sizing and the Kelly criterion

Selection and sizing are separate problems, and the second is more neglected. The Kelly criterion, from John Kelly's 1956 Bell Labs paper and brought into markets by **Ed Thorp**, gives the bet fraction that maximises the long-run growth rate of capital:

For a simple binary bet with probability *p* of winning *b*-to-1, losing with probability *q* = 1 − *p*:

**f\* = (bp − q) / b**

Properties worth internalising:
- Kelly maximises the **expected logarithm** of wealth, i.e. the geometric growth rate — not expected wealth, which would recommend betting everything.
- **Over-betting is catastrophically worse than under-betting.** The growth-rate curve is roughly parabolic around f\*; betting 2× Kelly gives an expected growth rate of *zero*, and beyond that, ruin. Under-betting merely costs a little growth.
- **Full Kelly's drawdowns are intolerable in practice.** The probability of at some point halving your capital under full Kelly is approximately 50%.
- Therefore **fractional Kelly** — half or quarter — is what practitioners actually use. The justification is not squeamishness: the edge *p* is itself estimated with error, and if your estimate of edge is too high, your Kelly fraction is too high in exactly the situations where it hurts most. Half-Kelly retains about 75% of the growth rate with roughly half the volatility.

For discretionary equity investing, where you cannot estimate *p* and *b* to two decimal places, Kelly functions as a *discipline* rather than a formula: it says that position size should scale with the edge and inversely with the odds against, that no single position should be large enough that being wrong is terminal, and that correlated positions must be sized as one position. Concentrated managers who run 8–10% positions are implicitly running something like quarter-Kelly on a high assumed edge.

---

## 7. Portfolio construction: concentration versus diversification

There is no correct answer; there is a coherent and an incoherent pairing of choices.

**The coherent concentrated position** (Nomad, Akre, Train, Hohn, Vinall — 8 to 25 holdings): justified only if you genuinely have deeper knowledge than the market on each name, and — critically — only if your **capital is structured to survive the drawdowns concentration produces**. Lindsell Train's severe post-2020 underperformance is what this looks like from the inside. A concentrated manager with monthly-liquidity capital is an accident waiting to happen.

**The coherent diversified position** (Schloss, Tweedy Browne — 60 to 100+ holdings): justified when the edge is statistical rather than specific. Schloss bought baskets of statistically cheap securities without meeting management; the edge was the aggregate characteristic, not the individual insight, and diversification was the mechanism that turned a small edge into a reliable one. This is Grinold and Kahn's fundamental law in narrative form: information ratio ≈ information coefficient × √breadth. You can be modestly right about many things or very right about few, but not modestly right about few.

**The incoherent position** — 45 stocks selected by "high conviction" — has neither the depth of concentration nor the statistical reliability of breadth, and describes most active funds. It is also, not coincidentally, the position that minimises career risk.

**Correlation is the thing actually being managed.** Ten positions in different companies that all depend on the same interest-rate path, the same consumer, or the same commodity is one position. Real diversification is across return *drivers*, which is precisely Swensen's insight in `02`.

---

## 8. Risk: permanent loss versus volatility

The tradition represented in `02` defines risk as **the probability of permanent impairment of capital**, not as standard deviation of returns. The distinction is not semantic:

- Volatility is symmetric and measurable; permanent loss is asymmetric and must be judged.
- Volatility is an *opportunity* for an investor with permanent capital and a *threat* for one facing redemptions — which means risk is a property of the investor-plus-asset pair, not of the asset. This is the most important practical consequence of the whole framework.
- The three real sources of permanent loss are: **paying too high a price** for even a good business; **owning a deteriorating business** whose value is genuinely falling; and **leverage**, which converts a temporary decline into a permanent one by forcing sale at the bottom. LTCM in 1998 is the canonical demonstration.
- Academic risk measures still have uses — for a market maker or a pod PM with a daily VaR limit, volatility *is* the operative risk because the drawdown limit is real. Do not confuse a philosophical position with a job description.

**Base rates.** Before any specific analysis, establish the outside view: what proportion of large acquisitions create value? What proportion of turnarounds turn? How often does a company sustain 20% growth for a decade? (Very rarely — Mauboussin's work on this is the standard reference.) The inside view — the compelling specific story — systematically overrides the outside view, and the correction is to write the base rate down first.

---

## 9. Writing the thesis, and the pre-mortem

**The written thesis** is the highest-leverage practice in this file, and the one most consistently shared by the people in `02` — Nomad's letters, Rochon's annual reviews, Bloomstran's Semper Augustus letters, Terry Smith's look-through disclosures. Writing forces the resolution of vagueness that thinking permits.

A usable structure:

1. **What the business does**, in three sentences, without jargon, including how it makes money per unit.
2. **The base rate** for businesses of this type doing what you expect.
3. **Why it is mispriced** — and this must name the mechanism: forced selling, index exclusion, complexity, a temporary problem mistaken for permanent, time horizon, or an under-followed market. "The market is wrong" is not a mechanism.
4. **The reverse DCF**: what the current price implies, and the specific assumption you disagree with.
5. **The moat and its falsification tests** — the named series you will monitor.
6. **Management and incentives** — what they are paid on, what they own.
7. **What has to go right**, listed, with rough probabilities.
8. **What would make me sell** — written *now*, before ownership creates commitment bias.
9. **Position size and why** — the explicit link to the strength of the edge.
10. **The date.** So that it can be scored later.

**The pre-mortem** (Gary Klein's technique, adopted widely in this cohort) is run before committing: *assume it is three years from now and this investment has lost 60% of its value. Write the story of what happened.* Doing it prospectively, in the past tense, defeats the optimism that a "list the risks" exercise never does. Add: **who is on the other side of this trade, and what do they know?**

**Scoring.** Keep a decision journal with the date, the thesis, the probability estimates and the price. Review annually, and score decisions on process rather than outcome — Annie Duke's "resulting" error is judging a good decision badly because it turned out poorly. Rochon publishes his mistakes each year; Kahneman, Sibony and Sunstein's *Noise* provides the theoretical case for why structured, independent, written judgements are more accurate than discussed ones.

## Sources

- [Aswath Damodaran homepage](https://pages.stern.nyu.edu/~adamodar/) — NYU Stern (valuation methods, data sets, R&D capitalisation method)
- [SEC EDGAR](https://www.sec.gov/edgar) — U.S. Securities and Exchange Commission (10-K, DEF 14A, 8-K, 13D/G)
- [Chuck Akre](https://en.wikipedia.org/wiki/Chuck_Akre) — Wikipedia (three-legged stool, compounding machines)
- [Terry Smith (businessman)](https://en.wikipedia.org/wiki/Terry_Smith_(businessman)) — Wikipedia (*Accounting for Growth*)
- [Edward O. Thorp](https://en.wikipedia.org/wiki/Edward_O._Thorp) — Wikipedia (Kelly criterion adoption, 1956 Kelly paper)
- [Tweedy, Browne](https://en.wikipedia.org/wiki/Tweedy,_Browne) — Wikipedia (*What Has Worked in Investing*; Hollinger/Conrad Black SEC report, 2003)
- [Joel Greenblatt](https://en.wikipedia.org/wiki/Joel_Greenblatt) — Wikipedia (special situations, magic formula)
- [Walter Schloss](https://en.wikipedia.org/wiki/Walter_Schloss) — Wikipedia (diversified statistical value approach)

## Open questions

- Buffett's owner-earnings definition is quoted from the 1986 Berkshire letter from general knowledge; the letter itself was not fetched in this session.
- The Kelly half-Kelly properties (≈75% of growth rate at ≈half the volatility; ~50% probability of a 50% drawdown under full Kelly) are standard results stated from knowledge, not from a fetched source. They should be verified against Thorp's "The Kelly Criterion in Blackjack, Sports Betting, and the Stock Market" (1997/2006).
- Grinold & Kahn's fundamental law is stated in its common approximate form; the exact formulation including the transfer coefficient is in the book.
- IFRS 16 / ASC 842 lease treatment is stated from general knowledge; no standard-setter document was fetched.
- Mauboussin's base-rate work on sustained growth is referenced without a fetched citation.
