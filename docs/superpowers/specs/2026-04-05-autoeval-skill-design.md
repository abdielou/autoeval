# autoeval — Skill Design Spec

A Claude Code skill that transforms a vague optimization problem into a fully scaffolded, runnable autonomous optimization loop. Invoked via `/autoeval <problem description>`.

## Core Concept

The skill bridges the gap between "I have an idea" and "I have an autonomous experiment running overnight." It guides users through problem definition, metric design, and eval suite construction — then scaffolds a complete loop that a Claude Code meta-agent can run autonomously.

The loop follows the universal pattern: **change -> run -> score -> keep/discard -> repeat**.

The meta-agent is always Claude Code via the `claude` CLI. There is no custom loop runner — the loop logic lives in `program.md`, a directive file that Claude Code follows autonomously. This matches the established patterns from autoagent (Kevin Gu) and autoresearch (Karpathy).

## Architecture

### Orchestrator + Phase Skills

The skill is decomposed into an orchestrator and six phase skills:

- **`autoeval`** — orchestrator. Entry point, arg parsing, state management, phase routing, resume logic.
- **`autoeval:problem-definition`** — Phase 1. Interactive discovery, loop type classification, exit ramp.
- **`autoeval:metric-design`** — Phase 2. Interactive metric exploration, stress-testing via Socrates, scoring function lock-in.
- **`autoeval:eval-suite`** — Phase 3. The crown jewel. Interactive eval case building, scoring implementation, coverage strategy.
- **`autoeval:harness-scaffold`** — Phase 4. Seed implementation generation with marked edit surface.
- **`autoeval:program-md`** — Phase 5. Meta-agent directive generation.
- **`autoeval:loop-setup`** — Phase 6. Environment setup, verification, kickoff instructions.

### Reference File

- **`loop-types.md`** — the 12 loop type taxonomy (Training, Agent Harness, Generative Output, Algorithm Performance, Retrieval & Ranking, Pipeline Optimization, Simulation Calibration, Strategy & Decision, Adversarial, Data Curation, Control Systems, Interface Optimization). Loaded by Phase 1 for classification. Maintained as a separate file for independent updates.

### State Directory

All phase state persists in `.planning/autoeval/`:

```
.planning/autoeval/
  state.md            # current phase, flags, output directory
  problem.md          # Phase 1 output
  metric.md           # Phase 2 output
  eval-strategy.md    # Phase 3 coverage map
  baseline-score.md   # Phase 4 baseline score
```

`state.md` fields:
- `phase`: current phase number (1-6) or "complete"
- `auto`: whether `--auto` was passed
- `interactive`: whether user chose step-through after Phase 2
- `output_dir`: resolved output directory path

This enables resume across sessions — on re-invocation, the orchestrator reads `state.md` to determine where to pick up.

## Invocation

```
/autoeval <problem description>
/autoeval --auto <problem description>
```

- Without `--auto`: Phases 1-2 are always interactive. After Phase 2 locks in the metric, the skill asks: "Metric locked in. Want me to build the rest autonomously, or step through each phase?"
- With `--auto`: Phases 1-2 are interactive. Phases 3-6 execute autonomously after the metric is agreed upon, with one exception — if the eval suite has weak coverage or the scoring function can't be verified automatically, the skill pauses and asks rather than producing a bad eval.

## Phase Details

### Phase 1: Problem Definition

**Mode:** Always interactive.

**Flow:**
1. Read the user's problem description from args
2. Ask clarifying questions one at a time:
   - What are you building?
   - What are the inputs and outputs?
   - What does "good" look like in plain language?
   - What constraints exist (hardware, latency, cost, dependencies)?
3. Classify against the loop type taxonomy (from `loop-types.md`)
4. Invoke Socrates to evaluate: is this an optimization problem or a "just build it" problem?
5. **Exit ramp** — if not an optimization problem:
   - Explain why the problem doesn't benefit from the loop pattern
   - Suggest what the user could do instead (e.g., "this is a just-build-it problem — try asking Claude Code directly")
   - Stop. Autoeval only builds loops.
