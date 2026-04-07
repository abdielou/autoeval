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

0. **Check Steering** -- Before each iteration, check `steering.md` for guidance from the user. Run:
   ```bash
   if [ -f steering.md ] && [ -s steering.md ]; then
     CURRENT_COMMIT=$(git rev-parse --short HEAD)
     cat steering.md
   fi
   ```
   The file contains entries tagged with commit hashes:
   ```
   ## after abc1234
   Focus on X, stop trying Y.
   ```
   Find the entry whose commit hash is closest to (but not after) the current HEAD. That is your active steering. Follow it — it overrides your own hypothesis when they conflict. If no entry applies to the current commit, ignore steering and hypothesize freely.

1. **Hypothesize** -- Use the deep reasoning model to generate your hypothesis. Run:
   ```bash
   claude --model {deep_model} -p "$(cat <<'PROMPT'
   I'm optimizing [problem description]. Current best score: [X.XX].

   Recent experiments (git log):
   $(git log --oneline -10)

   Current implementation:
   $(cat [edit surface files])

   Last eval result:
   $(cat [last eval output])

   Worst-scoring eval cases: [list them]

   Failed experiments (avoid repeating these):
   $(if [ -d failed_experiments ] && [ "$(ls failed_experiments/ 2>/dev/null)" ]; then ls -1 failed_experiments/ | tail -10; else echo "None yet"; fi)

   Active steering from the user (if any):
   $(if [ -f steering.md ] && [ -s steering.md ]; then cat steering.md; else echo "None"; fi)

   What is the single most promising change to try next? Be specific: name the file, the function, and the exact modification. Explain your reasoning. If there is active steering, prioritize it. Avoid approaches that match failed experiments listed above — read the relevant diff files if you're unsure whether your idea overlaps.
   PROMPT
   )"
   ```
   Read the response and use it to guide your next change. You may adapt the suggestion if it doesn't fully apply, but take the reasoning seriously.

2. **Change** -- Make a focused modification to the edit surface based on the hypothesis. Change one thing at a time so you can attribute score changes to specific modifications.

3. **Run** -- Execute the eval suite:
   [exact eval command]
   [If metric is noisy: run N times and take the median — see Noisy Metric Protocol below]

4. **Score** -- Read the eval output. The composite score is [description of scoring]. Current best: [baseline from Phase 4].

5. **Log** -- Append the eval result to `progress.jsonl` for the monitoring dashboard:
   ```bash
   echo '{"iteration": N, "timestamp": "'$(date -Iseconds)'", "score": X.XX, "components": {COMPONENT_SCORES}, "hypothesis": "HYPOTHESIS_TEXT", "kept": true/false, "failure_reason": "REASON_OR_NULL"}' >> progress.jsonl
   ```
   Replace N with the iteration number, COMPONENT_SCORES with the components object from the eval JSON output, and HYPOTHESIS_TEXT with your hypothesis. Always append — even for reverted experiments (set `"kept": false`). For reverted experiments, set `failure_reason` to a brief explanation of what regressed (e.g., "sharpness dropped 0.12, firing_pattern regressed"). For kept experiments, set it to `null`.

6. **Decide:**
   - If score >= previous best:
     ```bash
     git add -A && git commit -m "hypothesis: [why] -- change: [what] -- score [X.XX]"
     ```
   - If score < previous best — **save the failed experiment before reverting:**
     ```bash
     mkdir -p failed_experiments
     ITER=$(printf "%03d" N)
     SCORE=$(printf "%.4f" X.XX)
     DIFF_FILE="failed_experiments/${ITER}_score_${SCORE}.md"
     cat > "$DIFF_FILE" << 'EXPEOF'
     # Failed Experiment — Iteration N

     ## Hypothesis
     [Your hypothesis text]

     ## Score
     [X.XX] (previous best: [Y.YY], delta: [diff])

     ## Component Scores
     [Paste the component scores from the eval output]

     ## Diff
     ```diff
     $(git diff)
     ```

     ## Why It Failed
     [Brief analysis of why this change hurt the score — which components regressed and why]
     EXPEOF
     git checkout -- .
     ```
     The diff, hypothesis, score, and failure analysis are preserved in `failed_experiments/` for future reference. The agent should check this folder before hypothesizing to avoid repeating failed approaches.

7. **Repeat** -- Go back to step 1. Try a different approach.

## Exploration Schedule

Every 5th iteration, do an **exploration round** instead of incremental improvement. Use the deep reasoning model to generate a fundamentally different approach:

```bash
claude --model {deep_model} -p "$(cat <<'PROMPT'
I'm optimizing [problem description]. Current best score: [X.XX].

Full experiment history:
$(git log --oneline)

Current implementation:
$(cat [edit surface files])

I've been making incremental improvements but may be stuck in a local optimum.
Propose a fundamentally different approach — not a tweak, but a different
algorithm, architecture, or strategy. Explain why it might break through
the current ceiling.
PROMPT
)"
```

- Try the suggested approach on a new branch: `git checkout -b explore/[idea]`
- Consider techniques you haven't tried yet from the Domain-Specific Guidance
- Look at the worst-scoring eval cases — what class of problem is the current approach failing on?
- If the branch scores better, merge it back. If not, return to main.

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

## Session Limits

Run exactly **{max_iterations} iterations** in this session. A wrapper script will restart you with fresh context.

**This is non-negotiable:**
- Count your iterations. After iteration {max_iterations}, you MUST exit.
- Do NOT ask the user what to do. Do NOT offer options. Do NOT wait for input.
- Do NOT stop early because context is getting full. The wrapper handles restarts.
- Do NOT be conversational about ending. Just do it.

**Exit procedure** (execute mechanically after iteration {max_iterations}):
1. Revert any uncommitted changes: `git checkout -- .`
2. Print exactly: `SESSION COMPLETE: {N} iterations, best score: {X.XX}`
3. Stop immediately. No summary. No suggestions. No questions.

The wrapper script (`run-loop.py`) will relaunch you with fresh context. All state is on disk — git log, progress.jsonl, the code itself. The next session picks up seamlessly.

**If stuck before reaching the limit**, use an exploration round rather than stopping:
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
