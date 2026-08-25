---
id: finance.quant
title: Quantitative finance — the technical track
domain: 36_finance_careers
tags: [quant, stochastic-calculus, capm, factor-models, fama-french, black-scholes, greeks, volatility-surface, statistical-arbitrage, market-microstructure, backtesting, overfitting, deflated-sharpe, machine-learning, alternative-data, python, kdb, hiring]
jurisdiction: global
status: draft
confidence: medium
updated: 2026-08-25
sources:
  - {title: "Renaissance Technologies", url: "https://en.wikipedia.org/wiki/Renaissance_Technologies", publisher: "Wikipedia", accessed: 2026-08-25}
  - {title: "Jim Simons", url: "https://en.wikipedia.org/wiki/Jim_Simons", publisher: "Wikipedia", accessed: 2026-08-25}
  - {title: "Robert Mercer", url: "https://en.wikipedia.org/wiki/Robert_Mercer", publisher: "Wikipedia", accessed: 2026-08-25}
  - {title: "Peter Fitzhugh Brown", url: "https://en.wikipedia.org/wiki/Peter_Fitzhugh_Brown", publisher: "Wikipedia", accessed: 2026-08-25}
  - {title: "Elwyn Berlekamp", url: "https://en.wikipedia.org/wiki/Elwyn_Berlekamp", publisher: "Wikipedia", accessed: 2026-08-25}
  - {title: "Edward O. Thorp", url: "https://en.wikipedia.org/wiki/Edward_O._Thorp", publisher: "Wikipedia", accessed: 2026-08-25}
  - {title: "Jane Street Capital", url: "https://en.wikipedia.org/wiki/Jane_Street_Capital", publisher: "Wikipedia", accessed: 2026-08-25}
  - {title: "Optiver", url: "https://en.wikipedia.org/wiki/Optiver", publisher: "Wikipedia", accessed: 2026-08-25}
  - {title: "Nassim Nicholas Taleb", url: "https://en.wikipedia.org/wiki/Nassim_Nicholas_Taleb", publisher: "Wikipedia", accessed: 2026-08-25}
related: [finance.industry_map, finance.craft, finance.what_they_studied, finance.breaking_in]
---

# Quantitative finance — the technical track

**Summary.** The systematic side of investing: the mathematics you actually need, the models and where they fail, statistical arbitrage, market microstructure, the many ways a backtest lies to you, the honest track record of machine learning in finance, the data and technology stack, and how quant researchers are actually hired. The organising fact of this file is that **the hard part is not the mathematics — it is not being fooled by your own research**, and the profession's most valuable literature is about that.

> ⚠️ **On strategy descriptions.** Nothing here is a strategy that works. Published strategies are, almost by construction, either capacity-constrained, decayed, or never worked out of sample. The value of the material below is in the vocabulary and the failure modes.

## Key facts

| Item | Detail | Source |
|---|---|---|
| Renaissance research staff | ~150 researchers and programmers, ~half with PhDs; Wall Street experience explicitly disfavoured | Wikipedia |
| Renaissance key hires 1993 | Robert Mercer (PhD CS, UIUC 1972) and Peter Brown (PhD CS, CMU, under Geoffrey Hinton), both from IBM speech recognition | Wikipedia |
| Berlekamp's PhD advisors | Robert Gallager, Peter Elias, **Claude Shannon**, John Wozencraft (MIT, 1964) | Wikipedia |
| Medallion 1990 (post-rebuild) | 55.9% gain | Wikipedia |
| Medallion 1988–2018 | 66.1% avg gross / 39.1% avg net annual return (reported) | Wikipedia |
| Renaissance external funds 2020 | Long-biased −20%, market-neutral −27%, global equities −25%, while Medallion +76% | Wikipedia |
| Thorp | *Beat the Market* (1967) described delta-hedged convertible arbitrage six years before Black–Scholes | Wikipedia |
| Jane Street stack | OCaml firm-wide, including an open-source compiler; increasingly Python for ML | Wikipedia |
| Optiver economics | €3.5bn revenue, €1.4bn net income, 2,112 staff (2024) → ~€1.66m revenue per head | Wikipedia |

---

