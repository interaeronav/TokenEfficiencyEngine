---
id: alibaba.cloud
title: Alibaba Cloud and infrastructure — silicon, RISC-V, AI build-out and export controls
domain: 37_alibaba_and_qwen
tags: [alibaba-cloud, t-head, pingtouge, yitian-710, hanguang-800, xuantie, risc-v, zhenwu, polardb, apsara, export-controls, ai-infrastructure, capex]
jurisdiction: global
status: stable
confidence: medium
updated: 2026-08-25
sources:
  - {title: "Alibaba Group Holding Ltd Form 20-F, fiscal year ended March 31, 2026", url: "https://www.sec.gov/Archives/edgar/data/1577552/000119312526231755/baba-20260331.htm", publisher: "U.S. Securities and Exchange Commission (EDGAR)", accessed: 2026-08-25}
  - {title: "Alibaba Group Announces June Quarter 2026 Results", url: "https://data.alibabagroup.com/ecms-files/1532295521/fa5d65fc-9b3e-4e82-a8fc-4ce1c3e2c407/Alibaba%20Group%20Announces%20June%20Quarter%202026%20Results.pdf", publisher: "Alibaba Group", accessed: 2026-08-25}
  - {title: "T-Head", url: "https://en.wikipedia.org/wiki/T-Head", publisher: "Wikipedia", accessed: 2026-08-25}
  - {title: "RISC-V", url: "https://en.wikipedia.org/wiki/RISC-V", publisher: "Wikipedia", accessed: 2026-08-25}
  - {title: "Alibaba Cloud", url: "https://en.wikipedia.org/wiki/Alibaba_Cloud", publisher: "Wikipedia", accessed: 2026-08-25}
related: [alibaba.overview, alibaba.structure, alibaba.qwen_models, alibaba.open_weight_landscape]
---

# Alibaba Cloud and infrastructure — silicon, RISC-V, AI build-out and export controls

**Summary.** Alibaba Cloud, founded September 2009, is the largest cloud provider in China and Asia-Pacific and ranked first in China's AI cloud market with 38.1% share (Omdia, 2025). Since the quarter ended 30 June 2026 it has been reported together with T-Head, Alibaba's chip design subsidiary, as a single segment — "AI Cloud and Compute Services" — with revenue of RMB 48,437 million in that quarter growing 45% year over year. The strategic thesis is vertical integration under constraint: US export controls since 2022 have restricted access to Nvidia's advanced accelerators, so Alibaba has built its own compute stack from Arm and RISC-V CPUs (Yitian 710, XuanTie), through its own AI processors (Hanguang 800, now the Zhenwu series), to an orchestration layer explicitly designed to manage heterogeneous chip clusters. Capital expenditure went from RMB 32.1 billion (FY2024) to RMB 126.1 billion (FY2026) to RMB 67.7 billion in a single quarter (June 2026).

> ⚠️ **Confidence note.** Financial and strategy statements are sourced to Alibaba's own filings (high confidence). Chip specifications and RISC-V core details are sourced to Wikipedia summaries and are `needs-verification` at the level of individual specifications — first-party T-Head/XRVM pages were not readable during research.

## Key facts

| Item | Value | Date / source |
|---|---|---|
| Founded | September 2009 | Wikipedia |
| Segment revenue, quarter ended 30 Jun 2026 | RMB 48,437 m (US$7,139 m), +45% YoY total and external | June 2026 results |
| AI-related product revenue, same quarter | RMB 12,376 m (US$1,824 m); 12th consecutive quarter of triple-digit growth | June 2026 results |
| Adjusted EBITA, same quarter | RMB 5,628 m (US$830 m), +133%, 12% margin | June 2026 results |
| Cloud Intelligence Group revenue, FY2026 | RMB 158,132 m (US$22,924 m), +34% on FY2025 | 20-F FY2026 |
| External revenue growth, quarter ended 31 Mar 2026 | +40%, with AI products 30% of that revenue | 20-F FY2026 |
| China AI cloud market share | 38.1%, ranked first | Omdia "AI Cloud Market: China – 2025", cited June 2026 results |
| China AI cloud market share (earlier citation) | 35.8%, ranked first | 20-F FY2026 |
| A-share listed companies served | ~67% | 20-F FY2026 |
| Capex FY2024 / FY2025 / FY2026 | RMB 32,087 m / 85,972 m / 126,063 m | 20-F FY2026 |
| Capex, quarter ended 30 Jun 2026 | RMB 67,678 m (US$9,975 m), +75% YoY | June 2026 results |
| Capital commitments contracted, not provided | RMB 54,136 m (US$7,848 m) at 31 Mar 2026 | 20-F FY2026 |
| Zhenwu AI processor adoption | 650+ external customers across 20+ industries | June 2026 results |

