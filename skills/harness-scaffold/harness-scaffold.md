---
name: harness-scaffold
description: "Phase 4 of autoeval -- generate the seed implementation with marked edit surface that the meta-agent will iterate on. Use when autoeval orchestrator routes to Phase 4, or when user invokes directly."
---

# Phase 4: Harness Scaffolding

Generate the seed implementation that the meta-agent will iterate on. This is intentionally minimal -- a working baseline, not a good solution. The meta-agent's job is to make it better.

## Prerequisites

- Read `.planning/autoeval/problem.md`, `.planning/autoeval/metric.md`, `.planning/autoeval/eval-strategy.md`
- Confirm we're in Phase 4 via `state.md`
- The eval suite from Phase 3 must exist and pass its sanity check

## Process

### Step 1: Design the Edit Surface

Based on the problem and loop type, determine:

**What the meta-agent CAN modify (edit surface):**
- The core implementation files where the optimization happens
- Mark these clearly with comments:
  ```
  # === EDIT SURFACE START ===
  # The meta-agent may modify anything between these markers
  ...
  # === EDIT SURFACE END ===
  ```

**What the meta-agent must NOT modify (fixed infrastructure):**
- Data loading and I/O wiring
- The eval suite and scoring functions
- Environment configuration
- The edit surface markers themselves

If interactive, present the edit surface plan and confirm with the user.

### Step 2: Generate Seed Implementation

Create the seed harness file(s) in the output directory:

**Requirements:**
- Language and framework chosen based on the problem domain
- Intentionally minimal -- the simplest possible approach that produces valid output
- Must run without errors
- Must produce output that the eval suite can score
- Edit surface clearly marked
- Fixed infrastructure clearly separated (in a different file or outside the markers)

**Common patterns by loop type:**
- **Training Loop:** `train.py` with basic model + training loop
- **Agent Harness Loop:** `agent.py` with system prompt + basic tool
- **Generative Output Loop:** `generate.py` with simplest synthesis approach
- **Algorithm Performance Loop:** `solution.py` with brute-force implementation
- **Retrieval/Ranking Loop:** `retrieval.py` with basic keyword search
- **Pipeline Optimization:** `pipeline.py` with sequential processing
- **Simulation Calibration:** `sim.py` with default parameters
- **Strategy/Decision:** `strategy.py` with naive heuristic
- **Adversarial:** `defense.py` with basic rules (or `attack.py`)
- **Data Curation:** `curate.py` with random sampling
- **Control Systems:** `controller.py` with simple PID
- **Interface Optimization:** layout/config files with default values

### Step 3: Generate Fixed Infrastructure

Create any supporting files the seed needs:
- Data loading utilities (if needed)
- Output formatting (to match eval expectations)
- Configuration files
- Helper scripts for running the harness

These files should be clearly documented as "do not modify" in comments.

### Step 4: Verify Baseline

Run the seed harness end-to-end:

1. Execute the seed implementation
2. Score its output with the eval suite
3. Record the baseline score

**The baseline score should be:**
- Above zero (the system produces something scoreable)
- Below the ceiling (there's room to improve)
- Near the floor value defined in Phase 2

Write `.planning/autoeval/baseline-score.md`:

```markdown
# Baseline Score

**Score:** [X.XX]
**Date:** [YYYY-MM-DD]
**Seed files:** [list of files]

## Component Breakdown
| Component | Score | Floor | Ceiling |
|-----------|-------|-------|---------|
| [name]    | [X.XX] | [min] | [max] |

## Notes
[Any observations about the baseline -- what's working, what's clearly broken, where the easy wins are]
```

### Step 5: Advance State

Update `state.md` to `phase: 5`.

If interactive, tell the user: "Seed harness built. Baseline score: [X.XX] (floor: [Y], ceiling: [Z]). Moving to program.md generation -- writing the directive the meta-agent will follow."

Return control to the orchestrator.