## 1. The mathematics actually required

Different seats need different depth. Be honest about which seat you want.

**Probability** — the non-negotiable core. Random variables, distributions, conditional expectation, the law of large numbers and the central limit theorem *and the conditions under which they fail*, martingales, Markov chains, hidden Markov models, Bayesian inference. Hidden Markov models deserve special mention: Leonard Baum, Renaissance's first modeller, co-invented the Baum–Welch algorithm for fitting them, and Mercer and Brown arrived from a speech-recognition group whose entire apparatus was HMM-based. Inferring hidden states from noisy sequential observations is the shape of the problem.

**Statistics** — estimation, hypothesis testing, confidence intervals, maximum likelihood, regression and its assumptions, heteroskedasticity, robust and shrinkage estimators, bootstrapping, and — most importantly for this field — **multiple-hypothesis testing**. If you test 1,000 strategies at the 5% level, 50 will appear significant by chance. This is the single most consequential piece of statistics in the discipline.

**Linear algebra** — matrix decompositions, eigenvalues and eigenvectors, PCA, SVD, covariance-matrix estimation and its instability. A sample covariance matrix from *N* assets and *T* observations is badly conditioned when *T* is not much larger than *N*, which it never is; Ledoit–Wolf shrinkage and random-matrix-theory filtering are the standard corrections and are used constantly in practice.

**Optimisation** — convex optimisation, quadratic programming (mean-variance is a QP), Lagrange multipliers and constraints, and the practical reality that unconstrained mean-variance optimisation is an error-maximising machine: it loads on whatever asset has the most overstated expected return.

**Time series** — stationarity and unit roots, ADF and KPSS tests, autocorrelation, ARMA, GARCH and volatility clustering, cointegration and the Engle–Granger and Johansen procedures (the statistical foundation of pairs trading), and regime-switching models.

**Stochastic calculus** — needed for derivatives pricing and essentially nothing else. Brownian motion, Itô's lemma, stochastic differential equations, the Girsanov theorem and change of measure, the Feynman–Kac representation, risk-neutral valuation. Shreve Volumes I and II are the standard path. **A statistical-arbitrage researcher can have a productive career without it; a derivatives quant cannot.**

**Numerical methods** — Monte Carlo simulation and variance reduction, finite differences for PDEs, binomial and trinomial trees, root-finding and interpolation for implied volatility.

---

## 2. The models

### CAPM
E[Rᵢ] = R_f + βᵢ(E[R_m] − R_f). Elegant, empirically poor. The security market line is flatter than CAPM predicts — low-beta stocks have historically earned more than the model says and high-beta stocks less (the "betting against beta" anomaly). Its enduring value is conceptual: only non-diversifiable risk should be compensated. Its damage is the widespread use of beta as a measure of risk in contexts where risk means permanent loss (see `06`).

### Factor models — the lineage
- **Fama–French three-factor (1992/1993)**: market, size (SMB), value (HML). The empirical demolition of single-factor CAPM.
- **Carhart four-factor (1997)**: adds momentum (UMD, from Jegadeesh and Titman, 1993). Momentum remains the most robust and the least theoretically comfortable anomaly.
- **Fama–French five-factor (2015)**: adds profitability (RMW) and investment (CMA). Note what this means for `02` and `06`: **"quality" and "capital discipline" became purchasable factors.** Much of what concentrated quality investors did for decades is now available in an ETF for a few basis points, which is a large part of why active quality managers have struggled since.
- **Hou–Xue–Zhang q-factor model (2015)** and the **q⁵** extension: market, size, investment, profitability (and expected growth), derived from investment-based asset pricing rather than empirical sorting.
- **Stambaugh–Yuan mispricing factors**, **Barillas–Shanken** model comparison, and the **factor zoo** critique (Harvey, Liu and Zhu, "…and the Cross-Section of Expected Returns", 2016) which argued that with hundreds of published factors, the appropriate *t*-statistic hurdle for a new one is around 3.0, not 2.0. Take that seriously: most published factors are probably data-mined.

### Black–Scholes: the assumptions and the failures
The 1973 model assumes geometric Brownian motion with constant volatility, continuous trading with no transaction costs, a constant risk-free rate, no dividends (in its base form), lognormal terminal prices, and the ability to hedge continuously.