## The service stack

Alibaba Cloud sells across the conventional three tiers plus a fourth that it now leads with:

- **IaaS** — Elastic Compute Service (ECS), Object Storage Service (OSS), Virtual Private Cloud, block storage, CDN.
- **PaaS** — container services (ACK), serverless, message queuing, and the database family.
- **MaaS (model-as-a-service)** — the layer Alibaba now foregrounds. Model Studio / DashScope serve Qwen and third-party models via API; **Platform for AI (PAI)** provides training, fine-tuning, evaluation and deployment, with a serverless mode offering "end-to-end support for the fine-tuning, evaluation, and deployment of major open-source large models"; **Lingjun Intelligent Computing Service** is the large-scale GPU/accelerator cluster product.
- **Agent layer** — from 2026 the company markets AI agents, agent orchestration and "orchestration software that manages heterogeneous chip clusters, including our own proprietary chips" as first-class products. That last phrase is doing a lot of work: heterogeneous scheduling is what you build when your fleet contains several generations of restricted imported accelerators alongside your own silicon.

### Proprietary infrastructure software

Named in the FY2026 20-F:

- **Apsara** (Feitian) — the general-purpose distributed computing operating system underneath everything, in development since 2009.
- **Shenlong** — the hardware virtualisation architecture (a smartNIC/DPU-offload design comparable in intent to AWS Nitro).
- **Pangu** — distributed cloud storage.
- **Luoshen** — the cloud network fabric.
- **Lingjun Intelligent Computing Cluster** — the AI training/inference cluster and a "global AI computing network".

### The database stack

- **PolarDB** — cloud-native transactional (OLTP) database with a three-tier disaggregated architecture (compute / memory / storage separated). In FY2026 Alibaba added "built-in model operator services to meet online inference demands" and a **LakeBase** architecture for managing large-scale metadata. PolarDB has MySQL-, PostgreSQL- and Oracle-compatible editions and is one of the few Chinese-origin databases with meaningful independent benchmarking history.
- **AnalyticDB** — cloud-native analytical (OLAP) database, now fully serverless with heterogeneous compute scheduling and large-model integration for real-time analytics and online inference.
- **Lindorm** — cloud-native multimodal database, upgraded for "full-stack AI multimodal data processing" with fused retrieval across modalities. In practice this is where vector search sits alongside wide-column and time-series data.
- **OceanBase** — the distributed relational database originally built for Alipay, now an Ant-affiliated company rather than an Alibaba Cloud product, but part of the same technical lineage.

## T-Head (Pingtouge) — the silicon programme

**T-Head** (平头哥, "Pingtouge", the honey badger) was established in **September 2018**, spun out of the DAMO Academy and built on the 2018 acquisition of **C-Sky Microsystems**, a Hangzhou embedded-CPU designer founded in 2001. From the quarter ended 30 June 2026 it is reported inside the AI Cloud and Compute Services segment.

The FY2026 20-F states the position bluntly: "T-Head, our chip design subsidiary, has brought its proprietary GPU into production at scale, supporting end-to-end AI workloads from training and fine-tuning to inference," and "our proprietary T-Head AI chips have achieved production at scale."

### The product line

