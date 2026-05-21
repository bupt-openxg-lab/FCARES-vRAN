---
name: ran-project
description: Use this skill for the ran research project when discussing or implementing C algorithm code, Python data analysis, experiment workflows, reproducibility, or paper writing. It defines explicit Planning Mode and Implementation Mode behavior, plus authorization boundaries for C and Python code changes.
---

# RAN Project

## Overview

This skill defines the working protocol for the ran research project. Use it to keep planning, implementation, C algorithm changes, Python analysis, experiments, and paper writing aligned with the user's intent.

## Interaction Modes

This project uses two explicit working modes: Planning Mode and Implementation Mode.

### Planning Mode

Use Planning Mode when the user is discussing ideas, requirements, experiment design, algorithm choices, paper structure, architecture, or feasibility.

In Planning Mode, Codex must:

- Do not edit files unless the user explicitly asks for a draft artifact.
- First restate the user's goal in concrete terms.
- Identify assumptions, missing information, possible ambiguity, and feasibility risks.
- Ask targeted questions when the requirement is underspecified or could materially change the solution.
- Separate confirmed facts from hypotheses.
- Avoid inventing project details, experiment results, citations, performance numbers, or implementation constraints.
- Prefer small iterative proposals over large final designs.
- End with either:
  - a concise agreed plan, or
  - specific questions needed before implementation.

Codex should not treat discussion as permission to implement. Phrases such as "我在想", "我们讨论一下", "是否可行", "帮我分析" imply Planning Mode unless the user says otherwise.

### Implementation Mode

Use Implementation Mode when the user gives a concrete target and asks Codex to execute, implement, modify, run, test, generate, or finalize something.

In Implementation Mode, Codex must:

- Follow the agreed plan or the user's latest explicit instruction.
- Inspect the relevant code/data/paper files before editing.
- Keep changes scoped to the stated goal.
- Avoid unrelated refactors.
- Run appropriate validation when available, such as build, tests, sample scripts, or sanity checks.
- Report what changed, what was verified, and any remaining uncertainty.
- If new ambiguity appears during implementation, stop and ask only when making a wrong assumption could cause significant rework or invalid results.

Implementation Mode is triggered by phrases such as "实现", "修改", "运行", "生成", "按这个方案做", "开始写代码", "落实到项目里".

## Mode Switching Rules

- Default to Planning Mode when the user's intent is exploratory.
- Default to Implementation Mode only when the requested outcome is concrete and actionable.
- If the mode is unclear, state the assumed mode briefly before proceeding.
- The user can explicitly switch modes by saying "进入规划模式" or "进入实现模式".
- A plan discussed in Planning Mode is not considered approved until the user explicitly says to implement it.

## Change Authorization Boundaries

Codex must treat C code and Python code differently because they carry different risk profiles in this project.

## Build Validation

When validating gNB builds in this repository, prefer the user's actual build flow:

```bash
cd /home/bupt/wlh/ran/cmake_targets
sudo ./build_oai --gNB -w OXGRF
```

Use this command when the user asks for the real/full gNB build or when confirming changes against the OXGRF workflow. If sudo or environment permissions are not available, report that clearly and fall back to narrower object/target compilation only as a partial check.

### Default Rule

- C changes are conservative: ask first unless already authorized by an agreed plan.
- Python analysis changes are flexible: proceed when the goal is clear, but protect data, results, reproducibility, and shared interfaces.

### C Code Changes

C code changes require explicit user approval before editing, unless all of the following are true:

- The target has already been discussed in Planning Mode.
- The expected behavior, input/output contract, and scope are clear.
- The user has explicitly approved moving to Implementation Mode for that target.
- The change stays within the agreed files/modules and does not alter unrelated APIs.
- The change does not introduce new external dependencies, build-system changes, or major architectural changes.

If any of these conditions are not met, Codex must ask before modifying C code.

C code includes `.c`, `.h`, build files directly affecting C compilation, algorithm kernels, memory-layout definitions, public C APIs, and C/Python binding layers.

### Python Code Changes

Codex may modify Python code without additional approval when the requested goal is clear and the changes are local to data analysis, plotting, experiment scripts, preprocessing, postprocessing, or utility code.

When writing Python scripts, Codex must assume the user may describe features incrementally. Before adding a new script, function, parser, plotter, analyzer, or utility, Codex should first inspect the existing Python code for similar functionality and prefer reuse, extension, or light refactoring over duplicating logic.

Codex should still ask before modifying Python code when the change would:

- Delete or overwrite data.
- Change experiment semantics in a way that affects reported results.
- Modify shared APIs used by C code or paper figures.
- Add heavy dependencies.
- Change project structure.
- Replace an established analysis method with a different statistical or algorithmic method.
- Affect reproducibility, such as random seeds, dataset splits, or evaluation metrics.

### Previously Discussed Goals

If a goal has been clearly discussed and agreed in Planning Mode, Codex may implement it without asking again, including C code changes, as long as the implementation stays within the agreed scope.

A goal is considered clear only when these are known:

- What behavior should be added, changed, or preserved.
- Which files/modules are likely involved.
- What inputs and outputs are expected.
- What correctness checks or tests should be used.
- What should not be changed.

If new ambiguity appears during implementation, Codex should pause and ask only when the ambiguity could affect correctness, public interfaces, experiment validity, or significant rework.
