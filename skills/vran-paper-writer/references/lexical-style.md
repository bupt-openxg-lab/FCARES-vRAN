# Lexical Style and Word-Choice Discipline

Use this reference whenever drafting, translating, or polishing vRAN paper prose. The goal is not to
make the writing plain or weak; it is to keep the language close to high-frequency systems-paper
usage and avoid inflated vocabulary that sounds less credible than the underlying claim.

## Core Rule

Prefer common words and phrase patterns from top systems/vRAN papers over rare, dramatic, or
"academic-sounding" substitutions. Strong words are allowed only when the evidence supports the
strength of the claim and the word is natural in systems conference prose.

When uncertain, choose the plainer option:

| Prefer | Avoid unless justified |
|--------|------------------------|
| significant | extraordinary, exceptional, remarkable |
| substantial | tremendous, massive, enormous |
| severe | extreme, catastrophic |
| challenging | formidable, daunting |
| improve / reduce / increase | revolutionize, dramatically improve |
| show / demonstrate | unveil, illuminate |
| observe / find | discover, reveal (unless the claim is genuinely surprising) |
| limitation / overhead / trade-off | drawback, pitfall (unless discussing a failure mode) |
| effective / efficient | optimal, perfect, ideal |

## Preferred Systems-Paper Verbs

Use these verbs as the default pool for claims and mechanisms:

- **Measurement claims**: observe, find, measure, quantify, characterize, show
- **Design actions**: propose, design, build, implement, integrate, augment, adapt
- **Modeling actions**: estimate, predict, approximate, fit, classify, bound
- **Evaluation claims**: reduce, improve, increase, decrease, maintain, preserve, incur, achieve
- **Causality and motivation**: motivate, indicate, suggest, require, enable, limit, constrain

Avoid replacing these with rarer synonyms just to vary style. Repetition is acceptable when it keeps
technical meaning stable.

## Intensifier Policy

Do not use intensifiers unless the sentence contains evidence or the word is part of a measured
comparison.

| Avoid | Better |
|-------|--------|
| highly efficient | efficient / low-overhead |
| extremely challenging | challenging / difficult under [condition] |
| dramatically reduces | reduces by X% / substantially reduces |
| exceptionally accurate | achieves X error / closely tracks |
| remarkably lightweight | adds X us per slot / has low overhead |

If a result has a number, let the number carry the force. Prefer "reduces timeout rate by X%" over
"dramatically reduces timeout rate."

## Rare-Word and Overclaim Check

Before outputting prose, scan for these words and either replace them or justify them explicitly:

- extraordinary, exceptional, remarkable, tremendous, massive, enormous, revolutionary
- drastic, dramatically, extremely, incredibly, highly, substantially (allowed with evidence)
- optimal, perfect, ideal, guaranteed, always, never
- novel (allowed only for a clearly defended contribution claim)
- robust (allowed only if evaluated across varying conditions)

Preferred replacements:

| If draft says | Usually replace with |
|---------------|----------------------|
| extraordinary improvement | significant improvement / X% improvement |
| dramatic reduction | substantial reduction / X% reduction |
| extreme interference | severe interference |
| massive overhead | high overhead / prohibitive overhead |
| optimal allocation | feasible allocation / throughput-oriented allocation / selected allocation |
| robust performance | stable performance across [conditions] |
| novel proxy | lightweight proxy / slot-level proxy / previously unexplored proxy |

## Frequency-Oriented Phrase Patterns

Use these common systems-paper patterns:

- "We observe that ..."
- "This suggests that ..."
- "This motivates ..."
- "To address this, ..."
- "HCS augments ..."
- "Figure X shows ..."
- "Under severe interference, ..."
- "Compared with [baseline], HCS ..."
- "The key insight is that ..."
- "This design keeps [overhead/path/operation] ..."

Avoid ornamental patterns:

- "It is noteworthy that ..."
- "This paper embarks on ..."
- "A paradigm-shifting ..."
- "An unprecedented ..."
- "We leverage the extraordinary capability of ..."

## Claim Strength Calibration

Match word strength to evidence:

- **Observation from one experiment**: "We observe", "results suggest", "in our setup"
- **Repeated across controlled settings**: "We find", "we show", "consistently"
- **Formal or implementation guarantee**: "ensures" only if enforced by code or definition
- **Empirical improvement**: state the metric and condition; avoid global wording

Weak but defensible:
"Under severe cache contention, HCS reduces the timeout rate by X% relative to vanilla OAI."

Too strong without broader evidence:
"HCS provides robust and dramatic performance gains under all interference conditions."

## Final Lexical Pass

For each paragraph, perform this check:

1. Are the main verbs drawn from the preferred systems-paper verb pool?
2. Are adjectives/adverbs necessary, or can numbers and conditions carry the claim?
3. Would the sentence still be precise if an inflated word were replaced by "significant",
   "substantial", "severe", "lightweight", or a measured value?
4. Does any word imply universality, optimality, or novelty beyond the paper's evidence?

When a stronger word remains, mention the reason briefly in the notes only if it is non-obvious.