| Chip | Type | Announced | Notes |
|---|---|---|---|
| **XuanTie 910 (C910)** | RISC-V CPU core | July 2019 | 2.5 GHz, 16-core, 64-bit RV64GC, out-of-order. Described as T-Head's first CPU. **Open-sourced October 2021.** |
| **Hanguang 800** | AI inference NPU | September 2019 | T-Head's first self-developed AI chip; used for Taobao image search and recommendation inference |
| **Yitian 710** | Arm server CPU | October 2021 | 5 nm; an IEEE study reported it as the fastest Arm-based cloud server CPU at the time |
| **Zhenyue 510** | SSD controller | 2023 | Enterprise data-centre storage |
| **XuanTie C920, C907, R910** | RISC-V cores | November 2023 | Targeting autonomous vehicles, AI, enterprise storage, network communications |
| **XuanTie C930** | Server-grade RISC-V core | March 2025 | Supports the **RVA23 profile**, which Ubuntu Linux requires from October 2025 |
| **PPU series** | AI accelerator | 2025 | Reported comparable to Nvidia H20 / A800 class; deployed by China Unicom |
| **Zhenwu series, incl. Zhenwu M890** | AI processor | 2026 | Latest AI processor; **650+ external customers across 20+ industries** via Alibaba Cloud, including autonomous driving, internet and financial services |

T-Head's portfolio now spans "GPU, CPU, storage and networking chips", which the June 2026 results describe as enabling "integrated hardware optimization across compute, storage and networking."

> ⚠️ Individual chip specifications above (clock speeds, process nodes, performance comparisons) come from a Wikipedia summary and are `needs-verification`. In particular, "comparable to Nvidia H20/A800" is a reported claim, not a measured result, and H20/A800 are themselves export-restricted derated parts rather than Nvidia's best silicon.

### Why the RISC-V work matters — properly

The XuanTie programme is the most strategically significant part of T-Head and the part most often underrated in Western coverage. Four reasons:

**1. RISC-V is licence-free and cannot be embargoed the way Arm can.** Arm is a UK/SoftBank-owned company subject to UK and, through its US operations, US export jurisdiction. The RISC-V ISA is an open specification stewarded by RISC-V International, which relocated its incorporation to Switzerland in 2020 specifically to reduce this exposure. For a Chinese firm planning a decade ahead under escalating controls, an ISA that nobody can revoke is worth a great deal even if the implementations are behind.

**2. Alibaba open-sourced its cores.** The XuanTie 910 design was released as open source in **October 2021** — a 64-bit out-of-order application-class core, not a microcontroller. That is an unusual act: it seeded a domestic (and international) ecosystem of derivative implementations and made XuanTie a de facto reference design in a way that a proprietary licence would not have. It is the same play, in hardware, that Qwen represents in models: give away the design, capture the ecosystem.

**3. The C930 crosses into server class.** Launched March 2025, the C930 supports **RVA23**, the profile that finally standardises the vector, hypervisor and cryptography extensions needed for general-purpose server software. RVA23 is the profile Ubuntu requires from its October 2025 release onward. A RISC-V core that can boot a mainstream distribution unmodified is the threshold between "embedded curiosity" and "possible datacentre CPU". Alibaba Cloud executives were reported in March 2025 as predicting RISC-V would become a mainstream cloud architecture "as early as 2030", and Chinese government bodies have been developing guidance to promote RISC-V nationally.

**4. It compounds with the AI accelerator work.** The reason to own a CPU architecture is not the CPU. It is that host CPU, accelerator, NIC and storage controller can be co-designed — which is exactly what the June 2026 results claim ("integrated hardware optimization across compute, storage and networking") and what the FY2026 20-F promises to deepen ("deepen T-Head's co-design with Alibaba Cloud infrastructure and our foundation models to deliver superior price-performance and lower inference costs").

The honest counterweight: as of August 2026 there is no public, independently verified benchmark showing a XuanTie-based server CPU or a Zhenwu accelerator matching a current-generation Western part on performance per watt at scale. The claims are Alibaba's own. What *is* verifiable is the direction and the money.

## The AI infrastructure build-out

The capex series is the strategy made numerical:

| Period | Capex | Note |
|---|---|---|
| FY2024 (to 31 Mar 2024) | RMB 32,087 m | Pre-pivot baseline |
| FY2025 | RMB 85,972 m | +168% |
| FY2026 | RMB 126,063 m (US$18,275 m) | +47% |
| Quarter ended 30 Jun 2026 | RMB 67,678 m (US$9,975 m) | +75% YoY; more in one quarter than all of FY2024 |

