---
name: program-md
description: "Phase 5 of autoeval -- generate the meta-agent directive (program.md) that drives the autonomous optimization loop. Use when autoeval orchestrator routes to Phase 5, or when user invokes directly."
---

# Phase 5: Program.md Generation

Write the meta-agent directive -- the `program.md` file that tells Claude Code how to run the autonomous optimization loop. This is the instruction manual for the overnight experiment.

## Prerequisites

- Read all prior state: `problem.md`, `metric.md`, `eval-strategy.md`, `baseline-score.md`
- Confirm we're in Phase 5 via `state.md`
- The seed harness and eval suite must exist and be verified

## Process

### Step 1: Generate program.md

Write `program.md` in the output directory with the following sections. Adapt the template to the specific problem -- this is a starting structure, not a rigid format.

```markdown
# [Problem Name] -- Autonomous Optimization Loop

## Goal

[2-3 sentences describing what this loop is trying to achieve, in plain language. Include the current baseline score and what a good target would be.]

## Edit Surface

You may modify these files:
- `[file1.py]` -- [what it contains, what to experiment with]
- `[file2.py]` -- [what it contains, what to experiment with]

You MUST NOT modify:
- `evals/` -- the eval suite is fixed. Do not modify scoring or cases.
- `[fixed_file.py]` -- [why it's fixed]
- `program.md` -- do not modify this directive

## Iteration Protocol

Follow this loop indefinitely:

1. **Analyze** -- Review the current implementation and previous experiment results. Identify a specific hypothesis to test.

2. **Change** -- Make a focused modification to the edit surface. Change one thing at a time so you can attribute score changes to specific modifications.

3. **Run** -- Execute the eval suite:
   [exact eval command]

4. **Score** -- Read the eval output. The composite score is [description of scoring]. Current best: [baseline from Phase 4].

5. **Decide:**
   - If score >= previous best: git add -A && git commit -m "experiment: [what you changed] -- score [X.XX]"
   - If score < previous best: git checkout -- . to revert all changes

6. **Repeat** -- Go back to step 1. Try a different approach.

## Scoring Interpretation

[Explain what the score means, what each component measures, and what tradeoffs to watch for]

- Score range: [floor] to [ceiling]
- Current baseline: [X.XX]
- Target: [reasonable target based on problem]

## Domain-Specific Guidance

[Tailored hints based on the loop type and problem domain. Examples:]

- [Specific techniques to try]
- [Common pitfalls to avoid]
- [Resources or approaches relevant to this domain]

## Constraints

- Do NOT modify the eval suite or scoring functions
- Do NOT modify fixed infrastructure files
- Do NOT skip the eval -- every change must be scored
- Do NOT make multiple unrelated changes in one iteration
- Keep experiments focused -- one hypothesis per iteration
- Commit messages must include the score for tracking

## NEVER STOP

Continue experimenting indefinitely. There is always room for improvement. If you feel stuck, try a radically different approach rather than stopping.

When you've exhausted incremental improvements in one direction:
- Step back and reconsider the overall architecture
- Try approaches you haven't tried yet
- Look at the worst-scoring cases and focus there
- Consider the domain guidance above for new ideas
```

### Step 2: Stress-Test with Socrates

Use the Socrates skill (if available) to review `program.md` for:

**Ambiguity:**
- Could any instruction be interpreted in a way that leads the meta-agent off-rails?
- Are the edit surface boundaries crystal clear?
- Is the eval command unambiguous?

**Missing constraints:**
- Could the meta-agent game the eval? (e.g., hardcoding outputs for known test cases)
- Are there modifications that would technically improve the score but defeat the purpose?
- Add explicit constraints for any discovered gaps

**Clarity:**
- Would a fresh Claude Code instance understand exactly what to do from this file alone?
- Are all file paths correct and commands runnable?

If Socrates is not available, review these questions manually. Fix any issues found.

### Step 3: Advance State

Update `state.md` to `phase: 6`.

If interactive, tell the user: "program.md generated. Moving to loop setup -- wiring everything together and verifying the baseline."

Return control to the orchestrator.