**Every one of these is false.** Returns have fat tails and volatility clusters (Mandelbrot); trading is discrete and costly; rates move; and continuous hedging is impossible. The market's response is the **volatility smile/skew**: implied volatility varies by strike and maturity, which is precisely the market saying "we do not believe the lognormal assumption." Equity index options show a pronounced downward skew — out-of-the-money puts are expensive — because crash risk is real and demand for protection is asymmetric. The skew was much flatter before October 1987 and has never returned.

The model's real function is as a **quoting convention**: it converts a price into an implied volatility, which is a comparable number. Nobody with a book believes the assumptions. Taleb's *Dynamic Hedging* (1997) is the practitioner's treatment of what you actually do when the model is wrong; his PhD (Paris Dauphine, 1998) was literally titled *The Microstructure of Dynamic Hedging*.

### The Greeks
**Delta** (∂V/∂S) — directional exposure, the hedge ratio. **Gamma** (∂²V/∂S²) — the rate of change of delta; long gamma means you buy low and sell high mechanically when rehedging, short gamma means the reverse and is how market makers get hurt. **Vega** (∂V/∂σ) — volatility exposure. **Theta** (∂V/∂t) — time decay, the rent paid for gamma. **Rho** (∂V/∂r). Plus the second-order Greeks a real book cares about: **vanna** (∂delta/∂σ), **volga/vomma** (∂vega/∂σ) and **charm** (∂delta/∂t).

The trading intuition that matters: **long gamma is long realised volatility and short theta; short gamma is short realised volatility and long theta.** A market maker who is systematically short gamma is being paid to absorb the risk of large moves, and will be fine until they are not.

### Volatility surfaces and term structure
Implied volatility as a function of strike and maturity, usually parameterised in moneyness. Local volatility (Dupire, 1994) fits the surface exactly but implies unrealistic forward dynamics; stochastic volatility (Heston, 1993; SABR for rates) models the dynamics better; rough volatility models (Gatheral, Jaisson and Rosenbaum, 2018) fit the empirical roughness of realised vol. **Interest-rate term structure**: Vasicek, Cox–Ingersoll–Ross, Hull–White, Heath–Jarrow–Morton, and the post-2008 multi-curve framework where discounting and forward-rate curves separated — a reminder that a model regime can end overnight.

---

## 3. Statistical arbitrage and mean reversion

**The classical form.** Pairs trading: find two assets whose price series are cointegrated, trade the spread when it deviates from its long-run relationship, and hold until it reverts. Generalised: build a factor model, compute residuals, and trade the residuals on the hypothesis that idiosyncratic moves mean-revert while factor moves do not.

**What actually matters in practice:**
- **Breadth over accuracy.** Grinold and Kahn's fundamental law — information ratio ≈ information coefficient × √breadth — is the mathematical justification for the whole enterprise. A signal with a 51% hit rate applied to 10,000 near-independent bets is a much better business than a 70% hit rate applied to ten. This is why Renaissance's model is what it is, and why it does not scale: breadth requires capacity in small, liquid, frequently-traded positions.
- **Cost dominates.** At short horizons, expected gross alpha per trade is a few basis points and the round-trip cost — spread, commission, market impact, borrow — is of the same order. A strategy that is profitable gross and unprofitable net is the normal outcome. **Model transaction costs before, not after.**
- **Decay.** Every published stat-arb signal decays. Thorp's own history is the honest illustration: he left blackjack when casinos adapted, and closed Ridgeline in September 2002 after the stat-arb landscape changed.
- **The August 2007 quant quake.** Over roughly 7–9 August 2007, many market-neutral quant equity funds suffered simultaneous, severe losses as one or more large books deleveraged into crowded positions, followed by a sharp rebound. The lesson — that "market-neutral" strategies sharing the same factor exposures are highly correlated in a liquidation — is the most important empirical event in the strategy's history. (`needs-verification` on specific fund-level figures; no source fetched.)

---

## 4. Market microstructure and execution

The mechanics of how a price is actually formed:

- **Limit order books**, price-time priority, market versus limit orders, hidden and iceberg orders, and the auction mechanisms at open and close.
- **The bid-ask spread's components**: order-processing cost, inventory-holding cost, and **adverse selection** — the market maker's loss to better-informed counterparties (Glosten–Milgrom, 1985; Kyle, 1985). Adverse selection is the reason market making is a real business with a real risk and not free money.
- **Market impact**: temporary and permanent. The empirical regularity is a roughly square-root relationship between impact and order size relative to daily volume — trading 4× the size costs roughly 2× the impact per share. This is *the* binding constraint on strategy capacity.
- **Execution algorithms**: VWAP, TWAP, implementation shortfall, percentage-of-volume, and the Almgren–Chriss framework for optimally trading off impact against timing risk.
- **Fragmentation and regulation**: lit exchanges, dark pools, internalisers, payment for order flow, and Reg NMS in the US / MiFID II in Europe. Citadel Securities' scale as an internaliser and Jane Street's ETF market-making franchise are direct consequences of this structure.
- **The ETF arbitrage mechanism** — creation and redemption baskets with authorised participants — is the single most important microstructure fact for anyone trying to understand Jane Street's business.

---

## 5. Backtesting and its traps

**This is the most important section in the file.** Marcos López de Prado's central claim in *Advances in Financial Machine Learning* (2018) — that most published quantitative finance research is false because of backtest overfitting — is, in my assessment, correct.

