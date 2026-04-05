---
name: eval-suite
description: "Phase 3 of autoeval -- build eval cases, scoring functions, and coverage strategy. The most critical phase of the optimization loop. Use when autoeval orchestrator routes to Phase 3, or when user invokes directly."
---

# Phase 3: Eval Suite

The crown jewel of autoeval. The eval suite is what makes the autonomous loop work -- a bad eval produces a bad loop. This phase builds the test cases, scoring functions, and coverage strategy that the meta-agent will be measured against.

<HARD-GATE>
Even in autonomous mode, if the eval suite has weak coverage or the scoring function can't be verified, PAUSE and ask the user. Never produce a bad eval silently.
</HARD-GATE>

## Prerequisites

- Read `.planning/autoeval/problem.md` and `.planning/autoeval/metric.md`
- Confirm we're in Phase 3 via `state.md`
- Know the output directory from `state.md`

## Process

### Step 1: Coverage Strategy

Before writing any code, map the eval landscape. This is a planning step.

**Identify coverage dimensions:**
- What types of inputs exist? (categories, difficulty levels, edge cases)
- What failure modes should be tested? (adversarial, degenerate, boundary)
- What reference data is needed? (golden outputs, comparison baselines)
- What's testable now vs. needs future expansion?

**For each dimension, assess:**
- How many cases are needed for a reliable signal?
- Can cases be generated programmatically or do they need manual curation?
- Are there existing datasets or references to draw from?

If interactive: present the coverage strategy to the user and get feedback before proceeding.

Write `.planning/autoeval/eval-strategy.md`:

```markdown
# Eval Coverage Strategy

## Dimensions
| Dimension | Description | Cases Needed | Source |
|-----------|-------------|-------------|--------|
| [name]    | [what it tests] | [count] | [generated/curated/reference] |

## Reference Data
- [What reference data is needed]
- [Where to source it]
- [How to format it]

## Coverage Gaps
- [What can't be tested automatically]
- [What needs future expansion]
- [Suggested approach for filling gaps]

## Eval Size Target
- Seed eval: [N] cases (enough for reliable signal)
- Target eval: [M] cases (comprehensive coverage)
```

### Step 2: Scaffold Eval Directory

Create the eval directory structure in the output directory:

```
{output_dir}/evals/
  cases/              # Individual test cases
  scoring/            # Scoring function implementations
  runner.py           # Runs all cases, aggregates scores, outputs summary
  README.md           # How to run, expand, and understand the eval
```

The runner and scoring files should use the language most natural for the problem domain. Python is the default -- adapt if the problem calls for something else (e.g., `runner.js` for a Node project).

**Runner requirements:**
- Accept a command or path to the system under test
- Run all cases in `cases/`
- Apply scoring functions from `scoring/`
- Output a JSON summary: `{"score": 0.XX, "components": {...}, "cases": [...]}`
- Print a human-readable summary to stdout
- Exit code 0 on success (regardless of score), non-zero on eval infrastructure failure

### Step 3: Build Cases

For each dimension from the coverage strategy:

If interactive:
1. Propose a batch of cases for the dimension
2. Explain what each case tests and why
3. Get user feedback -- too easy? missing edge cases? wrong assumptions?
4. Write the approved cases to `evals/cases/`

If autonomous:
1. Generate cases for all dimensions
2. Include edge cases and adversarial scenarios
3. Write to `evals/cases/`

**Case format:** Each case is a file (or entry in a cases file) containing:
- Input data or input specification
- Expected behavior description (not necessarily exact output -- could be constraints)
- Difficulty/category tags for analysis

The exact format depends on the problem domain. For simple cases, a JSON or YAML file per case works well. For complex cases (e.g., reference audio files), use a directory per case.

### Step 4: Implement Scoring Functions

Translate the metric design from Phase 2 into working code.

Create scoring function(s) in `evals/scoring/`:
- Each metric component gets its own function
- A composer function combines components into the composite score
- All functions are well-documented with expected input/output types

**Quality checks:**
- Scoring functions must be deterministic (same input = same score), except for LLM-as-judge components which should use temperature=0 or majority voting
- Scores must be in the expected range (0-1 or the defined floor-ceiling range)
- Edge cases handled: empty input, malformed output, timeout

### Step 5: Sanity Check

Run the eval suite against a trivial/null input to verify it works:

**Verify:**
- Runs without errors
- Scores are not all zeros (eval is measuring something)
- Scores are not all ones (eval has discriminating power)
- Floor value matches expectation from Phase 2
- Individual case results make sense

If any check fails, fix the eval before proceeding. If interactive, show results to the user.

### Step 6: Eval Integrity Validation

<HARD-GATE>
This step catches evals that look functional but measure nothing real. Do NOT skip this. A bad eval that runs cleanly is worse than one that crashes -- it produces false confidence and wastes the entire loop.
</HARD-GATE>

**Check 1: Reference data provenance ("grading your own homework")**

