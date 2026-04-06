# autoeval — Autonomous Optimization Loop Scaffolder

A Claude Code skill that transforms a vague optimization problem into a fully scaffolded, runnable autonomous experiment loop — bridging the gap between "I have an idea" and "I have an autonomous experiment running overnight."

## What it does

The `/autoeval` command guides you through defining your optimization problem, designing an automatic scoring function, and building a complete eval suite — then scaffolds everything the meta-agent needs to run overnight: a `program.md` directive, seed implementation, and kickoff command.

### Key features

- **Problem classification** — maps your problem against a 12-type loop taxonomy (Training, Agent Harness, Generative Output, Algorithm Performance, and 8 more)
- **Metric design** — interactive exploration of scoring functions with stress-testing for gameability, signal strength, and cost
- **Eval suite building** — the crown jewel. Coverage strategy, test cases, scoring functions, sanity checks, and gap documentation
- **Edit surface marking** — clearly separates what the meta-agent can modify from fixed infrastructure
- **program.md generation** — complete meta-agent directive with iteration protocol, constraints, and domain guidance
- **Exit ramp** — identifies problems that aren't suited for optimization loops and says so, rather than building a bad loop
- **Socrates integration** — dialectic stress-testing at key decision points (optional, via [zetaminusone/socrates](https://github.com/ZetaMinusOne/socrates))

### Inspired by

- **[autoresearch](https://github.com/karpathy/autoresearch)** — autonomous ML research (Andrej Karpathy, 2025)
- **[autoagent](https://github.com/kevinrgu/autoagent)** — autonomous agent harness engineering (Kevin Gu, 2025)
- **[AIDE](https://github.com/WecoAI/aideml)** — AI-driven ML experiment iteration (Weco AI)
- **[OpenEvolve](https://github.com/algorithmicsuperintelligence/openevolve)** — open-source AlphaEvolve, evolutionary code optimization
- **[AI-Scientist](https://github.com/SakanaAI/AI-Scientist)** — fully automated open-ended scientific discovery (Sakana AI)

All share the same core loop: change → run → score → keep/discard → repeat. autoeval helps you set up that loop for any problem.

## Installation

### Plugin Marketplace (recommended)

**Interactive:**

```
/plugin
```

Go to the Marketplaces tab, add `abdielou/autoeval`, then switch to the Discover tab and install.

**CLI:**

```
/plugin marketplace add abdielou/autoeval
/plugin install autoeval@abdielou-autoeval
```

### Manual (git clone)

**User-level** (available in all projects):

```bash
git clone https://github.com/abdielou/autoeval.git ~/.claude/skills/autoeval
```

**Project-level** (available in one project):

```bash
git clone https://github.com/abdielou/autoeval.git .claude/skills/autoeval
```

### Local development

```bash
claude --plugin-dir ./path/to/autoeval
```

## Usage

```
/autoeval <describe your optimization problem>
/autoeval --auto <describe your optimization problem>
```

**Examples:**

```
/autoeval optimize my sorting algorithm for speed on large datasets
/autoeval improve my classifier's accuracy on the test suite
/autoeval --auto tune my prompt to maximize extraction accuracy
```

The `--auto` flag makes Phases 3-6 run autonomously after the interactive metric design is locked in.

## How it works

autoeval runs through 6 phases:

1. **Problem Definition** (interactive) — clarify what you're building, classify the loop type, exit if it's not an optimization problem
2. **Metric Design** (interactive) — find an automatic scoring function, stress-test it for gameability and signal strength
3. **Eval Suite** (interactive) — build test cases, scoring functions, and coverage strategy
4. **Harness Scaffolding** — generate a minimal seed implementation with marked edit surface
5. **Program.md Generation** — write the meta-agent directive with iteration protocol and constraints
6. **Loop Setup** — wire everything together, verify baseline, provide kickoff command

Phases 1-2 are always interactive. Phases 3-6 are interactive by default, or autonomous with `--auto`.

### What it produces

| Artifact | Description |
|----------|-------------|
| `program.md` | Meta-agent directive — goal, edit surface, eval commands, keep/discard rules |
| Seed harness | Minimal baseline implementation with clearly marked edit surface |
| `evals/` | Test cases, scoring functions, runner script, coverage documentation |
| Environment files | Dependencies, Dockerfile (optional), .gitignore |

### Kicking off the experiment

After autoeval completes:

```bash
claude --dangerously-skip-permissions --append-system-prompt-file program.md "Start the optimization loop."
```

The meta-agent reads `program.md` and begins the autonomous loop — modifying the seed implementation, scoring each change, keeping improvements, and repeating indefinitely.

## Loop type taxonomy

autoeval classifies problems against 12 loop types:

| # | Loop Type | Edit Surface | Scoring Function |
|---|-----------|-------------|-----------------|
| 1 | Training | Model/training code | Validation loss, accuracy |
| 2 | Agent Harness | Prompt, tools, orchestration | Task pass rate, benchmark |
| 3 | Generative Output | Synthesis algorithms | Reference similarity, LLM-as-judge |
| 4 | Algorithm Performance | Implementation code | Speed, memory, accuracy |
| 5 | Retrieval & Ranking | Chunking, indexing, re-ranking | Recall, precision, MRR |
| 6 | Pipeline Optimization | Processing stages, filters | Throughput, quality, cost |
| 7 | Simulation Calibration | Sim parameters, physics models | Fit to real-world data |
| 8 | Strategy & Decision | Decision rules, heuristics | Win rate, expected value |
| 9 | Adversarial | Attack/defense mechanisms | Vulnerability rate, resistance |
| 10 | Data Curation | Dataset composition, filtering | Downstream model performance |
| 11 | Control Systems | Controller params, architecture | Tracking error, stability |
| 12 | Interface Optimization | UI layout, interaction flows | Task completion, engagement |

## Repository structure

```
autoeval/
├── .claude-plugin/
│   ├── plugin.json            # Plugin metadata and command registration
│   └── marketplace.json       # Marketplace distribution config
├── skills/
│   ├── autoeval/
│   │   └── autoeval.md        # Orchestrator — entry point, state, routing
│   ├── problem-definition/
│   │   └── problem-definition.md  # Phase 1 — discovery, classification, exit ramp
│   ├── metric-design/
│   │   └── metric-design.md   # Phase 2 — scoring function design
│   ├── eval-suite/
│   │   └── eval-suite.md      # Phase 3 — eval cases and scoring
│   ├── harness-scaffold/
│   │   └── harness-scaffold.md  # Phase 4 — seed implementation
│   ├── program-md/
│   │   └── program-md.md      # Phase 5 — meta-agent directive
│   ├── loop-setup/
│   │   └── loop-setup.md      # Phase 6 — environment and kickoff
│   └── _shared/
│       ├── loop-types.md      # 12 loop type taxonomy
│       └── state-format.md    # State file format spec
├── .gitignore
└── README.md
```

## License

MIT