Alibaba's stated reasons for the June 2026 spike: "fluctuations in procurement cycles, increase in CPU-compute capacity driven by anticipated growing customer adoption of AI agents, and higher pricing of a broad range of chip components." Two of those three are worth noting. **CPU compute for agents** — not just accelerators — because agentic workloads are orchestration-heavy and tool-call-heavy, which is CPU and network work as much as matrix multiply. And **higher pricing of chip components**, which is what a constrained supply chain looks like on an income statement.

The FY2026 20-F commits to continue: "We will continue to invest in AI infrastructure... building a reliable, efficient and globally distributed AI infrastructure network," and "We will continue to expand T-Head's compute supply and contribute high-quality compute to our cloud infrastructure and MaaS platform."

Funding: the HK$80 billion share placing priced 24 August 2026, plus RMB 71,774 million (US$10,405 million) of other bank borrowings at 31 March 2026 "primarily used for our capital expenditures".

## Export controls and how Chinese cloud providers have responded

The FY2026 20-F's risk factors are the best primary-source summary available. Condensed:

- **Since 2022** the US has implemented successive measures restricting export to China of advanced computing chips, advanced semiconductors, supercomputer technology, semiconductor manufacturing equipment, and components and technology for manufacturing such equipment in China — including "export restrictions on advanced computing chips of Nvidia."
- **Japan and the Netherlands** issued parallel restrictions on advanced chip-manufacturing equipment.
- **January 2026:** the US House of Representatives passed the **Remote Access Security Act**, which if enacted would restrict China-based companies' access to compute resources of service providers powered by advanced US chips — closing the "rent, don't buy" workaround.
- The Commerce Department has indicated it is developing a **Supply Chain ICTS Class Rule** on cloud computing products and services, which could restrict Chinese-headquartered cloud providers in the US market — a direct threat to Alibaba Cloud's international expansion.
- **February 2026:** the US Department of Defense added Alibaba Group to the **Chinese Military Companies (CMC) list**, then withdrew the list; Alibaba warns it may be included when republished.
- **From the other direction:** in May 2023 the Cyberspace Administration of China restricted a US memory manufacturer's products from key infrastructure, and in **September 2025** it requested Chinese technology companies halt purchases of certain chips — pushing domestic demand toward domestic silicon whether or not it is competitive.
- **Outbound investment:** the US Treasury Outbound Investment Rule took effect 2 January 2025 and was codified by the **COINS Act in December 2025**, restricting US investment into Chinese semiconductor, quantum and AI companies.

**The four-part response pattern, common to Alibaba, Tencent, Baidu and ByteDance:**

1. **Stockpile before each control tightens.** Successive rounds of restriction produced buying waves ahead of effective dates.
2. **Buy the derated export-compliant parts** (Nvidia H20 and similar) while they remain legal, accepting worse memory bandwidth and interconnect.
3. **Build domestic silicon** — Alibaba's T-Head, Huawei's Ascend, Baidu's Kunlun, Cambricon. Accept a performance deficit and compensate with cluster scale and software.
4. **Compensate in software and architecture.** This is where the model work meets the infrastructure work, and it is not a coincidence that Chinese labs led on inference-efficient architectures: sparse mixture-of-experts with very low active-parameter fractions (Qwen3.5's 397B-A17B, DeepSeek's V3/V4 line), linear-attention hybrids that cut KV-cache cost by 4× (Qwen3-Next, Qwen3.5, Kimi Linear), aggressive quantisation (FP8 checkpoints published alongside BF16 as standard), and multi-token prediction for speculative decoding. When you cannot buy more FLOPs, you buy fewer FLOPs per token. See `05`.

The cancellation of the **Cloud Intelligence Group spin-off in November 2023**, explicitly attributed to export-control uncertainty, is the clearest evidence that this constraint shapes corporate structure and not just procurement.

## International expansion

Alibaba Cloud's overseas footprint was built out from 2015: Singapore (August 2015, and the designated overseas headquarters), United States (October 2015), Korea via SK Holdings C&C (April 2016), Japan as a SoftBank joint venture (May 2016), Germany with Vodafone (November 2016), India (December 2017), Indonesia (February 2018), Philippines (June 2021). It was the official cloud services provider to the Olympic Games from January 2017. In September 2022 it pledged US$1 billion to upgrade its global partner ecosystem.