Trace every reference, baseline, or ground truth used in scoring back to its source. For each one, classify it:

| Source | Verdict |
|--------|---------|
| Real-world data (recordings, datasets, human-labeled) | Valid |
| External authoritative source (published benchmarks, specs) | Valid |
| Generated by the same approach as the system under test | **INVALID -- self-referential** |
| Generated by a simpler version of the same technique | **INVALID -- self-referential** |
| Hardcoded expected outputs that mirror the seed implementation | **INVALID -- circular** |

If ANY reference is self-referential or circular, **stop and surface this to the user:**

> "The eval is grading its own homework. [Component X] compares the system output against [reference Y], which was generated using [same/similar technique]. This means a high score just means the system matches itself, not that it's actually good. The loop will converge on matching the synthetic reference, not on real quality."
>
> "To make this eval meaningful, you need [specific real data]. For example: [concrete suggestion for what to source and where to find it]."

Do NOT offer to generate synthetic references as a fallback. Do NOT silently proceed. The user must provide real reference data or consciously accept the limitation.

**Check 2: Discriminating power**

Run the eval against two inputs that a human would clearly judge as different quality:
- The seed implementation output (should score mid-range)
- A deliberately degraded version (shuffled, noisy, truncated -- should score significantly lower)

If the score difference is less than 0.15, the eval lacks discriminating power. Surface this:

> "The eval can't tell good from bad. [Seed scored X.XX, degraded scored Y.XX]. The scoring function needs sharper signals."

**Check 3: Ceiling reachability**

Verify the theoretical ceiling score is achievable -- that there exists some input that could score near 1.0 (or the defined ceiling). If the scoring function's components are structurally capped below the ceiling (e.g., a metric that maxes out at 0.7 due to how it's computed), flag it.

**After all checks pass**, state what was validated:

> "Eval integrity verified: references sourced from [X], discriminating power confirmed ([seed: X.XX, degraded: Y.XX]), ceiling reachable."

### Step 7: Document Coverage

Write `evals/README.md`:

```markdown
# Eval Suite

## Running the Eval

[Exact command to run the eval with a target system]

## Output Format

JSON summary to stdout with structure:
{"score": 0.XX, "components": {"name": 0.XX}, "cases": [...]}

## Current Coverage

| Dimension | Cases | Status |
|-----------|-------|--------|
| [name]    | [N]   | [complete/partial] |

## Coverage Gaps

- [What's missing and why]
- [How to add more cases]
- [Suggested reference data sources]

## Expanding the Eval

To add a new case:
1. [Steps to create a new case file]
2. [How to add scoring for it]
3. [How to verify it works]
```

### Step 8: User Eval Review

<HARD-GATE>
The user MUST review and approve the eval before proceeding. The eval is the foundation of the entire loop -- if it measures the wrong thing, the loop optimizes toward garbage. Do NOT skip this step or rush through it.
</HARD-GATE>

Walk the user through the eval in plain language. No code -- the goal is for the user to understand what the loop will optimize toward and decide if that's what they actually want.

**Part 1: What's being scored**

Present each scoring component as a row:

| Component | Weight | What it rewards | What it punishes |
|-----------|--------|----------------|-----------------|
| [name] | [X%] | [plain-English description of what a high score means] | [what a low score means] |

For each component, give a concrete example: "A score of 0.3 on [component] means [specific description]. A score of 0.9 means [specific description]."

**Part 2: What's NOT being scored**

Explicitly list qualities that a human might care about but the eval does not capture:

> "This eval does **not** measure:
> - [Quality X] -- [why it's excluded and whether it matters]
> - [Quality Y] -- [why it's excluded and whether it matters]
>
> If any of these matter to you, we should add them before starting the loop."

This is critical. Unstated gaps become blind spots the meta-agent will exploit.

**Part 3: Score intuition**

Give the user concrete intuition for what scores mean in their domain:

> "For your problem, here's what different scores feel like:
> - **0.3** -- [concrete description of what a 0.3 output looks/sounds/behaves like]
> - **0.5** -- [concrete description]
> - **0.7** -- [concrete description]
> - **0.9** -- [concrete description]"

If possible, reference the baseline score: "Your seed implementation scores [X.XX], which corresponds to [description]."

**Part 4: Gaming risks**

Identify specific ways the meta-agent could inflate the score without genuine improvement:

> "Ways the agent could game this eval:
> - [Specific gaming strategy and what it would look like]
> - [Another strategy]
>
> The current eval [does/does not] have defenses against these. [If not: here's what we could add.]"

**After presenting all four parts**, ask:

> "Does this eval capture what you care about? Anything to add, remove, or reweight before we proceed?"

Wait for the user's response. If they request changes, make them and re-run the integrity validation (Step 6). Only proceed once the user explicitly approves.

### Step 9: Advance State

Update `state.md` to `phase: 4`.

Tell the user: "Eval approved. Moving to harness scaffolding -- creating the seed implementation the meta-agent will iterate on."

Return control to the orchestrator.