| Trap | What it is | The fix |
|---|---|---|
| **Overfitting / backtest selection bias** | Trying many variants and reporting the best. With enough trials any Sharpe ratio is achievable in-sample. | Track the number of trials; apply the **deflated Sharpe ratio** (Bailey & López de Prado) which adjusts the significance threshold for the number of configurations tried, the sample length, skew and kurtosis. |
| **Look-ahead bias** | Using data unavailable at decision time: restated fundamentals, close prices for a decision made at the open, index membership known only later. | Use point-in-time databases; timestamp every field with when it became knowable, not when it applies to. |
| **Survivorship bias** | Testing on today's index constituents. Delisted, bankrupt and acquired names are missing, and they are the losers. | Use a database with delisted securities and delisting returns. |
| **Data-snooping across researchers** | The whole profession has tested the same data for forty years. Even a first personal trial is a late trial collectively. | Higher significance hurdles (Harvey–Liu–Zhu's *t* > 3.0); demand an economic mechanism, not just a pattern. |
| **Transaction cost naivety** | Assuming mid-price fills, ignoring impact, ignoring borrow cost and availability on the short side. | Model spread, commission, square-root impact and borrow explicitly; test sensitivity to a 2× cost assumption. |
| **Improper cross-validation** | Standard k-fold CV leaks information because financial observations overlap and are serially correlated. | **Purged k-fold with an embargo** — remove training observations whose labels overlap the test set, plus a gap. |
| **Regime dependence** | A strategy that works only in one rate, volatility or correlation regime. | Test across regimes explicitly; report performance conditional on regime rather than pooled. |
| **Non-synchronous data** | Closing prices across time zones, stale quotes in illiquid names. | Align timestamps; exclude illiquid names or model the staleness. |
| **Short-selling feasibility** | Assuming any short is available and cheap. Hard-to-borrow names are exactly where the anomaly lives. | Use borrow-cost data; cap short positions by realistic availability. |

**The single best defence** is a prior: require a *reason* the inefficiency should exist and persist — a structural constraint, a regulatory forced seller, a risk genuinely being borne, a behavioural bias with an identified mechanism. A pattern with no story is almost certainly noise, however good the *t*-statistic.

---

## 6. Machine learning in finance — the honest record

**Where ML genuinely works:**
- **Execution.** Predicting short-horizon price movement and optimal order placement from order-book state. High signal-to-noise by financial standards, huge sample sizes, immediate feedback.
- **Market making and options pricing surfaces.** Function approximation where the ground truth is well-defined.
- **Alternative-data extraction.** Turning satellite imagery, receipts, credit-card panels, job postings, app downloads or text into structured features. This is a *data-processing* problem where ML is unambiguously the right tool, and the resulting features then feed conventional models.
- **NLP on filings, transcripts and news.** Sentiment, topic and change-detection in 10-Ks. The move from bag-of-words to transformers materially improved this.
- **Risk and portfolio construction.** Covariance estimation, hierarchical risk parity, regime detection.

**Where it mostly does not work:** medium-horizon (days to months) return prediction from price and fundamental data. The reasons are structural, not fixable by better models — the signal-to-noise ratio is extremely low, the data-generating process is non-stationary because other participants adapt, the effective sample size is small (75 years of monthly equity data is 900 observations, and they are not independent), and the labels are ambiguous.

**The honest summary:** ML has been transformative for feature extraction and execution, and disappointing as a return-forecasting oracle. Renaissance's own record is instructive here — Medallion is a short-horizon, high-breadth machine, and Renaissance's *long-horizon* external funds have been comparatively mediocre, with 2020 losses of 20–27% in the very year Medallion gained 76%.

---

## 7. Data vendors and alternative data

**Market data.** Refinitiv (LSEG), Bloomberg, ICE, Nasdaq, exchange direct feeds. **Reference and fundamentals.** S&P Global Market Intelligence (Compustat), FactSet, MSCI, Morningstar. **Point-in-time and academic.** CRSP and Compustat via WRDS — the standard academic source and essential for survivorship-free equity research. **Risk models.** MSCI Barra, Axioma (SimCorp), Northfield. **Options.** OptionMetrics (IvyDB). **Consensus estimates.** IBES, Visible Alpha. **Short interest and borrow.** IHS Markit (S&P Global), DataExplorers.

**Alternative data** — credit-card transaction panels, satellite and geolocation, web-scraped pricing, app-download and web-traffic data, shipping and customs records, job postings, patent filings, expert-network calls. Millennium was reported to manage close to 400 providers and over 2,000 data sets as at February 2020. Two cautions: **short history** (most alt-data sets begin after 2015, giving no cross-regime test), and **legal and privacy risk** (material non-public information, terms-of-service violations, personal-data regulation). Alt-data alpha also decays fast once several buyers hold the same feed.

**[FREE] alternatives for someone starting out**: SEC EDGAR full-text search and the financial statement data sets, FRED (Federal Reserve Economic Data), the Fama–French data library at Dartmouth (Kenneth French's site), Yahoo/Stooq daily prices, and central bank and statistical-office releases. **[NA]/[ZA]** Bank of Namibia and NAMFISA publications, NSX and JSE data, and Statistics South Africa.

---

## 8. The technology stack

| Layer | Typical tools |
|---|---|
| Research | **Python** — NumPy, pandas, polars, scikit-learn, statsmodels, PyTorch/JAX; Jupyter; **R** in some statistics-heavy shops |
| Time-series storage | **kdb+/q** (the industry standard for tick data, and a genuinely distinctive skill), ClickHouse, Arctic/MongoDB, Parquet on object storage |
| Production / low latency | **C++** (dominant), **Rust** (growing, for memory safety without a GC), **OCaml** (Jane Street firm-wide, including an open-source compiler), Java in some bank contexts, FPGA and kernel-bypass networking at the latency frontier |
| Infrastructure | Linux, Docker/Kubernetes, Kafka, Airflow/Prefect, git, CI |
| Numerical / stats | BLAS/LAPACK, Eigen, CVXPY, cvxopt |

**Practical advice.** For research roles, Python plus real statistics is the requirement and C++ is a strong differentiator. For low-latency trading roles, C++ is the requirement. **kdb+/q is disproportionately valuable relative to how hard it is to learn** because so few people know it and every large systematic shop uses it. Software-engineering discipline — version control, testing, reproducible pipelines, code review — separates researchers whose results can be trusted from those whose cannot, and is undervalued by candidates.

---

## 9. How quant researchers are actually hired

**The pipeline.** PhDs in mathematics, physics, statistics, computer science, electrical engineering and operations research; strong master's degrees in the same; competitive-programming and olympiad backgrounds (IMO, IOI, Putnam) for trading roles; and, increasingly, ML researchers hired directly from technology companies. Renaissance's policy of preferring scientists and disfavouring Wall Street experience is the extreme statement of the norm.

**The seats, which are genuinely different jobs:**
- **Quant researcher (buy-side)** — finds and validates signals. Statistics-heavy. Judged on out-of-sample P&L.
- **Quant trader** — runs a book, manages risk, makes fast decisions. Probability and speed under pressure.
- **Quant developer** — builds the research and execution infrastructure. Often the largest headcount and often the highest leverage.
- **Quant analyst / "strat" (sell-side)** — derivatives pricing, model validation, risk. More stochastic calculus, less P&L exposure.

**The process, typically four to seven stages:**
1. **Screening** — CV, and often an online test (mathematics, probability, coding).
2. **Mental mathematics and estimation** — timed arithmetic under pressure (the Optiver-style 80-question test is the archetype), Fermi estimation.
3. **Probability and games** — classic problems: expected value of dice and coin games, conditional probability, Bayes, optimal stopping, martingale arguments, game theory and adverse selection ("I will only sell you this if it is bad for you"). *Heard on the Street* and *A Practical Guide to Quantitative Finance Interviews* (Zhou) are the standard preparation.
4. **Statistics and modelling** — regression assumptions, overfitting, cross-validation for time series, how you would validate a signal, how you would detect look-ahead bias.
5. **Coding** — algorithms and data structures, plus practical data manipulation. For dev roles, systems design and low-latency C++.
6. **Research presentation** — for PhDs, present your thesis to non-specialists. This tests communication as much as content.
7. **Culture and judgement** — for trading roles especially, the willingness to state a probability, be told you are wrong, and update without defensiveness.

**What is actually being selected for:** speed and accuracy under time pressure, comfort reasoning about uncertainty in explicit probabilities, resistance to being fooled by your own analysis, and the ability to communicate a technical result to someone who will not read your code. The mathematics is a filter, not the objective.

**Compensation** is the highest entry-level in finance and is discussed in `01` and `08`; the reported figures there are `needs-verification`.

## Sources

- [Renaissance Technologies](https://en.wikipedia.org/wiki/Renaissance_Technologies) — Wikipedia
- [Jim Simons](https://en.wikipedia.org/wiki/Jim_Simons) — Wikipedia
- [Robert Mercer](https://en.wikipedia.org/wiki/Robert_Mercer) — Wikipedia
- [Peter Fitzhugh Brown](https://en.wikipedia.org/wiki/Peter_Fitzhugh_Brown) — Wikipedia
- [Elwyn Berlekamp](https://en.wikipedia.org/wiki/Elwyn_Berlekamp) — Wikipedia
- [Edward O. Thorp](https://en.wikipedia.org/wiki/Edward_O._Thorp) — Wikipedia
- [Jane Street Capital](https://en.wikipedia.org/wiki/Jane_Street_Capital) — Wikipedia
- [Optiver](https://en.wikipedia.org/wiki/Optiver) — Wikipedia
- [Millennium Management, LLC](https://en.wikipedia.org/wiki/Millennium_Management,_LLC) — Wikipedia (alternative-data provider counts)
- [Nassim Nicholas Taleb](https://en.wikipedia.org/wiki/Nassim_Nicholas_Taleb) — Wikipedia (*Dynamic Hedging*; PhD title)

## Open questions

- All model citations (Fama–French 1992/1993/2015, Carhart 1997, Jegadeesh–Titman 1993, Hou–Xue–Zhang 2015, Harvey–Liu–Zhu 2016, Glosten–Milgrom 1985, Kyle 1985, Dupire 1994, Heston 1993, Gatheral et al. 2018, Almgren–Chriss, Bailey & López de Prado on the deflated Sharpe ratio, Ledoit–Wolf shrinkage) are stated from general knowledge. **No academic paper was fetched in this session.** Years and attributions should be verified against the papers.
- The August 2007 "quant quake" description has no fetched source and no fund-level figures.
- The square-root market-impact law is an empirical regularity widely reported in the market-microstructure literature; no source fetched.
- Data-vendor ownership (LSEG/Refinitiv, S&P Global/IHS Markit, SimCorp/Axioma) is stated from general knowledge and changes with corporate activity.
- Compensation figures referenced from `01` remain unverified.
