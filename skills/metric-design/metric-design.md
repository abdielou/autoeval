---
name: metric-design
description: "Phase 2 of autoeval -- interactive metric exploration and scoring function design with stress-testing. Use when autoeval orchestrator routes to Phase 2, or when user invokes directly."
---

# Phase 2: Metric Design

The hardest and most valuable phase. Help the user find an automatic scoring function that the meta-agent can use to evaluate each iteration of the optimization loop.

<HARD-GATE>
This phase MUST be interactive. The scoring function is the foundation of the entire loop -- a bad metric produces a bad loop. Do not rush or skip the stress-testing step.
</HARD-GATE>

## Prerequisites

- Read `.planning/autoeval/problem.md` -- load the full problem context
- Confirm we're in Phase 2 via `state.md`

## Process

### Step 1: Explore Scoring Approaches

Walk through these questions **one at a time**, adapting based on the problem type from Phase 1:

1. **Can the output be compared against known-good references?**
   - Exact match (diff, string comparison)
   - Similarity metrics (spectral matching, cosine similarity, BLEU/ROUGE)
   - Structural comparison (AST diff, schema validation)

2. **Is it binary pass/fail?**
   - Does the code compile / tests pass / output validate
   - Does the system meet a hard constraint (latency < Xms, memory < Y MB)

3. **Does it need LLM-as-judge?**
   - Qualitative evaluation where human judgment matters
   - Can we define rubrics that make LLM scoring reliable?
   - Cost implications: LLM-as-judge is expensive per iteration

4. **Is there a proxy metric that correlates with quality?**
   - Latency, token count, error rate, code coverage
   - Something cheap to measure that predicts the expensive-to-measure quality

5. **Can multiple metrics compose into a single score?**
   - Weighted sum (0.5 x accuracy + 0.3 x speed + 0.2 x size)
   - Threshold + optimize (must pass X, then optimize Y)
   - Pareto (track multiple metrics, keep improvements on any without regression)

### Step 2: Define Floor and Ceiling

For the proposed metric:
- **Floor:** What score does a random/trivial/worst-case baseline get? (This is the starting point)
- **Ceiling:** What score represents perfect performance? (This is the theoretical maximum)
- **Current state:** If there's an existing system, where does it score?

These establish the dynamic range. A metric where floor=0.95 and ceiling=1.0 is very different from floor=0.1 and ceiling=1.0.

### Step 3: Stress-Test the Metric

Use the Socrates skill (if available) to pressure-test the proposed metric. If Socrates is not available, work through these questions manually:

**Gameability:**
- Can the meta-agent find a shortcut that scores well but doesn't actually solve the problem?
- Example: An agent that always outputs the same "safe" answer might score well on average but be useless for hard cases
- What constraints prevent gaming?

**Signal strength:**
- Do small meaningful improvements produce measurably different scores?
- Or is the metric too noisy -- random variation drowns out real improvements?
- How many eval cases are needed for a reliable signal?

**Cost per evaluation:**
- How long does one eval run take? (This x hundreds of iterations = total loop time)
- Can we use a cheap proxy for exploration and the expensive metric for validation?

**Failure modes:**
- What does the meta-agent optimize for if the metric has blind spots?
- Are there known weaknesses we should document for the user?

### Step 4: Lock In the Metric

Present the final metric design to the user for approval:

> "Here's the scoring function I'm proposing: [description]. It composes [N] components with weights [X]. The floor is [Y] and ceiling is [Z]. Known weaknesses: [list]. Does this look right?"

Wait for explicit approval before proceeding.

### Step 5: Write Metric Design

Write `.planning/autoeval/metric.md`:

```markdown
# Metric Design

## Scoring Function
[Plain language description of what the metric measures]

## Pseudocode
[Pseudocode implementation of the scoring function]

## Components
| Component | Weight | Description | Floor | Ceiling |
|-----------|--------|-------------|-------|---------|
| [name]    | [0.X]  | [what it measures] | [min] | [max] |

## Composite Score Formula
[How components combine into a single score]

## Floor and Ceiling
- **Floor (worst case):** [value] -- [what produces this score]
- **Ceiling (perfect):** [value] -- [what this represents]

## Known Weaknesses
- [Gameability risk and mitigation]
- [Blind spots in the metric]
- [Cost considerations]

## Data Requirements
- [Reference files, APIs, datasets needed for scoring]
- [Where to source them]
```

### Step 6: Handoff Decision

Update `state.md` to `phase: 3`.

If `auto: true` in state, tell the user: "Metric locked in. Proceeding autonomously through eval suite, harness, program.md, and loop setup."

Otherwise, ask: **"Metric locked in. Want me to build the rest autonomously, or step through each phase?"**

- If autonomous: set `interactive: false` in `state.md`
- If step-through: set `interactive: true` in `state.md`

Return control to the orchestrator.
