---
name: loop-setup
description: "Phase 6 of autoeval -- wire everything together, verify the baseline runs end-to-end, and provide the kickoff command. Use when autoeval orchestrator routes to Phase 6, or when user invokes directly."
---

# Phase 6: Loop Setup

The final phase. Wire everything together, verify the full loop works end-to-end, and give the user the command to kick off the autonomous experiment.

## Prerequisites

- Read all prior state
- Confirm we're in Phase 6 via `state.md`
- All artifacts must exist: eval suite, seed harness, program.md

## Process

### Step 1: Environment Setup

Generate environment files in the output directory:

**Dependency manifest** (choose based on problem domain):
- Python: `pyproject.toml` or `requirements.txt`
- Node: `package.json`
- Other: appropriate manifest for the domain

Include all dependencies needed by:
- The seed harness
- The eval suite
- The scoring functions

**Dockerfile** (optional -- generate if the problem benefits from isolation):
- Base image appropriate for the domain
- Install dependencies
- Copy project files
- Set working directory

**.gitignore** (if not already present in output dir):
- Generated artifacts (model checkpoints, audio files, etc.)
- Temporary files
- Environment-specific files

### Step 2: Initialize Git

If the output directory is not already a git repo:

```bash
cd {output_dir}
git init
```

Stage and commit all generated files:

```bash
git add -A
git commit -m "autoeval: initial baseline -- score {baseline_score}"
```

If the output directory IS already a git repo, commit the autoeval files:

```bash
git add program.md evals/ {seed_files} {env_files}
git commit -m "autoeval: initial baseline -- score {baseline_score}"
```

### Step 3: End-to-End Verification

Run the complete loop once manually to verify everything works:

1. **Install dependencies** (if applicable)
2. **Run the seed harness** -- confirm it executes without errors
3. **Run the eval suite** -- confirm it scores the seed output
4. **Verify the score matches the baseline from Phase 4**

If anything fails, fix it before presenting the kickoff command. The user should never receive a broken loop.

### Step 4: Present Kickoff

Update `state.md` to `phase: complete`.

Present the final summary to the user:

---

**autoeval setup complete.**

**Problem:** [one-line summary]
**Loop type:** [classification]
**Baseline score:** [X.XX] (floor: [Y], ceiling: [Z])
**Eval cases:** [N] cases across [M] dimensions

**To start the autonomous experiment:**

```bash
cd {output_dir}
claude --prompt-file program.md
```

**Monitoring:**
- Check progress: `git log --oneline` -- each successful iteration is a commit with the score
- Stop the loop: interrupt the Claude Code session (Ctrl+C)
- Steer the loop: edit `program.md` constraints or domain guidance, then restart

**Expanding the eval:**
- See `evals/README.md` for how to add cases
- See `.planning/autoeval/eval-strategy.md` for coverage gaps and expansion plan

---
