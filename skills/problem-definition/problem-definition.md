---
name: problem-definition
description: "Phase 1 of autoeval -- interactive discovery to clarify the optimization problem, classify the loop type, and identify exit ramps. Use when autoeval orchestrator routes to Phase 1, or when user invokes directly."
---

# Phase 1: Problem Definition

Interactive discovery session that clarifies the user's optimization problem, classifies it against the loop type taxonomy, and determines whether it's actually suited for an autonomous optimization loop.

<HARD-GATE>
This phase MUST be interactive. Do not skip questions or assume answers. Each question is one message -- wait for the user's response before continuing.
</HARD-GATE>

## Prerequisites

- Read `.planning/autoeval/state.md` to confirm we're in Phase 1
- If no state exists, this was invoked directly -- create initial state first
- Load the user's problem description from the invocation args or ask for it

## Process

### Step 1: Understand the Problem

Ask the following questions **one at a time**. Adapt based on answers -- skip questions that have already been answered. Use multiple choice when possible.

1. **What are you building?** -- Get a concrete description, not an abstract goal
2. **What are the inputs and outputs?** -- What goes in, what comes out, in what format
3. **What does "good" look like in plain language?** -- How would a human judge the quality of the output
4. **What constraints exist?** -- Hardware, latency, cost, dependencies, API limits, time budget per iteration

### Step 2: Classify the Loop Type

Read the loop type taxonomy from `skills/_shared/loop-types.md`.

Based on the user's answers, identify which loop type(s) fit:

1. Present your classification with reasoning: "This looks like a **[Loop Type]** because [reason]"
2. If the problem could map to multiple types, explain the distinction and let the user choose
3. If the problem suggests a composed loop (primary + nested), present both options:
   - **Simple:** Single loop with [primary type] -- faster to set up, easier to debug
   - **Composed:** [Primary type] wrapping [secondary type] -- higher ceiling, more complex

   Use the Socrates skill (if available) to help evaluate the tradeoffs between simple and composed. Let the user decide.

### Step 3: Exit Ramp Check

Evaluate whether this problem is actually suited for an autonomous optimization loop. Use the Socrates skill (if available) to stress-test this.

**Good candidates have:**
- A broad problem space where many approaches could work (not one obvious solution)
- An output that can be automatically scored (not requiring human judgment every iteration)
- An edit surface where small changes can produce measurable differences
- Enough iteration headroom -- the problem benefits from 10+ experiments, not just 1-2

**Bad candidates (exit ramp):**
- Well-defined workflows with clear requirements ("just build it")
- Problems where the solution is obvious but needs implementation time
- Problems requiring human judgment on every output
- Problems with no automatable scoring function

**If exiting:**

> "This isn't a strong candidate for an autonomous optimization loop because [specific reason]. It's a [characterization] problem -- [suggestion for what to do instead, e.g., 'you could ask Claude Code to build it directly']. Autoeval only scaffolds optimization loops, so I'll stop here."

**Do not offer to build the solution directly. Stop.**

Update `state.md` to `phase: exit` and return control to the orchestrator.

### Step 4: Write Problem Definition

Write `.planning/autoeval/problem.md`:

```markdown
# Problem Definition

## Summary
[2-3 sentence problem description]

## Inputs
[What goes into the system -- format, sources, constraints]

## Outputs
[What comes out -- format, quality expectations]

## Success Criteria
[What "good" looks like in plain language]

## Constraints
[Hardware, latency, cost, dependencies, time budget]

## Loop Type
**Primary:** [Loop type name]
**Reasoning:** [Why this classification]
**Composed:** [Secondary loop type, if any, or "None"]

## Output Directory
[Resolved path from orchestrator]
```

### Step 5: Advance State

Update `.planning/autoeval/state.md` to `phase: 2`.

Tell the user: "Problem defined. Moving to metric design -- this is where we figure out how to automatically score your system's output."

Return control to the orchestrator to invoke Phase 2.
