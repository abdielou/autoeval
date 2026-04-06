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

**`monitor.py`** -- progress dashboard for monitoring the loop in real time. Generate this file using the template in `skills/_shared/monitor-template.py`. The template is a self-contained Python script (stdlib only) that:

- Reads `progress.jsonl` for iteration data (scores, components, hypotheses, timestamps)
- Falls back to parsing `git log` commit messages if `progress.jsonl` doesn't exist yet
- Serves an HTML dashboard on `localhost:8080` using Chart.js (CDN)
- Auto-refreshes every 30 seconds

Read `skills/_shared/monitor-template.py` and write it verbatim as `monitor.py` in the output directory. Do NOT modify the template -- it is designed to work with any autoeval loop.

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

Present the final summary to the user and **wait for explicit confirmation before providing the kickoff command:**

---

**autoeval setup complete.** Here's what was built:

**Problem:** [one-line summary]
**Loop type:** [classification]
**Baseline score:** [X.XX] (floor: [Y], ceiling: [Z])
**Eval cases:** [N] cases across [M] dimensions
**Output directory:** `{output_dir}`

**What the loop will do:** The meta-agent will modify [edit surface description], run the eval suite after each change, keep improvements, and commit them. Each iteration takes roughly [time estimate based on eval complexity].

**Before you kick it off, confirm:**
1. The eval references are real data, not synthetic stubs (see eval integrity report)
2. The baseline score makes sense for a seed implementation
3. You're comfortable with the edit surface -- what the agent is allowed to change
4. The output directory is correct and you're OK with it being modified autonomously

Ready to start? (yes/no)

---

<HARD-GATE>
Wait for the user to explicitly confirm. Do NOT provide the kickoff command until the user says yes. If they raise concerns, address them first.
</HARD-GATE>

**After user confirms**, ask which model and effort level to use:

> "Which model and effort level for the loop?
>
> **Model:** `opus` (strongest, slowest, most expensive), `sonnet` (balanced -- recommended), `haiku` (fastest, cheapest, least capable)
>
> **Effort:** `high` (thorough -- recommended), `medium` (faster iterations), `low` (fastest, minimal reasoning)
>
> Defaults: `--model sonnet --effort high`"

Update `state.md` to `phase: complete` and present the kickoff:

```bash
cd {output_dir}
claude --dangerously-skip-permissions --model {model} --effort {effort} --append-system-prompt-file program.md "Start the optimization loop. Read the edit surface files, run the eval, and begin iterating."
```

> `--append-system-prompt-file` loads program.md as background instructions. The quoted string is the initial prompt that kicks off the first iteration.
>
> **Permission modes:** `--dangerously-skip-permissions` bypasses all permission prompts — only use in isolated environments (containers, VMs). For safer unattended operation with background safety checks, use `--enable-auto-mode` instead.

**Monitoring -- open a second terminal and run:**

```bash
cd {output_dir}
python monitor.py
```

This opens a live dashboard at `http://localhost:8080` showing:
- Composite score progression over iterations
- Individual component scores (toggleable)
- Best score, floor/ceiling bounds
- Hypothesis text on hover
- Summary stats: iteration count, time elapsed, delta from baseline

The dashboard auto-refreshes every 30 seconds.

**Other controls:**
- Stop the loop: interrupt the Claude Code session (Ctrl+C)
- Steer the loop: edit `program.md` constraints or domain guidance, then restart

**Expanding the eval:**
- See `evals/README.md` for how to add cases
- See `.planning/autoeval/eval-strategy.md` for coverage gaps and expansion plan

---
