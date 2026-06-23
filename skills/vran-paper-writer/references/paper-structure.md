# Paper Structure Guide — HCS vRAN Paper

Annotated outline for the full paper. Use this to:
- Know what belongs in each section
- Maintain argument continuity across sessions
- Verify completeness before submission

---

## Target Venue Style Notes

**SIGCOMM / MobiCom / INFOCOM / MobiSys style**:
- 12 pages (double-column, 10pt, ACM/IEEE format)
- Abstract: 150–200 words
- Introduction: 1–1.5 pages
- Background: 0.5–1 page (optional if tight)
- Design: 3–4 pages (main contribution)
- Evaluation: 3–4 pages
- Related Work: 0.5–1 page
- Conclusion: 0.25 page

---

## Section-by-Section Guide

### Abstract (~180 words)
**Must contain**:
1. Problem: vRAN scheduling ignores compute feasibility → timeout under interference
2. Observation: FFT latency as disturbance proxy; codeblock-grouped linear model
3. Contribution: HCS — a constraint-aware scheduler
4. Result: X% timeout reduction, Y improvement in effective throughput under contention

**Tone**: Dense, no fluff. Every sentence is a claim.

---

### 1. Introduction (~1 page)

**Paragraph 1 — vRAN context** (3–4 sentences)
- Operators moving to commodity-server vRAN; flexible and cost-effective
- But: real-time PHY processing must meet strict per-slot deadlines (~0.5 ms)

**Paragraph 2 — The problem** (4–5 sentences)  
- In practice, co-located workloads cause noisy-neighbor / cache interference
- Existing MAC schedulers are compute-blind: assign RBs without knowing compute load
- This causes deadline misses → corrupted slots → throughput collapse

**Paragraph 3 — Key observations** (3–4 sentences)
- Observation 1: FFT latency reflects system disturbance state in real time
- Observation 2: Decoding latency is linear in RB count *within* a codeblock group
- Observation 3: Codeblock count introduces step changes in compute cost

**Paragraph 4 — Our approach** (3–4 sentences)
- HCS: classify disturbance state → predict deadline-miss risk → cap RB allocation
- Lightweight enough for per-slot online use

**Paragraph 5 — Contributions** (bulleted)
- Measurement study of noisy-neighbor interference in OAI vRAN (§X)
- Computation feasibility model: disturbance state × codeblock grouping (§X)
- HCS scheduler design and OAI deployment results (§X)

**Paragraph 6 — Roadmap** (1–2 sentences)
- "The rest of the paper is organized as follows..."

---

### 2. Background and Motivation (~0.75 page)

**§2.1 vRAN Architecture**
- CU/DU/RU split; where MAC scheduling happens (vDU)
- Real-time constraint: slot duration 0.5 ms (NR numerology μ=1); PDSCH must be decoded before HARQ feedback

**§2.2 Interference in Commodity Servers**
- Noisy-neighbor effect: co-located VMs/containers compete for LLC, DRAM bandwidth
- Cache contention: LDPC decoding is memory-bandwidth-intensive → highly sensitive to LLC pressure
- Cite: prior work on interference in cloud/edge servers if available

**§2.3 Problem Statement**
- Formal: given interference, the actual decoding latency L(RB, state) may exceed deadline D
- Current schedulers set RB = argmax throughput without checking L(RB, state) ≤ D
- This section ends by motivating the measurement study in §3

---

### 3. Measurement Study (~1 page)

**§3.1 Experimental Setup**
- OAI platform; server spec; interference injection method (specify what generates noisy-neighbor / cache pressure)
- Metrics collected: FFT latency, LDPC decoding latency, RB count, codeblock count, slot deadline hit/miss

**§3.2 FFT Latency as Disturbance Proxy**
- Show: FFT latency changes significantly with interference, is measurable early in slot
- Justify: why FFT is a good proxy (measured before the heavier LDPC decoding)
- Key figure: CDF or scatter of FFT latency under normal / mild / severe interference

**§3.3 Decoding Latency vs. RB Count**
- Show: within a fixed codeblock count and disturbance state, latency is approximately linear in RB
- Show: codeblock count boundaries cause step changes
- Key figure: latency vs. RB scatter, colored by codeblock group

