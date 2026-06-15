#!/usr/bin/env bash
set -euo pipefail

ROOT="${DEBUG_ROOT:-.debug}"

usage() {
  echo "Usage:"
  echo "  $0 <slug> [question title]"
  echo
  echo "Example:"
  echo "  $0 current-investigation 'Current bug investigation snapshot'"
  echo "  $0 root-cause 'What is the most likely root cause?'"
}

if [[ $# -lt 1 ]]; then
  usage
  exit 1
fi

RAW_SLUG="$1"
shift || true
TITLE="${*:-$RAW_SLUG}"

SLUG="$(printf '%s' "$RAW_SLUG" \
  | tr '[:upper:]' '[:lower:]' \
  | sed -E 's/[^a-z0-9._-]+/-/g; s/^-+//; s/-+$//')"

if [[ -z "$SLUG" ]]; then
  echo "Error: invalid slug."
  exit 1
fi

mkdir -p "$ROOT"

LAST_NUM="$(find "$ROOT" -maxdepth 1 -type d -name 'Q[0-9][0-9]-*' -print \
  | sed -E 's|.*/Q([0-9][0-9])-.*|\1|' \
  | sort -n \
  | tail -1 || true)"

if [[ -z "$LAST_NUM" ]]; then
  NUM=1
else
  NUM=$((10#$LAST_NUM + 1))
fi

QID="$(printf 'Q%02d' "$NUM")"
QDIR="$ROOT/${QID}-${SLUG}"

if [[ -e "$QDIR" ]]; then
  echo "Error: $QDIR already exists."
  exit 1
fi

mkdir -p "$QDIR/notes" "$QDIR/artifacts"

cat > "$QDIR/global_issue.md" <<EOM
# ${QID}: ${TITLE}

## Symptom
TODO

## Expected behavior
TODO

## Actual behavior
TODO

## Reproduction steps
TODO

## Environment
TODO

## Relevant commands
TODO

## Relevant logs
TODO

## Suspected files / modules
- TODO

## Constraints
- Do not modify business code during investigation.
- Do not write a patch unless explicitly requested.
- Record facts, hypotheses, evidence, counter-evidence, and next experiments separately.
EOM

cat > "$QDIR/brief.md" <<EOM
# Brief: ${QID} ${TITLE}

## Question
TODO: State the precise question being investigated.

## Why this question matters
TODO: Explain how this question helps narrow down the bug.

## Scope
- Analyze only this question.
- Do not modify business code.
- Do not jump to final patch unless explicitly requested.
- Separate facts, hypotheses, evidence, counter-evidence, and next experiments.

## Out of scope
- TODO

## Expected output
- Suspicious code paths
- Confirmed facts
- Hypotheses with evidence
- Verification experiments
- Confidence level
EOM

cat > "$QDIR/claude.md" <<EOM
# Claude Investigation: ${QID} ${TITLE}

## Current understanding
TODO

## Facts
- TODO

## Hypotheses
### H1: TODO
- Evidence:
- Counter-evidence:
- How to verify:
- Confidence:

## Suspicious code paths
- TODO

## Proposed experiments
1. TODO

## Agreement with Codex
- TODO

## Disagreement with Codex
- TODO

## Questions for Codex / user
- TODO
EOM

cat > "$QDIR/codex.md" <<EOM
# Codex Investigation: ${QID} ${TITLE}

## Current understanding
TODO

## Facts
- TODO

## Hypotheses
### H1: TODO
- Evidence:
- Counter-evidence:
- How to verify:
- Confidence:

## Suspicious code paths
- TODO

## Proposed experiments
1. TODO

## Agreement with Claude
- TODO

## Disagreement with Claude
- TODO

## Questions for Claude / user
- TODO
EOM

cat > "$QDIR/evidence.md" <<EOM
# Evidence: ${QID} ${TITLE}

## Logs
TODO

## Command outputs
TODO

## Observed behavior
TODO

## Relevant code snippets
TODO

## Notes
TODO
EOM

cat > "$QDIR/experiments.md" <<EOM
# Experiments: ${QID} ${TITLE}

## Experiment 1
- Purpose:
- Command / change:
- Expected result:
- Actual result:
- Interpretation:

## Experiment 2
- Purpose:
- Command / change:
- Expected result:
- Actual result:
- Interpretation:
EOM

cat > "$QDIR/consensus.md" <<EOM
# Local Consensus: ${QID} ${TITLE}

## Confirmed facts
- TODO

## Strongest hypotheses
### H1: TODO
- Supported by:
- Contradicted by:
- Confidence:
- Next verification:

## Disagreements
- Claude:
- Codex:
- Current judgment:

## Next experiments
1. TODO

## Patch direction, if confirmed
- TODO

## Do not do
- TODO
EOM

cat > "$QDIR/open_questions.md" <<EOM
# Open Questions: ${QID} ${TITLE}

- TODO
EOM

cat > "$QDIR/prompt_claude.md" <<EOM
你现在参与一个 bug 排查任务。请只分析下面这个问题目录：

- ${QDIR}

请先阅读：
- ${QDIR}/global_issue.md
- ${QDIR}/brief.md
- ${QDIR}/evidence.md
- ${QDIR}/codex.md 如果存在有效内容
- ${QDIR}/consensus.md 如果存在有效内容

你的任务：
1. 只围绕 ${QID}: ${TITLE} 这个问题分析。
2. 不要修改业务代码。
3. 不要修改 Codex 的文件。
4. 把你的局部观点写入 ${QDIR}/claude.md。
5. 如需追加过程性记录，新建文件到 ${QDIR}/notes/claude-YYYYMMDD-HHMM.md，不要覆盖旧 notes。
6. 结论必须区分 fact / hypothesis / evidence / counter-evidence / next experiment。
7. 如果你认为问题定义不准确，请在 ${QDIR}/claude.md 里增加 “Scope correction” 部分。
8. 暂时不要写 patch，除非用户明确要求。

输出重点：
- 当前最可疑的代码路径
- 已确认事实
- 候选根因假设
- 每个假设的证据和反证
- 下一步最小验证实验
- 置信度
EOM

cat > "$QDIR/prompt_codex.md" <<EOM
你现在参与一个 bug 排查任务。请只分析下面这个问题目录：

- ${QDIR}

请先阅读：
- ${QDIR}/global_issue.md
- ${QDIR}/brief.md
- ${QDIR}/evidence.md
- ${QDIR}/claude.md 如果存在有效内容
- ${QDIR}/consensus.md 如果存在有效内容

你的任务：
1. 只围绕 ${QID}: ${TITLE} 这个问题分析。
2. 不要修改业务代码。
3. 不要修改 Claude 的文件。
4. 把你的局部观点写入 ${QDIR}/codex.md。
5. 如需追加过程性记录，新建文件到 ${QDIR}/notes/codex-YYYYMMDD-HHMM.md，不要覆盖旧 notes。
6. 不要默认 Claude 的判断是正确的；需要明确写出同意、不同意和替代解释。
7. 结论必须区分 fact / hypothesis / evidence / counter-evidence / next experiment。
8. 暂时不要写 patch，除非用户明确要求。

输出重点：
- 当前最可疑的代码路径
- 对 Claude 观点的同意点
- 对 Claude 观点的分歧点
- 候选根因假设
- 每个假设的证据和反证
- 下一步最小验证实验
- 置信度
EOM

echo "Created: $QDIR"
echo
echo "Claude prompt:"
echo "  $QDIR/prompt_claude.md"
echo
echo "Codex prompt:"
echo "  $QDIR/prompt_codex.md"