The current region and availability-zone count could not be confirmed from a first-party page during research; secondary summaries give figures around 29 regions and 87 availability zones, which is **`needs-verification`**.

The strategic position outside China is asymmetric. In Asia-Pacific — particularly South-East Asia, where Lazada and a large Chinese-merchant customer base give it distribution — Alibaba Cloud is a genuine competitor to AWS, Azure and Google Cloud. In North America and Europe it is a minor player facing an increasingly hostile regulatory posture (see the ICTS cloud rule above). The FY2026 20-F's framing — "a reliable, efficient and globally distributed AI infrastructure network" — is aspirational for the West and operational for Asia and the Middle East.

## Open-source contributions

Beyond Qwen (the subject of `04`–`08`), the notable open-source outputs:

- **XuanTie C910 RTL** (open-sourced October 2021) and subsequent core releases.
- **ModelScope** — Alibaba's model hub, the Chinese-market alternative to Hugging Face, which mirrors the Qwen releases and is the recommended download route for users without Hugging Face access (`SGLANG_USE_MODELSCOPE=true`, `VLLM_USE_MODELSCOPE=true`).
- **MS-SWIFT** — the ModelScope fine-tuning framework, one of the three training frameworks Alibaba itself recommends for Qwen (`07`).
- **Qwen-Agent**, **Qwen Code**, **Qwen-MM-Plugins**, **FlashQLA** (a linear-attention kernel library built on TileLang, MIT-licensed) — the tooling around the models.
- Participation in international open-source foundations in software engineering, cloud-native applications and databases, per the FY2026 20-F.
- **Dragonwell** (an OpenJDK distribution), **Nacos**, **Dubbo**, **RocketMQ**, **Seata** and **Higress** in the Java/microservices world — a large and long-standing contribution that predates the AI era. These are `needs-verification` as to current status but are well-established Apache Software Foundation or CNCF projects of Alibaba origin.

## Sources

- [Alibaba Group Holding Ltd, Form 20-F FY2026](https://www.sec.gov/Archives/edgar/data/1577552/000119312526231755/baba-20260331.htm) — SEC EDGAR, filed 20 May 2026: cloud revenue and growth, 35.8% AI cloud share, PAI and Lingjun, Apsara/Shenlong/Pangu/Luoshen, PolarDB/AnalyticDB/Lindorm, T-Head GPU in production, capex series, capital commitments, full export-control and CMC List risk factors, bank borrowings
- [Alibaba Group Announces June Quarter 2026 Results (PDF)](https://data.alibabagroup.com/ecms-files/1532295521/fa5d65fc-9b3e-4e82-a8fc-4ce1c3e2c407/Alibaba%20Group%20Announces%20June%20Quarter%202026%20Results.pdf) — segment revenue and EBITA, AI product revenue, Omdia 38.1% figure, Zhenwu M890 and 650+ customers, quarterly capex and its drivers
- [T-Head — Wikipedia](https://en.wikipedia.org/wiki/T-Head) — founding, C-Sky acquisition, XuanTie 910, Hanguang 800, Yitian 710, Zhenyue 510, PPU series
- [RISC-V — Wikipedia](https://en.wikipedia.org/wiki/RISC-V) — XuanTie 910 specifications and open-sourcing, C920/C907/R910, C930 and RVA23, China's RISC-V policy direction
- [Alibaba Cloud — Wikipedia](https://en.wikipedia.org/wiki/Alibaba_Cloud) — founding date, international data-centre timeline, partner ecosystem pledge

## Open questions

- Current Alibaba Cloud region and availability-zone counts are `needs-verification` — the first-party global-locations page was not readable.
- All T-Head chip specifications (process nodes, core counts, clock speeds, performance claims) are `needs-verification` against first-party documentation.
- No independently verified benchmark of Zhenwu, PPU or XuanTie C930 against current Western parts was located. Treat all comparative performance claims as vendor or press assertions.
- Alibaba Cloud's revenue split between China and international is `needs-verification`.
- The status of the announced multi-year AI infrastructure investment programme (widely reported at RMB 380 bn over three years from February 2025) could not be confirmed in the FY2026 20-F text retrieved; treat that specific figure as `needs-verification`. The audited capex series above is the reliable substitute.