**§3.4 Disturbance State Classification**
- Three states: normal / mild / severe; derived from FFT latency thresholds
- Justify threshold choices (e.g., percentile-based)

---

### 4. System Design: HCS (~2 pages)

**§4.1 Overview**
- High-level architecture diagram: where HCS sits relative to MAC scheduler, RIC (if applicable)
- Two-phase design: (A) disturbance detection, (B) feasibility-constrained scheduling

**§4.2 Disturbance State Detection**
- Algorithm: measure FFT latency → classify state using thresholds
- Latency of this step (must be negligible relative to slot budget)

**§4.3 Computation Feasibility Model**
- Input: candidate RB allocation r, current codeblock count c, disturbance state s
- Output: predicted latency L̂(r, c, s); risk P(L̂ > D)
- Model: local linear model per (c, s) group — intercept + slope × r
- Training: offline, on OAI measurement data from §3
- Online use: simple linear evaluation — O(1) per scheduling decision

**§4.4 Constraint-Aware Scheduling**
- Modified scheduler: find max r* such that P(L̂(r*, c, s) > D) < threshold τ
- Fallback logic: if no valid r* exists, use minimum viable allocation
- Integration with existing OAI MAC scheduler (describe hook / API)

**§4.5 Design Choices and Alternatives**
- Why piecewise linear and not a neural network? → online latency, interpretability
- Why FFT proxy and not direct measurement? → FFT happens earlier in slot processing pipeline
- Why three states? → empirical finding that finer granularity provides diminishing returns

---

### 5. Evaluation (~2.5 pages)

**§5.1 Experimental Setup**
- OAI version; hardware; UE simulation or real UE; interference generation method
- Baseline: vanilla OAI MAC scheduler (throughput-maximizing, compute-blind)
- Metrics: computation timeout rate, effective throughput, RB utilization

**§5.2 Timeout Reduction**
- HCS vs. baseline under three interference levels
- Key result: X% reduction in timeout rate under severe interference
- Figure: bar chart or CDF of timeout rate

**§5.3 Effective Throughput**
- Effective throughput = throughput of successfully decoded slots (timeouts → zero contribution)
- HCS may allocate fewer RBs per slot but avoids timeouts → net improvement
- Figure: throughput vs. interference level for HCS vs. baseline

**§5.4 Overhead Analysis**
- Scheduling overhead: time added by HCS per slot (µs)
- Model accuracy: predicted vs. actual latency (RMSE or similar)

**§5.5 Sensitivity Analysis** (if space allows)
- Effect of threshold τ choice
- Effect of disturbance state misclassification rate

---

### 6. Related Work (~0.5 page)

**Group 1: Compute-aware vRAN scheduling**
- Nuberu (MobiCom 2021): GPU-aware scheduling; HCS differs by targeting CPU-side interference
- vrAIn (MobiCom 2020): DRL-based resource control; HCS is lightweight and deterministic

**Group 2: Interference modeling in cloud/edge**
- Prior work on noisy-neighbor effects; HCS leverages a novel proxy metric (FFT latency)

**Group 3: RAN functional split and real-time processing**
- Concordia, Slingshot: focus on fronthaul / PHY resilience; HCS addresses the scheduling layer

**Closing sentence**: Contrast the key differentiator — "Unlike prior work, HCS requires no hardware changes and integrates directly with an existing open-source vRAN platform."

---

### 7. Conclusion (~0.2 page)

- Restate problem (1 sentence)
- Restate approach (1–2 sentences)  
- Restate key results with numbers
- Forward-looking: future extension (e.g., to multi-UE scheduling, GPU-based vRAN, or O-RAN xApp integration)

---

## Status Tracker

Update this as sections are completed:

| Section | Chinese draft | English draft | Polished | Done |
|---------|--------------|---------------|----------|------|
| Abstract | — | — | — | — |
| 1. Introduction | — | — | — | — |
| 2. Background | ✅ | — | — | — |
| 3. Measurement | ✅ | — | — | — |
| 4. Design | — | — | — | — |
| 5. Evaluation | — | — | — | — |
| 6. Related Work | — | — | — | — |
| 7. Conclusion | — | — | — | — |

*(Update this table as you go — tell Claude which sections are done and it will update its context accordingly)*
