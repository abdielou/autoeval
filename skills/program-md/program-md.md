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

Write `program.md` in the output directory with the following sections. Adapt the template to the specific problem -- this is a starting structure, not a rigid format. Include the Noisy Metric Protocol section only if the scoring function has noisy components (LLM-as-judge, stochastic outputs). Set the time budget based on how long one eval run takes.

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

## Time Budget

Each iteration should take no more than [N] minutes. If an approach requires more time, break it into smaller steps. The goal is rapid iteration — many small experiments beat a few large ones.

## Iteration Protocol

Follow this loop indefinitely:

1. **Hypothesize** -- Review the current implementation, previous experiment results (check `git log --oneline`), and worst-scoring eval cases. Formulate a specific, testable hypothesis: "I believe [change] will improve [component] because [reasoning]."

2. **Change** -- Make a focused modification to the edit surface. Change one thing at a time so you can attribute score changes to specific modifications.

3. **Run** -- Execute the eval suite:
   [exact eval command]
   [If metric is noisy: run N times and take the median — see Noisy Metric Protocol below]

4. **Score** -- Read the eval output. The composite score is [description of scoring]. Current best: [baseline from Phase 4].

5. **Log** -- Append the eval result to `progress.jsonl` for the monitoring dashboard:
   ```bash
   echo '{"iteration": N, "timestamp": "'$(date -Iseconds)'", "score": X.XX, "components": {COMPONENT_SCORES}, "hypothesis": "HYPOTHESIS_TEXT", "kept": true/false}' >> progress.jsonl
   ```
   Replace N with the iteration number, COMPONENT_SCORES with the components object from the eval JSON output, and HYPOTHESIS_TEXT with your hypothesis. Always append — even for reverted experiments (set `"kept": false`).

6. **Decide:**
   - If score >= previous best: git add -A && git commit -m "hypothesis: [why] -- change: [what] -- score [X.XX]"
   - If score < previous best: git checkout -- . to revert all changes (but progress.jsonl keeps the record)

7. **Repeat** -- Go back to step 1. Try a different approach.

## Exploration Schedule

Every 5th iteration, do an **exploration round** instead of incremental improvement:

- Try a fundamentally different approach, not a tweak to the current one
- Consider techniques you haven't tried yet from the Domain-Specific Guidance
- Look at the worst-scoring eval cases — what class of problem is the current approach failing on?
- If stuck in a local optimum, create a new branch (`git checkout -b explore/[idea]`) to try a radical departure without losing the current best. If it scores better, merge it back. If not, return to main.

## Experiment Branching

When you have multiple promising directions:

1. Create a branch: `git checkout -b explore/[direction-name]`
2. Run several iterations on that branch
3. If the branch's best score exceeds main: merge it back (`git checkout main && git merge explore/[name]`)
4. If the branch stalls: return to main (`git checkout main`) and try a different direction
5. Keep branches around — a stalled branch may become useful later when combined with other improvements

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

## Noisy Metric Protocol

[Include this section if the scoring function has noisy components like LLM-as-judge]

When the metric has noisy components:
- Run the eval [N] times per iteration (e.g., 3-5 runs)
- Use the **median** score (not mean — more robust to outliers)
- Only count an improvement if the median exceeds the previous best
- For the final score of a promising experiment, run [M] times (e.g., 10 runs) to confirm

## NEVER STOP

Continue experimenting indefinitely. There is always room for improvement. If you feel stuck, use an exploration round rather than stopping.

When you've exhausted incremental improvements in one direction:
- Step back and reconsider the overall architecture
- Try approaches you haven't tried yet
- Look at the worst-scoring cases and focus there
- Create an exploration branch for a radically different approach
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
