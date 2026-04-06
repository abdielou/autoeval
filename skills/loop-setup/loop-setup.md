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

**`run-loop.py`** -- cross-platform wrapper script (Python, stdlib only) that launches claude sessions with auto-restart. Read `skills/_shared/run-loop-template.py` and write it to the output directory, substituting:
- `{runner_model}` — the user's chosen runner model
- `{effort}` — the user's chosen effort level
- `{timeout_minutes}` — calculated as 2x the expected time for {max_iterations} iterations (minimum 30 minutes)

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

**After user confirms**, ask which models and effort level to use:

> "The loop uses two models -- a **runner** for the main iteration cycle (editing code, running evals, committing) and a **deep reasoning model** for hypothesis generation and exploration rounds (called via `claude -p` one-shot).
>
> **Runner model** (runs the session, does most of the work):
> - `sonnet` -- balanced speed/quality (recommended)
> - `haiku` -- fastest, cheapest, good for narrow edit surfaces
> - `opus` -- strongest but expensive for a long-running loop
>
> **Deep reasoning model** (called for hypothesis + exploration rounds):
> - `opus` -- best for creative leaps and novel approaches (recommended)
> - `sonnet` -- cheaper, still capable
>
> **Effort:** `high` (thorough -- recommended), `medium` (faster iterations), `low` (fastest, minimal reasoning)
>
> Defaults: runner=`sonnet`, deep=`opus`, effort=`high`"

Substitute the user's chosen deep model into the `program.md` template where `{deep_model}` appears (the `claude --model {deep_model} -p` calls in the Hypothesize step and Exploration Schedule). Also substitute `{max_iterations}` (default: 15) into the Session Limits section of `program.md`.

Update `state.md` to `phase: complete` and present the kickoff:

---

**To start the loop** (Terminal 1):

```bash
cd {output_dir}
python run-loop.py
```

This launches claude sessions that auto-restart with fresh context every {max_iterations} iterations. A hard timeout of {timeout_minutes} minutes acts as a safety net.

**To monitor progress** (Terminal 2):

```bash
cd {output_dir}
python monitor.py
```

Live dashboard at `http://localhost:8080` showing:
- Composite score progression over iterations
- Individual component scores (toggleable)
- Best score, floor/ceiling bounds
- Hypothesis text on hover
- Summary stats: iteration count, time elapsed, delta from baseline

Auto-refreshes every 30 seconds.

**Controls:**
- Stop the loop: Ctrl+C in Terminal 1 (waits for current iteration to finish)
- Resume after stopping: `python run-loop.py` (picks up from git history)
- Steer the loop: edit `program.md` constraints or domain guidance — takes effect at next session restart
- Custom timeout: `python run-loop.py --timeout 45` (minutes per session)

**Expanding the eval:**
- See `evals/README.md` for how to add cases
- See `.planning/autoeval/eval-strategy.md` for coverage gaps and expansion plan

> **Permission modes:** `run-loop.py` uses `--dangerously-skip-permissions` — only run in isolated environments (containers, VMs). Edit the script to use `--enable-auto-mode` for safer unattended operation.

---