6. If the problem maps to a composed loop (primary + nested): present both the simple and complex options, let the user choose
7. Determine output directory:
   - If working directory is empty: default to root
   - If working directory has existing files: ask the user where to scaffold

**Output:** `.planning/autoeval/problem.md`
- Problem summary
- Inputs/outputs
- Success criteria (plain language)
- Constraints
- Loop type classification with reasoning
- Output directory decision

### Phase 2: Metric Design

**Mode:** Always interactive.

**Flow:**
1. Load problem context from `.planning/autoeval/problem.md`
2. Walk through scoring function discovery, one question at a time:
   - Can output be compared against known-good references?
   - Is it binary pass/fail?
   - Does it need LLM-as-judge?
   - Is there a proxy metric that correlates with quality?
   - Can multiple metrics compose into a single score?
3. For each candidate metric, invoke Socrates to stress-test:
   - Can this metric be gamed? (meta-agent finds a shortcut that scores well but doesn't solve the problem)
   - Is the signal strong enough for hill-climbing?
   - Is it cheap enough to run on every iteration?
4. Establish floor (worst case / random baseline) and ceiling (perfect score)
5. If composite score: define weights and justify them
6. Lock in the final metric with user approval

**Output:** `.planning/autoeval/metric.md`
- Scoring function description (plain language + pseudocode)
- Metric components and weights (if composite)
- Floor and ceiling values
- Known weaknesses / gameability risks
- Data requirements (reference files, APIs, etc.)

**Gate:** This is the handoff point. After Phase 2 completes:
- If `--auto` was passed: proceed through Phases 3-6 autonomously
- Otherwise: ask "Metric locked in. Want me to build the rest autonomously, or step through each phase?"

### Phase 3: Eval Suite (The Crown Jewel)

**Mode:** Interactive by default, autonomous if handed off. Pauses even in autonomous mode if coverage is weak.

This is the most important phase. The eval suite is what makes the autonomous loop work — a bad eval produces a bad loop. The skill should spend the most interactive effort here.

**Flow:**
1. Load problem + metric context
2. **Coverage strategy first** — before writing any code:
   - What dimensions of the problem space need coverage? (input types, edge cases, difficulty levels)
   - What reference data is needed and where does it come from?
   - What's testable now vs. what needs future work?
   - Write to `.planning/autoeval/eval-strategy.md`
3. **Scaffold the eval directory** in the user's output location:
   ```
   evals/
     cases/          # individual test cases (input + expected behavior)
     scoring/        # scoring function implementations
     runner.py       # runs all cases, aggregates scores, outputs summary (language adapts to problem domain)
     README.md       # how to run, how to expand, coverage gaps
   ```
4. **Build cases interactively** — for each dimension in the strategy:
   - Propose a set of cases
   - Get user feedback (too easy? missing edge cases? wrong assumptions?)
   - Write the approved cases
5. **Implement scoring functions** — translate the metric from Phase 2 into working code
6. **Sanity check** — run the eval suite against a trivial/null input:
   - Runs without errors
   - Scores are not all zeros or all ones
   - Floor/ceiling values match expectations
7. **Document coverage gaps** — update `evals/README.md` with what's covered, what's missing, and how to add more

**Output:**
- `evals/` directory with runnable cases and scoring
- `.planning/autoeval/eval-strategy.md`

### Phase 4: Harness Scaffolding

**Mode:** Autonomous by default (interactive if user opted in).

**Flow:**
1. Load problem, metric, and loop type context
2. Generate seed implementation file(s):
   - Language/framework based on problem domain
   - Intentionally minimal — a working baseline, not a good solution
   - Edit surface marked with comments (e.g., `# === EDIT SURFACE START ===`)
3. Generate fixed infrastructure the meta-agent should NOT touch:
   - Data loading, I/O wiring, environment setup
   - Clearly separated from the edit surface
4. Verify the seed harness runs end-to-end:
   - Execute seed -> produce output -> score with eval suite
   - Confirm it produces a valid (but low) baseline score

**Output:**
- Seed harness file(s) in the output directory
- `.planning/autoeval/baseline-score.md` — baseline score from running seed against eval suite

### Phase 5: Program.md Generation

**Mode:** Autonomous by default (interactive if user opted in).

**Flow:**
1. Load all prior context (problem, metric, eval strategy, baseline score)
2. Generate `program.md` containing:
   - **Goal:** what the meta-agent is trying to achieve, in plain language
   - **Edit surface:** which files can be modified, which are fixed, with file paths
   - **Eval instructions:** exact commands to run the eval suite and interpret the score
   - **Keep/discard rules:** "if score >= previous best, commit and continue; otherwise revert"
   - **Domain-specific guidance:** tailored hints based on loop type and problem
   - **Constraints:** what the meta-agent must NOT do (don't modify eval suite, don't change fixed infrastructure)
   - **Iteration protocol:** the exact change -> run -> score -> keep/discard -> repeat loop as step-by-step instructions
   - **The "NEVER STOP" directive:** autonomous loop continuation
3. Invoke Socrates to review `program.md` for:
   - Ambiguity that could cause the meta-agent to go off-rails
   - Missing constraints that could let it game the eval
   - Unclear scoring interpretation

**Output:**
- `program.md` in the output directory

### Phase 6: Loop Setup

**Mode:** Autonomous by default (interactive if user opted in).

**Flow:**
1. Generate environment setup:
   - Dependency manifest (`pyproject.toml`, `package.json`, etc.)
   - Dockerfile if the problem benefits from isolation
   - `.gitignore` for generated artifacts
2. Initialize git repo in the output directory (if not already one)
3. Commit all generated files as the baseline
4. Run full end-to-end verification:
   - Seed harness executes
   - Eval suite scores it
   - Score matches baseline from Phase 4
5. Present kickoff command:
   ```
   cd <output-dir>
   claude "$(cat program.md)"
   ```
6. Brief the user:
   - How to monitor progress (check git log for iterations)
   - How to stop the loop
   - How to manually steer (edit `program.md` constraints)

**Output:**
- Environment files (dependency manifest, Dockerfile, .gitignore)
- Git commit with full baseline
- Kickoff instructions

## Artifacts Summary

A completed autoeval run produces:

| Artifact | Description |
|---|---|
| `program.md` | Meta-agent directive with goal, edit surface, eval instructions, keep/discard rules |
| Seed harness file(s) | Minimal but functional baseline implementation with marked edit surface |
| `evals/` | Eval cases, scoring functions, runner script, coverage documentation |
| Environment files | Dependency manifest, Dockerfile (optional), .gitignore |
| `.planning/autoeval/` | Phase state files for resume capability |

## Exit Ramp Behavior

If autoeval determines the problem is not a good candidate for an autonomous optimization loop, it:
1. Explains why the problem doesn't benefit from the loop pattern
2. Suggests what the user could do instead
3. Stops — autoeval only builds loops, it does not offer to build the solution directly

## Socrates Integration Points

Socrates (dialectic reasoning skill) is invoked at three points:
1. **Phase 1** — evaluate whether the problem is actually an optimization problem; evaluate simple vs. composed loop architecture
2. **Phase 2** — stress-test candidate metrics for gameability, signal strength, and cost
3. **Phase 5** — review `program.md` for ambiguity, missing constraints, and unclear scoring

## File Structure (Skill Package)

This repo is the skill package. Structure:

```
skills/
  autoeval/
    autoeval.md                   # orchestrator skill
    problem-definition.md         # Phase 1
    metric-design.md              # Phase 2
    eval-suite.md                 # Phase 3
    harness-scaffold.md           # Phase 4
    program-md.md                 # Phase 5
    loop-setup.md                 # Phase 6
    references/
      loop-types.md               # 12 loop type taxonomy
```
