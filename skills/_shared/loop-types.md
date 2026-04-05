# Autonomous Optimization Loop Types

A taxonomy of 12 meta-level patterns where a meta-agent autonomously iterates on a system to improve a measurable score.

Every loop shares the same abstract structure: **change -> run -> score -> keep/discard -> repeat**

Two axes distinguish loop types:
- **Edit surface** -- what the meta-agent is allowed to modify
- **Scoring function** -- how the result is automatically evaluated

---

## 1. Training Loop

**Edit surface:** Model architecture, training code, hyperparameters, data loading, optimization strategy.
**Scoring function:** Validation loss, accuracy, bits-per-byte, or other training metrics.

The meta-agent modifies a training script and measures whether the model got better. Autoresearch (Karpathy, 2025) is the canonical example.

## 2. Agent Harness Loop

**Edit surface:** System prompt, tool definitions, orchestration logic, sub-agent architecture, routing, verification steps.
**Scoring function:** Task pass rate, benchmark score, cost efficiency.

The meta-agent improves an AI agent's scaffolding. Autoagent (Kevin Gu, 2025) is the canonical example. Subsumes prompt-only optimization as a special case.

## 3. Generative Output Loop

**Edit surface:** Generation algorithms, synthesis parameters, transformation pipelines, rendering logic.
**Scoring function:** Similarity to reference outputs (spectral matching, perceptual metrics, structural similarity), LLM-as-judge, or composite quality scores.

Covers any loop where the system produces an artifact -- audio, images, video, text, code -- and is scored against quality targets. Includes DSP/signal synthesis, procedural content generation, and style transfer.

## 4. Algorithm Performance Loop

**Edit surface:** Implementation code, data structures, algorithmic approach, parallelization strategy, compiler flags, system configuration.
**Scoring function:** Speed, memory usage, accuracy, scalability, or weighted tradeoffs.

The meta-agent optimizes how something runs. Includes algorithmic optimization, hyperparameter search, and compiler/codegen optimization.

## 5. Retrieval and Ranking Loop

**Edit surface:** Chunking strategy, embedding model/configuration, indexing approach, retrieval logic, re-ranking rules, context assembly.
**Scoring function:** Recall, precision, MRR, NDCG, downstream task accuracy, answer quality.

The meta-agent optimizes how information is found and surfaced. RAG systems are the most common instance.

## 6. Pipeline Optimization Loop

**Edit surface:** Processing stages, transformation logic, filtering rules, data flow architecture, stage ordering.
**Scoring function:** Output quality, throughput, latency, error rate, cost.

The meta-agent improves a multi-stage data processing pipeline. Includes ETL, media processing, data cleaning, and feature engineering.

## 7. Simulation Calibration Loop

**Edit surface:** Simulation parameters, physics models, environment rules, agent behavior models.
**Scoring function:** Fit to real-world observed data (RMSE, correlation, distribution matching).

The meta-agent tunes a simulation to match reality. Includes physics, financial models, climate, traffic, and digital twins.

## 8. Strategy and Decision Loop

**Edit surface:** Decision rules, heuristics, evaluation functions, planning algorithms, game trees, resource allocation logic.
**Scoring function:** Win rate, expected value, regret, distance from known-optimal solutions.

The meta-agent improves a decision-making system. Includes game-playing, scheduling, trading strategies, and resource allocation.

## 9. Adversarial Loop

**Edit surface:** Attack vectors, defense mechanisms, detection rules, filtering logic, hardening measures.
**Scoring function:** Vulnerability discovery rate, resistance to attacks, false positive/negative rates.

The meta-agent improves either an attacker or defender. Includes security testing, robustness evaluation, jailbreak resistance, and content filtering.

## 10. Data Curation Loop

**Edit surface:** Dataset composition, filtering criteria, sampling strategy, augmentation methods, labeling rules, synthetic data generation.
**Scoring function:** Downstream model performance, data quality metrics, coverage, diversity.

The meta-agent optimizes the data itself. Score measured indirectly by training/evaluating a downstream system on the curated data.

## 11. Control Systems Loop

**Edit surface:** Controller parameters (PID gains, MPC horizons), control architecture, sensor fusion logic, actuator mapping.
**Scoring function:** Tracking error, stability margins, settling time, energy efficiency, safety constraint satisfaction.

The meta-agent tunes a control system -- robotics, industrial automation, autonomous vehicles, HVAC, power grid.

## 12. Interface Optimization Loop

**Edit surface:** UI layout, interaction flows, content presentation, notification logic, onboarding sequences.
**Scoring function:** Task completion rate, engagement metrics, conversion, time-on-task, error rate.

The meta-agent optimizes how humans interact with a system. Extends traditional A/B testing into autonomous iteration.

---

## Properties

**Composability:** Loop types can nest. An outer agent harness loop might contain an inner prompt optimization sub-loop.

**Edit surface width:** Narrower surfaces converge faster but have lower ceilings. Wider surfaces explore more but need more experiments.

**Scoring function reliability:** Deterministic/cheap scores (unit tests, loss) vs. noisy/expensive (LLM-as-judge). Loop effectiveness depends heavily on scoring quality.

**Convergence characteristics:** Some loops hill-climb smoothly (parameter tuning). Others have discontinuous jumps (adding a new tool). The meta-agent's exploration strategy should match the landscape.
