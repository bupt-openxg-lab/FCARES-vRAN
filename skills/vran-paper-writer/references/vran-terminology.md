# vRAN Terminology Reference

Preferred English renderings for key Chinese technical terms in this paper.
Use the "Preferred" column consistently throughout the paper.

## Core RAN Architecture Terms

| Chinese | Preferred English | Avoid |
|---------|------------------|-------|
| 虚拟无线接入网 | virtualized radio access network (vRAN) | virtual RAN |
| 基带处理单元 | baseband unit (BBU) | — |
| 分布式单元 | distributed unit (DU / vDU) | distributed node |
| 集中式单元 | central unit (CU / vCU) | centralized unit |
| 无线单元 | radio unit (RU) | radio head |
| 功能分割 | functional split | function split |
| 前传 | fronthaul | front-haul |
| 中传 | midhaul | mid-haul |

## Scheduler / MAC Layer Terms

| Chinese | Preferred English | Avoid |
|---------|------------------|-------|
| 资源块 | resource block (RB) | resource unit |
| 时隙 | slot | subframe (avoid for NR) |
| 调度器 | scheduler | schedule module |
| 调度决策 | scheduling decision | scheduling result |
| 候选RB分配 | candidate RB allocation | candidate scheduling |
| 安全RB上界 | safe RB limit | maximum safe RB |
| 计算截止时刻 | processing deadline | computation deadline |
| 截止时间违例 | deadline miss | timeout violation |
| 计算超时 | computation timeout | processing overflow |
| 有效吞吐量 | effective throughput | actual throughput |

## Physical Layer / LDPC Terms

| Chinese | Preferred English | Avoid |
|---------|------------------|-------|
| 码块 | codeblock (CB) | code block (two words OK in prose) |
| 码块数量 | codeblock count | number of codeblocks |
| LDPC译码 | LDPC decoding | LDPC decode |
| 译码时延 | decoding latency | decoding delay |
| FFT时延 | FFT processing latency | FFT delay |
| 下行共享信道 | PDSCH (Physical Downlink Shared Channel) | downlink channel |

## Interference / Disturbance Terms

| Chinese | Preferred English | Avoid |
|---------|------------------|-------|
| 系统侧扰动 | system-side disturbance | system noise |
| 干扰邻居 | noisy-neighbor interference | noisy neighbor effect |
| 缓存争用 | cache contention | cache conflict |
| 扰动状态 | disturbance state | interference state |
| 正常/轻度/重度 | normal / mild / severe | low/medium/high |
| 代理指标 | proxy indicator / proxy metric | proxy signal |

## Modeling Terms

| Chinese | Preferred English | Avoid |
|---------|------------------|-------|
| 局部线性模型 | local linear model | piecewise linear |
| 按码块分组 | codeblock-grouped / grouped by codeblock count | CB-based grouping |
| 性能模型 | performance model | performance formula |
| 在线推理 | online inference | real-time inference |
| 预测 | predict / estimate | calculate (if not a formula) |
| 阈值 | threshold | limit (use threshold for probabilistic context) |
| 风险 | risk / probability | chance |

## Evaluation Terms

| Chinese | Preferred English | Avoid |
|---------|------------------|-------|
| 计算超时率 | computation timeout rate | timeout frequency |
| 资源争用场景 | resource contention scenario | competing workload case |
| 吞吐量 | throughput | bandwidth |
| 部署验证 | deployment and validation | experiment verification |

## Citation-Worthy Claims Template

Use this framing pattern when asserting measurements:

> "We observe that [phenomenon], where [quantity] varies by [magnitude] across [conditions].
> This finding motivates [design decision]."

Never assert without evidence in the main body. All quantified claims need a figure/table reference.

---

## Common Mistranslations to Avoid

| Wrong | Correct |
|-------|---------|
| "timeout" used as a verb | "trigger a timeout" / "cause a deadline miss" |
| "the model" without antecedent | "our feasibility model" / "the codeblock-grouped model" |
| "performance" (generic) | specify: latency / throughput / timeout rate |
| "system" without qualifier | "the vRAN system" / "the OAI deployment" |
| "we found that it can" | "we show that" / "results demonstrate that" |
