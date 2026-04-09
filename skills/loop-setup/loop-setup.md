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

**`monitor.py`** -- progress dashboard for monitoring the loop in real time.

<HARD-GATE>
You MUST use the template at `skills/_shared/monitor-template.py`. Read it and write it VERBATIM as `monitor.py` in the output directory. Do NOT write your own dashboard. Do NOT modify the template. It handles Windows port detection quirks, auto-refresh, Chart.js rendering, and git log fallback. Copy it exactly.
</HARD-GATE>

Read `skills/_shared/monitor-template.py` and write it verbatim as `monitor.py` in the output directory. No substitutions needed — it works with any autoeval loop as-is.

**`run-loop.py`** -- cross-platform wrapper script (Python, stdlib only) that launches claude sessions with auto-restart.

<HARD-GATE>
You MUST use the template at `skills/_shared/run-loop-template.py`. Read it, substitute ONLY the configuration variables, and write it verbatim to the output directory. Do NOT write your own run-loop.py from scratch. Do NOT modify the logic, the Popen usage, the Ctrl+C handling, or the session management. The template has been tested and fixed for cross-platform issues (Windows signal handling, process killing) that you will get wrong if you write it yourself.
</HARD-GATE>

Read `skills/_shared/run-loop-template.py` and write it to the output directory, substituting ONLY these values in the configuration block at the top:
- `{runner_model}` — the user's chosen runner model
- `{effort}` — the user's chosen effort level
- `{timeout_minutes}` — calculated as 2x the expected time for {max_iterations} iterations (minimum 30 minutes)

Do NOT change anything else in the template. The template uses `Popen` (not `subprocess.run`), does NOT use `-p` flag (the prompt is a positional argument for interactive mode), and has double Ctrl+C handling. These are all intentional.

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

**After user confirms**, ask two questions in sequence:

**Question 1: Where to run?**

> "How do you want to run the loop?
>
> **A. Claude API** (default) — uses `claude` CLI, costs tokens, best quality
> **B. Local model** — uses a compatible CLI (e.g., `claudish`) pointed at a local model (e.g., Gemma 4 via LM Studio). Free to run overnight.
>
> Default: A"

If user picks **B**, ask for:
- CLI command (e.g., `claudish`)
- Model name (e.g., `gemma-4-27b`)

Both the runner and deep reasoning calls will use the same CLI and model.

If user picks **A**, use defaults: CLI = `claude`.

**Question 2: Model and effort?**

> "Which models and effort level?
>
> **Runner model:** `sonnet` (recommended), `haiku` (cheapest), `opus` (strongest)
> **Deep reasoning model:** `opus` (recommended), `sonnet` (cheaper)
> **Effort:** `high` (recommended), `medium`, `low`
>
> Defaults: runner=`sonnet`, deep=`opus`, effort=`high`"

Skip the runner model question if they already specified a local model in Question 1.

Substitute the user's choices into the templates:
- `CLI` variable in `run-loop.py` config block
- `{runner_model}`, `{effort}` into `run-loop.py` config block
- `{deep_model}` into `program.md` where `{deep_model}` appears
- `{deep_cli}` into `program.md` where `{deep_cli}` appears
- `{max_iterations}` (default: 15) into the Session Limits section of `program.md`

Update `state.md` to `phase: complete`.

<HARD-GATE>
After the user confirms AND selects models, you MUST present the full kickoff instructions below. This is the FINAL output of the entire autoeval process. The user needs to know exactly how to run the loop. Do NOT end the conversation without showing these commands. Do NOT summarize or abbreviate them.
</HARD-GATE>

Present the following in full:

---

**You're all set. Here's how to run everything:**

**Step 1 — Start the loop** (open a terminal):

```bash
cd {output_dir}
python run-loop.py
```

This launches claude sessions that auto-restart with fresh context every {max_iterations} iterations. A hard timeout of {timeout_minutes} minutes acts as a safety net.

**Step 2 — Monitor progress** (open a second terminal):

```bash
cd {output_dir}
python monitor.py
```

Opens a live dashboard at `http://localhost:8080` — score chart, component breakdown, hypothesis history. Auto-refreshes every 30 seconds.

**Step 3 — Steer the loop** (optional, any time):

Append to `steering.md` to guide the agent without stopping the loop:

```markdown
## after <commit-hash>
Your guidance here. The agent reads this before each iteration.
```

**Controls:**
- **Stop the loop:** Ctrl+C once kills the current session; Ctrl+C again within 3s stops the loop
- **Resume:** `python run-loop.py` (picks up from git history)
- **Permanent changes:** edit `program.md` — takes effect at next session restart
- **Custom timeout:** `python run-loop.py --timeout 45`

> **Permission modes:** `run-loop.py` uses `--dangerously-skip-permissions` — only run in isolated environments (containers, VMs). Edit the script to use `--enable-auto-mode` for safer unattended operation.

---

---
