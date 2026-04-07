# autoeval — Autonomous Optimization Loop Scaffolder

> **ALPHA — DO NOT USE.** Currently testing loop types with real problems. Example executions will be added for each of the 12 types. Moves out of alpha once all are validated.

A Claude Code skill that transforms an optimization problem into a fully scaffolded autonomous experiment loop. Describe what you want to optimize, and autoeval builds the eval suite, seed implementation, monitoring dashboard, and loop runner — everything you need to kick off an overnight experiment.

## Install

```
/plugin marketplace add abdielou/autoeval
/plugin install autoeval@abdielou-autoeval
```

## Use

```
/autoeval optimize my bin packing heuristic for minimum waste
/autoeval improve my classifier's accuracy on the test suite
/autoeval --auto tune my prompt to maximize extraction accuracy
```

autoeval walks you through defining the problem, designing the scoring function, and building the eval suite. Then it scaffolds the loop and tells you how to run it.

The `--auto` flag makes the later phases run autonomously after the interactive metric design is locked in.

## What it produces

| File | What it does |
|------|-------------|
| `program.md` | Meta-agent directive — goal, edit surface, iteration protocol, constraints |
| `evals/` | Test cases, scoring functions, eval runner |
| `run-loop.py` | Launches claude sessions with auto-restart and timeout |
| `monitor.py` | Live dashboard at localhost:8080 |
| `steering.md` | Guide the agent mid-run without stopping the loop |
| Seed harness | Minimal baseline implementation with marked edit surface |

## Run the loop

**Terminal 1 — start the loop:**

```bash
cd <output-dir>
python run-loop.py
```

Sessions auto-restart every N iterations with fresh context. Ctrl+C once kills the current session; Ctrl+C again within 3 seconds stops the loop entirely.

**Terminal 2 — monitor progress:**

```bash
cd <output-dir>
python monitor.py
```

Live chart showing score over iterations, component scores (toggleable), failed experiments as red X markers, hypothesis on hover, and summary stats. Auto-refreshes every 30 seconds.

## Dual-model architecture

The loop uses two models to balance cost and quality:

- **Runner** (sonnet) — handles the iteration cycle: editing code, running evals, committing
- **Deep reasoning** (opus) — called one-shot for hypothesis generation and exploration rounds

Opus-level creativity for the "think hard" steps at ~10% of the cost.

## Steering

Guide the loop agent mid-run without stopping it. Append entries to `steering.md` tagged with the commit hash they apply after:

```markdown
## after 7f5ad6f
Stop trying to optimize the greedy heuristic. The biggest gain is switching
to a scoring-based approach. Look at the best-fit-decreasing literature.

## after a1b2c3d
The classifier is plateauing at 96.2%. The bottleneck is feature engineering,
not model choice. Try polynomial features on columns 3-7.
```

The agent reads this before each iteration and follows it. Old entries are automatically irrelevant once HEAD moves past them.

For permanent changes, edit `program.md` — takes effect at the next session restart.

## Learning from failed experiments

Most optimization loops silently discard failed attempts. autoeval preserves them.

When an experiment fails, before reverting the code, the agent saves the full diff, hypothesis, score breakdown, and failure analysis to `failed_experiments/`. The monitoring dashboard shows a **Failed Experiments** table with the last 20 failures. Before each new hypothesis, the deep reasoning model sees past failures and avoids repeating them.

Failed iterations become institutional knowledge the loop builds up over time.

## Loop types

autoeval classifies your problem against 12 optimization loop types:

| | | | |
|---|---|---|---|
| Training | Agent Harness | Generative Output | Algorithm Performance |
| Retrieval & Ranking | Pipeline Optimization | Simulation Calibration | Strategy & Decision |
| Adversarial | Data Curation | Control Systems | Interface Optimization |

Each type defines what the agent edits and how it's scored. See [loop-types.md](skills/_shared/loop-types.md) for details.

## Eval integrity

The eval suite goes through integrity validation before the loop starts:

- **Self-referential detection** — catches evals that "grade their own homework"
- **Discriminating power** — verifies the eval can tell good output from bad
- **Ceiling reachability** — confirms the theoretical best score is actually achievable
- **User review** — plain-language walkthrough of what's scored, what's not, and how the agent could game it

## Inspired by

[autoresearch](https://github.com/karpathy/autoresearch) | [autoagent](https://github.com/kevinrgu/autoagent) | [AIDE](https://github.com/WecoAI/aideml) | [OpenEvolve](https://github.com/algorithmicsuperintelligence/openevolve) | [AI-Scientist](https://github.com/SakanaAI/AI-Scientist)

## License

MIT
