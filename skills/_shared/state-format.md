# autoeval State Format

All state persists in `.planning/autoeval/` in the user's working directory.

## state.md

```yaml
---
phase: 1          # Current phase (1-6), "complete", or "exit"
auto: false       # Whether --auto was passed
interactive: true # Whether user chose step-through after Phase 2
output_dir: "."   # Resolved output directory path
started: "2026-04-05"
---
```

## Phase Output Files

| Phase | File | Contents |
|-------|------|----------|
| 1 | `problem.md` | Problem summary, I/O, success criteria, constraints, loop type, output dir |
| 2 | `metric.md` | Scoring function spec, components, weights, floor/ceiling, risks |
| 3 | `eval-strategy.md` | Coverage dimensions, reference data sources, testability assessment |
| 4 | `baseline-score.md` | Seed harness score against eval suite |
| 5 | -- | Output is `program.md` in the output directory |
| 6 | -- | Output is environment files in the output directory |

## Resume Protocol

On re-invocation, the orchestrator:
1. Reads `state.md` to determine current phase
2. Checks if the current phase's output file exists (phase may be partially complete)
3. Routes to the appropriate phase skill
4. If no state exists, this is a new run -- start Phase 1
